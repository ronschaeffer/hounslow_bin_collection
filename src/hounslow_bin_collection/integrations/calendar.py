"""
ICS calendar integration for bin collection data.
"""

from datetime import datetime, timedelta
import logging

from ics import Calendar, Event
from ics.alarm import DisplayAlarm

from ..config import Config
from ..models import BinCollectionData, _parse_date

# Short display names matching the council website terminology
WASTE_NAMES = {
    "general_waste": "Black Bin",
    "recycling": "Recycling",
    "food_waste": "Food Waste",
    "garden_waste": "Garden Waste",
}

logger = logging.getLogger(__name__)

# Waste type to search terms mapping (shared with MQTT integration)
WASTE_TYPE_MAPPING = {
    "general_waste": ["general waste", "household waste", "refuse"],
    "recycling": ["recycling", "recyclable"],
    "food_waste": ["food waste", "food"],
    "garden_waste": ["garden waste", "green waste", "garden"],
}


class BinCollectionCalendar:
    """Creates ICS calendar files for bin collection dates."""

    def __init__(self, config: Config):
        """Initialize calendar generator.

        Args:
            config: Configuration containing calendar settings
        """
        self.config = config

    def generate_calendar(
        self, bin_data: BinCollectionData, output_path: str | None = None
    ) -> str:
        """Generate ICS calendar file for bin collection dates.

        Args:
            bin_data: Bin collection data
            output_path: Optional output file path

        Returns:
            Path to generated calendar file

        Raises:
            Exception: If calendar generation fails
        """
        try:
            logger.info("Generating calendar for %s", bin_data.address)

            calendar = Calendar()

            # Add events for each collection type
            waste_dates = self._extract_waste_dates(bin_data)
            for waste_type, next_date in waste_dates.items():
                if next_date:
                    self._add_collection_events(
                        calendar, waste_type, next_date, bin_data
                    )

            # Determine output path
            if not output_path:
                output_dir = self.config.get_output_dir()
                filename = self.config.get_calendar_filename()
                output_path = str(output_dir / filename)

            # Write calendar file
            with open(output_path, "w") as f:
                f.writelines(calendar.serialize_iter())

            logger.info("Calendar generated: %s", output_path)
            return output_path

        except Exception as e:
            logger.error("Failed to generate calendar: %s", e)
            raise

    def _extract_waste_dates(
        self, bin_data: BinCollectionData
    ) -> dict[str, str | None]:
        """Extract next collection dates for each waste type.

        Args:
            bin_data: Bin collection data

        Returns:
            Dictionary mapping waste types to next collection dates
        """
        waste_dates: dict[str, str | None] = {}

        # Prefer bin_schedule (pre-parsed by extractor) over text matching
        if bin_data.bin_schedule:
            for waste_type in WASTE_TYPE_MAPPING:
                schedule = bin_data.bin_schedule.get(waste_type, {})
                next_date = schedule.get("next_date", "")
                waste_dates[waste_type] = _parse_date(next_date)
            return waste_dates

        # Fallback: search collections by text, preferring entries with dates
        for waste_type, search_terms in WASTE_TYPE_MAPPING.items():
            found_date = None
            for term in search_terms:
                for collection in bin_data.collections:
                    if (
                        term.lower() in collection.text.lower()
                        and collection.next_date_iso
                    ):
                        found_date = collection.next_date_iso
                        break
                if found_date:
                    break
            waste_dates[waste_type] = found_date

        return waste_dates

    def _add_collection_events(
        self,
        calendar: Calendar,
        waste_type: str,
        first_date: str,
        bin_data: BinCollectionData,
    ):
        """Add collection events to calendar.

        Args:
            calendar: ICS calendar object
            waste_type: Type of waste
            first_date: First collection date
            bin_data: Bin collection data
        """
        try:
            collection_date = datetime.strptime(first_date, "%Y-%m-%d")

            # Generate recurring events (assume weekly collections for 52 weeks)
            for week_offset in range(52):
                event_date = collection_date + timedelta(weeks=week_offset)

                event = Event()
                event.name = WASTE_NAMES.get(
                    waste_type, waste_type.replace("_", " ").title()
                )
                event.begin = event_date
                event.make_all_day()
                event.description = f"Bin collection for {bin_data.address}"
                event.location = bin_data.address
                event.categories = {"Utilities", "Bin Collection"}

                # Evening reminder: 5 hours before end of day = ~7 PM evening before
                evening_alarm = DisplayAlarm()
                evening_alarm.trigger = timedelta(hours=-29)
                evening_alarm.display_text = "Put bins out tonight"
                event.alarms.append(evening_alarm)

                # Morning reminder: 6 AM on collection day = 18 hours before end of day
                morning_alarm = DisplayAlarm()
                morning_alarm.trigger = timedelta(hours=-18)
                morning_alarm.display_text = "Bins are being collected today"
                event.alarms.append(morning_alarm)

                calendar.events.add(event)

        except ValueError as e:
            logger.warning("Could not parse date %s: %s", first_date, e)

    def generate_outlook_calendar(
        self, bin_data: BinCollectionData, output_path: str | None = None
    ) -> str:
        """Generate Outlook-compatible ICS calendar.

        Args:
            bin_data: Bin collection data
            output_path: Optional output file path

        Returns:
            Path to generated calendar file
        """
        return self.generate_calendar(bin_data, output_path)

    def get_next_collection_summary(
        self, bin_data: BinCollectionData
    ) -> dict[str, str]:
        """Get a summary of next collection dates.

        Args:
            bin_data: Bin collection data

        Returns:
            Dictionary with waste types and next collection dates
        """
        waste_dates = self._extract_waste_dates(bin_data)
        summary = {}

        for waste_type, next_date in waste_dates.items():
            if next_date:
                try:
                    collection_date = datetime.strptime(next_date, "%Y-%m-%d")
                    days_until = (collection_date.date() - datetime.now().date()).days

                    if days_until == 0:
                        summary[waste_type] = "Today"
                    elif days_until == 1:
                        summary[waste_type] = "Tomorrow"
                    elif days_until < 7:
                        summary[waste_type] = f"In {days_until} days"
                    else:
                        summary[waste_type] = collection_date.strftime("%B %d, %Y")
                except ValueError:
                    summary[waste_type] = next_date
            else:
                summary[waste_type] = "Unknown"

        return summary


def get_calendar_url(config: Config) -> str | None:
    """
    Generate calendar subscription URL for MQTT status publishing.

    Args:
        config: Configuration object

    Returns:
        Calendar URL or None if not configured
    """
    if not config.get("calendar.enabled", False):
        return None

    url_override = config.get("calendar.calendar_url_override")
    if url_override:
        filename = config.get_calendar_filename()
        if not url_override.endswith(".ics"):
            return f"{url_override.rstrip('/')}/{filename}"
        return url_override

    return None
