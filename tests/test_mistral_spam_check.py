import json
from unittest.mock import MagicMock, patch

from email_utils import config as config_module
from email_utils.mistral_spam_check import check_spam_with_mistral


def _mock_config(
    tmp_path,
    monkeypatch,
    temperature=None,
    model="mistral-large-2512",
    endpoint=None,
    max_tokens=None,
):
    """Helper to set up a mock config file."""
    lines = "[mistral]\napi_key = test-key\n"
    if model is not None:
        lines += f"model = {model}\n"
    if endpoint is not None:
        lines += f"endpoint = {endpoint}\n"
    if max_tokens is not None:
        lines += f"max_tokens = {max_tokens}\n"
    lines += "timeout = 10.0\n"
    if temperature is not None:
        lines += f"temperature = {temperature}\n"
    config_file = tmp_path / "config.ini"
    config_file.write_text(lines)
    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)


def _make_mock_response(response_json):
    """Create a mock Mistral API response."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(response_json)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


class TestCheckSpamWithMistral:
    @patch("email_utils.mistral_spam_check.Mistral")
    def test_uses_large_3_by_default(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, model=None)

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_mistral_cls.return_value = mock_client

        check_spam_with_mistral("test")

        call_kwargs = mock_client.chat.complete.call_args[1]
        assert call_kwargs["model"] == "mistral-large-2512"

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_spam_detected(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        spam_response = {"is_spam": "yes", "confidence": 94, "reason": "Phishing attempt"}
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(spam_response)
        mock_mistral_cls.return_value = mock_client

        result = check_spam_with_mistral("Subject: Urgent action required\n\nClick here now!")
        assert result["is_spam"] == "yes"
        assert result["confidence"] == 94
        assert result["reason"] == "Phishing attempt"

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_not_spam(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)

        ham_response = {"is_spam": "no", "confidence": 5, "reason": "Regular correspondence"}
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(ham_response)
        mock_mistral_cls.return_value = mock_client

        result = check_spam_with_mistral("Subject: Meeting tomorrow\n\nSee you at 3pm.")
        assert result["is_spam"] == "no"
        assert result["confidence"] == 5

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_error_returns_consistent_keys(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)

        mock_client = MagicMock()
        mock_client.chat.complete.side_effect = Exception("API timeout")
        mock_mistral_cls.return_value = mock_client

        result = check_spam_with_mistral("some email content")
        assert result["is_spam"] == "no"
        assert result["confidence"] == 0
        assert "Error" in result["reason"]

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_temperature_passed_when_configured(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_mistral_cls.return_value = mock_client

        check_spam_with_mistral("test")

        call_kwargs = mock_client.chat.complete.call_args[1]
        assert call_kwargs["temperature"] == 0.0

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_temperature_omitted_when_not_configured(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_mistral_cls.return_value = mock_client

        check_spam_with_mistral("test")

        call_kwargs = mock_client.chat.complete.call_args[1]
        assert "temperature" not in call_kwargs

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_uses_json_mode_and_system_message(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_mistral_cls.return_value = mock_client

        check_spam_with_mistral("test email")

        mock_mistral_cls.assert_called_once_with(api_key="test-key", timeout_ms=10_000)
        call_kwargs = mock_client.chat.complete.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}
        assert call_kwargs["max_tokens"] == 256
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1] == {"role": "user", "content": "test email"}

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_max_tokens_is_configurable(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, max_tokens=512)

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_mistral_cls.return_value = mock_client

        check_spam_with_mistral("test")

        call_kwargs = mock_client.chat.complete.call_args[1]
        assert call_kwargs["max_tokens"] == 512

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_invalid_json_includes_response_details(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)

        mock_response = _make_mock_response({})
        mock_response.choices[0].message.content = '{"is_spam":"yes","reason":"truncated'
        mock_response.choices[0].finish_reason = "length"
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_cls.return_value = mock_client

        result = check_spam_with_mistral("test")

        assert result["is_spam"] == "no"
        assert result["confidence"] == 0
        assert "Error parsing Mistral response" in result["reason"]
        assert "finish_reason=length" in result["reason"]
        assert "raw_response=" in result["reason"]
        assert "truncated" in result["reason"]

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_uses_eu_endpoint(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, endpoint="eu")

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_mistral_cls.return_value = mock_client

        check_spam_with_mistral("test")

        mock_mistral_cls.assert_called_once_with(
            api_key="test-key",
            timeout_ms=10_000,
            server_url="https://api.eu.mistral.ai",
        )

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_uses_us_endpoint(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, endpoint="us")

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_mistral_cls.return_value = mock_client

        check_spam_with_mistral("test")

        mock_mistral_cls.assert_called_once_with(
            api_key="test-key",
            timeout_ms=10_000,
            server_url="https://api.us.mistral.ai",
        )

    @patch("email_utils.mistral_spam_check.Mistral")
    def test_unknown_endpoint_returns_error(self, mock_mistral_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, endpoint="antarctica")

        result = check_spam_with_mistral("test")

        mock_mistral_cls.assert_not_called()
        assert result["is_spam"] == "no"
        assert result["confidence"] == 0
        assert "Unknown Mistral endpoint" in result["reason"]
