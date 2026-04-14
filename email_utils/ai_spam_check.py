from typing import Any

from email_utils.config import load_config


def check_spam_with_ai(email_content: str) -> dict[str, Any]:
    """Check if an email is spam using the configured AI provider.

    Dispatches to the appropriate provider based on the 'provider'
    setting in config.ini (defaults to 'anthropic').
    """
    try:
        config = load_config()
        provider = config.get("settings", "provider", fallback="anthropic")

        if provider == "anthropic":
            from email_utils.anthropic_spam_check import check_spam_with_anthropic

            return check_spam_with_anthropic(email_content)
        elif provider == "openai":
            from email_utils.openai_spam_check import check_spam_with_openai

            return check_spam_with_openai(email_content)
        else:
            return {
                "is_spam": "no",
                "confidence": 0,
                "reason": f"Unknown AI provider: {provider}",
            }
    except Exception as e:
        return {
            "is_spam": "no",
            "confidence": 0,
            "reason": f"Error checking spam with AI: {e}",
        }
