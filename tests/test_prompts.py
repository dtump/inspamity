from email_utils.prompts import SYSTEM_PROMPT


def test_system_prompt_calibrates_high_confidence() -> None:
    assert "estimated probability that the email is spam" in SYSTEM_PROMPT
    assert "Reserve 95-100" in SYSTEM_PROMPT
    assert "Missing context never justifies high confidence" in SYSTEM_PROMPT


def test_system_prompt_does_not_infer_private_context_or_reputation() -> None:
    assert "Do not infer 'unsolicited'" in SYSTEM_PROMPT
    assert "Do not judge a domain by whether you recognize it" in SYSTEM_PROMPT
    assert "Do not invent domain reputation" in SYSTEM_PROMPT


def test_system_prompt_treats_incomplete_authentication_conservatively() -> None:
    assert "Treat an absent or 'not found' SPF/DKIM result as unknown" in SYSTEM_PROMPT
    assert "Missing authentication, softfail" in SYSTEM_PROMPT


def test_system_prompt_does_not_equate_bulk_mail_features_with_spam() -> None:
    assert "Promotional content or an urgent call to action is not" in SYSTEM_PROMPT
    assert (
        "Third-party delivery, link-tracking, and unsubscribe domains are common" in SYSTEM_PROMPT
    )
    assert "imperfect grammar, and awkward translation are weak signals" in SYSTEM_PROMPT
