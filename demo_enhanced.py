#!/usr/bin/env python3
"""
Final demonstration of the working Hounslow bin collection browser automation.
"""

import json
import sys

from src.hounslow_bin_collection.browser_collector import fetch_collection_data_browser


def demonstrate_enhanced_matching():
    """Demonstrate enhanced address matching capabilities."""
    print("\n🎯 Enhanced Address Matching Demo")
    print("=" * 50)
    print("Testing with different address formats...")

    from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector

    test_cases = [
        ("TW3 3EB", "7 Bath Rd", "Abbreviated street name"),
        ("TW3 3EB", "Bath Road", "Street name only"),
        ("TW7 7HX", "136 Worple Rd", "Abbreviated + house number"),
    ]

    with BrowserWasteCollector(headless=True) as collector:
        for postcode, address, description in test_cases:
            print(f"\n🔍 {description}: '{address}' in {postcode}")
            try:
                result = collector.fetch_collection_data(postcode, address)
                print(f"   ✅ Found: {result['address']}")
                print(f"   📍 UPRN: {result['uprn']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

    print("\n💡 The system automatically handles:")
    print("   • Street abbreviations (Rd → Road, St → Street, etc.)")
    print("   • Partial addresses (house numbers, street names)")
    print("   • Case variations and formatting differences")
    print("\n🔗 For manual verification:")
    print("   https://my.hounslow.gov.uk/service/Waste_and_recycling_collections")


def test_final_solution():
    """Test the complete working solution."""
    print("=== HOUNSLOW BIN COLLECTION - BROWSER AUTOMATION SUCCESS ===")
    print()

    # Test data using Hounslow Council's own address
    test_postcode = "TW3 3EB"
    test_address = "7 Bath Rd"

    print(f"Testing with postcode: {test_postcode}")
    print(f"Looking for address: {test_address}")
    print("(Using Hounslow Council's own address for demonstration)")
    print()

    try:
        print("Starting browser automation...")
        result = fetch_collection_data_browser(
            test_postcode, test_address, headless=True
        )

        print("✅ SUCCESS: Collection data retrieved!")
        print()

        # Display key information
        print(f"📍 Address: {result.get('address', 'Unknown')}")
        print(f"📮 Postcode: {result.get('postcode', 'Unknown')}")
        print(f"🏠 UPRN: {result.get('uprn', 'Unknown')}")
        print()

        # Display collection information
        collections = result.get("collections", [])
        print("🗑️ COLLECTION SCHEDULE:")
        print("-" * 50)

        general_waste = None
        recycling = None
        food_waste = None
        garden_waste = None
        next_dates = []

        for collection in collections:
            waste_type = collection.get("type", "Unknown")
            collection_date = collection.get("date", "Unknown")
            next_dates.append(f"{collection_date} ({waste_type})")

            if "general" in waste_type.lower() or "refuse" in waste_type.lower():
                general_waste = collection_date
            elif "recycling" in waste_type.lower():
                recycling = collection_date
            elif "food" in waste_type.lower():
                food_waste = collection_date
            elif "garden" in waste_type.lower():
                garden_waste = collection_date

        # Display specific collection types
        if general_waste:
            print(f"🗑️  General Waste: {general_waste}")
        if recycling:
            print(f"♻️  Recycling: {recycling}")
        if food_waste:
            print(f"🥬 Food Waste: {food_waste}")
        if garden_waste:
            print(f"🌿 Garden Waste: {garden_waste}")

        print()
        print("📅 NEXT COLLECTIONS:")
        print("-" * 20)
        for date_info in next_dates[:3]:  # Show next 3 collections
            print(f"• {date_info}")

        print()
        print("⚠️  IMPORTANT NOTES:")
        print("- Collection dates may vary due to holidays")
        print("- Always check official council website for latest updates")
        print("- Place bins out before 7 AM on collection day")
        print()
        print("✨ Browser automation successfully bypassed all API restrictions!")
        print(
            "🔗 Manual verification: https://my.hounslow.gov.uk/service/Waste_and_recycling_collections"
        )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Please check your postcode and address are valid.")
        return False

    return True


def main():
    """Main function to run demonstrations."""
    if len(sys.argv) > 1 and sys.argv[1] == "--enhanced":
        # Enhanced matching demo
        demonstrate_enhanced_matching()
    elif len(sys.argv) > 1 and sys.argv[1] == "--json":
        # Output raw JSON for integration using Hounslow Council's address
        result = fetch_collection_data_browser("TW3 3EB", "7 Bath Rd", headless=True)
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        test_final_solution()


if __name__ == "__main__":
    main()
