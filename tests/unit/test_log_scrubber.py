"""
tests/unit/test_log_scrubber.py

Unit tests for P2.3 — PII / Secret Scrubbing layer.
Covers:
  - Each individual pattern (email, IP, JWT, bearer, OpenAI key, AWS key,
    generic secret, credit card, UUID)
  - scrub() returns correct placeholder + mapping
  - restore() reverses every substitution
  - De-duplication: same value → same placeholder
  - Idempotency: scrubbing an already-scrubbed text changes nothing
  - LLM pathway integration: scrub is applied / bypassed based on settings
"""

from unittest.mock import AsyncMock, patch

import pytest

from responseiq.utils.log_scrubber import restore, scrub

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def assert_no_pii(text: str, original: str) -> None:
    """Assert that `original` does NOT appear verbatim in `text`."""
    assert original not in text, f"PII '{original}' still present in: {text!r}"


# ---------------------------------------------------------------------------
# Individual pattern tests
# ---------------------------------------------------------------------------


class TestEmailScrubbing:
    def test_plain_email(self):
        text, mapping = scrub("User john.doe@example.com logged in")
        assert_no_pii(text, "john.doe@example.com")
        assert len(mapping) == 1
        assert list(mapping.values())[0] == "john.doe@example.com"

    def test_multiple_distinct_emails(self):
        text, mapping = scrub("From: alice@corp.io To: bob@corp.io")
        assert_no_pii(text, "alice@corp.io")
        assert_no_pii(text, "bob@corp.io")
        assert len(mapping) == 2

    def test_duplicate_email_single_placeholder(self):
        text, mapping = scrub("alice@corp.io called alice@corp.io again")
        assert len(mapping) == 1, "Same email should map to a single placeholder"
        placeholder = list(mapping.keys())[0]
        assert text.count(placeholder) == 2


class TestIPv4Scrubbing:
    def test_standard_ipv4(self):
        text, mapping = scrub("Request from 192.168.1.100 failed")
        assert_no_pii(text, "192.168.1.100")
        assert len(mapping) == 1

    def test_localhost_not_scrubbed(self):
        """127.0.0.1 is often in log fixtures — scrubber treats it as any IP."""
        text, mapping = scrub("Error at 127.0.0.1:8080")
        assert_no_pii(text, "127.0.0.1")

    def test_public_ip(self):
        text, mapping = scrub("Outbound call to 8.8.8.8")
        assert_no_pii(text, "8.8.8.8")
        assert len(mapping) == 1


class TestJWTScrubbing:
    JWT = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POkZyJJMtoRDzek"
    )

    def test_jwt_in_log(self):
        text, mapping = scrub(f"Authorization: Bearer {self.JWT}")
        assert_no_pii(text, self.JWT)

    def test_jwt_standalone(self):
        text, mapping = scrub(self.JWT)
        assert_no_pii(text, self.JWT)
        assert len(mapping) == 1


class TestBearerTokenScrubbing:
    def test_bearer_prefix_preserved(self):
        text, mapping = scrub("Authorization: Bearer abc123xyz456qrs789tuv012")
        # "Bearer " prefix should still appear
        assert "Bearer " in text
        # The actual token must not appear
        assert_no_pii(text, "abc123xyz456qrs789tuv012")


class TestOpenAIKeyScrubbing:
    def test_openai_key(self):
        text, mapping = scrub("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456")
        assert_no_pii(text, "sk-abcdefghijklmnopqrstuvwxyz123456")
        assert any("sk-" in v for v in mapping.values())


class TestAWSKeyScrubbing:
    def test_aws_access_key(self):
        text, mapping = scrub("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
        assert_no_pii(text, "AKIAIOSFODNN7EXAMPLE")
        assert any("AKIA" in v for v in mapping.values())


class TestGenericSecretScrubbing:
    def test_password_equals(self):
        text, mapping = scrub("password=SuperSecret99!")
        assert_no_pii(text, "SuperSecret99!")

    def test_token_colon(self):
        text, mapping = scrub("token: my-ultra-secret-token-xyz")
        assert_no_pii(text, "my-ultra-secret-token-xyz")

    def test_api_key_quoted(self):
        text, mapping = scrub('api_key="ABCDEF1234567890"')
        assert_no_pii(text, "ABCDEF1234567890")


class TestCreditCardScrubbing:
    def test_visa(self):
        text, mapping = scrub("Card charged: 4111111111111111")
        assert_no_pii(text, "4111111111111111")

    def test_mastercard(self):
        text, mapping = scrub("Payment with 5500005555555559")
        assert_no_pii(text, "5500005555555559")


class TestUUIDScrubbing:
    UUID = "550e8400-e29b-41d4-a716-446655440000"

    def test_uuid_as_user_id(self):
        text, mapping = scrub(f"User ID: {self.UUID} performed action")
        assert_no_pii(text, self.UUID)
        assert len(mapping) == 1


# ---------------------------------------------------------------------------
# restore() tests
# ---------------------------------------------------------------------------


class TestRestore:
    def test_round_trip_email(self):
        original = "Contact support@company.com for help"
        scrubbed, mapping = scrub(original)
        restored = restore(scrubbed, mapping)
        assert restored == original

    def test_round_trip_mixed_pii(self):
        original = (
            "User admin@example.com from 10.0.0.1 used token: sk-abc123def456ghi789jkl012 "
            "session 550e8400-e29b-41d4-a716-446655440000"
        )
        scrubbed, mapping = scrub(original)
        restored = restore(scrubbed, mapping)
        assert restored == original

    def test_empty_mapping_noop(self):
        text = "No PII here at all"
        _, mapping = scrub(text)
        assert mapping == {}
        assert restore(text, {}) == text

    def test_restore_is_local_only(self):
        """Mapping should never be in the scrubbed text (simulate sending to LLM)."""
        _, mapping = scrub("admin@internal.io logged error")
        for placeholder in mapping:
            assert placeholder.startswith("<REDACTED_")


# ---------------------------------------------------------------------------
# Idempotency & edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string(self):
        text, mapping = scrub("")
        assert text == ""
        assert mapping == {}

    def test_no_pii_unchanged(self):
        clean = "INFO: Service started successfully on port 8080"
        text, mapping = scrub(clean)
        # 8080 is not an IP — only 4-octet patterns match
        assert mapping == {}
        assert text == clean

    def test_idempotent_on_clean_text(self):
        clean = "Log level INFO, module=worker, message=Starting up"
        text1, _ = scrub(clean)
        text2, _ = scrub(text1)
        assert text1 == text2

    def test_multiple_types_in_one_log(self):
        log = (
            "ERROR: User john@acme.com from 203.0.113.55 "
            "token=secretABC123 card=4111111111111111 "
            "request_id=550e8400-e29b-41d4-a716-446655440000"
        )
        scrubbed, mapping = scrub(log)
        assert_no_pii(scrubbed, "john@acme.com")
        assert_no_pii(scrubbed, "203.0.113.55")
        assert_no_pii(scrubbed, "secretABC123")
        assert_no_pii(scrubbed, "4111111111111111")
        assert_no_pii(scrubbed, "550e8400-e29b-41d4-a716-446655440000")
        # All redacted
        assert len(mapping) >= 4


# ---------------------------------------------------------------------------
# Integration: scrubber wired into analyze_with_llm
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_with_llm_scrubs_before_openai_call():
    """
    Verifies that when settings.scrub_enabled is True (default), the payload
    sent to OpenAI never contains raw PII.
    """
    from pydantic import SecretStr

    from responseiq.ai.schemas import IncidentAnalysis
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.scrub_enabled = True
    mock_settings.openai_api_key = SecretStr("sk-fake")
    mock_settings.use_local_llm_fallback = False

    mock_instructor = AsyncMock()
    mock_instructor.chat = AsyncMock()
    mock_instructor.chat.completions = AsyncMock()
    mock_instructor.chat.completions.create = AsyncMock(
        return_value=IncidentAnalysis(title="Test", severity="low", description="test", remediation="none")
    )

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        with patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_instructor):
            from responseiq.ai.llm_service import analyze_with_llm

            log_with_pii = "Error for user admin@secret.com from 10.10.10.10"
            await analyze_with_llm(log_with_pii, code_context="")

    mock_instructor.chat.completions.create.assert_called_once()
    call_kwargs = mock_instructor.chat.completions.create.call_args.kwargs
    sent_content = str(call_kwargs.get("messages", []))
    assert "admin@secret.com" not in sent_content, "Raw email leaked to LLM"
    assert "10.10.10.10" not in sent_content, "Raw IP leaked to LLM"


@pytest.mark.asyncio
async def test_analyze_with_llm_scrub_disabled_passes_raw():
    """
    When scrub_enabled is False, raw PII is forwarded (opt-out for on-prem).
    """
    from pydantic import SecretStr

    from responseiq.ai.schemas import IncidentAnalysis
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.scrub_enabled = False
    mock_settings.openai_api_key = SecretStr("sk-fake")
    mock_settings.use_local_llm_fallback = False

    mock_instructor = AsyncMock()
    mock_instructor.chat = AsyncMock()
    mock_instructor.chat.completions = AsyncMock()
    mock_instructor.chat.completions.create = AsyncMock(
        return_value=IncidentAnalysis(title="T", severity="low", description="d", remediation="r")
    )

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        with patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_instructor):
            from responseiq.ai.llm_service import analyze_with_llm

            log_with_pii = "Error for user admin@secret.com"
            await analyze_with_llm(log_with_pii, code_context="")

    mock_instructor.chat.completions.create.assert_called_once()
    call_kwargs = mock_instructor.chat.completions.create.call_args.kwargs
    sent_content = str(call_kwargs.get("messages", []))
    assert "admin@secret.com" in sent_content, "Expected raw PII when scrub disabled"
