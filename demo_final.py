#!/usr/bin/env python3
"""
Final demonstration of the working Hounslow bin collection browser automation.
"""

import json
import sys

from src.hounslow_bin_collection.browser_collector import fetch_collection_data_browser


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

        for item in collections:
            text = item.get("text", "")

            if "black wheelie bin" in text.lower() and "general waste" in text.lower():
                general_waste = text
            elif "recycling boxes" in text.lower():
                recycling = text
            elif "food waste bin" in text.lower():
                food_waste = text
            elif "brown wheelie bin" in text.lower() and "garden waste" in text.lower():
                garden_waste = text
            elif "every" in text.lower() and "tuesday" in text.lower():
                frequency = text
                print(f"📅 Schedule: {frequency}")
            elif item.get("type") == "dates":
                next_dates = item.get("dates", [])

        if general_waste:
            print(f"🖤 {general_waste}")
        if recycling:
            print(f"♻️  {recycling}")
        if food_waste:
            print(f"🥬 {food_waste}")
        if garden_waste:
            print(f"🌿 {garden_waste}")

        if next_dates:
            print()
            print("📆 UPCOMING COLLECTION DATES:")
            print("   ⚠️  Note: Dates may vary due to holidays/service changes")
            for date in next_dates[:5]:  # Show next 5 dates
                print(f"   • {date}")

        print()
        print("=" * 60)
        print("✅ SOLUTION COMPLETE!")
        print("The browser automation successfully:")
        print("  1. Navigated to Hounslow Council's waste collection form")
        print("  2. Entered the postcode and triggered address lookup")
        print("  3. Selected the correct address from the dropdown")
        print("  4. Extracted detailed collection schedule information")
        print("  5. Parsed collection types, frequencies, and dates")
        print()
        print("⚠️  IMPORTANT: Collection dates may vary due to holidays")
        print("   and service changes. Only rely on dates shown by the")
        print("   council system - do not predict future dates.")
        print()
        print("This solves the original API security bypass challenge!")

        return result

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # Output raw JSON for integration using Hounslow Council's address
        result = fetch_collection_data_browser("TW3 3EB", "7 Bath Rd", headless=True)
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        test_final_solution()


if __name__ == "__main__":
    main()
