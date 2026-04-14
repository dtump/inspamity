import json
from unittest.mock import MagicMock, patch

from email_utils import config as config_module
from email_utils.anthropic_spam_check import check_spam_with_ai


def _mock_config(tmp_path, monkeypatch, temperature=None):
    """Helper to set up a mock config file."""
    lines = "[anthropic]\napi_key = test-key\nmodel = claude-haiku-4-5-latest\ntimeout = 10.0\n"
    if temperature is not None:
        lines += f"temperature = {temperature}\n"
    config_file = tmp_path / "config.ini"
    config_file.write_text(lines)
    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)


def _make_mock_response(response_json):
    """Create a mock Anthropic API response."""
    mock_content = MagicMock()
    mock_content.text = json.dumps(response_json)
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


class TestCheckSpamWithAi:
    @patch("email_utils.anthropic_spam_check.anthropic.Anthropic")
    def test_spam_detected(self, mock_anthropic_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        spam_response = {"is_spam": "yes", "confidence": 95, "reason": "Obvious spam"}
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(spam_response)
        mock_anthropic_cls.return_value = mock_client

        result = check_spam_with_ai("Subject: Buy now!!!\n\nCheap deals!")
        assert result["is_spam"] == "yes"
        assert result["confidence"] == 95
        assert result["reason"] == "Obvious spam"

    @patch("email_utils.anthropic_spam_check.anthropic.Anthropic")
    def test_not_spam(self, mock_anthropic_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        ham_response = {"is_spam": "no", "confidence": 10, "reason": "Legitimate newsletter"}
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(ham_response)
        mock_anthropic_cls.return_value = mock_client

        result = check_spam_with_ai("Subject: Weekly update\n\nHere's your digest.")
        assert result["is_spam"] == "no"
        assert result["confidence"] == 10

    @patch("email_utils.anthropic_spam_check.anthropic.Anthropic")
    def test_error_returns_consistent_keys(self, mock_anthropic_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch)

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API timeout")
        mock_anthropic_cls.return_value = mock_client

        result = check_spam_with_ai("some email content")
        assert result["is_spam"] == "no"
        assert result["confidence"] == 0
        assert "Error" in result["reason"]

    @patch("email_utils.anthropic_spam_check.anthropic.Anthropic")
    def test_temperature_passed_when_configured(self, mock_anthropic_cls, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, temperature=0.0)

        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_anthropic_cls.return_value = mock_client

        check_spam_with_ai("test")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "temperature" in call_kwargs
        assert call_kwargs["temperature"] == 0.0

    @patch("email_utils.anthropic_spam_check.anthropic.Anthropic")
    def test_temperature_omitted_when_not_configured(
        self, mock_anthropic_cls, tmp_path, monkeypatch
    ):
        _mock_config(tmp_path, monkeypatch)  # no temperature

        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(
            {"is_spam": "no", "confidence": 0, "reason": "test"}
        )
        mock_anthropic_cls.return_value = mock_client

        check_spam_with_ai("test")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "temperature" not in call_kwargs
