from email_utils.process_email import (
    clean_newlines,
    decode_email_header,
    format_email_content,
    get_email_content,
    truncate_text,
    truncate_url,
)


class TestDecodeEmailHeader:
    def test_plain_header(self):
        assert decode_email_header("Hello World") == "Hello World"

    def test_none_header(self):
        assert decode_email_header(None) == ""

    def test_rfc2047_utf8(self):
        encoded = "=?utf-8?B?SGVsbG8gV29ybGQ=?="
        assert decode_email_header(encoded) == "Hello World"

    def test_rfc2047_iso8859(self):
        encoded = "=?iso-8859-1?Q?caf=E9?="
        assert decode_email_header(encoded) == "caf\u00e9"


class TestCleanNewlines:
    def test_no_excess(self):
        assert clean_newlines("a\nb\n") == "a\nb\n"

    def test_excess_newlines(self):
        assert clean_newlines("a\n\n\n\nb") == "a\n\nb"

    def test_whitespace_only_lines(self):
        result = clean_newlines("a\n   \nb")
        assert "   " not in result


class TestTruncateText:
    def test_within_limit(self):
        text = "short text"
        assert truncate_text(text) == text

    def test_over_limit(self):
        text = "x" * 2500
        result = truncate_text(text)
        assert result.endswith("[EMAIL TRUNCATED]")
        assert len(result) < 2500

    def test_custom_limit(self):
        text = "x" * 50
        result = truncate_text(text, max_length=10)
        assert result.startswith("x" * 10)
        assert "[EMAIL TRUNCATED]" in result


class TestTruncateUrl:
    def test_within_limit(self):
        url = "https://example.com"
        assert truncate_url(url) == url

    def test_over_limit(self):
        url = "https://example.com/" + "a" * 200
        result = truncate_url(url)
        assert result.endswith("[TRUNCATED]")
        assert len(result) < len(url)


PLAIN_EMAIL = """\
From: sender@example.com
To: recipient@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 00:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Hello, this is a plain text email body.
"""

HTML_EMAIL = """\
From: sender@example.com
To: recipient@example.com
Subject: HTML Test
Content-Type: text/html; charset="utf-8"

<html>
<body>
<p>Hello <b>World</b></p>
<a href="https://example.com">Link</a>
<a href="https://other.com">Other</a>
<img src="https://example.com/img.png"/>
</body>
</html>
"""

DKIM_SPF_EMAIL = """\
From: sender@example.com
To: recipient@example.com
Subject: Auth Test
DKIM-Signature: v=1; a=rsa-sha256; d=example.com; s=selector;
Authentication-Results: mx.example.com; spf=pass
X-Mailer: TestMailer
Content-Type: text/plain; charset="utf-8"

Body text here.
"""


class TestGetEmailContent:
    def test_plain_text(self):
        result = get_email_content(PLAIN_EMAIL, is_string=True)
        assert "sender@example.com" in result["headers"]
        assert "Test Subject" in result["headers"]
        assert "plain text email body" in result["body"]
        assert result["is_html_email"] is False
        assert result["images"] == []
        assert result["links"] == []

    def test_html_email(self):
        result = get_email_content(HTML_EMAIL, is_string=True)
        assert result["is_html_email"] is True
        assert "Hello" in result["body"]
        assert "World" in result["body"]
        assert "https://example.com" in result["links"]
        assert "https://other.com" in result["links"]
        assert "https://example.com/img.png" in result["images"]

    def test_dkim_extraction(self):
        result = get_email_content(DKIM_SPF_EMAIL, is_string=True)
        assert result["dkim_domain"] == "example.com"

    def test_spf_extraction(self):
        result = get_email_content(DKIM_SPF_EMAIL, is_string=True)
        assert result["spf_result"] == "pass"

    def test_x_headers_removed(self):
        result = get_email_content(DKIM_SPF_EMAIL, is_string=True)
        assert "X-Mailer" in result["removed_headers"]
        assert "X-Mailer" not in result["headers"]

    def test_dkim_header_removed(self):
        result = get_email_content(DKIM_SPF_EMAIL, is_string=True)
        assert "DKIM-Signature" in result["removed_headers"]

    def test_data_uris_filtered(self):
        email_str = (
            'From: a@b.com\nContent-Type: text/html; charset="utf-8"\n\n'
            '<html><body><img src="data:image/png;base64,abc123"/>'
            '<img src="https://example.com/real.png"/></body></html>'
        )
        result = get_email_content(email_str, is_string=True)
        assert result["images"] == ["https://example.com/real.png"]

    def test_javascript_links_filtered(self):
        email_str = (
            'From: a@b.com\nContent-Type: text/html; charset="utf-8"\n\n'
            '<html><body><a href="javascript:alert(1)">Click</a>'
            '<a href="https://example.com">Real</a></body></html>'
        )
        result = get_email_content(email_str, is_string=True)
        assert result["links"] == ["https://example.com"]

    def test_mailto_links_filtered(self):
        email_str = (
            'From: a@b.com\nContent-Type: text/html; charset="utf-8"\n\n'
            '<html><body><a href="mailto:user@example.com">Email</a>'
            '<a href="https://example.com">Web</a></body></html>'
        )
        result = get_email_content(email_str, is_string=True)
        assert result["links"] == ["https://example.com"]

    def test_url_whitespace_stripped(self):
        email_str = (
            'From: a@b.com\nContent-Type: text/html; charset="utf-8"\n\n'
            '<html><body><a href="  https://example.com  ">Link</a></body></html>'
        )
        result = get_email_content(email_str, is_string=True)
        assert result["links"] == ["https://example.com"]


class TestFormatEmailContent:
    def test_basic_structure(self):
        content = get_email_content(PLAIN_EMAIL, is_string=True)
        formatted = format_email_content(content)
        assert "Email meta information:" in formatted
        assert "Summary:" in formatted
        assert "Email headers:" in formatted
        assert "Email body:" in formatted

    def test_html_metadata(self):
        content = get_email_content(HTML_EMAIL, is_string=True)
        formatted = format_email_content(content)
        assert "HTML email: Yes" in formatted
        assert "Image count: 1" in formatted
        assert "Link count: 2" in formatted
        assert "Links found:" in formatted
        assert "Images found:" in formatted

    def test_dkim_spf_in_summary(self):
        content = get_email_content(DKIM_SPF_EMAIL, is_string=True)
        formatted = format_email_content(content)
        assert "DKIM: present (from domain example.com)" in formatted
        assert "SPF: pass" in formatted

    def test_list_truncation(self):
        content = get_email_content(PLAIN_EMAIL, is_string=True)
        content["images"] = [f"https://example.com/img{i}.png" for i in range(10)]
        formatted = format_email_content(content)
        assert "[LIST TRUNCATED]" in formatted
