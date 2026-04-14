import json
from typing import Any

import anthropic

from email_utils.config import load_config

SYSTEM_PROMPT = (
    "You are a spam detection system. Analyze this email and classify it "
    "as spam or not. Note that legitimate newsletters are not spam.\n\n"
    "The attached email contains all headers, but is stripped from HTML "
    "and attachments. It is also truncated if it's too long. At the end "
    "it contains a summary of attachments, images and links that were "
    "in the email.\n\n"
    "Provide your analysis in JSON format with the following structure:\n"
    "{\n"
    '  "is_spam": "yes|no",\n'
    '  "confidence": 0-100,\n'
    '  "reason": "brief explanation of key factors that led to this '
    'classification"\n'
    "}\n\n"
    "Only output this JSON. Do not output anything else!"
)


def check_spam_with_ai(email_content: str) -> dict[str, Any]:
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


if __name__ == "__main__":
    test_content = "From: test@example.com\nSubject: Test\n\nThis is a test email"
    print(check_spam_with_ai(test_content))
