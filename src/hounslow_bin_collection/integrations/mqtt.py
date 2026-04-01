"""
MQTT integration for bin collection data using ha_mqtt_publisher library.
"""

from datetime import date, datetime
import json
import logging

from ha_mqtt_publisher import Device, Entity, publish_discovery_configs
from ha_mqtt_publisher.publisher import MQTTPublisher

from ..config import Config
from ..models import BinCollectionData, _parse_date

logger = logging.getLogger(__name__)

# Waste type to search terms mapping
WASTE_TYPE_MAPPING = {
    "general_waste": ["general waste", "household waste", "refuse"],
    "recycling": ["recycling", "recyclable"],
    "food_waste": ["food waste", "food"],
    "garden_waste": ["garden waste", "green waste", "garden"],
}

WASTE_ICONS = {
    "general_waste": "mdi:delete",
    "recycling": "mdi:recycle",
    "food_waste": "mdi:food-apple",
    "garden_waste": "mdi:leaf",
}

WASTE_COLORS = {
    "general_waste": "grey",
    "recycling": "blue",
    "food_waste": "green",
    "garden_waste": "brown",
}

TOPIC_PREFIX = "hounslow_bins"


def _compute_scheduled_text(iso_date: str) -> str:
    """Compute human-readable scheduled text from YYYY-MM-DD date."""
    try:
        collection_date = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return iso_date
    days = (collection_date - date.today()).days
    if days < 0:
        return "Passed"
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    if days < 7:
        return f"In {days} days"
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return f"{day_names[collection_date.weekday()]} {collection_date.strftime('%d %b')}"


def _compute_icon_color(iso_date: str, base_color: str) -> str:
    """Compute urgency-based icon color from YYYY-MM-DD date."""
    try:
        collection_date = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return "grey"
    days = (collection_date - date.today()).days
    if days == 0:
        return "red"
    if days == 1:
        return "orange"
    if days <= 3:
        return "amber"
    return base_color


class BinCollectionMQTTPublisher:
    """Publishes bin collection data to MQTT with Home Assistant discovery."""

    def __init__(self, config: Config):
        """Initialize MQTT publisher.

        Args:
            config: Configuration containing MQTT settings
        """
        self.config = config
        mqtt_config = config.get_mqtt_config()

        self.publisher = MQTTPublisher(
            broker_url=mqtt_config["broker_url"],
            broker_port=mqtt_config["broker_port"],
            client_id=mqtt_config["client_id"],
            security=mqtt_config["security"],
            auth=mqtt_config["auth"],
            last_will=mqtt_config["last_will"],
        )

        self.device = Device(
            config,
            identifiers=["hounslow_bins"],
            name=config.get("app.name", "Hounslow Bin Collection"),
            manufacturer=config.get("app.manufacturer", "ronschaeffer"),
            model=config.get("app.model", "Hounslow Bins"),
            sw_version=config.get("app.sw_version", "0.1.0"),
        )

    def publish_bin_data(self, bin_data: BinCollectionData) -> bool:
        """Publish bin collection data to MQTT.

        Args:
            bin_data: Bin collection data to publish

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Publishing bin data for %s", bin_data.address)

            if not self.publisher.connect():
                logger.error("Failed to connect to MQTT broker")
                return False

            # Extract next collection dates per waste type
            waste_dates = self._extract_waste_dates(bin_data)

            # Build discovery entities
            entities = []
            for waste_type, next_date in waste_dates.items():
                entities.append(self._create_waste_sensor(waste_type, next_date))

            # Consolidated "next collection" sensor
            entities.append(self._create_next_collection_sensor())

            # Status sensor
            entities.append(self._create_status_sensor())

            # Publish Home Assistant discovery configs
            if self.config.is_home_assistant_enabled():
                publish_discovery_configs(
                    self.config,
                    self.publisher,
                    entities=entities,
                    device=self.device,
                )

            # Publish state data for each waste type
            for waste_type, next_date in waste_dates.items():
                topic = f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state"
                payload = {
                    "date": next_date,
                    "waste_type": waste_type.replace("_", " ").title(),
                    "last_updated": datetime.now().isoformat(),
                }
                self.publisher.publish(topic, json.dumps(payload), retain=True)

            # Publish consolidated next collection sensor
            self._publish_next_collection(waste_dates)

            # Publish status
            status_payload = {
                "status": "online",
                "last_updated": datetime.now().isoformat(),
                "address": bin_data.address,
                "postcode": bin_data.postcode,
                "uprn": bin_data.uprn,
                "collection_count": len(bin_data.collections),
            }

            from .calendar import get_calendar_url

            calendar_url = get_calendar_url(self.config)
            if calendar_url:
                status_payload["calendar_url"] = calendar_url

            self.publisher.publish(
                f"{TOPIC_PREFIX}/bin_collection_status/state",
                json.dumps(status_payload),
                retain=True,
            )

            # Publish availability
            self.publisher.publish(f"{TOPIC_PREFIX}/status", "online", retain=True)

            self.publisher.disconnect()
            logger.info("Successfully published bin data to MQTT")
            return True

        except Exception as e:
            logger.error("Failed to publish bin data: %s", e)
            if hasattr(self, "publisher"):
                self.publisher.disconnect()
            return False

    def _publish_next_collection(self, waste_dates: dict[str, str | None]) -> None:
        """Publish the consolidated next-waste-collection sensor state.

        Finds the soonest collection across all waste types and publishes
        state + attributes for the mushroom dashboard card.
        """
        # Find soonest collection
        soonest_type = None
        soonest_date = None
        for waste_type, iso_date in waste_dates.items():
            if not iso_date:
                continue
            if soonest_date is None or iso_date < soonest_date:
                soonest_date = iso_date
                soonest_type = waste_type

        if soonest_type and soonest_date:
            display_name = soonest_type.replace("_", " ").title() + " Collection"
            scheduled = _compute_scheduled_text(soonest_date)
            icon = WASTE_ICONS.get(soonest_type, "mdi:delete")
            base_color = WASTE_COLORS.get(soonest_type, "grey")
            icon_color = _compute_icon_color(soonest_date, base_color)
        else:
            display_name = "No Collections Scheduled"
            scheduled = "Check collection schedule"
            icon = "mdi:calendar-clock"
            icon_color = "grey"
            soonest_date = None

        payload = {
            "name": display_name,
            "date": soonest_date,
            "scheduled": scheduled,
            "icon": icon,
            "icon_color": icon_color,
            "waste_type": soonest_type,
            "last_updated": datetime.now().isoformat(),
        }

        self.publisher.publish(
            f"{TOPIC_PREFIX}/next_waste_collection/state",
            json.dumps(payload),
            retain=True,
        )

    def _extract_waste_dates(
        self, bin_data: BinCollectionData
    ) -> dict[str, str | None]:
        """Extract next collection dates for each waste type.

        Args:
            bin_data: Bin collection data

        Returns:
            Dictionary mapping waste types to next collection dates (YYYY-MM-DD)
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

    def _create_waste_sensor(self, waste_type: str, next_date: str | None) -> Entity:
        """Create a waste collection sensor for discovery."""
        return Entity(
            config=self.config,
            device=self.device,
            component="sensor",
            name=f"{waste_type.replace('_', ' ').title()} Collection",
            unique_id=f"bin_collection_{waste_type}",
            state_topic=f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state",
            value_template="{{ value_json.date }}",
            json_attributes_topic=f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state",
            icon=WASTE_ICONS.get(waste_type, "mdi:delete"),
            availability_topic=f"{TOPIC_PREFIX}/status",
            payload_available="online",
            payload_not_available="offline",
        )

    def _create_next_collection_sensor(self) -> Entity:
        """Create the consolidated next-waste-collection sensor for discovery."""
        return Entity(
            config=self.config,
            device=self.device,
            component="sensor",
            name="Next Waste Collection",
            unique_id="next_waste_collection",
            state_topic=f"{TOPIC_PREFIX}/next_waste_collection/state",
            value_template="{{ value_json.name }}",
            json_attributes_topic=f"{TOPIC_PREFIX}/next_waste_collection/state",
            icon="mdi:calendar-clock",
            availability_topic=f"{TOPIC_PREFIX}/status",
            payload_available="online",
            payload_not_available="offline",
        )

    def _create_status_sensor(self) -> Entity:
        """Create overall status sensor for discovery."""
        return Entity(
            config=self.config,
            device=self.device,
            component="sensor",
            name="Bin Collection Status",
            unique_id="bin_collection_status",
            state_topic=f"{TOPIC_PREFIX}/bin_collection_status/state",
            value_template="{{ value_json.status }}",
            json_attributes_topic=f"{TOPIC_PREFIX}/bin_collection_status/state",
            icon="mdi:delete",
            entity_category="diagnostic",
            availability_topic=f"{TOPIC_PREFIX}/status",
            payload_available="online",
            payload_not_available="offline",
        )
