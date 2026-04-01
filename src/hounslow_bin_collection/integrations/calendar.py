"""
ICS calendar integration for bin collection data.
"""

from datetime import datetime, timedelta
import logging

from ics import Calendar, Event
from ics.alarm import DisplayAlarm

from ..config import Config
from ..models import BinCollectionData

logger = logging.getLogger(__name__)


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
        waste_dates = {}

        # Map waste types to search terms
        waste_type_mapping = {
            "general_waste": ["general waste", "household waste", "refuse"],
            "recycling": ["recycling", "recyclable"],
            "food_waste": ["food waste", "food"],
            "garden_waste": ["garden waste", "green waste", "garden"],
        }

        # Get next dates from collections
        next_dates = bin_data.get_next_dates()

        for waste_type, search_terms in waste_type_mapping.items():
            collection = bin_data.get_collection_by_type(search_terms[0])
            if collection and next_dates:
                waste_dates[waste_type] = next_dates[0] if next_dates else None
            else:
                waste_dates[waste_type] = None

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
            # Parse the first date
            collection_date = datetime.strptime(first_date, "%Y-%m-%d")

            # Generate recurring events (assume weekly collections)
            for week_offset in range(0, 52):  # Next 52 weeks
                event_date = collection_date + timedelta(weeks=week_offset)

                # Create event
                event = Event()
                event.name = f"{waste_type.replace('_', ' ').title()} Collection"
                event.begin = event_date  # ics library accepts datetime objects
                event.make_all_day()
                event.description = f"Bin collection for {bin_data.address}"
                event.location = bin_data.address
                event.categories = {"Utilities", "Bin Collection"}  # ics uses sets

                # Add reminders
                # Reminder the evening before at 7 PM
                reminder_time = event_date.replace(hour=19) - timedelta(days=1)
                event.alarms.append(
                    self._create_reminder(reminder_time, "Put bins out tonight")
                )

                # Morning reminder at 6 AM
                morning_reminder = event_date.replace(hour=6)
                event.alarms.append(
                    self._create_reminder(
                        morning_reminder, "Bins are being collected today"
                    )
                )

                calendar.events.add(event)

        except ValueError as e:
            logger.warning("Could not parse date %s: %s", first_date, e)

    def _create_reminder(self, reminder_time: datetime, message: str):
        """Create a reminder alarm.

        Args:
            reminder_time: When to trigger the reminder
            message: Reminder message

        Returns:
            Alarm object
        """
        alarm = DisplayAlarm()
        alarm.trigger = reminder_time
        alarm.display_text = message
        return alarm

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
        # Use the same generation logic but with Outlook-specific formatting
        calendar_path = self.generate_calendar(bin_data, output_path)

        # Post-process for Outlook compatibility if needed
        # Outlook generally handles standard ICS well, but we could add specific tweaks here

        return calendar_path

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
    # Check if calendar export is enabled
    if not config.get("calendar.enabled", False):
        return None

    # Get URL override from config
    url_override = config.get("calendar.calendar_url_override")

    if url_override:
        filename = config.get_calendar_filename()
        # If override doesn't end with filename, append it
        if not url_override.endswith(".ics"):
            return f"{url_override.rstrip('/')}/{filename}"
        return url_override

    return None  # No URL configured
