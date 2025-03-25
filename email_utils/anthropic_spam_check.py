#!/usr/bin/env python3
import json
import anthropic
import configparser
from pathlib import Path

def load_config():
    """Load configuration from config file."""
    config = configparser.ConfigParser()
    
    # Try system-wide config first
    system_config_path = Path('/etc/inspamity/config.ini')
    local_config_path = Path(__file__).parent / 'config.ini'
    
    # Try the system config first, then fall back to the local config
    if system_config_path.exists():
        config.read(system_config_path)
    elif local_config_path.exists():
        config.read(local_config_path)
    else:
        raise FileNotFoundError(f"Config file not found at {system_config_path} or {local_config_path}")
    
    return {
        'api_key': config.get('anthropic', 'api_key'),
        'model': config.get('anthropic', 'model', fallback='claude-3-5-haiku-latest'),
        'temperature': config.getfloat('anthropic', 'temperature', fallback=0.00),
        'timeout': config.getfloat('anthropic', 'timeout', fallback=20.0)
    }

def check_spam_with_ai(email_content):
    """
    Use Anthropic Claude API to check if an email is spam.
    
    Args:
        email_content (dict): Processed and formatted email content
    
    Returns:
        dict: AI analysis result with spam determination and explanation
    """
    try:
        config = load_config()
        
        # Create Anthropic client
        client = anthropic.Anthropic(api_key=config['api_key'], timeout=config['timeout'])
        
        # Define system prompt
        system_prompt = """
You are a spam detection system. Analyze this email and classify it as spam or not. Note that legitimate newsletters are not spam.

The attached email contains all headers, but is stripped from HTML and attachments. It is also truncated if it's too long. At the end it contains a summary of attachments, images and links that were in the email.

Provide your analysis in JSON format with the following structure:
{
  "is_spam": "yes|no",
  "confidence": 0-100,
  "reason": "brief explanation of key factors that led to this classification"
}

Only output this JSON. Do not output anything else!
"""
        
        # Make API call
        response = client.messages.create(
            model=config['model'],
            system=system_prompt,
            temperature=config['temperature'],
            max_tokens=100,
            messages=[
                {"role": "user", "content": email_content}
            ]
        )
        
        # Parse the response
        result = json.loads(response.content[0].text)
        return result
        
    except Exception as e:
        return {
            "reason": f"Error checking spam with AI: {str(e)}"
        }

if __name__ == "__main__":
    # This is just for testing
    test_content = {
        'headers': 'From: test@example.com\nSubject: Test',
        'body': 'This is a test email',
        'images': [],
        'links': [],
        'attachments': [],
        'is_html_email': False,
        'dkim_domain': None
    }
    print(check_spam_with_ai(test_content)) 