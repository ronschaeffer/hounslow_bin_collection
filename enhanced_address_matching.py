#!/usr/bin/env python3
"""
Enhanced address matching with abbreviation handling.
"""


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


def find_best_address_match(
    user_address: str, available_addresses: list[str]
) -> tuple[str, float]:
    """
    Find the best matching address from available options.

    Args:
        user_address: Address provided by user
        available_addresses: List of addresses from council website

    Returns:
        Tuple of (best_match, confidence_score)
    """
    variations = normalize_address_for_matching(user_address)
    best_match = None
    best_score = 0

    for variation in variations:
        for available in available_addresses:
            if variation.lower() in available.lower():
                # Calculate confidence score based on specificity
                score = len(variation) / len(available)  # More specific = higher score
                if score > best_score:
                    best_score = score
                    best_match = available

    return best_match, best_score


if __name__ == "__main__":
    # Test the address normalization
    test_addresses = [
        "7 Bath Rd",
        "10 Church St",
        "45 Victoria Ave",
        "Apartment 2, Oak Cl",
        "123a High Street",
    ]

    print("ADDRESS NORMALIZATION TEST:")
    print("=" * 50)

    for addr in test_addresses:
        variations = normalize_address_for_matching(addr)
        print(f"Input: '{addr}'")
        print(f"Variations: {variations}")
        print()

    # Test with real Hounslow addresses
    available_addresses = [
        "Hounslow Library, Hounslow House, 7, Bath Road, Hounslow, TW3 3EB",
        "10, Bath Road, Hounslow, TW3 3EB",
        "12, Bath Road, Hounslow, TW3 3EB",
    ]

    print("MATCHING TEST WITH REAL ADDRESSES:")
    print("=" * 50)

    test_inputs = ["7 Bath Rd", "Bath Road", "Library", "10 Bath Road"]

    for test_input in test_inputs:
        best_match, score = find_best_address_match(test_input, available_addresses)
        print(f"Input: '{test_input}'")
        print(f"Best match: '{best_match}'")
        print(f"Confidence: {score:.2f}")
        print()
