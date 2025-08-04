"""Configuration management for hounslow_bin_collection."""

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """Configuration manager."""

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, looks for config.yaml
                        in the project's config directory.
        """
        if config_path is None:
            # Look for config.yaml in project's config directory
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._config: dict[str, Any] = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._default_config()

        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f) or {}
            return config
        except (yaml.YAMLError, OSError) as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            return self._default_config()

    def _default_config(self) -> dict[str, Any]:
        """Return default configuration."""
        return {
            "app": {
                "name": "hounslow_bin_collection",
                "version": "0.1.0",
                "debug": False,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "settings": {
                "timeout": 30,
                "retry_count": 3,
                "batch_size": 100,
            },
            "address": {
                "postcode": None,
                "address_hint": None,
                "uprn": None,
            },
        }

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            "HOUNSLOW_POSTCODE": "address.postcode",
            "HOUNSLOW_ADDRESS": "address.address_hint",
            "UPRN": "address.uprn",
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self.set(config_key, env_value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'app.name', 'logging.level')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'app.debug')
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)


# Global config instance
config = Config()
