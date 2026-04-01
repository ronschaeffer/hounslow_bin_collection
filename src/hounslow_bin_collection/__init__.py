"""
Hounslow Bin Collection - Modern bin collection monitoring system.

This package provides:
- Browser-based data collection from Hounslow Council website
- MQTT integration with Home Assistant discovery
- ICS calendar generation for collection reminders
- Clean modular architecture separating core functionality from integrations
"""

from .collector import HounslowBinCollector
from .config import Config
from .integrations import BinCollectionCalendar, BinCollectionMQTTPublisher
from .models import AddressConfig, BinCollectionData, CollectionInfo
from .version import get_dynamic_version

__version__ = get_dynamic_version()
__author__ = "ronschaeffer"
__email__ = "ron@ronschaeffer.com"

__all__ = [
    "AddressConfig",
    # Integrations
    "BinCollectionCalendar",
    "BinCollectionData",
    "BinCollectionMQTTPublisher",
    "CollectionInfo",
    # Core functionality
    "Config",
    "HounslowBinCollector",
]
