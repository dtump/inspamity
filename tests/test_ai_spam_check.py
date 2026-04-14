from unittest.mock import patch

from email_utils import config as config_module
from email_utils.ai_spam_check import check_spam_with_ai


def _mock_config(tmp_path, monkeypatch, provider="anthropic"):
    """Helper to set up a mock config file with provider selection."""
    lines = f"[settings]\nprovider = {provider}\n"
    lines += "[anthropic]\napi_key = test\n"
    lines += "[openai]\napi_key = test\n"
    config_file = tmp_path / "config.ini"
    config_file.write_text(lines)
    monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
    monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)


class TestAiSpamCheckDispatcher:
    @patch("email_utils.anthropic_spam_check.check_spam_with_anthropic")
    def test_dispatches_to_anthropic(self, mock_anthropic, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, provider="anthropic")
        mock_anthropic.return_value = {"is_spam": "no", "confidence": 0, "reason": "test"}

        result = check_spam_with_ai("test email")
        mock_anthropic.assert_called_once_with("test email")
        assert result["is_spam"] == "no"

    @patch("email_utils.openai_spam_check.check_spam_with_openai")
    def test_dispatches_to_openai(self, mock_openai, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, provider="openai")
        mock_openai.return_value = {"is_spam": "yes", "confidence": 80, "reason": "spam"}

        result = check_spam_with_ai("test email")
        mock_openai.assert_called_once_with("test email")
        assert result["is_spam"] == "yes"

    def test_unknown_provider_returns_error(self, tmp_path, monkeypatch):
        _mock_config(tmp_path, monkeypatch, provider="unknown_provider")

        result = check_spam_with_ai("test email")
        assert result["is_spam"] == "no"
        assert result["confidence"] == 0
        assert "Unknown AI provider" in result["reason"]

    def test_defaults_to_anthropic_when_no_provider_set(self, tmp_path, monkeypatch):
        """When provider is not in config, defaults to anthropic."""
        config_file = tmp_path / "config.ini"
        config_file.write_text("[settings]\n[anthropic]\napi_key = test\n")
        monkeypatch.setattr(config_module, "SYSTEM_CONFIG_PATH", tmp_path / "nonexistent.ini")
        monkeypatch.setattr(config_module, "LOCAL_CONFIG_PATH", config_file)

        with patch("email_utils.anthropic_spam_check.check_spam_with_anthropic") as mock_anthropic:
            mock_anthropic.return_value = {"is_spam": "no", "confidence": 0, "reason": "test"}
            check_spam_with_ai("test")
            mock_anthropic.assert_called_once()
