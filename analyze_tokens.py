#!/usr/bin/env python3
"""
Improved test script to find authentication tokens on the Hounslow page
"""

import json
import re

import requests


def analyze_page_for_tokens():
    """Analyze the page for various token patterns"""
    url = "https://my.hounslow.gov.uk/service/Waste_and_recycling_collections"

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    try:
        response = session.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Cookies: {list(response.cookies.keys())}")

        content = response.text

        # Try different token patterns
        patterns = [
            (r'var CSRF_TOKEN = "([^"]+)"', "CSRF_TOKEN variable"),
            (r'"csrf[_-]?token":\s*"([^"]+)"', "JSON csrf_token"),
            (r'<meta name="csrf-token" content="([^"]+)"', "Meta csrf-token"),
            (r'<meta name="_token" content="([^"]+)"', "Meta _token"),
            (r'"auth-session":"([^"]+)"', "Auth session"),
            (r'"session":\s*{[^}]*"[^"]*token[^"]*":\s*"([^"]+)"', "Session token"),
            (r'["\']X-CSRF-TOKEN["\']\s*:\s*["\']([^"\']+)["\']', "X-CSRF-TOKEN"),
        ]

        print("\nSearching for tokens...")
        for pattern, description in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"✓ Found {description}: {matches[0][:10]}...")
            else:
                print(f"✗ No {description} found")

        # Look for iframe source which might have the actual form
        iframe_match = re.search(r'<iframe[^>]*src="([^"]*)"', content)
        if iframe_match:
            iframe_src = iframe_match.group(1)
            print(f"\n📝 Found iframe source: {iframe_src}")

            # Check if it's a relative URL
            if iframe_src.startswith("/"):
                iframe_url = f"https://my.hounslow.gov.uk{iframe_src}"
            else:
                iframe_url = iframe_src

            # Try to load the iframe content
            if iframe_url and iframe_url != "":
                try:
                    iframe_response = session.get(iframe_url, timeout=10)
                    print(f"Iframe status: {iframe_response.status_code}")

                    # Search iframe content for tokens
                    iframe_content = iframe_response.text
                    for pattern, description in patterns:
                        matches = re.findall(pattern, iframe_content, re.IGNORECASE)
                        if matches:
                            print(
                                f"✓ Found in iframe {description}: {matches[0][:10]}..."
                            )
                except Exception as e:
                    print(f"Could not load iframe: {e}")

        # Look for form data in JavaScript
        js_match = re.search(r"FS\.FormDefinition\s*=\s*({.*?});", content, re.DOTALL)
        if js_match:
            try:
                form_data = json.loads(js_match.group(1))
                print("\n📋 Found FormDefinition data")
                print(
                    f"Session info: {form_data.get('fillform-frame-1', {}).get('data', {}).get('session', {})}"
                )
            except json.JSONDecodeError:
                print("Could not parse FormDefinition JSON")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    analyze_page_for_tokens()
