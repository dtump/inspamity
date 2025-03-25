#!/usr/bin/env python3
import sys
import json
import configparser
import traceback
from datetime import datetime
from pathlib import Path

# Import functions from process_email.py
from email_utils.process_email import get_email_content, format_email_content
from email_utils.anthropic_spam_check import check_spam_with_ai

def main():
    try:
        # Read configuration
        config = configparser.ConfigParser()
        
        system_config_path = Path('/etc/inspamity/config.ini')
        local_config_path = Path(__file__).parent / 'config.ini'
        
        if system_config_path.exists():
            config.read(system_config_path)
        elif local_config_path.exists():
            config.read(local_config_path)
        else:
            raise FileNotFoundError(f"Config file not found at {system_config_path} or {local_config_path}")
        
        # Get debug settings
        debug_mode = config.getboolean('settings', 'debug_mode', fallback=False)
        debug_dir = config.get('settings', 'debug_directory', fallback='debug_logs')
        
        # Check if filename is provided as argument
        if len(sys.argv) > 1:
            email_file = Path(sys.argv[1])
            if not email_file.exists():
                raise FileNotFoundError(f"Email file not found: {email_file}")
            with open(email_file, 'r', encoding='utf-8') as f:
                email_content = f.read()
        else:
            # Read email from STDIN if no filename provided
            email_content = sys.stdin.read()
        
        # Check if input is empty
        if not email_content.strip():
            raise ValueError("Empty email input received")
        
        if debug_mode:
            # Ensure debug directory exists
            debug_path = Path(debug_dir)
            debug_path.mkdir(parents=True, exist_ok=True)
            
            # Create timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # Save raw email
            with open(debug_path / f"raw_email_{timestamp}.eml", 'w', encoding='utf-8') as f:
                f.write(email_content)
        
        # Process the email using the existing functions
        # First get the processed email content
        processed_email = get_email_content(email_content, is_string=True)
        
        # Format the content into readable output
        formatted_output = format_email_content(processed_email)
        
        # Use AI to check if the email is spam
        ai_result = check_spam_with_ai(formatted_output)
        
        if debug_mode:
            # Save formatted email
            with open(debug_path / f"processed_email_{timestamp}.txt", 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            
            # Save AI output
            with open(debug_path / f"ai_output_{timestamp}.json", 'w', encoding='utf-8') as f:
                json.dump(ai_result, f, indent=2)
        
        # Output JSON result to STDOUT
        print(json.dumps(ai_result))
        
        # Exit with success code
        sys.exit(0)
        
    except Exception as e:
        # Log the error if in debug mode
        if 'debug_mode' in locals() and debug_mode and 'debug_path' in locals():
            error_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            with open(debug_path / f"error_{error_timestamp}.log", 'w', encoding='utf-8') as f:
                f.write(f"Error: {str(e)}\n\n")
                f.write(traceback.format_exc())
        
        # Output error as JSON to STDERR
        error_json = {
            "error": True,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_json), file=sys.stderr)
        
        # Exit with error code
        sys.exit(254)

if __name__ == "__main__":
    main() 