#!/usr/bin/env python3
"""
Demo script showing environment variable configuration with enhanced address matching.
"""

import os
import sys

sys.path.insert(0, "src")

from hounslow_bin_collection.browser_collector import BrowserWasteCollector
from hounslow_bin_collection.config import Config


def demo_env_config_usage():
    """Demonstrate using environment variables for configuration."""
    print("Enhanced Address Matching with Environment Variables")
    print("=" * 60)

    # Example 1: Using environment variables
    print("\nMethod 1: Environment Variables")
    print("Set these in your .env file or docker environment:")
    print("   HOUNSLOW_POSTCODE=TW3 3EB")
    print("   HOUNSLOW_ADDRESS=7 Bath Rd")

    # Set environment variables for demo
    os.environ["HOUNSLOW_POSTCODE"] = "TW3 3EB"
    os.environ["HOUNSLOW_ADDRESS"] = "7 Bath Rd"

    # Load config - will pick up environment variables
    config = Config()

    postcode = config.get("address.postcode")
    address_hint = config.get("address.address_hint")

    print("\nConfiguration loaded:")
    print(f"   postcode: {postcode}")
    print(f"   address_hint: {address_hint}")

    # Use with browser collector
    if postcode and address_hint:
        print("\nTesting browser automation...")
        try:
            with BrowserWasteCollector(headless=True, timeout=15000) as collector:
                result = collector.fetch_collection_data(postcode, address_hint)
                print(f"   SUCCESS: Found: {result['address']}")
                print(f"   UPRN: {result['uprn']}")
        except Exception as e:
            print(f"   Note: {e}")

    # Example 2: Alternative UPRN method (for direct API - currently blocked)
    print("\nMethod 2: Direct UPRN (Legacy API - Currently Blocked)")
    print("   UPRN=100021577775")
    print("   Note: Direct UPRN API is blocked by council security")
    print("   Note: Browser automation (Method 1) is the working approach")

    os.environ["UPRN"] = "100021577775"
    config_uprn = Config()
    uprn = config_uprn.get("address.uprn")
    print(f"   UPRN loaded: {uprn} (for waste_sync.py only)")

    print("\nDocker Usage:")
    print("   docker run -e HOUNSLOW_POSTCODE='TW3 3EB' \\")
    print("              -e HOUNSLOW_ADDRESS='7 Bath Rd' \\")
    print("              hounslow-bin-collection")

    print("\nHome Assistant Integration:")
    print("   Add to your docker-compose.yml:")
    print("   environment:")
    print("     - HOUNSLOW_POSTCODE=your_postcode")
    print("     - HOUNSLOW_ADDRESS=your_address")
    print("     - MQTT_BROKER=192.168.1.100")
    print("     - MQTT_ENABLED=true")

    print("\nEnhanced Matching Benefits:")
    print("   - 'Bath Rd' automatically matches 'Bath Road' addresses")
    print("   - 'Worple Rd' automatically matches 'Worple Road' addresses")
    print("   - House numbers alone work: '7', '136', '24a'")
    print("   - Building names work: 'Library', 'Hounslow House'")
    print("   - Case insensitive matching")

    print("\nManual Verification (when needed):")
    print("   https://my.hounslow.gov.uk/service/Waste_and_recycling_collections")

    # Clean up
    for env_var in ["HOUNSLOW_POSTCODE", "HOUNSLOW_ADDRESS"]:
        if env_var in os.environ:
            del os.environ[env_var]


if __name__ == "__main__":
    demo_env_config_usage()
