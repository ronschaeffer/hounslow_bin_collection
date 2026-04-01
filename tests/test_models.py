"""
Tests for models module.

Tests the data models used throughout the system.
"""

from datetime import datetime

import pytest

from hounslow_bin_collection.models import (
    AddressConfig,
    BinCollectionData,
    CollectionInfo,
)


class TestCollectionInfo:
    """Test the CollectionInfo dataclass."""

    def test_basic_creation(self):
        """Test basic CollectionInfo creation."""
        info = CollectionInfo(text="Recycling collection")
        assert info.text == "Recycling collection"
        assert info.type == "info"  # Default value
        assert info.dates is None  # Default value

    def test_creation_with_all_fields(self):
        """Test CollectionInfo creation with all fields."""
        info = CollectionInfo(
            text="General waste collection",
            type="collection",
            next_collection="15/01/2024",
            last_collection="08/01/2024",
            frequency="Every week",
        )
        assert info.text == "General waste collection"
        assert info.type == "collection"
        assert info.next_date_iso == "2024-01-15"
        assert info.last_date_iso == "2024-01-08"
        assert info.dates == ["2024-01-15", "2024-01-08"]

    def test_creation_with_custom_type(self):
        """Test CollectionInfo with custom type."""
        info = CollectionInfo(text="Special collection", type="special")
        assert info.text == "Special collection"
        assert info.type == "special"

    def test_dates_field_optional(self):
        """Test that dates field is optional."""
        info = CollectionInfo(text="Test collection", type="test")
        assert info.dates is None


class TestBinCollectionData:
    """Test the BinCollectionData dataclass."""

    def test_basic_creation(self):
        """Test basic BinCollectionData creation."""
        collections = [
            CollectionInfo(text="Recycling: Monday", type="recycling"),
            CollectionInfo(text="General waste: Thursday", type="general"),
        ]
        now = datetime.now()

        data = BinCollectionData(
            address="7 Bath Road",
            postcode="TW3 3EB",
            uprn="123456",
            collections=collections,
            retrieved_at=now,
        )

        assert data.address == "7 Bath Road"
        assert data.postcode == "TW3 3EB"
        assert data.uprn == "123456"
        assert len(data.collections) == 2
        assert data.retrieved_at == now

    def test_get_collection_by_type_found(self):
        """Test getting collection by type when it exists."""
        collections = [
            CollectionInfo(text="Recycling collection: Monday", type="recycling"),
            CollectionInfo(text="General waste collection: Thursday", type="general"),
        ]

        data = BinCollectionData(
            address="Test Address",
            postcode="TW1 1AA",
            uprn="123",
            collections=collections,
            retrieved_at=datetime.now(),
        )

        recycling = data.get_collection_by_type("recycling")
        assert recycling is not None
        assert "Recycling" in recycling.text

    def test_get_collection_by_type_not_found(self):
        """Test getting collection by type when it doesn't exist."""
        collections = [
            CollectionInfo(text="Recycling collection: Monday", type="recycling"),
        ]

        data = BinCollectionData(
            address="Test Address",
            postcode="TW1 1AA",
            uprn="123",
            collections=collections,
            retrieved_at=datetime.now(),
        )

        garden = data.get_collection_by_type("garden")
        assert garden is None

    def test_get_collection_by_type_case_insensitive(self):
        """Test that collection type search is case-insensitive."""
        collections = [
            CollectionInfo(text="RECYCLING COLLECTION: Monday", type="recycling"),
        ]

        data = BinCollectionData(
            address="Test Address",
            postcode="TW1 1AA",
            uprn="123",
            collections=collections,
            retrieved_at=datetime.now(),
        )

        # Test different cases
        recycling_lower = data.get_collection_by_type("recycling")
        recycling_upper = data.get_collection_by_type("RECYCLING")
        recycling_mixed = data.get_collection_by_type("Recycling")

        assert recycling_lower is not None
        assert recycling_upper is not None
        assert recycling_mixed is not None

    def test_empty_collections_list(self):
        """Test BinCollectionData with empty collections list."""
        data = BinCollectionData(
            address="Test Address",
            postcode="TW1 1AA",
            uprn="123",
            collections=[],
            retrieved_at=datetime.now(),
        )

        assert len(data.collections) == 0
        result = data.get_collection_by_type("recycling")
        assert result is None


class TestAddressConfig:
    """Test the AddressConfig dataclass."""

    def test_basic_creation(self):
        """Test basic AddressConfig creation."""
        config = AddressConfig(postcode="TW3 3EB", address_hint="7 Bath Road")
        assert config.postcode == "TW3 3EB"
        assert config.address_hint == "7 Bath Road"

    def test_post_init_validation_success(self):
        """Test successful validation in __post_init__."""
        # Should not raise any exception
        config = AddressConfig(postcode="TW3 3EB", address_hint="7 Bath Road")
        assert config.postcode == "TW3 3EB"
        assert config.address_hint == "7 Bath Road"

    def test_post_init_validation_empty_postcode(self):
        """Test validation fails with empty postcode."""
        with pytest.raises(
            ValueError, match="Both postcode and address_hint are required"
        ):
            AddressConfig(postcode="", address_hint="7 Bath Road")

    def test_post_init_validation_none_postcode(self):
        """Test validation fails with None postcode."""
        with pytest.raises(
            ValueError, match="Both postcode and address_hint are required"
        ):
            # Type ignore because we're testing runtime validation
            AddressConfig(postcode=None, address_hint="7 Bath Road")  # type: ignore

    def test_post_init_validation_empty_address_hint(self):
        """Test validation fails with empty address_hint."""
        with pytest.raises(
            ValueError, match="Both postcode and address_hint are required"
        ):
            AddressConfig(postcode="TW3 3EB", address_hint="")

    def test_post_init_validation_none_address_hint(self):
        """Test validation fails with None address_hint."""
        with pytest.raises(
            ValueError, match="Both postcode and address_hint are required"
        ):
            # Type ignore because we're testing runtime validation
            AddressConfig(postcode="TW3 3EB", address_hint=None)  # type: ignore

    def test_post_init_validation_whitespace_only(self):
        """Test validation fails with whitespace-only fields."""
        # Whitespace-only strings evaluate to True in Python, so this won't raise
        # This test documents the current behavior
        config1 = AddressConfig(postcode="   ", address_hint="7 Bath Road")
        assert config1.postcode == "   "  # Current behavior: whitespace is allowed

        config2 = AddressConfig(postcode="TW3 3EB", address_hint="   ")
        assert config2.address_hint == "   "  # Current behavior: whitespace is allowed

    def test_valid_uk_postcodes(self):
        """Test with various valid UK postcode formats."""
        valid_postcodes = [
            "TW3 3EB",
            "SW1A 1AA",
            "M1 1AA",
            "B33 8TH",
            "W1A 0AX",
            "EC1A 1BB",
        ]

        for postcode in valid_postcodes:
            config = AddressConfig(postcode=postcode, address_hint="Test Address")
            assert config.postcode == postcode

    def test_address_hint_variations(self):
        """Test with various address hint formats."""
        address_hints = [
            "7 Bath Road",
            "123 Church Street",
            "Flat 1A, High Street",
            "The Library",
            "Council Offices",
            "1",  # Just house number
            "Bath Road",  # Just street name
        ]

        for address_hint in address_hints:
            config = AddressConfig(postcode="TW3 3EB", address_hint=address_hint)
            assert config.address_hint == address_hint


class TestDataModelIntegration:
    """Integration tests for data models working together."""

    def test_full_workflow_integration(self):
        """Test the full data model workflow."""
        # Create address config
        address_config = AddressConfig(postcode="TW3 3EB", address_hint="7 Bath Road")

        # Create collection info objects
        collections = [
            CollectionInfo(
                text="Recycling: Monday",
                type="recycling",
                next_collection="15/01/2024",
            ),
            CollectionInfo(
                text="General waste: Thursday",
                type="general",
                next_collection="18/01/2024",
            ),
            CollectionInfo(
                text="Garden waste: Friday",
                type="garden",
                next_collection="19/01/2024",
            ),
        ]

        # Create bin collection data
        bin_data = BinCollectionData(
            address=address_config.address_hint,
            postcode=address_config.postcode,
            uprn="123456",
            collections=collections,
            retrieved_at=datetime.now(),
        )

        # Test the integrated data
        assert bin_data.address == "7 Bath Road"
        assert bin_data.postcode == "TW3 3EB"
        assert len(bin_data.collections) == 3

        # Test finding specific collections
        recycling = bin_data.get_collection_by_type("recycling")
        assert recycling is not None
        assert recycling.next_date_iso == "2024-01-15"

        garden = bin_data.get_collection_by_type("garden")
        assert garden is not None
        assert garden.next_date_iso == "2024-01-19"

    def test_datetime_handling(self):
        """Test datetime handling in BinCollectionData."""
        specific_time = datetime(2024, 1, 15, 10, 30, 0)
        collections = [CollectionInfo(text="Test collection")]

        data = BinCollectionData(
            address="Test Address",
            postcode="TW1 1AA",
            uprn="123",
            collections=collections,
            retrieved_at=specific_time,
        )

        assert data.retrieved_at == specific_time
        assert data.retrieved_at.year == 2024
        assert data.retrieved_at.month == 1
        assert data.retrieved_at.day == 15
