import email
import re
from email.header import decode_header
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


def decode_email_header(header: str | None) -> str:
    """Decode email header to readable text."""
    if header is None:
        return ""
    decoded_header = ""
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            try:
                if encoding is not None:
                    decoded_part = part.decode(encoding)
                else:
                    decoded_part = part.decode("utf-8", errors="replace")
            except (LookupError, UnicodeDecodeError):
                decoded_part = part.decode("utf-8", errors="replace")
        else:
            decoded_part = part
        decoded_header += decoded_part
    return decoded_header


def clean_newlines(text: str) -> str:
    """Remove surplus newlines, keeping maximum 2 in a row."""
    # Replace whitespace-only lines with newlines
    text = re.sub(r"^\s+$", "\n", text, flags=re.MULTILINE)
    # Replace 3 or more newlines with 2 newlines
    return re.sub(r"\n{3,}", "\n\n", text)


def truncate_text(text: str, max_length: int = 2000) -> str:
    """Truncate text to max_length and add truncation tag if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n[EMAIL TRUNCATED]"


def truncate_url(url: str, max_length: int = 100) -> str:
    """Truncate URL to max_length and add truncation tag if needed."""
    if len(url) <= max_length:
        return url
    return url[:max_length] + " [TRUNCATED]"


def get_email_content(source: str | Path, is_string: bool = False) -> dict[str, Any]:
    """Extract content and metadata from an email file or string.

    Args:
        source: Either a file path or the email content as a string.
        is_string: If True, source is a string; if False, a file path.

    Returns:
        Dictionary with email content and metadata.
    """
    if is_string:
        # Parse email from string
        msg = email.message_from_string(source)
    else:
        # Parse email from file
        with open(source, "rb") as f:
            msg = email.message_from_binary_file(f)

    # Get all headers as text
    headers = ""
    removed_headers = []
    dkim_domain = None
    spf_result = None

    # First process DKIM headers if present
    for key in ["DKIM-Signature", "ARC-Message-Signature", "DomainKey-Signature"]:
        if key in msg:
            value = decode_email_header(msg[key])
            # Extract domain from DKIM signature
            domain_match = re.search(r"d=([^;]+)", value)
            if domain_match and not dkim_domain:
                dkim_domain = domain_match.group(1).strip()
            removed_headers.append(key)

    # Check for SPF results in ARC-Authentication-Results and Received-SPF headers
    for key in ["ARC-Authentication-Results", "Authentication-Results", "Received-SPF"]:
        if key in msg:
            value = decode_email_header(msg[key])
            spf_match = re.search(r"spf=(\w+)", value)
            if spf_match and not spf_result:
                spf_result = spf_match.group(1).strip().lower()

    # Process other headers
    for key in msg.keys():
        # Skip DKIM, Authentication/ARC and other processed headers
        skip_headers = {
            "dkim-signature",
            "arc-message-signature",
            "domainkey-signature",
            "arc-seal",
            "arc-authentication-results",
            "authentication-results",
            "received-spf",
            "mime-version",
        }
        if key.lower() in skip_headers:
            continue

        value = decode_email_header(msg[key])
        # Skip all X- headers
        if key.lower().startswith("x-"):
            removed_headers.append(key)
            continue
        headers += f"{key}: {value}\n"

    body_text = ""
    html_content = ""
    attachments = []
    is_html_email = False

    # Process each part of the email
    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))

        # Handle attachments
        if "attachment" in content_disposition:
            filename = part.get_filename()
            if filename:
                filename = decode_email_header(filename)
                # Get size of attachment in bytes
                size = len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                attachments.append((filename, size))
            continue

        # Extract the email body content
        if content_type == "text/html":
            is_html_email = True
            payload = part.get_payload(decode=True)
            if payload:
                html_content += payload.decode("utf-8", errors="replace")
        elif content_type == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                body_text += payload.decode("utf-8", errors="replace")

    # Prefer HTML body over plain text, converting HTML to text
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        body_text = soup.get_text()

    # Clean up surplus newlines
    body_text = clean_newlines(body_text)

    # Extract images and links if HTML content exists (with deduplication)
    images = []
    links = []
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and src not in images:
                images.append(src)

        for a in soup.find_all("a"):
            href = a.get("href")
            if href and href not in links:
                links.append(href)

    return {
        "headers": headers,
        "body": body_text,
        "images": images,
        "links": links,
        "attachments": attachments,
        "is_html_email": is_html_email,
        "removed_headers": removed_headers,
        "dkim_domain": dkim_domain,
        "spf_result": spf_result,
    }


def format_email_content(email_content: dict[str, Any]) -> str:
    """Format email content and metadata into a readable text output."""
    output = "Email meta information:\n\n"

    # Add requested metadata
    if email_content["images"]:
        output += "Images found:\n"
        # Limit to 5 images
        for img in email_content["images"][:5]:
            output += f"* {truncate_url(img)}\n"
        # Add truncated tag if more than 5 images
        if len(email_content["images"]) > 5:
            output += "[LIST TRUNCATED]\n"
        output += "\n"

    if email_content["links"]:
        output += "Links found:\n"
        # Limit to 5 links
        for link in email_content["links"][:5]:
            output += f"* {truncate_url(link)}\n"
        # Add truncated tag if more than 5 links
        if len(email_content["links"]) > 5:
            output += "[LIST TRUNCATED]\n"
        output += "\n"

    if email_content["attachments"]:
        output += "Attachments:\n"
        for filename, size in email_content["attachments"]:
            # Format size as KB, MB as appropriate
            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            output += f"* {filename} ({size_str})\n"
        output += "\n"

    if email_content["removed_headers"]:
        output += f"Removed headers: {', '.join(email_content['removed_headers'])}\n\n"

    # Add counts and HTML status
    output += "Summary:\n"
    output += f"* HTML email: {'Yes' if email_content['is_html_email'] else 'No'}\n"
    output += f"* Image count: {len(email_content['images'])}\n"
    output += f"* Link count: {len(email_content['links'])}\n"
    output += f"* Attachment count: {len(email_content['attachments'])}\n"

    # Add DKIM information
    if email_content["dkim_domain"]:
        output += f"* DKIM: present (from domain {email_content['dkim_domain']})\n"
    else:
        output += "* DKIM: absent\n"

    # Add SPF information
    if email_content["spf_result"]:
        output += f"* SPF: {email_content['spf_result']}\n"
    else:
        output += "* SPF: not found\n"

    output += "\n"

    output += "Email headers:\n"
    output += email_content["headers"] + "\n"

    output += "Email body:\n"
    output += truncate_text(email_content["body"]) + "\n\n"

    return output
