#!/usr/bin/env python3
# Script to run from the command line to check if an email is spam
# Provide a raw email file from a Maildir folder as input

import argparse
import json
from pathlib import Path

from email_utils.process_email import format_email_content, get_email_content


def main() -> None:
    parser = argparse.ArgumentParser(description="Process a single email file")
    parser.add_argument("email_file", help="Path to the email file")
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for processed email (STDOUT for console)",
    )
    parser.add_argument(
        "--output-json",
        "-j",
        action="store_true",
        help="If specified, output JSON instead of human-readable text",
    )
    parser.add_argument(
        "--check-ai", "-a", action="store_true", help="Use AI to check if the email is spam"
    )
    args = parser.parse_args()

    email_path = Path(args.email_file)

    try:
        # Get the processed email content
        email_content = get_email_content(email_path)

        # Format the content into readable output
        output = format_email_content(email_content)

        ai_output = ""
        error = False

        # Check for spam using AI if requested
        if args.check_ai:
            try:
                from email_utils.ai_spam_check import check_spam_with_ai

                # Send formatted email content to AI
                result = check_spam_with_ai(output)

                ai_output = ""

                if args.output_json:
                    ai_output = json.dumps(result)
                else:
                    ai_output = f"Is spam: {result.get('is_spam', 'Unknown')}\n"
                    ai_output += f"Confidence: {result.get('confidence', 'Unknown')}\n"
                    ai_output += f"Reason: {result.get('reason', 'No reason provided')}"

                if "is_spam" not in result or "confidence" not in result:
                    error = True
            except Exception as e:
                output += f"\n\nError performing AI spam check: {e}\n"

        # If no output and no check-ai specified, output to console
        if not args.output and not args.check_ai:
            print(output)

        # Output to file or console
        if args.output:
            if args.output == "STDOUT":
                print(output)
            else:
                output_file = Path(args.output)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"Processed: {email_path} -> {output_file}")

        if args.check_ai:
            print(ai_output)

            if error:
                exit(254)

    except Exception as e:
        print(f"Error processing {email_path}: {e}")


if __name__ == "__main__":
    main()
