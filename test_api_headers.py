#!/usr/bin/env python3
"""
Test script to check if the Hounslow Council API is working with different headers
"""

import json

import requests


def test_hounslow_api_with_headers(uprn="123456789"):
    """Test the Hounslow Council API with browser-like headers"""
    url = "https://my.hounslow.gov.uk/api/custom-widgets/getRoundDates"

    # Try with browser-like headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://my.hounslow.gov.uk/",
        "Origin": "https://my.hounslow.gov.uk",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    payload = {"uprn": uprn}

    print(f"Testing Hounslow API with browser headers: {url}")
    print(f"Payload: {payload}")
    print("-" * 50)

    try:
        # First, let's try to get the main page to establish a session
        session = requests.Session()
        print("Getting main page to establish session...")
        main_page = session.get(
            "https://my.hounslow.gov.uk/",
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        print(f"Main page status: {main_page.status_code}")

        # Now try the API with the session
        response = session.post(url, headers=headers, json=payload, timeout=10)
        print(f"API Status Code: {response.status_code}")
        print("-" * 50)

        # Try to parse JSON response
        try:
            api_response = response.json()
            print("Response JSON:")
            print(json.dumps(api_response, indent=2))
        except json.JSONDecodeError:
            print("Response Text (not JSON):")
            print(
                response.text[:500] + "..."
                if len(response.text) > 500
                else response.text
            )

        return response

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def test_main_website():
    """Test if we can access the main Hounslow website"""
    print("=== Testing main Hounslow website ===")
    try:
        response = requests.get("https://my.hounslow.gov.uk/", timeout=10)
        print(f"Main site status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        if "waste" in response.text.lower() or "bin" in response.text.lower():
            print("✓ Found waste/bin related content on main page")
        else:
            print("✗ No waste/bin content found on main page")
    except requests.exceptions.RequestException as e:
        print(f"Failed to access main site: {e}")


if __name__ == "__main__":
    test_main_website()

    print("\n" + "=" * 60 + "\n")

    # Test with browser-like headers
    print("=== Testing API with browser headers ===")
    test_hounslow_api_with_headers("123456789")
