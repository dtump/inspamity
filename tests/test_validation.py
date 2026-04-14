from email_utils.validation import validate_ai_response


class TestValidateAiResponse:
    def test_valid_response_passes_through(self):
        result = {"is_spam": "yes", "confidence": 85, "reason": "Obvious spam"}
        assert validate_ai_response(result) == result

    def test_missing_is_spam_defaults_to_no(self):
        result = {"confidence": 50, "reason": "test"}
        assert validate_ai_response(result)["is_spam"] == "no"

    def test_invalid_is_spam_defaults_to_no(self):
        result = {"is_spam": "maybe", "confidence": 50, "reason": "test"}
        assert validate_ai_response(result)["is_spam"] == "no"

    def test_missing_confidence_defaults_to_zero(self):
        result = {"is_spam": "yes", "reason": "test"}
        assert validate_ai_response(result)["confidence"] == 0

    def test_string_confidence_converted(self):
        result = {"is_spam": "yes", "confidence": "75", "reason": "test"}
        assert validate_ai_response(result)["confidence"] == 75

    def test_confidence_clamped_to_100(self):
        result = {"is_spam": "yes", "confidence": 150, "reason": "test"}
        assert validate_ai_response(result)["confidence"] == 100

    def test_confidence_clamped_to_zero(self):
        result = {"is_spam": "yes", "confidence": -10, "reason": "test"}
        assert validate_ai_response(result)["confidence"] == 0

    def test_invalid_confidence_defaults_to_zero(self):
        result = {"is_spam": "yes", "confidence": "high", "reason": "test"}
        assert validate_ai_response(result)["confidence"] == 0

    def test_missing_reason_gets_default(self):
        result = {"is_spam": "no", "confidence": 10}
        assert validate_ai_response(result)["reason"] == "No reason provided"

    def test_non_string_reason_converted(self):
        result = {"is_spam": "no", "confidence": 10, "reason": 42}
        assert validate_ai_response(result)["reason"] == "42"

    def test_empty_dict(self):
        result = validate_ai_response({})
        assert result == {"is_spam": "no", "confidence": 0, "reason": "No reason provided"}
