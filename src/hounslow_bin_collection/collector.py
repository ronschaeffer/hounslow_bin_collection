"""
Core bin collection functionality using browser automation.
Refactored from the working browser_collector.py for clean architecture.
"""

from datetime import datetime
import logging

from .browser_collector import BrowserWasteCollector
from .models import AddressConfig, BinCollectionData, CollectionInfo

logger = logging.getLogger(__name__)


class HounslowBinCollector:
    """Core bin collection functionality with clean interface."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """Initialize the collector.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Timeout for page operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout

    def collect_bin_data(self, address_config: AddressConfig) -> BinCollectionData:
        """Collect bin data for the given address.

        Args:
            address_config: Address configuration with postcode and address hint

        Returns:
            BinCollectionData with collection information

        Raises:
            Exception: If data collection fails
        """
        logger.info("Collecting bin data for %s", address_config.postcode)

        try:
            with BrowserWasteCollector(
                headless=self.headless, timeout=self.timeout
            ) as collector:
                result = collector.fetch_collection_data(
                    address_config.postcode, address_config.address_hint
                )

                # Convert to our clean data model
                collections = []
                for item in result.get("collections", []):
                    collection_info = CollectionInfo(
                        text=item.get("text", ""),
                        type=item.get("type", "info"),
                        dates=item.get("dates"),
                    )
                    collections.append(collection_info)

                bin_data = BinCollectionData(
                    address=result.get("address", ""),
                    postcode=result.get("postcode", ""),
                    uprn=result.get("uprn", ""),
                    collections=collections,
                    retrieved_at=datetime.now(),
                )

                logger.info("Successfully collected data for %s", bin_data.address)
                return bin_data

        except Exception as e:
            logger.error("Failed to collect bin data: %s", e)
            raise

    def get_next_collection_date(
        self, bin_data: BinCollectionData, waste_type: str
    ) -> str | None:
        """Get the next collection date for a specific waste type.

        Args:
            bin_data: Bin collection data
            waste_type: Type of waste (general, recycling, food, garden)

        Returns:
            Next collection date as string, or None if not found
        """
        # Get the collection info for this waste type
        collection_info = bin_data.get_collection_by_type(waste_type)
        if not collection_info:
            return None

        # Get next dates from the data
        next_dates = bin_data.get_next_dates()
        if next_dates:
            # Return the first/next date
            return next_dates[0] if next_dates else None

        return None

    def get_all_waste_types(self, bin_data: BinCollectionData) -> dict[str, str | None]:
        """Get next collection dates for all waste types.

        Args:
            bin_data: Bin collection data

        Returns:
            Dictionary mapping waste types to next collection dates
        """
        waste_types = {
            "general_waste": "general waste",
            "recycling": "recycling",
            "food_waste": "food waste",
            "garden_waste": "garden waste",
        }

        result = {}
        for key, waste_type in waste_types.items():
            result[key] = self.get_next_collection_date(bin_data, waste_type)

        return result
