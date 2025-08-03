"""Tests for hounslow_bin_collection package."""

import pytest
from src.hounslow_bin_collection import __version__, __author__


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_author():
    """Test that author is defined."""
    assert __author__ == "ronschaeffer"


def test_package_import():
    """Test that package can be imported."""
    import src.hounslow_bin_collection
    assert src.hounslow_bin_collection is not None


class TestHounslow_bin_collection:
    """Test class for hounslow_bin_collection functionality."""
    
    def test_placeholder(self):
        """Placeholder test - replace with actual tests."""
        assert True
        
    def test_with_fixture(self, sample_data):
        """Test using a fixture."""
        assert sample_data["name"] == "test"
        assert sample_data["value"] == 42
        assert len(sample_data["items"]) == 3
