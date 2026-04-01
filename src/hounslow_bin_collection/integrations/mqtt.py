"""
MQTT integration for bin collection data using ha_mqtt_publisher library.
"""

from datetime import datetime
import json
import logging

from ha_mqtt_publisher import Device, Entity, publish_discovery_configs
from ha_mqtt_publisher.publisher import MQTTPublisher

from ..config import Config
from ..models import BinCollectionData

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

TOPIC_PREFIX = "hounslow_bins"


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
            sensors = []
            for waste_type, next_date in waste_dates.items():
                sensor = self._create_waste_sensor(waste_type, next_date)
                sensors.append(sensor)

            status_sensor = self._create_status_sensor()
            sensors.append(status_sensor)

            # Publish Home Assistant discovery configs
            if self.config.is_home_assistant_enabled():
                publish_discovery_configs(
                    self.config,
                    self.publisher,
                    entities=sensors,
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

            # Publish status
            status_payload = {
                "status": "online",
                "last_updated": datetime.now().isoformat(),
                "address": bin_data.address,
                "postcode": bin_data.postcode,
                "uprn": bin_data.uprn,
                "collection_count": len(bin_data.collections),
            }

            # Add calendar URL if configured
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

        for waste_type, search_terms in WASTE_TYPE_MAPPING.items():
            # Try each search term until we find a match
            found_date = None
            for term in search_terms:
                collection = bin_data.get_collection_by_type(term)
                if collection and collection.dates:
                    found_date = collection.dates[0]
                    break
            waste_dates[waste_type] = found_date

        return waste_dates

    def _create_waste_sensor(self, waste_type: str, next_date: str | None) -> Entity:
        """Create a waste collection sensor for discovery.

        Args:
            waste_type: Type of waste (general_waste, recycling, etc.)
            next_date: Next collection date

        Returns:
            Entity object for this waste type
        """
        return Entity(
            config=self.config,
            device=self.device,
            component="sensor",
            name=f"{waste_type.replace('_', ' ').title()} Collection",
            unique_id=f"bin_collection_{waste_type}",
            state_topic=f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state",
            value_template="{{ value_json.date }}",
            json_attributes_topic=f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state",
            device_class="date" if next_date else None,
            icon=WASTE_ICONS.get(waste_type, "mdi:delete"),
            availability_topic=f"{TOPIC_PREFIX}/status",
            payload_available="online",
            payload_not_available="offline",
        )

    def _create_status_sensor(self) -> Entity:
        """Create overall status sensor for discovery.

        Returns:
            Status sensor
        """
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
