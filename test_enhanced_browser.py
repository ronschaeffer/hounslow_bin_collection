#!/usr/bin/env python3
"""Test the enhanced browser collector with address matching."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from hounslow_bin_collection.browser_collector import BrowserWasteCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_enhanced_matching():
    """Test enhanced address matching with Hounslow Council's address."""
    print("🧪 Testing Enhanced Browser Collector")
    print("=" * 50)

    # Test with abbreviated address
    test_cases = [
        {
            "postcode": "TW3 3EB",
            "address": "7 Bath Rd",  # Abbreviated form
            "description": "Hounslow Council HQ (abbreviated)",
        },
        {
            "postcode": "TW3 3EB",
            "address": "7 Bath Road",  # Full form
            "description": "Hounslow Council HQ (full)",
        },
        {
            "postcode": "TW3 3EB",
            "address": "Bath Road",  # Street only
            "description": "Hounslow Council HQ (street only)",
        },
    ]

    with BrowserWasteCollector(headless=True, timeout=30000) as collector:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['description']}")
            print(f"   Postcode: {test_case['postcode']}")
            print(f"   Address: {test_case['address']}")

            try:
                result = collector.fetch_collection_data(
                    postcode=test_case["postcode"], address_hint=test_case["address"]
                )

                print(
                    f"   ✅ Success! Found data for: {result.get('address', 'Unknown')}"
                )
                print(f"   📍 UPRN: {result.get('uprn', 'Not found')}")

                # Show upcoming collections
                collections = result.get("collections", [])
                if collections:
                    next_collection = collections[0]
                    collection_date = next_collection.get("date", "Date not available")
                    collection_type = next_collection.get("type", "Unknown type")
                    print(
                        f"   📅 Next collection: {collection_date} ({collection_type})"
                    )
                else:
                    print("   📅 No upcoming collections found")

            except Exception as e:
                print(f"   ❌ Failed: {e}")

    print("\n✨ Enhanced address matching test completed!")
    print("\n💡 Manual Verification:")
    print("   For 100% accuracy, verify addresses at:")
    print("   https://my.hounslow.gov.uk/service/Waste_and_recycling_collections")


if __name__ == "__main__":
    test_enhanced_matching()
