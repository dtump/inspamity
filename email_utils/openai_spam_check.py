import json
from typing import Any

from openai import OpenAI

from email_utils.config import load_config
from email_utils.prompts import SYSTEM_PROMPT


def check_spam_with_openai(email_content: str) -> dict[str, Any]:
    """Use OpenAI API to check if an email is spam.

    Args:
        email_content: Processed and formatted email content.

    Returns:
        AI analysis result with is_spam, confidence, and reason.
    """
    try:
        config = load_config()

        api_key = config.get("openai", "api_key")
        model = config.get("openai", "model", fallback="gpt-5.4-mini")
        timeout = config.getfloat("openai", "timeout", fallback=20.0)

        client = OpenAI(api_key=api_key, timeout=timeout)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_completion_tokens": 100,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": email_content},
            ],
        }

        # Only pass temperature if explicitly configured
        if config.has_option("openai", "temperature"):
            kwargs["temperature"] = config.getfloat("openai", "temperature")

        response = client.chat.completions.create(**kwargs)

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {
            "is_spam": "no",
            "confidence": 0,
            "reason": f"Error checking spam with AI: {e}",
        }
