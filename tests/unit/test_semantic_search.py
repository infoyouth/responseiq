"""tests/unit/test_semantic_search.py — P-F2 Semantic Incident Deduplication"""

from __future__ import annotations

import json
import math
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from responseiq.app import app
from responseiq.db import get_session
from responseiq.models.base import Incident, IncidentEmbedding, Log
from responseiq.services.semantic_search_service import (
    SemanticSearchService,
    _cosine_similarity,
)


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _make_vector(seed: float, dims: int = 8) -> list[float]:
    """Small reproducible unit vector for tests (not 1536-dim for speed)."""
    vec = [math.sin(seed * (i + 1)) for i in range(dims)]
    mag = math.sqrt(sum(x * x for x in vec))
    return [x / mag for x in vec]


def _seed_incident(session: Session, inc_id: int, description: str = "error") -> None:
    log = Log(id=inc_id, message=description, severity="high")
    session.add(log)
    session.add(Incident(id=inc_id, log_id=inc_id, severity="high", description=description, source="ai"))
    session.commit()


def _store_embedding(session: Session, incident_id: int, vector: list[float]) -> None:
    session.add(
        IncidentEmbedding(
            incident_id=incident_id,
            log_id=incident_id,
            embedding_json=json.dumps(vector),
            model="text-embedding-3-small",
        )
    )
    session.commit()


# ── unit: _cosine_similarity ─────────────────────────────────────────────────


def test_cosine_similarity_identical_vectors():
    v = [1.0, 0.0, 0.0]
    assert _cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector_returns_zero():
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.5]) == 0.0


def test_cosine_similarity_opposite_vectors():
    score = _cosine_similarity([1.0, 0.0], [-1.0, 0.0])
    assert score == pytest.approx(-1.0)


# ── unit: SemanticSearchService.generate_and_store ────────────────────────────


def test_generate_and_store_skips_when_no_api_key(session: Session):
    """When OPENAI_API_KEY is absent, returns None without error."""
    _seed_incident(session, 1)
    svc = SemanticSearchService(session)
    with patch("responseiq.services.semantic_search_service._get_openai_client", return_value=None):
        result = svc.generate_and_store(1)
    assert result is None


def test_generate_and_store_persists_embedding(session: Session):
    _seed_incident(session, 2, "DatabaseConnectionError: pool exhausted")
    fake_vector = _make_vector(0.42)

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=fake_vector)]
    mock_client.embeddings.create.return_value = mock_response

    svc = SemanticSearchService(session)
    with patch("responseiq.services.semantic_search_service._get_openai_client", return_value=mock_client):
        emb = svc.generate_and_store(2)

    assert emb is not None
    assert emb.incident_id == 2
    stored_vector = json.loads(emb.embedding_json)
    assert stored_vector == pytest.approx(fake_vector)


def test_generate_and_store_is_idempotent(session: Session):
    """Calling twice for the same incident does not create duplicate rows."""
    _seed_incident(session, 3)
    _store_embedding(session, 3, _make_vector(0.1))

    svc = SemanticSearchService(session)
    mock_client = MagicMock()
    with patch("responseiq.services.semantic_search_service._get_openai_client", return_value=mock_client):
        result = svc.generate_and_store(3)

    # OpenAI should NOT be called again
    mock_client.embeddings.create.assert_not_called()
    assert result is not None


def test_generate_and_store_returns_none_for_missing_incident(session: Session):
    svc = SemanticSearchService(session)
    with patch("responseiq.services.semantic_search_service._get_openai_client", return_value=MagicMock()):
        result = svc.generate_and_store(9999)
    assert result is None


# ── unit: SemanticSearchService.find_similar ─────────────────────────────────


def test_find_similar_returns_high_similarity_matches(session: Session):
    base_vec = _make_vector(1.0)
    near_vec = [x + 0.001 for x in base_vec]  # very close
    # normalise near_vec
    mag = math.sqrt(sum(x * x for x in near_vec))
    near_vec = [x / mag for x in near_vec]

    _seed_incident(session, 10)
    _seed_incident(session, 11)
    _store_embedding(session, 10, base_vec)
    _store_embedding(session, 11, near_vec)

    svc = SemanticSearchService(session)
    result = svc.find_similar(10, threshold=0.90)
    assert len(result.results) >= 1
    assert result.results[0].incident_id == 11


def test_find_similar_excludes_self(session: Session):
    vec = _make_vector(2.0)
    _seed_incident(session, 20)
    _store_embedding(session, 20, vec)

    svc = SemanticSearchService(session)
    result = svc.find_similar(20, threshold=0.0)  # threshold 0 → everything
    ids = [r.incident_id for r in result.results]
    assert 20 not in ids


def test_find_similar_threshold_filters_low_scores(session: Session):
    _seed_incident(session, 30)
    _seed_incident(session, 31)
    _store_embedding(session, 30, _make_vector(1.0))
    _store_embedding(session, 31, _make_vector(5.0))  # very different seed angle

    svc = SemanticSearchService(session)
    result = svc.find_similar(30, threshold=0.999)
    # near-impossible to hit 0.999 with different seed angles
    assert len(result.results) == 0


def test_find_similar_no_embedding_returns_empty(session: Session):
    _seed_incident(session, 40)
    svc = SemanticSearchService(session)
    result = svc.find_similar(40)
    assert result.results == []


def test_has_duplicate_returns_true_when_similar_exists(session: Session):
    base_vec = _make_vector(3.0)
    near_vec_raw = [x + 0.0001 for x in base_vec]
    mag = math.sqrt(sum(x * x for x in near_vec_raw))
    near_vec = [x / mag for x in near_vec_raw]

    _seed_incident(session, 50)
    _seed_incident(session, 51)
    _store_embedding(session, 50, base_vec)
    _store_embedding(session, 51, near_vec)

    svc = SemanticSearchService(session)
    assert svc.has_duplicate(50, threshold=0.90) is True


# ── integration: GET /api/v1/incidents/{id}/similar ──────────────────────────


def test_api_similar_endpoint_returns_empty_when_no_embeddings(client: TestClient, session: Session):
    _seed_incident(session, 100)
    resp = client.get("/api/v1/incidents/100/similar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []
    assert data["query_incident_id"] == 100


def test_api_similar_endpoint_returns_matches(client: TestClient, session: Session):
    base_vec = _make_vector(4.0, dims=8)
    near_vec_raw = [x + 0.0005 for x in base_vec]
    mag = math.sqrt(sum(x * x for x in near_vec_raw))
    near_vec = [x / mag for x in near_vec_raw]

    _seed_incident(session, 200)
    _seed_incident(session, 201)
    _store_embedding(session, 200, base_vec)
    _store_embedding(session, 201, near_vec)

    resp = client.get("/api/v1/incidents/200/similar?threshold=0.9")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) >= 1
    assert data["results"][0]["incident_id"] == 201


def test_api_similar_threshold_param_respected(client: TestClient, session: Session):
    _seed_incident(session, 300)
    _seed_incident(session, 301)
    _store_embedding(session, 300, _make_vector(6.0, dims=8))
    _store_embedding(session, 301, _make_vector(7.0, dims=8))

    # Very high threshold — expect no results for vectors with different seeds
    resp = client.get("/api/v1/incidents/300/similar?threshold=0.9999")
    assert resp.status_code == 200
    assert resp.json()["results"] == []
