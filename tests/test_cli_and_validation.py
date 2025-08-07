"""
Unit tests for the CLI commands and format detection functionality.
Tests the schedule.py and bin_schedule.py commands with various inputs.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from hounslow_bin_collection.enhanced_extractor import HounslowDataExtractor


class TestConfigYamlFormat:
    """Test configuration file format."""

    def test_config_yaml_format(self):
        """Test that config.yaml has the correct format."""
        import yaml

        config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check that it has the required structure
        assert "address" in config
        assert "app" in config
        assert config["app"]["name"] == "hounslow_bin_collection"


class TestCLICommands:
    """Test cases for CLI command functionality."""

    def test_schedule_command_exists(self):
        """Test that the schedule command file exists."""
        schedule_path = Path(__file__).parent.parent / "schedule.py"
        assert schedule_path.exists()

    def test_bin_schedule_command_exists(self):
        """Test that the bin_schedule command file exists."""
        bin_schedule_path = Path(__file__).parent.parent / "bin_schedule.py"
        assert bin_schedule_path.exists()

    def test_config_file_exists(self):
        """Test that the config file exists."""
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        assert config_path.exists()


class TestFormatDetection:
    """Test cases for website format change detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = HounslowDataExtractor()

    def test_page_validation_normal_content(self):
        """Test page validation with normal bin collection content."""
        normal_content = """
        Waste collection information

        Your bin collection schedule

        Black wheelie bin collection every Tuesday
        Recycling boxes collected weekly
        Next collection: 19/08/2025
        """

        result = self.extractor._validate_page_content(normal_content)
        assert result is True

    def test_page_validation_error_page(self):
        """Test page validation detects error pages."""
        error_content = """
        Page not found - 404
        The requested page could not be found
        """

        result = self.extractor._validate_page_content(error_content)
        assert result is False

    def test_page_validation_maintenance_page(self):
        """Test page validation detects maintenance pages."""
        maintenance_content = """
        Service temporarily unavailable
        The website is undergoing maintenance
        """

        result = self.extractor._validate_page_content(maintenance_content)
        assert result is False

    def test_page_validation_insufficient_content(self):
        """Test page validation fails with insufficient content."""
        short_content = "Error"

        result = self.extractor._validate_page_content(short_content)
        assert result is False

    def test_data_validation_valid_data(self):
        """Test data validation with valid bin collection data."""
        valid_data = [
            {
                "bin_type": "general_waste",
                "description": "General waste collection",
                "frequency": "Every 2 weeks on Tuesday",
                "next_collection": "19/08/2025",
            }
        ]

        result = self.extractor._validate_extracted_data(valid_data)
        assert result is True

    def test_data_validation_empty_data(self):
        """Test data validation fails with empty data."""
        empty_data = []

        result = self.extractor._validate_extracted_data(empty_data)
        assert result is False

    def test_data_validation_missing_required_fields(self):
        """Test data validation fails with missing required fields."""
        incomplete_data = [
            {
                "bin_type": "general_waste",
                # Missing description
                "frequency": "Weekly",
            }
        ]

        result = self.extractor._validate_extracted_data(incomplete_data)
        assert result is False

    def test_data_validation_no_schedule_info(self):
        """Test data validation fails when no schedule information is available."""
        no_schedule_data = [
            {
                "bin_type": "general_waste",
                "description": "General waste collection",
                "frequency": "Unknown",
                "next_collection": None,
                "last_collection": None,
            }
        ]

        result = self.extractor._validate_extracted_data(no_schedule_data)
        assert result is False


class TestConfigurationHandling:
    """Test cases for configuration file handling."""

    def test_config_yaml_format(self):
        """Test that config.yaml has the correct format."""
        import yaml

        config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check that it has the required structure
        assert "address" in config
        assert "app" in config
        assert config["app"]["name"] == "hounslow_bin_collection"
        assert "postcode" in config["address"]
        assert "address_hint" in config["address"]

    def test_config_standard_test_address(self):
        """Test that config uses the standard test address."""
        import yaml

        config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        address = config["address"]["address_hint"]
        # Should use the standardized test address
        assert "132 Worple Rd" in address or "132 Worple Road" in address


class TestAddressNormalization:
    """Test cases for address normalization functionality."""

    def test_normalize_address_basic(self):
        """Test basic address normalization."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        variations = normalize_address_for_matching("132 Worple Rd")

        # Should include original and expanded form
        assert "132 Worple Rd" in variations
        assert "132 Worple Road" in variations

        # Should include house number only
        assert "132" in variations

        # Should include street name only
        street_only = [v for v in variations if v.startswith("Worple")]
        assert len(street_only) > 0

    def test_normalize_address_various_abbreviations(self):
        """Test normalization with different street abbreviations."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        test_cases = [
            ("123 High St", "123 High Street"),
            ("45 Oak Ave", "45 Oak Avenue"),
            ("67 Park Ln", "67 Park Lane"),
        ]

        for original, expected in test_cases:
            variations = normalize_address_for_matching(original)
            assert original in variations
            assert expected in variations

    def test_normalize_address_no_duplicates(self):
        """Test that address normalization removes duplicates."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        variations = normalize_address_for_matching("132 Main Street")

        # Should not have duplicates
        assert len(variations) == len(set(variations))


class TestExtractorIntegration:
    """Integration tests for the enhanced extractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = HounslowDataExtractor()

    @patch("hounslow_bin_collection.enhanced_extractor.datetime")
    def test_extraction_with_format_validation(self, mock_datetime):
        """Test extraction with format validation enabled."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-08-07T10:00:00"

        # Mock iframe frame with valid content
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = """
        Waste collection information

        Black wheelie bin collection every Tuesday
        Recycling boxes collected weekly
        """

        # Mock successful bin extraction
        mock_bin_data = [
            {
                "bin_type": "general_waste",
                "description": "General waste collection",
                "frequency": "Every Tuesday",
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

            # Should succeed without errors
            assert "extraction_error" not in result
            assert len(result["collections"]) == 1
            assert result["method"] == "enhanced_table_extraction"

    @patch("hounslow_bin_collection.enhanced_extractor.datetime")
    def test_extraction_with_invalid_page(self, mock_datetime):
        """Test extraction properly handles invalid pages."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-08-07T10:00:00"

        # Mock iframe frame with error page content
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = "Page not found - 404 error"

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        # Should detect the format issue
        assert "extraction_error" in result
        assert "Website format validation failed" in result["extraction_error"]

    def test_bin_type_definitions(self):
        """Test that bin type definitions are properly configured."""
        bin_types = self.extractor.bin_types

        # Should have standard bin types
        assert "black wheelie bin" in bin_types
        assert "recycling boxes" in bin_types

        # Each bin type should have required fields
        for _bin_name, bin_info in bin_types.items():
            assert "type" in bin_info
            assert "keywords" in bin_info
            assert "icon" in bin_info
            assert isinstance(bin_info["keywords"], list)


class TestErrorHandling:
    """Test cases for error handling and robustness."""

    def test_enhanced_extractor_exception_handling(self):
        """Test that the enhanced extractor handles exceptions gracefully."""
        extractor = HounslowDataExtractor()

        # Mock frame that raises exceptions
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.side_effect = Exception("Connection error")

        # Should not raise exception, should return result with error info
        result = extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        assert isinstance(result, dict)
        assert "extraction_error" in result
        assert "Connection error" in result["extraction_error"]

    def test_validation_methods_exist(self):
        """Test that validation methods are available."""
        extractor = HounslowDataExtractor()

        # Should have validation methods
        assert hasattr(extractor, "_validate_page_content")
        assert hasattr(extractor, "_validate_extracted_data")
        assert callable(extractor._validate_page_content)
        assert callable(extractor._validate_extracted_data)


if __name__ == "__main__":
    pytest.main([__file__])
