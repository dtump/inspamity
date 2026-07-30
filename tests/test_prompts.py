from email_utils.prompts import SYSTEM_PROMPT


def test_system_prompt_defines_verdict_confidence() -> None:
    assert "Confidence is certainty in the chosen yes/no classification" in SYSTEM_PROMPT
    assert "is_spam=no with confidence=90" in SYSTEM_PROMPT
    assert "very confident that the email is not spam" in SYSTEM_PROMPT


def test_system_prompt_does_not_invent_context_or_reputation() -> None:
    assert "Do not invent subscription history, domain reputation" in SYSTEM_PROMPT
    assert "treat an unfamiliar domain as illegitimate" in SYSTEM_PROMPT


def test_system_prompt_handles_incomplete_authentication() -> None:
    assert "Treat absent or 'not found' SPF/DKIM as unknown" in SYSTEM_PROMPT
    assert "Authentication problems are weak evidence alone" in SYSTEM_PROMPT
    assert "authentication success does not prove legitimate content" in SYSTEM_PROMPT


def test_system_prompt_requires_combined_evidence() -> None:
    assert "Promotion, urgency, tracking links, many images, or awkward language" in SYSTEM_PROMPT
    assert "weak signals alone" in SYSTEM_PROMPT
    assert "Third-party senders and tracking domains can be legitimate" in SYSTEM_PROMPT
