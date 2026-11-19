import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from app.services.gemini_service import (
    GeminiService,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiAvailabilityError,
    GeminiValidationError,
    GeminiError,
)


class SampleSchema(BaseModel):
    name: str
    score: int


def test_gemini_missing_api_key_raises_auth_error():
    service = GeminiService(api_key="")
    service._api_key = ""
    with pytest.raises(GeminiAuthError) as exc_info:
        service.get_client()
    assert "GEMINI_API_KEY environment variable is missing" in str(exc_info.value)


def test_categorize_exceptions():
    service = GeminiService(api_key="dummy-key")

    auth_err = service.categorize_exception(Exception("401 Unauthorized API key"))
    assert isinstance(auth_err, GeminiAuthError)

    quota_err = service.categorize_exception(Exception("429 RESOURCE_EXHAUSTED quota exceeded"))
    assert isinstance(quota_err, GeminiQuotaError)

    avail_err = service.categorize_exception(Exception("503 UNAVAILABLE high demand"))
    assert isinstance(avail_err, GeminiAvailabilityError)


def test_generate_structured_with_mock():
    service = GeminiService(api_key="dummy-key")
    mock_client = MagicMock()
    service._client = mock_client

    mock_resp = MagicMock()
    mock_resp.parsed = SampleSchema(name="Test Candidate", score=9)
    mock_client.models.generate_content.return_value = mock_resp

    result = service.generate_structured("Evaluate candidate", SampleSchema)
    assert result.name == "Test Candidate"
    assert result.score == 9


def test_generate_structured_model_fallback_on_503():
    service = GeminiService(
        api_key="dummy-key",
        primary_model="primary-model",
        fallback_models=["fallback-model"],
    )
    mock_client = MagicMock()
    service._client = mock_client

    # First call on primary model fails with 503; second call on fallback succeeds
    def mock_generate(*args, **kwargs):
        model = kwargs.get("model")
        if model == "primary-model":
            raise Exception("503 UNAVAILABLE service overloaded")
        mock_resp = MagicMock()
        mock_resp.parsed = SampleSchema(name="Fallback Candidate", score=8)
        return mock_resp

    mock_client.models.generate_content.side_effect = mock_generate

    result = service.generate_structured("Evaluate", SampleSchema, max_retries_per_model=1)
    assert result.name == "Fallback Candidate"
    assert result.score == 8


def test_check_health_diagnostic_unconfigured():
    service = GeminiService(api_key="")
    service._api_key = ""
    health = service.check_health(test_call=False)
    assert health["configured"] is False
    assert health["status"] == "missing_key"
