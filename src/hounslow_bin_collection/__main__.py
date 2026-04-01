"""
Command-line interface for Hounslow Bin Collection system.
"""

import argparse
import logging
import sys

from . import (
    AddressConfig,
    BinCollectionCalendar,
    BinCollectionMQTTPublisher,
    Config,
    HounslowBinCollector,
)

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Hounslow Bin Collection System")

    # Global options
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument("--config", type=str, help="path to configuration file")

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="available commands")

    # Collect command
    collect_parser = subparsers.add_parser("collect", help="collect bin data")
    collect_parser.add_argument("--postcode", help="postcode to lookup")
    collect_parser.add_argument(
        "--address-hint", help="address hint for disambiguation"
    )
    collect_parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="run browser in headless mode",
    )
    collect_parser.add_argument(
        "--timeout", type=int, default=30000, help="browser timeout in milliseconds"
    )

    # MQTT command
    mqtt_parser = subparsers.add_parser("mqtt", help="publish data to MQTT")
    mqtt_parser.add_argument("--postcode", help="postcode to lookup")
    mqtt_parser.add_argument("--address-hint", help="address hint for disambiguation")

    # Calendar command
    calendar_parser = subparsers.add_parser("calendar", help="generate ICS calendar")
    calendar_parser.add_argument("--postcode", help="postcode to lookup")
    calendar_parser.add_argument(
        "--address-hint", help="address hint for disambiguation"
    )
    calendar_parser.add_argument("--output", help="output calendar file path")

    # All command (collect + MQTT + calendar)
    all_parser = subparsers.add_parser(
        "all", help="collect data and publish to MQTT and calendar"
    )
    all_parser.add_argument("--postcode", help="postcode to lookup")
    all_parser.add_argument("--address-hint", help="address hint for disambiguation")
    all_parser.add_argument("--output", help="output calendar file path")

    # Status command
    status_parser = subparsers.add_parser("status", help="show next collection dates")
    status_parser.add_argument("--postcode", help="postcode to lookup")
    status_parser.add_argument("--address-hint", help="address hint for disambiguation")

    # Serve command (HTTP server for ICS files)
    serve_parser = subparsers.add_parser("serve", help="serve ICS files over HTTP")
    serve_parser.add_argument(
        "--port", type=int, default=8080, help="HTTP port (default: 8080)"
    )
    serve_parser.add_argument(
        "--host", default="0.0.0.0", help="bind address (default: 0.0.0.0)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Load configuration
        config = Config(args.config)

        # Override with command line arguments where applicable
        if hasattr(args, "postcode") and args.postcode:
            config.config.setdefault("address", {})["postcode"] = args.postcode
        if hasattr(args, "address_hint") and args.address_hint:
            config.config.setdefault("address", {})["address_hint"] = args.address_hint

        # Validate postcode is available from CLI args or config
        if hasattr(args, "postcode") and not config.get("address.postcode"):
            parser.error(
                "postcode is required: use --postcode or set it in config.yaml / HOUNSLOW_POSTCODE"
            )

        # Execute command
        if args.command == "collect":
            return cmd_collect(config, args)
        elif args.command == "mqtt":
            return cmd_mqtt(config, args)
        elif args.command == "calendar":
            return cmd_calendar(config, args)
        elif args.command == "all":
            return cmd_all(config, args)
        elif args.command == "status":
            return cmd_status(config, args)
        elif args.command == "serve":
            return cmd_serve(config, args)
        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error("Command failed: %s", e)
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


def cmd_collect(config: Config, args) -> int:
    """Collect bin data command."""
    logger.info("Collecting bin data...")

    address_config = AddressConfig(
        postcode=config.get("address.postcode"),
        address_hint=config.get("address.address_hint"),
    )

    collector = HounslowBinCollector(
        headless=getattr(args, "headless", True),
        timeout=getattr(args, "timeout", 30000),
    )

    bin_data = collector.collect_bin_data(address_config)

    print(f"\nBin collection data for {bin_data.address}:")
    print(f"Postcode: {bin_data.postcode}")
    print(f"UPRN: {bin_data.uprn}")
    print(f"Retrieved: {bin_data.retrieved_at}")
    print("\nCollections:")

    for collection in bin_data.collections:
        print(f"- {collection.text} ({collection.type})")
        if collection.dates:
            next_dates = bin_data.get_next_dates()
            if next_dates:
                print(f"  Next date: {next_dates[0]}")

    return 0


def cmd_mqtt(config: Config, args) -> int:
    """Publish to MQTT command."""
    if not config.is_mqtt_enabled():
        logger.error("MQTT is not enabled or configured")
        return 1

    logger.info("Publishing to MQTT...")

    # Collect data first
    address_config = AddressConfig(
        postcode=config.get("address.postcode"),
        address_hint=config.get("address.address_hint"),
    )

    collector = HounslowBinCollector()
    bin_data = collector.collect_bin_data(address_config)

    # Publish to MQTT
    mqtt_publisher = BinCollectionMQTTPublisher(config)
    success = mqtt_publisher.publish_bin_data(bin_data)

    if success:
        logger.info("Successfully published to MQTT")
        return 0
    else:
        logger.error("Failed to publish to MQTT")
        return 1


def cmd_calendar(config: Config, args) -> int:
    """Generate calendar command."""
    if not config.is_calendar_enabled():
        logger.error("Calendar generation is not enabled")
        return 1

    logger.info("Generating calendar...")

    # Collect data first
    address_config = AddressConfig(
        postcode=config.get("address.postcode"),
        address_hint=config.get("address.address_hint"),
    )

    collector = HounslowBinCollector()
    bin_data = collector.collect_bin_data(address_config)

    # Generate calendar
    calendar_gen = BinCollectionCalendar(config)
    output_path = calendar_gen.generate_calendar(
        bin_data, getattr(args, "output", None)
    )

    logger.info("Calendar generated: %s", output_path)

    # Show calendar URL if configured
    from .integrations.calendar import get_calendar_url

    calendar_url = get_calendar_url(config)
    if calendar_url:
        print(f"🔗 Calendar URL: {calendar_url}")

    return 0


def cmd_all(config: Config, args) -> int:
    """Run all integrations command."""
    logger.info("Running all integrations...")

    # Collect data first
    address_config = AddressConfig(
        postcode=config.get("address.postcode"),
        address_hint=config.get("address.address_hint"),
    )

    collector = HounslowBinCollector()
    bin_data = collector.collect_bin_data(address_config)

    # Show status
    print(f"\nBin collection data for {bin_data.address}:")
    print(f"Retrieved: {bin_data.retrieved_at}")

    results = []

    # Data export (JSON output like Twickenham Events)
    try:
        output_dir = config.get_output_dir()
        data_filename = config.get_data_filename()
        data_path = output_dir / data_filename

        # Convert to dict for JSON serialization
        data_dict = {
            "last_updated": bin_data.retrieved_at.isoformat(),
            "postcode": bin_data.postcode,
            "address": bin_data.address,
            "uprn": bin_data.uprn,
            "collections": [
                {
                    "text": collection.text,
                    "type": collection.type,
                    "dates": collection.dates if collection.dates else [],
                }
                for collection in bin_data.collections
            ],
        }

        import json

        with open(data_path, "w") as f:
            json.dump(data_dict, f, indent=2)

        results.append(("Data Export", f"✓ ({data_path})"))
    except Exception as e:
        logger.error("Data export failed: %s", e)
        results.append(("Data Export", "✗"))

    # MQTT integration
    if config.is_mqtt_enabled():
        try:
            mqtt_publisher = BinCollectionMQTTPublisher(config)
            success = mqtt_publisher.publish_bin_data(bin_data)
            results.append(("MQTT", "✓" if success else "✗"))
        except Exception as e:
            logger.error("MQTT failed: %s", e)
            results.append(("MQTT", "✗"))
    else:
        results.append(("MQTT", "Disabled"))

    # Calendar integration
    if config.is_calendar_enabled():
        try:
            calendar_gen = BinCollectionCalendar(config)
            output_path = calendar_gen.generate_calendar(
                bin_data, getattr(args, "output", None)
            )
            results.append(("Calendar", f"✓ ({output_path})"))
        except Exception as e:
            logger.error("Calendar failed: %s", e)
            results.append(("Calendar", "✗"))
    else:
        results.append(("Calendar", "Disabled"))

    print("\nIntegration Results:")
    for integration, result in results:
        print(f"- {integration}: {result}")

    return 0


def cmd_status(config: Config, args) -> int:
    """Show status command."""
    logger.info("Checking collection status...")

    # Collect data first
    address_config = AddressConfig(
        postcode=config.get("address.postcode"),
        address_hint=config.get("address.address_hint"),
    )

    collector = HounslowBinCollector()
    bin_data = collector.collect_bin_data(address_config)

    # Generate summary
    calendar_gen = BinCollectionCalendar(config)
    summary = calendar_gen.get_next_collection_summary(bin_data)

    print(f"\nNext bin collections for {bin_data.address}:")
    for waste_type, next_date in summary.items():
        print(f"- {waste_type.replace('_', ' ').title()}: {next_date}")

    return 0


def cmd_serve(config: Config, args) -> int:
    """Serve ICS calendar files over HTTP."""
    from .integrations.web_server import start_server

    output_dir = str(config.get_output_dir())
    logger.info("Starting calendar web server on %s:%s", args.host, args.port)
    start_server(output_dir, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
