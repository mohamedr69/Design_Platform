"""Where the G and Desktop lines meet in the merged installation."""
import pytest

from app.ai import sheet_reader, verification
from app.ai.sheet_reader import ReviewReason


@pytest.mark.parametrize("kind", ["unavailable", "unsupported_model", "model_substituted", "model_unverified",
                                  "invalid_request", "transport", "rate_limit"])
def test_the_routes_errors_are_provider_errors_not_invalid_answers(kind):
    """The merged provider's route errors (FI-P1 Stage 0.2) mean the model gave no usable answer because of
    the route: Desktop's classifiers file them as provider errors, never as an invalid answer."""
    assert sheet_reader.error_reason(f"{kind}: detail") == ReviewReason.AI_PROVIDER_ERROR
    assert verification.call_outcome(f"{kind}: detail") == "provider_error"


def test_an_answer_that_is_not_usable_is_still_an_invalid_response():
    assert sheet_reader.error_reason("invalid_response: no JSON") == ReviewReason.AI_INVALID_RESPONSE
    assert verification.call_outcome("invalid_response: no JSON") == "invalid_response"
    assert sheet_reader.error_reason("timeout: 5 s") == ReviewReason.AI_TIMEOUT
