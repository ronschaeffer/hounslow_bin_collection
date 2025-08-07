#!/usr/bin/env python3
"""
CLI command to show detailed bin collection schedule.
Shows: General Waste: Every 2 weeks on Tuesday (Next: 19/08/2025) format
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hounslow_bin_collection.browser_collector import BrowserWasteCollector


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.ERROR  # Minimal output by default
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def format_schedule_summary(raw_data: dict) -> str:
    """Format raw enhanced data into the requested schedule format."""
    lines = []

    # Extract collections with detailed schedule info
    collections = raw_data.get("collections", [])
    bin_schedule = raw_data.get("bin_schedule", {})

    # Use bin_schedule if available (has the structured data we want)
    if bin_schedule:
        for bin_type, details in bin_schedule.items():
            # Clean up bin type name
            if bin_type == "general_waste":
                name = "General Waste"
            elif bin_type == "recycling":
                name = "Recycling"
            elif bin_type == "food_waste":
                name = "Food Waste"
            elif bin_type == "garden_waste":
                name = "Garden Waste"
            else:
                name = bin_type.replace("_", " ").title()

            # Extract frequency and next date
            frequency = details.get("frequency", "")
            next_date = details.get("next_date", "")

            # Use the exact frequency from the website, but clean it up slightly
            if frequency:
                # Remove the "(subject to change during public holidays)" part for cleaner display
                freq_display = frequency.replace(
                    " (subject to change during public holidays)", ""
                )
                # Capitalize first letter if needed
                if freq_display and not freq_display[0].isupper():
                    freq_display = freq_display[0].upper() + freq_display[1:]
            else:
                freq_display = ""

            # Format the line
            if next_date and freq_display:
                lines.append(f"{name}: {freq_display} (Next: {next_date})")
            elif next_date:
                lines.append(f"{name}: (Next: {next_date})")
            elif freq_display:
                lines.append(f"{name}: {freq_display}")
            else:
                lines.append(f"{name}: ")

    # Fallback to parsing collections directly
    else:
        for collection in collections:
            if collection.get("type") == "dates":
                continue

            # Extract details
            text = collection.get("text", "")
            frequency = collection.get("frequency", "")
            next_collection = collection.get("next_collection", "")

            # Determine bin type from text
            text_lower = text.lower()
            if "black" in text_lower and "general" in text_lower:
                name = "General Waste"
            elif "recycling" in text_lower:
                name = "Recycling"
            elif "green" in text_lower and "food" in text_lower:
                name = "Food Waste"
            elif "brown" in text_lower and "garden" in text_lower:
                name = "Garden Waste"
            else:
                continue  # Skip unknown types

            # Parse frequency
            if "every 2 weeks" in frequency.lower():
                freq_display = "Every 2 weeks on Tuesday"
            elif "every week" in frequency.lower():
                freq_display = "Every week on Tuesday"
            else:
                freq_display = "Schedule unknown"

            # Format the line
            if next_collection:
                lines.append(f"{name}: {freq_display} (Next: {next_collection})")
            else:
                lines.append(f"{name}: {freq_display}")

    return "\n".join(lines) if lines else "No collection schedule found"


def main():
    """Main function for bin schedule command."""
    parser = argparse.ArgumentParser(
        description="Show bin collection schedule in summary format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config/config.yaml
  %(prog)s --postcode "TW7 7HX" --address "132 Worple Rd"
  %(prog)s --postcode "TW7 7HX" --address "136" --json
        """,
    )

    # Address options
    parser.add_argument("--postcode", "-p", help="Postcode (e.g., TW7 7HX)")
    parser.add_argument("--address", "-a", help="Address hint (e.g., '132 Worple Rd')")
    parser.add_argument("--config", "-c", help="Use address from config file")

    # Output options
    parser.add_argument("--json", action="store_true", help="Output raw JSON data")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed logs"
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if exact address not found (no fallback)",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Get address details
    if args.config:
        try:
            config = load_config(args.config)
            address_info = config["address"]
            postcode = address_info["postcode"]

            # Support both old and new config formats
            if "address_hint" in address_info:
                # New format with address_hint
                address_hint = address_info["address_hint"]
            else:
                # Old format with separate house_number and street_name
                house_number = address_info["house_number"]
                street_name = address_info["street_name"]
                address_hint = f"{house_number} {street_name}"
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return 1

    elif args.postcode and args.address:
        postcode = args.postcode
        address_hint = args.address

    else:
        print("❌ Error: Provide either --config or both --postcode and --address")
        return 1

    # Show what we're doing
    if not args.quiet:
        print(f"🔍 Getting schedule for {address_hint}, {postcode}...")

    # Fetch the data
    try:
        with BrowserWasteCollector(headless=True) as collector:
            raw_data = collector.fetch_collection_data(postcode, address_hint)

            # Check if we got a different address than requested
            actual_address = raw_data.get("address", "")
            if actual_address and not args.quiet:
                # Normalize addresses for comparison
                def normalize_address(addr):
                    """Normalize address for comparison by handling common abbreviations."""
                    addr = addr.lower()
                    # Handle common abbreviations
                    addr = (
                        addr.replace(" road", " rd")
                        .replace(" street", " st")
                        .replace(" avenue", " ave")
                    )
                    addr = (
                        addr.replace(" lane", " ln")
                        .replace(" close", " cl")
                        .replace(" place", " pl")
                    )
                    # Remove punctuation and extra spaces
                    import re

                    addr = re.sub(r"[,.]", "", addr)
                    addr = re.sub(r"\s+", " ", addr).strip()
                    return addr

                normalized_requested = normalize_address(address_hint)
                normalized_actual = normalize_address(actual_address)

                # Check if they're substantially different
                if normalized_requested not in normalized_actual and not any(
                    word in normalized_actual
                    for word in normalized_requested.split()
                    if len(word) > 2
                ):
                    if args.strict:
                        print(
                            f"❌ Error: Requested address '{address_hint}' not found."
                        )
                        print(f"💡 Available address in {postcode}: {actual_address}")
                        print(
                            "💡 Tip: Use exact address or remove --strict flag for fallback"
                        )
                        return 1
                    else:
                        print(
                            f"⚠️  Warning: Requested address '{address_hint}' not found."
                        )
                        print(f"📍 Using fallback address: {actual_address}")
                        print()

            if args.json:
                print(json.dumps(raw_data, indent=2, default=str))
            else:
                schedule = format_schedule_summary(raw_data)
                print()
                print(schedule)

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
