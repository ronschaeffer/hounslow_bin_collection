#!/usr/bin/env python3
"""
CLI command for Hounslow bin collection lookup.
Usage: python bin_lookup.py --postcode TW7 7HX --address "136 Worple Rd"
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hounslow_bin_collection.collector import HounslowBinCollector
from hounslow_bin_collection.models import AddressConfig


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from YAML file if provided."""
    if not config_path:
        return {}

    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️  Warning: Could not load config file: {e}")
        return {}


def format_collection_info(result, format_type: str = "pretty"):
    """Format collection information for display."""
    if format_type == "json":
        # JSON output for automation
        output = {
            "address": result.address,
            "postcode": result.postcode,
            "uprn": result.uprn,
            "retrieved_at": result.retrieved_at.isoformat(),
            "collections": {},
        }

        # Add specific collection types
        collection_types = [
            ("general_waste", result.get_general_waste_info()),
            ("recycling", result.get_recycling_info()),
            ("food_waste", result.get_food_waste_info()),
            ("garden_waste", result.get_garden_waste_info()),
        ]

        for waste_type, info in collection_types:
            if info:
                output["collections"][waste_type] = {
                    "description": info.text,
                    "type": info.type,
                    "dates": info.dates,
                }

        # Add next collection dates
        next_dates = result.get_next_dates()
        if next_dates:
            output["next_collection_dates"] = next_dates

        return json.dumps(output, indent=2)

    else:
        # Pretty formatted output for humans
        lines = []
        lines.append("🗑️  HOUNSLOW BIN COLLECTION RESULTS")
        lines.append("=" * 50)
        lines.append(f"📍 Address: {result.address}")
        lines.append(f"📮 Postcode: {result.postcode}")
        lines.append(f"🆔 UPRN: {result.uprn}")
        lines.append(
            f"🕒 Retrieved: {result.retrieved_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append("")

        # Next collection dates
        next_dates = result.get_next_dates()
        if next_dates:
            lines.append(f"📅 Next Collections: {', '.join(next_dates[:5])}")
            lines.append("")

        lines.append("🗑️  COLLECTION TYPES:")
        lines.append("-" * 30)

        # Display each collection type
        collection_types = [
            ("♻️  General Waste", result.get_general_waste_info()),
            ("📦 Recycling", result.get_recycling_info()),
            ("🥬 Food Waste", result.get_food_waste_info()),
            ("🌱 Garden Waste", result.get_garden_waste_info()),
        ]

        for emoji_type, info in collection_types:
            if info:
                lines.append(f"{emoji_type}: {info.text}")
            else:
                lines.append(f"{emoji_type}: Not available")

        lines.append("")
        lines.append("💡 Tip: Use --format json for machine-readable output")

        return "\n".join(lines)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Look up Hounslow bin collection information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --postcode "TW7 7HX" --address "136 Worple Rd"
  %(prog)s --postcode "TW3 3EB" --address "7 Bath Rd" --format json
  %(prog)s --config config/config.yaml  # Use address from config
  %(prog)s --postcode "TW7 7HX" --address "136" --verbose  # House number only

Address Tips:
  • Use "Rd" instead of "Road" for better matching
  • Try house number only if full address doesn't work
  • Include area name if needed: "136 Worple Rd Isleworth"
        """,
    )

    # Address input options
    address_group = parser.add_argument_group("Address Input")
    address_group.add_argument("--postcode", "-p", help="Postcode (e.g., TW7 7HX)")
    address_group.add_argument(
        "--address", "-a", help="Address hint (e.g., '136 Worple Rd')"
    )
    address_group.add_argument("--config", "-c", help="Use address from config file")

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--format",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format (default: pretty)",
    )
    output_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Browser options
    browser_group = parser.add_argument_group("Browser Options")
    browser_group.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default)",
    )
    browser_group.add_argument(
        "--show-browser",
        action="store_true",
        help="Show browser window (for debugging)",
    )
    browser_group.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Browser timeout in seconds (default: 30)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Determine address source
    if args.config:
        # Load from config file
        config = load_config(args.config)
        if not config or "address" not in config:
            print("❌ Error: Config file must contain 'address' section")
            return 1

        address_info = config["address"]
        postcode = address_info["postcode"]
        house_number = address_info["house_number"]
        street_name = address_info["street_name"]
        address_hint = f"{house_number} {street_name}"

        print(f"📁 Using address from config: {address_hint}, {postcode}")

    elif args.postcode and args.address:
        # Use command line arguments
        postcode = args.postcode
        address_hint = args.address

    else:
        print("❌ Error: Must provide either --config or both --postcode and --address")
        parser.print_help()
        return 1

    # Validate inputs
    if not postcode or not address_hint:
        print("❌ Error: Both postcode and address are required")
        return 1

    # Create address config
    try:
        address_config = AddressConfig(
            postcode=postcode.strip(), address_hint=address_hint.strip()
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1

    # Setup browser options
    headless = args.headless and not args.show_browser
    timeout_ms = args.timeout * 1000

    if args.verbose:
        print(f"🔧 Browser config: headless={headless}, timeout={args.timeout}s")

    # Perform lookup
    try:
        if not args.verbose:
            print(f"🚀 Looking up collections for {address_hint}, {postcode}...")

        collector = HounslowBinCollector(headless=headless, timeout=timeout_ms)
        result = collector.collect_bin_data(address_config)

        # Display results
        output = format_collection_info(result, args.format)
        print(output)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
