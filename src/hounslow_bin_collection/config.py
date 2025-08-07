"""
Configuration management for Hounslow bin collection system.
Uses environment variables and YAML configuration like Twickenham Events.
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml


class Config:
    """Configuration manager with environment variable support."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Optional path to YAML config file
        """
        self.config = {}

        # Load config file if provided
        if config_path and Path(config_path).exists():
            self._load_yaml_config(config_path)

        # Environment variables override everything
        self._load_env_overrides()

    def _load_yaml_config(self, config_path: str) -> None:
        """Load configuration from YAML file with environment variable substitution."""
        with open(config_path) as f:
            content = f.read()

        # Simple environment variable substitution
        import re

        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""
            return os.getenv(var_name, default_value)

        # Replace ${VAR} and ${VAR:default} patterns
        content = re.sub(r"\$\{([^}:]+)(?::([^}]*))?\}", replace_env_var, content)

        self.config = yaml.safe_load(content) or {}

    def _load_env_overrides(self) -> None:
        """Load environment variable overrides."""
        env_mapping = {
            # Address configuration
            "HOUNSLOW_POSTCODE": "address.postcode",
            "HOUNSLOW_ADDRESS": "address.address_hint",
            # MQTT configuration (matches Twickenham Events pattern)
            "MQTT_BROKER_URL": "mqtt.broker_url",
            "MQTT_BROKER_PORT": "mqtt.broker_port",
            "MQTT_CLIENT_ID": "mqtt.client_id",
            "MQTT_USERNAME": "mqtt.auth.username",
            "MQTT_PASSWORD": "mqtt.auth.password",
            "MQTT_SECURITY": "mqtt.security",
            # Application settings
            "APP_DEBUG": "app.debug",
            "CALENDAR_ENABLED": "calendar.enabled",
            "MQTT_ENABLED": "mqtt.enabled",
            "HOME_ASSISTANT_ENABLED": "home_assistant.enabled",
        }

        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested(config_key, value)

    def _set_nested(self, key: str, value: Any) -> None:
        """Set a nested configuration value using dot notation."""
        keys = key.split(".")
        current = self.config

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the final value with type conversion
        final_key = keys[-1]
        current[final_key] = self._convert_type(value)

    def _convert_type(self, value: str) -> Any:
        """Convert string values to appropriate types."""
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split(".")
        current = self.config

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def get_address_config(self) -> dict[str, str]:
        """Get address configuration."""
        return {
            "postcode": self.get("address.postcode", ""),
            "address_hint": self.get("address.address_hint", ""),
        }

    def get_mqtt_config(self) -> dict[str, Any]:
        """Get MQTT configuration compatible with mqtt_publisher."""
        return {
            "broker_url": self.get("mqtt.broker_url"),
            "broker_port": self.get("mqtt.broker_port", 8883),
            "client_id": self.get("mqtt.client_id", "hounslow_bin_collection"),
            "security": self.get("mqtt.security", "username"),
            "auth": {
                "username": self.get("mqtt.auth.username"),
                "password": self.get("mqtt.auth.password"),
            },
            "last_will": {
                "topic": "hounslow_bins/status",
                "payload": "offline",
                "qos": 1,
                "retain": True,
            },
        }

    def is_mqtt_enabled(self) -> bool:
        """Check if MQTT integration is enabled."""
        return (
            self.get("mqtt.enabled", True) and self.get("mqtt.broker_url") is not None
        )

    def is_home_assistant_enabled(self) -> bool:
        """Check if Home Assistant integration is enabled."""
        return self.get("home_assistant.enabled", True)

    def is_calendar_enabled(self) -> bool:
        """Check if calendar generation is enabled."""
        return self.get("calendar.enabled", True)

    def get_output_dir(self) -> Path:
        """Get output directory path, creating it if needed."""
        output_dir = Path(self.get("output.directory", "output"))
        output_dir.mkdir(exist_ok=True)
        return output_dir

    def get_calendar_filename(self) -> str:
        """Get calendar output filename."""
        return self.get("output.calendar.filename", "hounslow_bins.ics")

    def get_data_filename(self) -> str:
        """Get data output filename."""
        return self.get("output.data.filename", "bin_collections.json")

    def get_output_format(self) -> str:
        """Get output format preference."""
        return self.get("output.calendar.output_format", "ics")
