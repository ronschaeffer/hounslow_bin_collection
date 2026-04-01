"""Tests for hounslow_bin_collection package."""

from hounslow_bin_collection import __author__, __version__


def test_version():
    """Test that version is defined."""
    # Handle git-versioned strings like "0.1.0-6dd7913-dirty"
    assert __version__.startswith("0.1.0")


def test_author():
    """Test that author is defined."""
    assert __author__ == "ronschaeffer"


def test_package_import():
    """Test that package can be imported."""
    import hounslow_bin_collection

    assert hounslow_bin_collection is not None


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
