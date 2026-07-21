"""Regression tests for the anonymised, manually reviewed spam corpus."""

import html
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path

import pytest

from email_utils.process_email import format_email_content, get_email_content

CORPUS_DIR = Path(__file__).parent / "fixtures" / "spam"
FIXTURES = sorted(CORPUS_DIR.glob("*.eml"))
FORBIDDEN_IDENTIFIERS = re.compile(
    r"(?:"
    r"mail\.cybje\.nl|moowh\.nl|cybje\.nl|dorinda\.eu|tump\.me|"
    r"51\.38\.38\.65|2001:41d0:305:2100::a165|"
    r"\b(?:dick(?:\s+tump)?|cybje|dorinda(?:\s+hensema)?|magda(?:\s+tump)?)\b"
    r")",
    re.IGNORECASE,
)


def _decoded_fixture_text(path: Path) -> str:
    """Return all decoded headers and textual MIME parts for privacy checks."""
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    content = [str(value) for _, value in message.items()]
    for part in message.walk():
        if part.get_content_maintype() != "text":
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            content.append(payload.decode(charset, errors="replace"))
        except LookupError:
            content.append(payload.decode("utf-8", errors="replace"))
    return html.unescape("\n".join(content))


def _canonical_fingerprint(path: Path) -> str:
    """Make duplicate campaign copies compare equal despite formatting differences."""
    parsed = get_email_content(path)
    subject = re.search(r"^Subject: (.*)$", parsed["headers"], flags=re.MULTILINE)
    text = f"{subject.group(1) if subject else ''}\n{parsed['body']}"
    return re.sub(r"\s+", " ", text).strip().lower()


def test_spam_corpus_has_twenty_unique_fixtures():
    assert len(FIXTURES) == 20
    fingerprints = [_canonical_fingerprint(path) for path in FIXTURES]
    assert len(fingerprints) == len(set(fingerprints))


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda path: path.stem)
def test_spam_fixture_is_safe_and_processable(fixture: Path):
    raw_text = fixture.read_text(encoding="utf-8", errors="replace")
    decoded_text = _decoded_fixture_text(fixture)
    parsed = get_email_content(fixture)
    formatted = format_email_content(parsed)

    assert not FORBIDDEN_IDENTIFIERS.search(raw_text)
    assert not FORBIDDEN_IDENTIFIERS.search(decoded_text)
    assert not FORBIDDEN_IDENTIFIERS.search(formatted)
    assert parsed["body"].strip()
    assert "Email meta information:" in formatted
    assert "Email headers:" in formatted
    assert "Email body:" in formatted
