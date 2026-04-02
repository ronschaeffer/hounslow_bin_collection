"""
MQTT integration for bin collection data using ha_mqtt_publisher library.
"""

from datetime import UTC, date, datetime
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

# Short display names matching the council website terminology
WASTE_NAMES = {
    "general_waste": "Black Bin",
    "recycling": "Recycling",
    "food_waste": "Food Waste",
    "garden_waste": "Garden Waste",
}

WASTE_ICONS = {
    "general_waste": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "food_waste": "mdi:leaf",
    "garden_waste": "mdi:tree",
}

WASTE_EMOJI = {
    "general_waste": "\U0001f5d1\ufe0f",  # 🗑️
    "recycling": "\u267b\ufe0f",  # ♻️
    "food_waste": "\U0001f96c",  # 🥬
    "garden_waste": "\U0001f333",  # 🌳
}

WASTE_COLORS = {
    "general_waste": "grey",
    "recycling": "green",
    "food_waste": "green",
    "garden_waste": "brown",
}

TOPIC_PREFIX = "hounslow_bins"
AVAILABILITY_TOPIC = f"{TOPIC_PREFIX}/status"

# Threshold for page accessibility alert (seconds)
PAGE_STALE_THRESHOLD = 86400  # 24 hours


def _now_iso() -> str:
    """UTC timestamp in ISO 8601 with Z suffix."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    if days == 2:
        return "In 2 days"
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

    def publish_bin_data(
        self,
        bin_data: BinCollectionData,
        *,
        success: bool = True,
        error_message: str | None = None,
        last_success_iso: str | None = None,
    ) -> bool:
        """Publish bin collection data to MQTT.

        Args:
            bin_data: Bin collection data to publish
            success: Whether the collection run succeeded
            error_message: Error detail if success is False
            last_success_iso: ISO timestamp of last successful scrape (for
                page accessibility tracking). If None, uses current time
                when success=True.

        Returns:
            True if MQTT publish succeeded, False otherwise
        """
        try:
            logger.info("Publishing bin data for %s", bin_data.address)

            if not self.publisher.connect():
                logger.error("Failed to connect to MQTT broker")
                return False

            now = _now_iso()

            # Extract next collection dates per waste type
            waste_dates = self._extract_waste_dates(bin_data)

            # Build all discovery entities
            entities = self._build_entities(waste_dates)

            # Publish Home Assistant discovery configs
            if self.config.is_home_assistant_enabled():
                publish_discovery_configs(
                    self.config,
                    self.publisher,
                    entities=entities,
                    device=self.device,
                )

            # --- State data per waste type ---
            for waste_type, next_date in waste_dates.items():
                topic = f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state"
                name = WASTE_NAMES.get(waste_type, waste_type.replace("_", " ").title())
                payload = {
                    "date": next_date,
                    "name": name,
                    "emoji": WASTE_EMOJI.get(waste_type, ""),
                    "last_updated": now,
                }
                self.publisher.publish(topic, json.dumps(payload), retain=True)

            # --- Consolidated next collection ---
            self._publish_next_collection(waste_dates, now)

            # --- Diagnostic: status ---
            effective_last_success = last_success_iso
            if success and not effective_last_success:
                effective_last_success = now

            status_payload = self._build_status_payload(
                bin_data, now, success, error_message
            )
            self.publisher.publish(
                f"{TOPIC_PREFIX}/bin_collection_status/state",
                json.dumps(status_payload),
                retain=True,
            )

            # --- Diagnostic: last_run (timestamp) ---
            self.publisher.publish(
                f"{TOPIC_PREFIX}/diagnostics/last_run/state",
                json.dumps({"last_run": now}),
                retain=True,
            )

            # --- Diagnostic: last_run_status ---
            run_status_payload = {
                "status": "success" if success else "error",
                "last_updated": now,
            }
            if error_message:
                run_status_payload["error"] = error_message
            self.publisher.publish(
                f"{TOPIC_PREFIX}/diagnostics/last_run_status/state",
                json.dumps(run_status_payload),
                retain=True,
            )

            # --- Diagnostic: page_accessible (binary_sensor) ---
            page_stale = False
            if effective_last_success:
                try:
                    last_dt = datetime.fromisoformat(
                        effective_last_success.replace("Z", "+00:00")
                    )
                    age_seconds = (datetime.now(UTC) - last_dt).total_seconds()
                    page_stale = age_seconds > PAGE_STALE_THRESHOLD
                except (ValueError, TypeError):
                    page_stale = not success
            else:
                page_stale = not success

            self.publisher.publish(
                f"{TOPIC_PREFIX}/diagnostics/page_accessible/state",
                json.dumps(
                    {
                        "page_accessible": "OFF" if page_stale else "ON",
                        "last_successful_scrape": effective_last_success or "unknown",
                        "last_updated": now,
                    }
                ),
                retain=True,
            )

            # --- Diagnostic: collection_count ---
            active_count = sum(1 for d in waste_dates.values() if d)
            self.publisher.publish(
                f"{TOPIC_PREFIX}/diagnostics/collection_count/state",
                json.dumps(
                    {
                        "count": active_count,
                        "total_types": len(waste_dates),
                        "last_updated": now,
                    }
                ),
                retain=True,
            )

            # --- Diagnostic: sw_version ---
            from .. import __version__

            self.publisher.publish(
                f"{TOPIC_PREFIX}/diagnostics/sw_version/state",
                json.dumps({"version": __version__}),
                retain=True,
            )

            # --- Availability ---
            self.publisher.publish(AVAILABILITY_TOPIC, "online", retain=True)

            self.publisher.disconnect()
            logger.info("Successfully published bin data to MQTT")
            return True

        except Exception as e:
            logger.error("Failed to publish bin data: %s", e)
            if hasattr(self, "publisher"):
                self.publisher.disconnect()
            return False

    def _build_entities(self, waste_dates: dict[str, str | None]) -> list[Entity]:
        """Build all discovery entities."""
        entities: list[Entity] = []

        # Per-waste-type sensors
        for waste_type, next_date in waste_dates.items():
            entities.append(self._create_waste_sensor(waste_type, next_date))

        # Consolidated next collection
        entities.append(self._create_next_collection_sensor())

        # Diagnostic sensors
        entities.append(
            Entity(
                config=self.config,
                device=self.device,
                component="sensor",
                name="Last Run",
                unique_id="last_run",
                state_topic=f"{TOPIC_PREFIX}/diagnostics/last_run/state",
                value_template="{{ value_json.last_run }}",
                device_class="timestamp",
                entity_category="diagnostic",
                icon="mdi:clock-outline",
                availability_topic=AVAILABILITY_TOPIC,
            )
        )

        entities.append(
            Entity(
                config=self.config,
                device=self.device,
                component="sensor",
                name="Last Run Status",
                unique_id="last_run_status",
                state_topic=f"{TOPIC_PREFIX}/diagnostics/last_run_status/state",
                value_template="{{ value_json.status }}",
                json_attributes_topic=f"{TOPIC_PREFIX}/diagnostics/last_run_status/state",
                entity_category="diagnostic",
                icon="mdi:check-circle",
                availability_topic=AVAILABILITY_TOPIC,
            )
        )

        entities.append(
            Entity(
                config=self.config,
                device=self.device,
                component="binary_sensor",
                name="Council Page Accessible",
                unique_id="page_accessible",
                state_topic=f"{TOPIC_PREFIX}/diagnostics/page_accessible/state",
                value_template="{{ value_json.page_accessible }}",
                json_attributes_topic=f"{TOPIC_PREFIX}/diagnostics/page_accessible/state",
                device_class="problem",
                entity_category="diagnostic",
                icon="mdi:web",
                payload_on="OFF",
                payload_off="ON",
                availability_topic=AVAILABILITY_TOPIC,
            )
        )

        entities.append(
            Entity(
                config=self.config,
                device=self.device,
                component="sensor",
                name="Collection Types Found",
                unique_id="collection_count",
                state_topic=f"{TOPIC_PREFIX}/diagnostics/collection_count/state",
                value_template="{{ value_json.count }}",
                json_attributes_topic=f"{TOPIC_PREFIX}/diagnostics/collection_count/state",
                state_class="measurement",
                entity_category="diagnostic",
                icon="mdi:counter",
                availability_topic=AVAILABILITY_TOPIC,
            )
        )

        entities.append(
            Entity(
                config=self.config,
                device=self.device,
                component="sensor",
                name="Software Version",
                unique_id="sw_version",
                state_topic=f"{TOPIC_PREFIX}/diagnostics/sw_version/state",
                value_template="{{ value_json.version }}",
                entity_category="diagnostic",
                icon="mdi:tag",
                availability_topic=AVAILABILITY_TOPIC,
            )
        )

        # Status sensor
        entities.append(self._create_status_sensor())

        # Control buttons
        entities.append(
            Entity(
                config=self.config,
                device=self.device,
                component="button",
                name="Refresh",
                unique_id="refresh",
                command_topic=f"{TOPIC_PREFIX}/cmd/refresh",
                icon="mdi:refresh",
            )
        )

        return entities

    def _build_status_payload(
        self,
        bin_data: BinCollectionData,
        now: str,
        success: bool,
        error_message: str | None,
    ) -> dict:
        """Build the status sensor payload."""
        payload: dict = {
            "status": "online" if success else "error",
            "last_updated": now,
            "address": bin_data.address,
            "postcode": bin_data.postcode,
            "uprn": bin_data.uprn,
            "collection_count": len(bin_data.collections),
        }
        if error_message:
            payload["error"] = error_message

        from .calendar import get_calendar_url

        calendar_url = get_calendar_url(self.config)
        if calendar_url:
            payload["calendar_url"] = calendar_url

        return payload

    def _publish_next_collection(
        self, waste_dates: dict[str, str | None], now: str
    ) -> None:
        """Publish the consolidated next-waste-collection sensor state."""
        soonest_type = None
        soonest_date = None
        for waste_type, iso_date in waste_dates.items():
            if not iso_date:
                continue
            if soonest_date is None or iso_date < soonest_date:
                soonest_date = iso_date
                soonest_type = waste_type

        if soonest_type and soonest_date:
            display_name = WASTE_NAMES.get(
                soonest_type, soonest_type.replace("_", " ").title()
            )
            scheduled = _compute_scheduled_text(soonest_date)
            icon = WASTE_ICONS.get(soonest_type, "mdi:trash-can")
            emoji = WASTE_EMOJI.get(soonest_type, "")
            base_color = WASTE_COLORS.get(soonest_type, "grey")
            icon_color = _compute_icon_color(soonest_date, base_color)
        else:
            display_name = "No Collections Scheduled"
            scheduled = "Check collection schedule"
            icon = "mdi:calendar-clock"
            emoji = ""
            icon_color = "grey"
            soonest_date = None

        payload = {
            "name": display_name,
            "date": soonest_date,
            "scheduled": scheduled,
            "icon": icon,
            "emoji": emoji,
            "icon_color": icon_color,
            "waste_type": soonest_type,
            "last_updated": now,
        }

        self.publisher.publish(
            f"{TOPIC_PREFIX}/next_waste_collection/state",
            json.dumps(payload),
            retain=True,
        )

    def _extract_waste_dates(
        self, bin_data: BinCollectionData
    ) -> dict[str, str | None]:
        """Extract next collection dates for each waste type (YYYY-MM-DD)."""
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
            name=WASTE_NAMES.get(waste_type, waste_type.replace("_", " ").title()),
            unique_id=f"bin_collection_{waste_type}",
            state_topic=f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state",
            value_template="{{ value_json.date }}",
            json_attributes_topic=f"{TOPIC_PREFIX}/bin_collection_{waste_type}/state",
            icon=WASTE_ICONS.get(waste_type, "mdi:delete"),
            availability_topic=AVAILABILITY_TOPIC,
            payload_available="online",
            payload_not_available="offline",
        )

    def _create_next_collection_sensor(self) -> Entity:
        """Create the consolidated next-waste-collection sensor."""
        return Entity(
            config=self.config,
            device=self.device,
            component="sensor",
            name="Next Waste Collection",
            unique_id="next_waste_collection",
            state_topic=f"{TOPIC_PREFIX}/next_waste_collection/state",
            value_template="{{ value_json.name }}",
            json_attributes_topic=f"{TOPIC_PREFIX}/next_waste_collection/state",
            availability_topic=AVAILABILITY_TOPIC,
            payload_available="online",
            payload_not_available="offline",
        )

    def _create_status_sensor(self) -> Entity:
        """Create overall status sensor."""
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
            availability_topic=AVAILABILITY_TOPIC,
            payload_available="online",
            payload_not_available="offline",
        )
