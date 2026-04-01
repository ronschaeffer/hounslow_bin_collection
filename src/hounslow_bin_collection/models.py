"""
Data models for Hounslow bin collection system.
"""

from dataclasses import dataclass, field
from datetime import datetime


def _parse_date(date_str: str) -> str | None:
    """Parse DD/MM/YYYY to YYYY-MM-DD, returning None on failure."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        # Already in YYYY-MM-DD format?
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            return None


@dataclass
class CollectionInfo:
    """Information about a single collection item."""

    text: str
    type: str = "info"
    next_collection: str | None = None
    last_collection: str | None = None
    frequency: str = ""
    icon: str = ""

    @property
    def next_date_iso(self) -> str | None:
        """Next collection date in YYYY-MM-DD format."""
        return _parse_date(self.next_collection or "")

    @property
    def last_date_iso(self) -> str | None:
        """Last collection date in YYYY-MM-DD format."""
        return _parse_date(self.last_collection or "")

    @property
    def dates(self) -> list[str] | None:
        """List of dates in YYYY-MM-DD format (next, then last)."""
        result = []
        if self.next_date_iso:
            result.append(self.next_date_iso)
        if self.last_date_iso:
            result.append(self.last_date_iso)
        return result if result else None


@dataclass
class BinCollectionData:
    """Complete bin collection data for an address."""

    address: str
    postcode: str
    uprn: str
    collections: list[CollectionInfo]
    retrieved_at: datetime
    bin_schedule: dict = field(default_factory=dict)

    def get_collection_by_type(self, collection_type: str) -> CollectionInfo | None:
        """Get collection info for a specific waste type."""
        for collection in self.collections:
            if collection_type.lower() in collection.text.lower():
                return collection
        return None

    def get_next_dates(self) -> list[str]:
        """Get all upcoming collection dates in YYYY-MM-DD format."""
        dates = []
        for collection in self.collections:
            if collection.next_date_iso:
                dates.append(collection.next_date_iso)
        return sorted(set(dates))

    def get_general_waste_info(self) -> CollectionInfo | None:
        """Get general waste collection info."""
        return self.get_collection_by_type("general waste")

    def get_recycling_info(self) -> CollectionInfo | None:
        """Get recycling collection info."""
        return self.get_collection_by_type("recycling")

    def get_food_waste_info(self) -> CollectionInfo | None:
        """Get food waste collection info."""
        return self.get_collection_by_type("food waste")

    def get_garden_waste_info(self) -> CollectionInfo | None:
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
