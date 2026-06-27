#!/usr/bin/env python3
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from email_utils.ai_spam_check import check_spam_with_ai
from email_utils.config import load_config
from email_utils.process_email import format_email_content, get_email_content

DEBUG_DIR_MODE = 0o700
DEBUG_FILE_MODE = 0o600


def prepare_debug_directory(debug_dir: str) -> Path:
    """Create and lock down the debug directory for private mail artifacts."""
    debug_path = Path(debug_dir)
    debug_path.mkdir(parents=True, mode=DEBUG_DIR_MODE, exist_ok=True)
    debug_path.chmod(DEBUG_DIR_MODE)
    return debug_path


def write_private_text(path: Path, content: str) -> None:
    """Write a debug text file without allowing group/other access."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, DEBUG_FILE_MODE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = -1
            f.write(content)
    finally:
        if fd != -1:
            os.close(fd)
        path.chmod(DEBUG_FILE_MODE)


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a debug JSON file without allowing group/other access."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, DEBUG_FILE_MODE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = -1
            json.dump(payload, f, indent=2)
    finally:
        if fd != -1:
            os.close(fd)
        path.chmod(DEBUG_FILE_MODE)


def main() -> None:
    try:
        config = load_config()

        debug_mode = config.getboolean("settings", "debug_mode", fallback=False)
        debug_dir = config.get("settings", "debug_directory", fallback="debug_logs")

        # Check if filename is provided as argument
        if len(sys.argv) > 1:
            email_file = Path(sys.argv[1])
            if not email_file.exists():
                raise FileNotFoundError(f"Email file not found: {email_file}")
            with open(email_file, encoding="utf-8", errors="replace") as f:
                email_content = f.read()
        else:
            # Read email from STDIN if no filename provided
            email_content = sys.stdin.read()

        if not email_content.strip():
            raise ValueError("Empty email input received")

        if debug_mode:
            debug_path = prepare_debug_directory(debug_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            write_private_text(debug_path / f"raw_email_{timestamp}.eml", email_content)

        # Process the email
        processed_email = get_email_content(email_content, is_string=True)
        formatted_output = format_email_content(processed_email)

        # Use AI to check if the email is spam
        ai_result = check_spam_with_ai(formatted_output)

        if debug_mode:
            write_private_text(debug_path / f"processed_email_{timestamp}.txt", formatted_output)
            write_private_json(debug_path / f"ai_output_{timestamp}.json", ai_result)

        print(json.dumps(ai_result))
        sys.exit(0)

    except Exception as e:
        if "debug_mode" in locals() and debug_mode and "debug_path" in locals():
            error_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            write_private_text(
                debug_path / f"error_{error_timestamp}.log",
                f"Error: {e}\n\n{traceback.format_exc()}",
            )

        error_json = {"error": True, "message": str(e), "timestamp": datetime.now().isoformat()}
        print(json.dumps(error_json), file=sys.stderr)
        sys.exit(254)


if __name__ == "__main__":
    main()
