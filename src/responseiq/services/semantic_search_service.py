"""
src/responseiq/services/semantic_search_service.py

Semantic incident deduplication via text embeddings (P-F2).

Architecture
────────────
1. On new incident creation the ARQ worker calls
   ``SemanticSearchService.generate_and_store(incident_id)``.
   This generates a 1536-dim embedding for the incident's log message
   using ``text-embedding-3-small`` (cheap, fast) and stores it in the
   ``IncidentEmbedding`` table as a JSON-encoded float array.

2. ``find_similar(incident_id, threshold)`` queries similar incidents.

   Two execution paths (auto-detected at runtime):
     a. **pgvector path** (Postgres + pgvector extension installed):
        Uses ``embedding_json::vector <=> query::vector`` SQL expression
        (cosine distance, O(log n) with an index).  No schema change
        required — Postgres casts the text JSON blob to VECTOR inline.
     b. **Python fallback** (SQLite / Postgres without pgvector):
        Loads all embeddings and computes cosine similarity in pure Python.
        Correct but O(n) — fine for ≤ 10k incidents.

3. ``GET /api/v1/incidents/{id}/similar`` calls ``find_similar``.

pgvector upgrade path
─────────────────────
The JSON blob column is SQLite + Postgres compatible today.
To add a native VECTOR(1536) column (optional performance boost):
  - Create Alembic migration: ``ALTER TABLE incidentembedding ADD COLUMN pgvec VECTOR(1536)``
  - Backfill: ``UPDATE incidentembedding SET pgvec = embedding_json::vector``
  - Add ``ivfflat`` index for ANN: ``CREATE INDEX ON incidentembedding USING ivfflat (pgvec vector_cosine_ops)``
  - All callers remain unchanged (the cast path already works today).

Configuration
─────────────
    OPENAI_API_KEY  — required for embedding generation.
                      When absent, ``generate_and_store`` silently no-ops.
"""

from __future__ import annotations

import json
import math
from typing import List, Optional

from sqlmodel import Session, select

from responseiq.config.settings import settings
from responseiq.models.base import Incident, IncidentEmbedding
from responseiq.schemas.semantic import SimilarIncidentOut, SimilaritySearchResult
from responseiq.utils.logger import logger

_EMBEDDING_MODEL = "text-embedding-3-small"
_EMBEDDING_DIMS = 1536


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Pure-Python cosine similarity. O(n) — fine for ≤ 10k incidents."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def _get_openai_client():  # type: ignore[return]
    """Return a sync OpenAI client or None when not configured."""
    api_key = settings.openai_api_key or ""
    if not api_key:
        return None
    try:
        from openai import OpenAI  # type: ignore[import-untyped]

        return OpenAI(api_key=api_key)
    except Exception as exc:  # pragma: no cover
        logger.warning("SemanticSearch: OpenAI client init failed: %s", exc)
        return None


def _is_pgvector_available(session: Session) -> bool:
    """Return True when connected to Postgres with the pgvector extension installed.

    pgvector enables O(log n) ANN similarity search via the ``<=>`` cosine-
    distance operator and an optional ``ivfflat`` index.  When not available
    the pure-Python O(n) fallback is used transparently.
    """
    try:
        from sqlalchemy import text

        dialect = session.bind.dialect.name  # type: ignore[union-attr]
        if not dialect.startswith("postgresql"):
            return False
        result = session.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
        return result is not None
    except Exception:
        return False


class SemanticSearchService:
    """Generates, stores, and queries incident embeddings."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── write ────────────────────────────────────────────────────────────

    def generate_and_store(self, incident_id: int) -> Optional[IncidentEmbedding]:
        """
        Generate an embedding for *incident_id* and persist it.

        Idempotent — if an embedding already exists it is returned unchanged.
        Returns ``None`` when OpenAI is unavailable or the incident does not
        exist.
        """
        # idempotency guard
        existing = self._session.exec(
            select(IncidentEmbedding).where(IncidentEmbedding.incident_id == incident_id)
        ).first()
        if existing:
            return existing

        incident = self._session.get(Incident, incident_id)
        if not incident:
            logger.warning("SemanticSearch: incident %d not found", incident_id)
            return None

        text = _build_embedding_text(incident)
        client = _get_openai_client()
        if client is None:
            logger.debug(
                "SemanticSearch: OpenAI not configured — skipping embedding for incident %d",
                incident_id,
            )
            return None

        try:
            response = client.embeddings.create(model=_EMBEDDING_MODEL, input=text)
            vector: List[float] = response.data[0].embedding
        except Exception as exc:
            logger.warning(
                "SemanticSearch: embedding generation failed for incident %d: %s",
                incident_id,
                exc,
            )
            return None

        embedding = IncidentEmbedding(
            incident_id=incident_id,
            log_id=incident.log_id,
            embedding_json=json.dumps(vector),
            model=_EMBEDDING_MODEL,
        )
        self._session.add(embedding)
        self._session.commit()
        self._session.refresh(embedding)
        logger.info(
            "SemanticSearch: embedding stored",
            incident_id=incident_id,
            model=_EMBEDDING_MODEL,
        )
        return embedding

    # ── read ─────────────────────────────────────────────────────────────

    def find_similar(
        self,
        incident_id: int,
        threshold: float = 0.92,
        limit: int = 10,
    ) -> SimilaritySearchResult:
        """
        Return incidents with cosine similarity ≥ *threshold* to *incident_id*.

        Auto-selects execution path:
          - pgvector path (Postgres + pgvector): O(log n) ANN via ``<=>`` operator.
          - Pure-Python fallback (SQLite / no pgvector): O(n) cosine loop.

        Results are sorted by similarity descending.  The query incident
        itself is excluded from results.
        """
        query_emb = self._session.exec(
            select(IncidentEmbedding).where(IncidentEmbedding.incident_id == incident_id)
        ).first()

        if query_emb is None:
            return SimilaritySearchResult(
                query_incident_id=incident_id,
                threshold=threshold,
                results=[],
            )

        query_vector: List[float] = json.loads(query_emb.embedding_json)

        # pgvector fast path — O(log n) with ivfflat index
        if _is_pgvector_available(self._session):
            logger.debug("SemanticSearch: using pgvector ANN path for incident %d", incident_id)
            return self._find_similar_pgvector(incident_id, query_vector, threshold, limit)

        # Pure-Python fallback — O(n), acceptable for ≤ 10k incidents
        logger.debug("SemanticSearch: using pure-Python cosine path for incident %d", incident_id)
        return self._find_similar_python(incident_id, query_vector, threshold, limit)

    def _find_similar_pgvector(
        self,
        incident_id: int,
        query_vector: List[float],
        threshold: float,
        limit: int,
    ) -> SimilaritySearchResult:
        """ANN similarity search via pgvector ``<=>`` cosine-distance operator.

        The ``embedding_json`` TEXT column is cast inline to ``vector`` — no
        schema migration required.  Cosine distance = 1 - cosine_similarity,
        so ``distance <= (1 - threshold)`` is equivalent to ``similarity >= threshold``.
        """
        from sqlalchemy import text

        distance_threshold = 1.0 - threshold
        query_json = json.dumps(query_vector)

        sql = text("""
            SELECT incident_id,
                   log_id,
                   model,
                   embedding_json,
                   (embedding_json::vector <=> :query::vector) AS distance
            FROM   incidentembedding
            WHERE  incident_id != :qid
              AND  (embedding_json::vector <=> :query::vector) <= :dist_threshold
            ORDER  BY distance ASC
            LIMIT  :lim
        """)
        rows = self._session.execute(
            sql,
            {"query": query_json, "qid": incident_id, "dist_threshold": distance_threshold, "lim": limit},
        ).fetchall()

        results: List[SimilarIncidentOut] = []
        for row in rows:
            similarity_score = round(1.0 - float(row.distance), 4)
            incident = self._session.get(Incident, row.incident_id)
            results.append(
                SimilarIncidentOut(
                    incident_id=row.incident_id,
                    log_id=row.log_id,
                    similarity_score=similarity_score,
                    description=incident.description if incident else None,
                    severity=incident.severity if incident else None,
                    model=row.model,
                )
            )

        return SimilaritySearchResult(
            query_incident_id=incident_id,
            threshold=threshold,
            results=results,
        )

    def _find_similar_python(
        self,
        incident_id: int,
        query_vector: List[float],
        threshold: float,
        limit: int,
    ) -> SimilaritySearchResult:
        """Pure-Python cosine similarity — O(n) fallback for SQLite / no pgvector."""
        all_embeddings = self._session.exec(
            select(IncidentEmbedding).where(IncidentEmbedding.incident_id != incident_id)
        ).all()

        scored: List[tuple[float, IncidentEmbedding]] = []
        for emb in all_embeddings:
            try:
                vec = json.loads(emb.embedding_json)
                score = _cosine_similarity(query_vector, vec)
                if score >= threshold:
                    scored.append((score, emb))
            except Exception as exc:
                logger.debug("SemanticSearch: skipping malformed embedding id=%s: %s", emb.id, exc)
                continue

        scored.sort(key=lambda t: t[0], reverse=True)

        results: List[SimilarIncidentOut] = []
        for score, emb in scored[:limit]:
            incident = self._session.get(Incident, emb.incident_id)
            results.append(
                SimilarIncidentOut(
                    incident_id=emb.incident_id,
                    log_id=emb.log_id,
                    similarity_score=round(score, 4),
                    description=incident.description if incident else None,
                    severity=incident.severity if incident else None,
                    model=emb.model,
                )
            )

        return SimilaritySearchResult(
            query_incident_id=incident_id,
            threshold=threshold,
            results=results,
        )

    def has_duplicate(self, incident_id: int, threshold: float = 0.92) -> bool:
        """Return True when a near-duplicate already exists above *threshold*."""
        result = self.find_similar(incident_id, threshold=threshold, limit=1)
        return len(result.results) > 0


# ── helpers ────────────────────────────────────────────────────────────────


def _build_embedding_text(incident: Incident) -> str:
    """Compose a rich text string from incident fields for embedding."""
    parts = []
    if incident.severity:
        parts.append(f"severity:{incident.severity}")
    if incident.description:
        parts.append(incident.description)
    if incident.source:
        parts.append(f"source:{incident.source}")
    return " | ".join(parts) if parts else f"incident:{incident.id}"
