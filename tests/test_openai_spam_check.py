import json
from unittest.mock import MagicMock, patch

from email_utils import config as config_module
from email_utils.openai_spam_check import check_spam_with_openai


def _mock_config(tmp_path, monkeypatch, temperature=None, model="gpt-5.6-luna"):
    """Helper to set up a mock config file."""
    lines = "[openai]\napi_key = test-key\n"
    if model is not None:
        lines += f"model = {model}\n"
    lines += "timeout = 10.0\n"
    if temperature is not None:
        lines += f"temperature = {temperature}\n"
    config_file = tmp_path / "config.ini"
    config_file.write_text(lines)
    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)


def _make_mock_response(response_json):
    """Create a mock OpenAI API response."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(response_json)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


class TestCheckSpamWithOpenai:
    @patch("email_utils.openai_spam_check.OpenAI")
    def test_uses_luna_by_default(self, mock_openai_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, model=None)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_openai_cls.return_value = mock_client

        check_spam_with_openai("test")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-5.6-luna"

    @patch("email_utils.openai_spam_check.OpenAI")
    def test_spam_detected(self, mock_openai_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        spam_response = {"is_spam": "yes", "confidence": 92, "reason": "Phishing attempt"}
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(spam_response)
        mock_openai_cls.return_value = mock_client

        result = check_spam_with_openai("Subject: Urgent action required\n\nClick here now!")
        assert result["is_spam"] == "yes"
        assert result["confidence"] == 92
        assert result["reason"] == "Phishing attempt"

    @patch("email_utils.openai_spam_check.OpenAI")
    def test_not_spam(self, mock_openai_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        ham_response = {"is_spam": "no", "confidence": 5, "reason": "Regular correspondence"}
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(ham_response)
        mock_openai_cls.return_value = mock_client

        result = check_spam_with_openai("Subject: Meeting tomorrow\n\nSee you at 3pm.")
        assert result["is_spam"] == "no"
        assert result["confidence"] == 5

    @patch("email_utils.openai_spam_check.OpenAI")
    def test_error_returns_consistent_keys(self, mock_openai_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API timeout")
        mock_openai_cls.return_value = mock_client

        result = check_spam_with_openai("some email content")
        assert result["is_spam"] == "no"
        assert result["confidence"] == 0
        assert "Error" in result["reason"]

    @patch("email_utils.openai_spam_check.OpenAI")
    def test_temperature_passed_when_configured(self, mock_openai_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_openai_cls.return_value = mock_client

        check_spam_with_openai("test")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "temperature" in call_kwargs
        assert call_kwargs["temperature"] == 0.0

    @patch("email_utils.openai_spam_check.OpenAI")
    def test_temperature_omitted_when_not_configured(self, mock_openai_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)  # no temperature

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_openai_cls.return_value = mock_client

        check_spam_with_openai("test")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "temperature" not in call_kwargs

    @patch("email_utils.openai_spam_check.OpenAI")
    def test_uses_system_message(self, mock_openai_cls, tmp_path, monkeypatch):
        """Verify the system prompt is passed as a system message."""
        _mock_config(tmp_path, monkeypatch)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_openai_cls.return_value = mock_client

        check_spam_with_openai("test email")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "test email"
