#!/usr/bin/env python3
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

from email_utils.ai_spam_check import check_spam_with_ai
from email_utils.config import load_config
from email_utils.process_email import format_email_content, get_email_content


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
            debug_path = Path(debug_dir)
            debug_path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            with open(debug_path / f"raw_email_{timestamp}.eml", "w", encoding="utf-8") as f:
                f.write(email_content)

        # Process the email
        processed_email = get_email_content(email_content, is_string=True)
        formatted_output = format_email_content(processed_email)

        # Use AI to check if the email is spam
        ai_result = check_spam_with_ai(formatted_output)

        if debug_mode:
            with open(debug_path / f"processed_email_{timestamp}.txt", "w", encoding="utf-8") as f:
                f.write(formatted_output)

            with open(debug_path / f"ai_output_{timestamp}.json", "w", encoding="utf-8") as f:
                json.dump(ai_result, f, indent=2)

        print(json.dumps(ai_result))
        sys.exit(0)

    except Exception as e:
        if "debug_mode" in locals() and debug_mode and "debug_path" in locals():
            error_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            with open(debug_path / f"error_{error_timestamp}.log", "w", encoding="utf-8") as f:
                f.write(f"Error: {e}\n\n")
                f.write(traceback.format_exc())

        error_json = {"error": True, "message": str(e), "timestamp": datetime.now().isoformat()}
        print(json.dumps(error_json), file=sys.stderr)
        sys.exit(254)


if __name__ == "__main__":
    main()
