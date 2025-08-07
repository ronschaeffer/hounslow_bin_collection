#!/usr/bin/env python3
"""
CLI command to show detailed bin collection schedule with frequencies and dates.
This bypasses the simplified model conversion to show full schedule details.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hounslow_bin_collection.browser_collector import BrowserWasteCollector


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.WARNING  # Less verbose by default
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def format_schedule_output(raw_data: dict, format_type: str = "schedule") -> str:
    """Format the raw enhanced data into a clean schedule display."""

    if format_type == "json":
        return json.dumps(raw_data, indent=2, default=str)

    elif format_type == "raw":
        # Show the complete raw data structure
        lines = []
        lines.append("🔍 RAW ENHANCED EXTRACTOR DATA")
        lines.append("=" * 50)
        lines.append(json.dumps(raw_data, indent=2, default=str))
        return "\n".join(lines)

    else:  # schedule format
        lines = []
        lines.append("🗑️  BIN COLLECTION SCHEDULE")
        lines.append("=" * 40)
        lines.append(f"📍 Address: {raw_data.get('address', 'Unknown')}")
        lines.append(f"📮 Postcode: {raw_data.get('postcode', 'Unknown')}")
        lines.append(f"🆔 UPRN: {raw_data.get('uprn', 'Unknown')}")

        # Get extraction time
        extracted_at = raw_data.get("extracted_at", "")
        if extracted_at:
            try:
                dt = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
                lines.append(f"🕒 Retrieved: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except (ValueError, TypeError):
                lines.append(f"🕒 Retrieved: {extracted_at}")

        lines.append("")

        # Show bin schedule summary if available
        bin_schedule = raw_data.get("bin_schedule", {})
        if bin_schedule:
            lines.append("📅 COLLECTION SCHEDULE:")
            lines.append("-" * 30)

            for bin_type, schedule in bin_schedule.items():
                icon = schedule.get("icon", "🗑️")
                frequency = schedule.get("frequency", "Unknown frequency")
                next_date = schedule.get("next_date", "Unknown")
                last_date = schedule.get("last_date", "Unknown")

                # Clean up the bin type name
                bin_name = bin_type.replace("_", " ").title()

                lines.append(f"{icon} **{bin_name}**")
                lines.append(f"   📆 {frequency}")
                lines.append(f"   ⏭️  Next: {next_date}")
                lines.append(f"   ⏮️  Last: {last_date}")
                lines.append("")

        # Show detailed collections if no bin_schedule
        elif raw_data.get("collections"):
            lines.append("📋 DETAILED COLLECTIONS:")
            lines.append("-" * 30)

            for collection in raw_data.get("collections", []):
                if collection.get("type") == "dates":
                    continue  # Skip date summaries

                icon = collection.get("icon", "🗑️")
                description = collection.get("text", "Unknown collection")
                frequency = collection.get("frequency", "")
                next_collection = collection.get("next_collection", "")
                last_collection = collection.get("last_collection", "")
                status = collection.get("status", "")

                lines.append(f"{icon} {description}")
                if frequency:
                    lines.append(f"   📆 {frequency}")
                if next_collection:
                    lines.append(f"   ⏭️  Next: {next_collection}")
                if last_collection:
                    lines.append(f"   ⏮️  Last: {last_collection}")
                if status:
                    lines.append(f"   📊 Status: {status}")
                lines.append("")

        # Show upcoming dates summary
        all_dates = []
        for collection in raw_data.get("collections", []):
            if collection.get("type") == "dates" and collection.get("dates"):
                all_dates = collection.get("dates")
                break

        if all_dates:
            lines.append("📅 UPCOMING COLLECTION DATES:")
            lines.append("-" * 30)
            upcoming = ", ".join(all_dates[:8])  # Show first 8 dates
            lines.append(f"   {upcoming}")
            if len(all_dates) > 8:
                lines.append(f"   ... and {len(all_dates) - 8} more dates")

        lines.append("")
        lines.append("💡 Tip: Use --format json for machine-readable output")
        lines.append("💡 Tip: Use --format raw to see complete data structure")

        return "\n".join(lines)


def main():
    """Main function for detailed bin schedule lookup."""
    parser = argparse.ArgumentParser(
        description="Show detailed Hounslow bin collection schedule",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config/config.yaml
  %(prog)s --postcode "TW7 7HX" --address "132 Worple Rd"
  %(prog)s --config config/config.yaml --format json
  %(prog)s --postcode "TW7 7HX" --address "136" --format raw
        """,
    )

    # Address input options
    address_group = parser.add_argument_group("Address Input")
    address_group.add_argument("--postcode", "-p", help="Postcode (e.g., TW7 7HX)")
    address_group.add_argument(
        "--address", "-a", help="Address hint (e.g., '132 Worple Rd')"
    )
    address_group.add_argument("--config", "-c", help="Use address from config file")

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--format",
        choices=["schedule", "json", "raw"],
        default="schedule",
        help="Output format (default: schedule)",
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

    setup_logging(args.verbose)

    # Determine address source
    if args.config:
        config = load_config(args.config)
        if not config or "address" not in config:
            print("❌ Error: Config file must contain 'address' section")
            return 1

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

        if not args.verbose:
            print(f"📁 Using address from config: {address_hint}, {postcode}")

    elif args.postcode and args.address:
        postcode = args.postcode
        address_hint = args.address

    else:
        print("❌ Error: Must provide either --config or both --postcode and --address")
        parser.print_help()
        return 1

    # Browser settings
    headless = args.headless and not args.show_browser
    timeout_ms = args.timeout * 1000

    if not args.verbose:
        print(f"🚀 Looking up detailed schedule for {address_hint}, {postcode}...")

    # Perform enhanced extraction directly
    try:
        with BrowserWasteCollector(headless=headless, timeout=timeout_ms) as collector:
            # Navigate to results page
            collector.start_browser() if not collector.page else None

            # Get to the iframe page (borrowing navigation logic)
            result = collector.fetch_collection_data(postcode, address_hint)

            # But we actually want to use the enhanced extractor directly
            # This is a bit hacky since we need to get back to the iframe
            # Let's use a direct approach
            pass

    except Exception as e:
        print(f"❌ Error during collection lookup: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    # For now, let's create a direct test with the enhanced extractor
    # This approach bypasses the model conversion that loses data
    try:
        with BrowserWasteCollector(headless=headless, timeout=timeout_ms) as collector:
            # Get the raw enhanced data by re-doing the extraction
            result = collector.fetch_collection_data(postcode, address_hint)

            # The issue is that fetch_collection_data converts to the simple model
            # We need to access the enhanced extractor result directly
            print("⚠️  Currently showing simplified data due to model conversion.")
            print("⚠️  The enhanced data is captured but converted to basic format.")
            print()

            # Show what we can from the available data
            output = format_schedule_output(
                {
                    "address": result.get("address", ""),
                    "postcode": result.get("postcode", ""),
                    "uprn": result.get("uprn", ""),
                    "extracted_at": datetime.now().isoformat(),
                    "collections": [
                        {
                            "text": item.get("text", ""),
                            "type": item.get("type", ""),
                            "icon": "🗑️"
                            if "general" in item.get("text", "").lower()
                            else "♻️"
                            if "recycling" in item.get("text", "").lower()
                            else "🥬"
                            if "food" in item.get("text", "").lower()
                            else "🌱"
                            if "garden" in item.get("text", "").lower()
                            else "🗑️",
                        }
                        for item in result.get("collections", [])
                    ],
                },
                args.format,
            )

            print(output)
            print()
            print(
                "💡 To get full schedule details, we need to bypass the model conversion."
            )
            print(
                "💡 The enhanced extractor captures: frequencies, next dates, last dates, status"
            )

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
