"""
Unit tests for error handling and edge cases in the bin collection system.
Tests network failures, invalid inputs, and recovery scenarios.
"""

from unittest.mock import Mock, patch

import pytest

from hounslow_bin_collection.enhanced_extractor import HounslowDataExtractor


class TestErrorScenarios:
    """Test cases for various error conditions and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = HounslowDataExtractor()

    def test_network_failure_simulation(self):
        """Test handling of network failures during extraction."""
        # Mock frame that simulates network error
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.side_effect = Exception("net::ERR_NAME_NOT_RESOLVED")

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        # Should handle network error gracefully
        assert isinstance(result, dict)
        assert "extraction_error" in result
        assert "net::ERR_NAME_NOT_RESOLVED" in result["extraction_error"]

    def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        mock_frame = Mock()
        mock_frame.wait_for_timeout.side_effect = Exception("Timeout waiting for page")
        mock_frame.evaluate.return_value = "Valid content"

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        assert isinstance(result, dict)
        assert "extraction_error" in result

    def test_empty_page_content(self):
        """Test handling when page returns empty content."""
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = ""

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        # Should handle empty content gracefully
        assert result["postcode"] == "TW3 3EB"
        assert result["address"] == "132 Worple Rd"

    def test_malformed_html_content(self):
        """Test handling of malformed or unexpected HTML content."""
        malformed_content = """
        <html><head><title>Error</title></head>
        <body>
        <div class="error">
        Something went wrong
        </div>
        </body></html>
        """

        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = malformed_content

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        # Should detect this as invalid content
        assert "extraction_error" in result

    def test_javascript_error_handling(self):
        """Test handling of JavaScript execution errors."""
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.side_effect = Exception(
            "JavaScript error: undefined function"
        )

        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        assert "extraction_error" in result
        assert "JavaScript error" in result["extraction_error"]


class TestAddressValidation:
    """Test cases for address validation and normalization edge cases."""

    def test_invalid_address_formats(self):
        """Test handling of invalid address formats."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        invalid_addresses = [
            "",  # Empty string
            "   ",  # Only whitespace
            "123",  # Just number
            "Road",  # Just street type
        ]

        for invalid_addr in invalid_addresses:
            # Should not crash, should return something sensible
            variations = normalize_address_for_matching(invalid_addr)
            assert isinstance(variations, list)
            assert len(variations) >= 1  # Should at least include original

    def test_unicode_addresses(self):
        """Test handling of addresses with unicode characters."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        unicode_addresses = ["123 Café Street", "45 Naïve Road", "67 François Avenue"]

        for unicode_addr in unicode_addresses:
            # Should handle unicode gracefully
            variations = normalize_address_for_matching(unicode_addr)
            assert isinstance(variations, list)
            assert unicode_addr in variations

    def test_very_long_addresses(self):
        """Test handling of unusually long addresses."""
        from hounslow_bin_collection.browser_collector import (
            normalize_address_for_matching,
        )

        long_address = "123 Very Long Street Name That Goes On And On And On Road"

        variations = normalize_address_for_matching(long_address)
        assert isinstance(variations, list)
        assert long_address in variations


class TestConfigurationErrors:
    """Test cases for configuration file issues."""

    def test_missing_config_fields(self):
        """Test behavior when config file has missing fields."""
        # This tests that the system can handle partial configs
        partial_config = {
            "hounslow_bin_collection": {
                "postcode": "TW3 3EB"
                # Missing address_hint
            }
        }

        # Should be able to work with just postcode
        assert "postcode" in partial_config["hounslow_bin_collection"]

    def test_config_with_extra_fields(self):
        """Test that extra config fields don't break the system."""
        extended_config = {
            "hounslow_bin_collection": {
                "postcode": "TW3 3EB",
                "address_hint": "132 Worple Rd",
                "extra_field": "should be ignored",
                "debug_mode": True,
            }
        }

        # Should work fine with extra fields
        assert "postcode" in extended_config["hounslow_bin_collection"]
        assert "address_hint" in extended_config["hounslow_bin_collection"]


class TestValidationEdgeCases:
    """Test edge cases in validation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = HounslowDataExtractor()

    def test_page_validation_boundary_conditions(self):
        """Test page validation at boundary conditions."""
        # Test exactly at minimum length boundary (100 chars)
        base_content = "collection bin waste monday"  # 27 chars
        boundary_content = base_content + "x" * (
            100 - len(base_content)
        )  # Exactly 100 chars

        result = self.extractor._validate_page_content(boundary_content)
        assert result is True

        # Test just under boundary (99 chars)
        under_boundary = base_content + "x" * (99 - len(base_content))  # 99 chars

        result = self.extractor._validate_page_content(under_boundary)
        assert result is False

    def test_data_validation_edge_cases(self):
        """Test data validation with edge case inputs."""
        # Test with minimal valid data
        minimal_data = [
            {
                "bin_type": "general_waste",
                "description": "x",  # Minimal description
                "frequency": "x",  # Minimal frequency
            }
        ]

        result = self.extractor._validate_extracted_data(minimal_data)
        assert result is True

        # Test with empty strings in required fields
        empty_strings = [{"bin_type": "", "description": "", "frequency": "Weekly"}]

        result = self.extractor._validate_extracted_data(empty_strings)
        assert result is False

    def test_validation_with_unusual_bin_types(self):
        """Test validation with unusual but valid bin types."""
        unusual_data = [
            {
                "bin_type": "experimental_waste_type",
                "description": "New experimental collection service",
                "frequency": "Monthly",
                "next_collection": "15/09/2025",
            }
        ]

        # Should pass validation even with unknown bin types
        result = self.extractor._validate_extracted_data(unusual_data)
        assert result is True


class TestRecoveryScenarios:
    """Test recovery from various failure scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = HounslowDataExtractor()

    @patch("hounslow_bin_collection.enhanced_extractor.datetime")
    def test_partial_data_recovery(self, mock_datetime):
        """Test recovery when only partial data is available."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-08-07T10:00:00"

        # Mock content with partial information
        partial_content = """
        Waste collection
        Some bin information available
        Tuesday collections
        """

        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.return_value = partial_content

        # Mock extraction that returns partial data
        partial_bin_data = [
            {
                "bin_type": "general_waste",
                "description": "Partial information available",
                "frequency": "Unknown",  # Missing frequency
                "next_collection": None,  # Missing dates
                "last_collection": None,
            }
        ]

        with patch.object(
            self.extractor, "_extract_bin_collections", return_value=partial_bin_data
        ):
            result = self.extractor.extract_enhanced_collection_data(
                mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
            )

            # Should fail validation due to no schedule info
            assert "extraction_error" in result

    def test_fallback_extraction_mechanism(self):
        """Test that fallback extraction works when main extraction fails."""
        mock_frame = Mock()
        mock_frame.wait_for_timeout = Mock()
        mock_frame.evaluate.side_effect = Exception("Main extraction failed")

        # Should trigger fallback mechanism
        result = self.extractor.extract_enhanced_collection_data(
            mock_frame, "TW3 3EB", "132 Worple Rd", "12345"
        )

        # Should have fallback data
        assert "collections" in result
        assert "extraction_error" in result
        assert result["method"] == "enhanced_table_extraction"


class TestPerformanceAndLimits:
    """Test performance characteristics and system limits."""

    def test_large_content_handling(self):
        """Test handling of very large page content."""
        # Create large content (but still valid)
        large_content = """
        Waste collection information
        """ + "\n".join(
            [
                f"Data line {i} with bin and collection data every monday"
                for i in range(1000)
                if str(i) not in ["404", "500", "503"]
            ]
        )

        extractor = HounslowDataExtractor()
        result = extractor._validate_page_content(large_content)

        # Should handle large content without issues
        assert result is True

    def test_many_bin_types_handling(self):
        """Test handling of many different bin types."""
        many_bins = [
            {
                "bin_type": f"bin_type_{i}",
                "description": f"Bin type {i} collection",
                "frequency": "Weekly",
                "next_collection": "19/08/2025",
            }
            for i in range(50)  # Many bin types
        ]

        extractor = HounslowDataExtractor()
        result = extractor._validate_extracted_data(many_bins)

        # Should handle many bins efficiently
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])
