import json
from typing import Any

from mistralai.client import Mistral

from email_utils.config import load_config
from email_utils.prompts import SYSTEM_PROMPT
from email_utils.validation import validate_ai_response

MISTRAL_ENDPOINTS = {
    "global": None,
    "eu": "https://api.eu.mistral.ai",
    "us": "https://api.us.mistral.ai",
}
RESPONSE_PREVIEW_LIMIT = 1000


def _response_preview(content: Any) -> str:
    """Return a bounded representation of an invalid provider response."""
    preview = repr(content)
    if len(preview) > RESPONSE_PREVIEW_LIMIT:
        return f"{preview[:RESPONSE_PREVIEW_LIMIT]}..."
    return preview


def check_spam_with_mistral(email_content: str) -> dict[str, Any]:
    """Use the Mistral API to check if an email is spam.

    Args:
        email_content: Processed and formatted email content.

    Returns:
        AI analysis result with is_spam, confidence, and reason.
    """
    try:
        config = load_config()

        api_key = config.get("mistral", "api_key")
        model = config.get("mistral", "model", fallback="mistral-large-2512")
        timeout = config.getfloat("mistral", "timeout", fallback=20.0)
        max_tokens = config.getint("mistral", "max_tokens", fallback=256)
        endpoint = config.get("mistral", "endpoint", fallback="global").strip().lower()

        if endpoint not in MISTRAL_ENDPOINTS:
            supported = ", ".join(MISTRAL_ENDPOINTS)
            raise ValueError(f"Unknown Mistral endpoint: {endpoint}. Expected one of: {supported}")

        client_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout_ms": int(timeout * 1000),
        }
        if server_url := MISTRAL_ENDPOINTS[endpoint]:
            client_kwargs["server_url"] = server_url

        client = Mistral(**client_kwargs)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": email_content},
            ],
            "response_format": {"type": "json_object"},
        }

        # Only pass temperature if explicitly configured
        if config.has_option("mistral", "temperature"):
            kwargs["temperature"] = config.getfloat("mistral", "temperature")

        response = client.chat.complete(**kwargs)
        choice = response.choices[0]
        content = choice.message.content

        try:
            result = json.loads(content)
        except (json.JSONDecodeError, TypeError) as error:
            return {
                "is_spam": "no",
                "confidence": 0,
                "reason": (
                    f"Error parsing Mistral response: {error}; "
                    f"finish_reason={choice.finish_reason}; "
                    f"raw_response={_response_preview(content)}"
                ),
            }

        return validate_ai_response(result)

    except Exception as e:
        return {
            "is_spam": "no",
            "confidence": 0,
            "reason": f"Error checking spam with AI: {e}",
        }
