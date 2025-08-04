#!/usr/bin/env python3
"""
Test address matching flexibility - show how partial addresses work.
Enhanced with smart matching and manual verification guidance.
"""

from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector


def normalize_address_for_matching(user_address: str) -> list[str]:
    """
    Generate multiple variations of an address for better matching.

    Args:
        user_address: The address provided by user

    Returns:
        List of address variations to try
    """
    variations = [user_address]  # Always include original

    # Common abbreviation expansions
    expansions = {
        "rd": "road",
        "st": "street",
        "ave": "avenue",
        "ln": "lane",
        "cl": "close",
        "cres": "crescent",
        "gdns": "gardens",
        "pk": "park",
        "pl": "place",
        "sq": "square",
        "ter": "terrace",
        "way": "way",
        "dr": "drive",
        "ct": "court",
    }

    # Try expanding abbreviations
    lower_address = user_address.lower()
    for abbrev, full in expansions.items():
        if f" {abbrev}" in lower_address or lower_address.endswith(f" {abbrev}"):
            expanded = lower_address.replace(f" {abbrev}", f" {full}")
            variations.append(expanded.title())
        # Also try the reverse (full to abbreviated)
        if f" {full}" in lower_address:
            abbreviated = lower_address.replace(f" {full}", f" {abbrev}")
            variations.append(abbreviated.title())

    # Try just the house number if present
    words = user_address.split()
    if words and words[0].replace("a", "").replace("b", "").replace("c", "").isdigit():
        variations.append(words[0])

    # Try just the street name (remove house number)
    if len(words) > 1:
        street_only = " ".join(words[1:])
        variations.append(street_only)

    return list(set(variations))  # Remove duplicates


def find_best_matches(
    user_address: str, available_addresses: list[str]
) -> list[tuple[str, str]]:
    """
    Find all matching addresses with the variation that matched.

    Args:
        user_address: Address provided by user
        available_addresses: List of addresses from council website

    Returns:
        List of tuples: (matched_address, matching_variation)
    """
    variations = normalize_address_for_matching(user_address)
    matches = []

    for variation in variations:
        for available in available_addresses:
            if variation.lower() in available.lower():
                matches.append((available, variation))

    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match, variation in matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append((match, variation))

    return unique_matches


def test_address_matching_flexibility():
    """Test different levels of address matching with enhanced logic."""

    test_postcode = "TW3 3EB"  # Hounslow Council area

    print("=== ENHANCED ADDRESS MATCHING FLEXIBILITY TEST ===")
    print(f"Testing postcode: {test_postcode}")
    print()
    print("📋 MANUAL VERIFICATION RECOMMENDED:")
    print("For best results, manually check your exact address at:")
    print("🌐 https://my.hounslow.gov.uk/service/Waste_and_recycling_collections")
    print("This ensures you get the exact format the council uses.")
    print()

    # Test different address variations
    address_variations = [
        "7 Bath Rd",  # Minimal address with abbreviation
        "7 Bath Road",  # Full road name
        "Bath Rd",  # Just street name with abbreviation
        "Bath Road",  # Full street name
        "7",  # Just house number
        "Hounslow House",  # Building name only
        "Library",  # Partial building name
        "7 Bath Rd Hounslow",  # Include area with abbreviation
        "wrong street",  # Intentionally wrong
    ]

    with BrowserWasteCollector(headless=True) as collector:
        page = collector.page
        if not page:
            print("Failed to start browser")
            return

        try:
            # Navigate and set up form
            page.goto(collector.FORM_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            iframe_element = page.query_selector('iframe[id="fillform-frame-1"]')
            iframe_frame = iframe_element.content_frame()
            iframe_frame.wait_for_load_state("networkidle")

            # Dismiss cookie dialog
            cookie_close = page.query_selector('button:has-text("Close")')
            if cookie_close and cookie_close.is_visible():
                cookie_close.click()
                page.wait_for_timeout(1000)

            # Click address tab
            address_tab = iframe_frame.query_selector('text="Your address"')
            address_tab.click()
            iframe_frame.wait_for_timeout(2000)

            # Enter postcode to get address list
            postcode_input = iframe_frame.query_selector("#searchPostcode")
            postcode_input.fill("")
            postcode_input.fill(test_postcode)
            postcode_input.press("Enter")
            iframe_frame.wait_for_timeout(4000)

            # Get all available addresses
            address_dropdown = iframe_frame.query_selector("#selectedAddress")
            options = address_dropdown.query_selector_all("option")

            # Extract available addresses
            available_addresses = []
            print("AVAILABLE ADDRESSES FROM COUNCIL WEBSITE:")
            print("-" * 60)
            for i, option in enumerate(options):
                value = option.get_attribute("value")
                text = option.text_content() or ""
                if value:  # Skip placeholder
                    available_addresses.append(text.strip())
                    print(f"{i}: {text.strip()}")
            print()

            print("ENHANCED ADDRESS MATCHING TEST RESULTS:")
            print("-" * 60)

            # Test each address variation with enhanced matching
            for test_address in address_variations:
                print(f"Testing: '{test_address}'")

                # Use enhanced matching
                matches = find_best_matches(test_address, available_addresses)

                if matches:
                    print(f"  ✅ ENHANCED MATCHES: {len(matches)} address(es)")
                    for match, variation in matches:
                        print(f"    → Matched '{variation}' in: {match}")
                else:
                    # Try basic matching as fallback
                    basic_matches = []
                    for address in available_addresses:
                        if test_address.lower() in address.lower():
                            basic_matches.append(address)

                    if basic_matches:
                        print(f"  ⚠️  BASIC MATCHES: {len(basic_matches)} address(es)")
                        for match in basic_matches:
                            print(f"    → {match}")
                    else:
                        print(
                            "  ❌ NO MATCH - Consider checking council website manually"
                        )
                print()

            print("=" * 60)
            print("💡 RECOMMENDATIONS:")
            print("1. Use full street names (Road, Street, Avenue) not abbreviations")
            print("2. Building names like 'Library', 'Hounslow House' work excellently")
            print("3. House numbers alone often work: '7', '10', '24a'")
            print("4. When in doubt, check the exact format at:")
            print(
                "   https://my.hounslow.gov.uk/service/Waste_and_recycling_collections"
            )
            print("5. Copy the exact address text from the dropdown for 100% accuracy")

        except Exception as e:
            print(f"Error: {e}")
            print()
            print("🔧 TROUBLESHOOTING:")
            print("If this test fails, you can still check your address manually at:")
            print("https://my.hounslow.gov.uk/service/Waste_and_recycling_collections")


if __name__ == "__main__":
    test_address_matching_flexibility()
