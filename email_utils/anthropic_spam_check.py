import json
from typing import Any

import anthropic

from email_utils.config import load_config
from email_utils.prompts import SYSTEM_PROMPT


def check_spam_with_anthropic(email_content: str) -> dict[str, Any]:
    """Use Anthropic Claude API to check if an email is spam.

    Args:
        email_content: Processed and formatted email content.

    Returns:
        AI analysis result with is_spam, confidence, and reason.
    """
    try:
        config = load_config()

        api_key = config.get("anthropic", "api_key")
        model = config.get("anthropic", "model", fallback="claude-haiku-4-5-latest")
        timeout = config.getfloat("anthropic", "timeout", fallback=20.0)

        client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

        kwargs: dict[str, Any] = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "max_tokens": 100,
            "messages": [{"role": "user", "content": email_content}],
        }

        # Only pass temperature if explicitly configured
        if config.has_option("anthropic", "temperature"):
            kwargs["temperature"] = config.getfloat("anthropic", "temperature")

        response = client.messages.create(**kwargs)

        return json.loads(response.content[0].text)

    except Exception as e:
        return {
            "is_spam": "no",
            "confidence": 0,
            "reason": f"Error checking spam with AI: {e}",
        }
