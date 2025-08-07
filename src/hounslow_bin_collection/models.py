"""
Data models for Hounslow bin collection system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CollectionInfo:
    """Information about a single collection item."""

    text: str
    type: str = "info"
    dates: Optional[list[str]] = None


@dataclass
class BinCollectionData:
    """Complete bin collection data for an address."""

    address: str
    postcode: str
    uprn: str
    collections: list[CollectionInfo]
    retrieved_at: datetime

    def get_collection_by_type(self, collection_type: str) -> Optional[CollectionInfo]:
        """Get collection info for a specific waste type."""
        for collection in self.collections:
            if collection_type.lower() in collection.text.lower():
                return collection
        return None

    def get_next_dates(self) -> list[str]:
        """Get all upcoming collection dates."""
        for collection in self.collections:
            if collection.type == "dates" and collection.dates:
                return collection.dates
        return []

    def get_general_waste_info(self) -> Optional[CollectionInfo]:
        """Get general waste collection info."""
        return self.get_collection_by_type("general waste")

    def get_recycling_info(self) -> Optional[CollectionInfo]:
        """Get recycling collection info."""
        return self.get_collection_by_type("recycling")

    def get_food_waste_info(self) -> Optional[CollectionInfo]:
        """Get food waste collection info."""
        return self.get_collection_by_type("food waste")

    def get_garden_waste_info(self) -> Optional[CollectionInfo]:
        """Get garden waste collection info."""
        return self.get_collection_by_type("garden waste")


@dataclass
class AddressConfig:
    """Address configuration for bin collection lookup."""

    postcode: str
    address_hint: str

    def __post_init__(self):
        """Validate required fields."""
        if not self.postcode or not self.address_hint:
            raise ValueError("Both postcode and address_hint are required")
