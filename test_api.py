#!/usr/bin/env python3
"""
Test script to check if the Hounslow Council API is working
"""

import json

import requests


def test_hounslow_api(uprn="test"):
    """Test the Hounslow Council API with a test UPRN"""
    url = "https://my.hounslow.gov.uk/api/custom-widgets/getRoundDates"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"uprn": uprn}

    print(f"Testing Hounslow API: {url}")
    print(f"Payload: {payload}")
    print("-" * 50)

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)

        # Try to parse JSON response
        try:
            api_response = response.json()
            print("Response JSON:")
            print(json.dumps(api_response, indent=2))
        except json.JSONDecodeError:
            print("Response Text (not JSON):")
            print(response.text)

        return response

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


if __name__ == "__main__":
    # Test with a dummy UPRN first
    print("=== Testing with dummy UPRN ===")
    test_hounslow_api("123456789")

    print("\n" + "=" * 60 + "\n")

    # Test with invalid UPRN to see error handling
    print("=== Testing with invalid UPRN ===")
    test_hounslow_api("invalid")
