"""Opt-in live LLM benchmark for the anonymised spam corpus.

This suite is always skipped unless explicitly enabled, so normal tests and CI
never contact a provider.
"""

import logging
import os
import time
from pathlib import Path

import pytest

from email_utils.ai_spam_check import check_spam_with_ai
from email_utils.process_email import format_email_content, get_email_content

LOGGER = logging.getLogger(__name__)

pytestmark = pytest.mark.live_llm

if os.environ.get("INSPAMITY_RUN_LIVE_LLM") != "1":
    pytest.skip(
        "Set INSPAMITY_RUN_LIVE_LLM=1 and configure a provider API key to run live LLM tests.",
        allow_module_level=True,
    )


CORPUS_DIR = Path(__file__).parent / "fixtures" / "spam"
ALL_FIXTURES = sorted(CORPUS_DIR.glob("*.eml"))

try:
    FIXTURE_COUNT = int(os.environ.get("INSPAMITY_LIVE_LLM_FIXTURE_COUNT", "5"))
except ValueError as error:
    raise pytest.UsageError(
        "INSPAMITY_LIVE_LLM_FIXTURE_COUNT must be a positive integer."
    ) from error

if not 1 <= FIXTURE_COUNT <= len(ALL_FIXTURES):
    raise pytest.UsageError(
        f"INSPAMITY_LIVE_LLM_FIXTURE_COUNT must be between 1 and {len(ALL_FIXTURES)}."
    )

FIXTURES = ALL_FIXTURES[:FIXTURE_COUNT]


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda path: path.stem)
def test_live_llm_classifies_reviewed_fixture_as_spam(fixture: Path):
    content = format_email_content(get_email_content(fixture))
    start = time.monotonic()
    result = check_spam_with_ai(content)
    elapsed = time.monotonic() - start

    assert set(result) == {"is_spam", "confidence", "reason"}
    LOGGER.info(
        "LLM benchmark result: fixture=%s is_spam=%s confidence=%s reason=%s duration=%.2fs",
        fixture.name,
        result["is_spam"],
        result["confidence"],
        result["reason"],
        elapsed,
    )
    assert result["is_spam"] == "yes", f"{fixture.name}: {result} ({elapsed:.2f}s)"
