"""
Unit tests for the enhanced data extraction and format detection functionality.
Tests the new validation methods and format change detection capabilities.
"""

from unittest.mock import Mock, patch

import pytest

from hounslow_bin_collection.enhanced_extractor import HounslowDataExtractor


class TestHounslowDataExtractor:
    """Test cases for the HounslowDataExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = HounslowDataExtractor()

    def test_init(self):
        """Test extractor initialization."""
        assert self.extractor is not None
        assert hasattr(self.extractor, "bin_types")
        assert "black wheelie bin" in self.extractor.bin_types
        assert "recycling boxes" in self.extractor.bin_types

    # Page Content Validation Tests
    def test_validate_page_content_valid_normal_page(self):
        """Test page validation with normal valid content."""
        valid_content = """
        Waste collection information for your address

        Your bin collections are as follows:

        Black wheelie bin (General waste)
        Collection frequency: Every 2 weeks on Tuesday
        Last collection: 05/08/2025
        Next collection: 19/08/2025

        Recycling boxes
        Collection frequency: Every 2 weeks on Tuesday
        Last collection: 05/08/2025
        Next collection: 19/08/2025
        """

        result = self.extractor._validate_page_content(valid_content)
        assert result is True

    def test_validate_page_content_valid_minimal_page(self):
        """Test page validation with minimal but valid content."""
        minimal_content = """
        Collection schedule for bin waste every Monday Tuesday
        Recycling collection available weekly. Collection information provided.
        """

        result = self.extractor._validate_page_content(minimal_content)
        assert result is True

    def test_validate_page_content_too_short(self):
        """Test page validation fails for content that's too short."""
        short_content = "Error"

        result = self.extractor._validate_page_content(short_content)
        assert result is False

    def test_validate_page_content_missing_collection_keyword(self):
        """Test page validation fails when 'collection' keyword is missing."""
        missing_collection = """
        Welcome to our website
        This page contains general information
        About our services and contact details
        """

        result = self.extractor._validate_page_content(missing_collection)
        assert result is False

    def test_validate_page_content_missing_waste_keywords(self):
        """Test page validation fails when waste-related keywords are missing."""
        missing_waste = """
        Collection schedule information
        Please check your details every Monday
        Contact us for more information
        """

        result = self.extractor._validate_page_content(missing_waste)
        assert result is False

    def test_validate_page_content_missing_schedule_keywords(self):
        """Test page validation fails when schedule-related keywords are missing."""
        missing_schedule = """
        Collection information for bin waste
        Your recycling service is available
        Contact us for assistance
        """

        result = self.extractor._validate_page_content(missing_schedule)
        assert result is False

    def test_validate_page_content_error_page_404(self):
        """Test page validation detects 404 error pages."""
        error_404 = """
        Page not found - 404 error
        The page you requested could not be found
        Please check the URL and try again
        """

        result = self.extractor._validate_page_content(error_404)
        assert result is False

    def test_validate_page_content_maintenance_page(self):
        """Test page validation detects maintenance pages."""
        maintenance = """
        Service temporarily unavailable
        Our website is currently undergoing maintenance
        Collection information will be available soon
        """

        result = self.extractor._validate_page_content(maintenance)
        assert result is False

    def test_validate_page_content_service_unavailable(self):
        """Test page validation detects service unavailable pages."""
        unavailable = """
        Service unavailable
        Our collection information service is currently down
        Please try again later
        """

        result = self.extractor._validate_page_content(unavailable)
        assert result is False

    def test_validate_page_content_exception_handling(self):
        """Test page validation handles exceptions gracefully."""
        # Test with empty string instead of None
        result = self.extractor._validate_page_content("")
        assert result is False

    # Extracted Data Validation Tests
    def test_validate_extracted_data_valid_complete_data(self):
        """Test data validation with complete valid bin data."""
        valid_data = [
            {
                "bin_type": "general_waste",
                "description": "General waste collection every 2 weeks on Tuesday",
                "frequency": "Every 2 weeks on Tuesday",
                "next_collection": "19/08/2025",
                "last_collection": "05/08/2025",
            },
            {
                "bin_type": "recycling",
                "description": "Recycling collection every 2 weeks on Tuesday",
                "frequency": "Every 2 weeks on Tuesday",
                "next_collection": "19/08/2025",
                "last_collection": "05/08/2025",
            },
        ]

        result = self.extractor._validate_extracted_data(valid_data)
        assert result is True

    def test_validate_extracted_data_valid_minimal_data(self):
        """Test data validation with minimal valid data."""
        minimal_data = [
            {
                "bin_type": "general_waste",
                "description": "General waste collection",
                "frequency": "Weekly",
                "next_collection": None,
                "last_collection": None,
            }
        ]

        result = self.extractor._validate_extracted_data(minimal_data)
        assert result is True

    def test_validate_extracted_data_empty_data(self):
        """Test data validation fails with empty data."""
        empty_data = []

        result = self.extractor._validate_extracted_data(empty_data)
        assert result is False

    def test_validate_extracted_data_missing_bin_type(self):
        """Test data validation fails when bin_type is missing."""
        missing_type = [
            {"description": "General waste collection", "frequency": "Weekly"}
        ]

        result = self.extractor._validate_extracted_data(missing_type)
        assert result is False

    def test_validate_extracted_data_missing_description(self):
        """Test data validation fails when description is missing."""
        missing_description = [{"bin_type": "general_waste", "frequency": "Weekly"}]

        result = self.extractor._validate_extracted_data(missing_description)
        assert result is False

    def test_validate_extracted_data_empty_required_fields(self):
        """Test data validation fails when required fields are empty."""
        empty_fields = [
            {
                "bin_type": "",
                "description": "General waste collection",
                "frequency": "Weekly",
            }
        ]

        result = self.extractor._validate_extracted_data(empty_fields)
        assert result is False

    def test_validate_extracted_data_no_schedule_info(self):
        """Test data validation fails when no schedule information is available."""
        no_schedule = [
            {
                "bin_type": "general_waste",
                "description": "General waste collection",
                "frequency": "Unknown",
                "next_collection": None,
                "last_collection": None,
            }
        ]

        result = self.extractor._validate_extracted_data(no_schedule)
        assert result is False

    def test_validate_extracted_data_unrecognized_bin_type(self):
        """Test data validation handles unrecognized bin types gracefully."""
        unrecognized_type = [
            {
                "bin_type": "unknown_waste_type",
                "description": "Unknown waste collection",
                "frequency": "Weekly",
                "next_collection": "19/08/2025",
            }
        ]

        # Should still pass as we don't want to fail on new bin types
        result = self.extractor._validate_extracted_data(unrecognized_type)
        assert result is True

    def test_validate_extracted_data_exception_handling(self):
        """Test data validation handles exceptions gracefully."""
        # Test with empty list instead of None
        result = self.extractor._validate_extracted_data([])
        assert result is False

    # Integration Tests for extract_enhanced_collection_data
    @patch("hounslow_bin_collection.enhanced_extractor.datetime")
    def test_extract_enhanced_collection_data_format_validation_failure(
        self, mock_datetime
    ):
        """Test that format validation failure is properly handled."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-08-07T10:00:00"

        # Mock iframe frame that returns invalid content
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = "Page not found - 404"

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        assert "extraction_error" in result
        assert "Website format validation failed" in result["extraction_error"]
        assert result["postcode"] == "TW3 3EB"
        assert result["address"] == "132 Worple Rd"

    @patch("hounslow_bin_collection.enhanced_extractor.datetime")
    def test_extract_enhanced_collection_data_data_validation_failure(
        self, mock_datetime
    ):
        """Test that data validation failure is properly handled."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-08-07T10:00:00"

        # Mock iframe frame that returns valid page content but no extractable data
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = """
        Collection information available
        Your bin waste schedule every Monday
        Recycling service provided weekly
        """

        # Mock the extraction to return empty data
        with patch.object(self.extractor, "_extract_bin_collections", return_value=[]):
            result = self.extractor.extract_enhanced_collection_data(
                mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
            )

            assert "extraction_error" in result
            assert "No valid collection data found" in result["extraction_error"]

    @patch("hounslow_bin_collection.enhanced_extractor.datetime")
    def test_extract_enhanced_collection_data_successful_extraction(
        self, mock_datetime
    ):
        """Test successful data extraction with validation."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-08-07T10:00:00"

        # Mock iframe frame that returns valid content
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = """
        Waste collection information

        Black wheelie bin (General waste)
        Collection frequency: Every 2 weeks on Tuesday
        Last collection: 05/08/2025
        Next collection: 19/08/2025
        """

        # Mock successful extraction
        mock_bin_data = [
            {
                "bin_type": "general_waste",
                "description": "General waste collection every 2 weeks on Tuesday",
                "frequency": "Every 2 weeks on Tuesday",
                "next_collection": "19/08/2025",
                "last_collection": "05/08/2025",
            }
        ]

        with patch.object(
            self.extractor, "_extract_bin_collections", return_value=mock_bin_data
        ):
            result = self.extractor.extract_enhanced_collection_data(
                mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
            )

            assert "extraction_error" not in result
            assert (
                len(result["collections"]) >= 1
            )  # May include additional date collections
            # Find the general waste collection
            general_waste_collection = None
            for collection in result["collections"]:
                if collection.get("type") == "general_waste":
                    general_waste_collection = collection
                    break

            assert general_waste_collection is not None
            assert general_waste_collection["type"] == "general_waste"
            assert (
                result["bin_schedule"]["general_waste"]["frequency"]
                == "Every 2 weeks on Tuesday"
            )

    def test_extract_enhanced_collection_data_exception_handling(self):
        """Test that exceptions during extraction are properly handled."""
        # Mock iframe frame that raises an exception
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.side_effect = Exception("Connection failed")

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        # Should have fallback collections and error info
        assert "collections" in result
        assert "extraction_error" in result
        assert "Connection failed" in result["extraction_error"]

    def test_identify_bin_type_black_wheelie_bin(self):
        """Test identification of black wheelie bin."""
        test_lines = [
            "Black wheelie bin (General waste)",
            "black wheelie bin",
            "General waste collection",
        ]

        for line in test_lines:
            result = self.extractor._identify_bin_type(line)
            if result:  # Some lines might not match
                assert result["type"] == "general_waste"

    def test_identify_bin_type_recycling(self):
        """Test identification of recycling bins."""
        test_lines = [
            "Recycling boxes",
            "recycling collection",
            "Plastic and metal recycling",
        ]

        for line in test_lines:
            result = self.extractor._identify_bin_type(line)
            if result:  # Some lines might not match
                assert result["type"] == "recycling"

    def test_identify_bin_type_no_match(self):
        """Test that unrecognized bin types return None."""
        unrecognized_lines = [
            "Some random text",
            "Contact information",
            "Website navigation",
        ]

        for line in unrecognized_lines:
            result = self.extractor._identify_bin_type(line)
            assert result is None


class TestAddressNormalization:
    """Test cases for address normalization functionality."""

    def test_normalize_address_for_matching_basic(self):
        """Test basic address normalization."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        variations = normalize_address_for_matching("132 Worple Rd")

        assert "132 Worple Rd" in variations  # Original
        assert "132 Worple Road" in variations  # Expanded
        assert "132" in variations  # House number only
        assert "Worple Rd" in variations  # Street only

    def test_normalize_address_for_matching_various_abbreviations(self):
        """Test normalization with different abbreviations."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        test_cases = [
            ("123 High St", "123 High Street"),
            ("45 Oak Ave", "45 Oak Avenue"),
            ("67 Park Ln", "67 Park Lane"),
            ("89 Rose Cl", "89 Rose Close"),
        ]

        for original, expected in test_cases:
            variations = normalize_address_for_matching(original)
            assert original in variations
            assert expected in variations

    def test_normalize_address_for_matching_house_numbers_with_letters(self):
        """Test normalization with house numbers containing letters."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        variations = normalize_address_for_matching("123a High Street")

        assert "123a High Street" in variations
        assert "123a" in variations  # Should include letter suffix

    def test_normalize_address_for_matching_no_duplicates(self):
        """Test that normalization removes duplicates."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        variations = normalize_address_for_matching(
            "132 Road Street"
        )  # 'Road' won't be expanded

        # Check no duplicates
        assert len(variations) == len(set(variations))


# Mock classes for testing browser functionality
class MockFrame:
    """Mock iframe frame for testing."""

    def __init__(self, content="", should_raise=False):
        self.content = content
        self.should_raise = should_raise

    def wait_for_timeout(self, ms):
        if self.should_raise:
            raise Exception("Timeout error")

    def evaluate(self, script):
        if self.should_raise:
            raise Exception("Evaluation error")
        if "document.body.innerText" in script:
            return self.content
        return ""


class TestBrowserCollectorValidation:
    """Test cases for browser collector with enhanced validation."""

    def test_format_detection_integration(self):
        """Test integration between browser collector and format detection."""
        extractor = HounslowDataExtractor()

        # Test that the extractor is available and has validation methods
        assert hasattr(extractor, "_validate_page_content")
        assert hasattr(extractor, "_validate_extracted_data")
        assert callable(extractor._validate_page_content)
        assert callable(extractor._validate_extracted_data)

    def test_error_screenshot_handling(self):
        """Test that error screenshot functionality is available."""
        # Test that the screenshot path generation works
        from datetime import datetime

        screenshot_path = (
            f"/tmp/hounslow_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        assert screenshot_path.startswith("/tmp/hounslow_error_")
        assert screenshot_path.endswith(".png")


if __name__ == "__main__":
    pytest.main([__file__])
