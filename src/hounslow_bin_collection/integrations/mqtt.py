"""
MQTT integration for bin collection data using ha_mqtt_publisher library.
"""

from datetime import datetime
import logging

from ha_mqtt_publisher.ha_discovery import Device, Sensor, publish_discovery_configs
from ha_mqtt_publisher.publisher import MQTTPublisher

from ..config import Config
from ..models import BinCollectionData

logger = logging.getLogger(__name__)


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

        # Create device for Home Assistant discovery
        self.device = Device(config)

    def publish_bin_data(self, bin_data: BinCollectionData) -> bool:
        """Publish bin collection data to MQTT.

        Args:
            bin_data: Bin collection data to publish

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Publishing bin data for %s", bin_data.address)

            # Connect to MQTT broker
            if not self.publisher.connect():
                logger.error("Failed to connect to MQTT broker")
                return False

            # Get all waste type dates
            waste_dates = self._extract_waste_dates(bin_data)

            # Create and publish sensors for each waste type
            sensors = []
            for waste_type, next_date in waste_dates.items():
                sensor = self._create_waste_sensor(waste_type, next_date, bin_data)
                sensors.append(sensor)

            # Create and publish status sensor
            status_sensor = self._create_status_sensor(bin_data)
            sensors.append(status_sensor)

            # Publish Home Assistant discovery configs
            if self.config.is_home_assistant_enabled():
                publish_discovery_configs(self.publisher, sensors)

            # Publish actual sensor data
            for sensor in sensors:
                topic = f"hounslow_bins/{sensor.object_id}/state"
                payload = sensor.get_state_payload()
                self.publisher.publish(topic, payload, retain=True)

            # Publish enhanced status with calendar URL
            self._publish_enhanced_status(bin_data)

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

    def _create_waste_sensor(
        self, waste_type: str, next_date: str | None, bin_data: BinCollectionData
    ) -> Sensor:
        """Create a waste collection sensor.

        Args:
            waste_type: Type of waste (general_waste, recycling, etc.)
            next_date: Next collection date
            bin_data: Full bin collection data

        Returns:
            Sensor object for this waste type
        """
        # Calculate days until collection
        if next_date:
            try:
                datetime.strptime(next_date, "%Y-%m-%d")  # Validate date format
                # Future enhancement: calculate days until collection
            except ValueError:
                logger.warning("Could not parse date %s", next_date)

        # Create sensor
        sensor = Sensor(
            config=self.config,
            device=self.device,
            name=f"{waste_type.replace('_', ' ').title()} Collection",
            unique_id=f"hounslow_bins_bin_collection_{waste_type}",
            state_topic=f"hounslow_bins/bin_collection_{waste_type}/state",
            device_class="date" if next_date else None,
            icon=self._get_waste_icon(waste_type),
            availability_topic="hounslow_bins/status",
            payload_available="online",
            payload_not_available="offline",
        )

        return sensor

    def _create_status_sensor(self, bin_data: BinCollectionData) -> Sensor:
        """Create overall status sensor.

        Args:
            bin_data: Bin collection data

        Returns:
            Status sensor
        """
        sensor = Sensor(
            config=self.config,
            device=self.device,
            name="Bin Collection Status",
            unique_id="hounslow_bins_bin_collection_status",
            state_topic="hounslow_bins/bin_collection_status/state",
            icon="mdi:delete",
            availability_topic="hounslow_bins/status",
            payload_available="online",
            payload_not_available="offline",
        )

        return sensor

    def _publish_enhanced_status(self, bin_data: BinCollectionData) -> None:
        """Publish enhanced status information including calendar URL.

        Args:
            bin_data: Bin collection data
        """
        from datetime import datetime

        from .calendar import get_calendar_url

        # Create enhanced status payload
        status_payload = {
            "status": "online",
            "last_updated": datetime.now().isoformat(),
            "address": bin_data.address,
            "postcode": bin_data.postcode,
            "uprn": bin_data.uprn,
            "collection_count": len(bin_data.collections),
        }

        # Add calendar URL if configured
        calendar_url = get_calendar_url(self.config)
        if calendar_url:
            status_payload["calendar_url"] = calendar_url

        # Publish to status topic
        self.publisher.publish(
            "hounslow_bins/enhanced_status", status_payload, retain=True
        )

    def _get_waste_icon(self, waste_type: str) -> str:
        """Get icon for waste type.

        Args:
            waste_type: Type of waste

        Returns:
            Material Design icon string
        """
        icons = {
            "general_waste": "mdi:delete",
            "recycling": "mdi:recycle",
            "food_waste": "mdi:food-apple",
            "garden_waste": "mdi:leaf",
        }
        return icons.get(waste_type, "mdi:delete")
