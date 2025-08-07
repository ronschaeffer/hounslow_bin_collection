"""Pytest configuration and fixtures."""

from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"name": "test", "value": 42, "items": ["a", "b", "c"]}


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def mock_iframe_frame():
    """Provide a mock iframe frame for testing."""
    frame = Mock()
    frame.wait_for_timeout = Mock()
    frame.evaluate = Mock(return_value="Mock page content")
    return frame


@pytest.fixture
def sample_bin_data():
    """Provide sample bin collection data for testing."""
    return [
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


@pytest.fixture
def sample_collection_result():
    """Provide sample collection result data for testing."""
    return {
        "postcode": "TW3 3EB",
        "address": "132 Worple Rd, Hounslow TW3 3EB",
        "uprn": "12345",
        "collections": [
            {
                "text": "General Waste: Every 2 weeks on Tuesday (Next: 19/08/2025)",
                "type": "general_waste",
                "frequency": "Every 2 weeks on Tuesday",
                "next_collection": "19/08/2025",
                "last_collection": "05/08/2025",
            }
        ],
        "extracted_at": "2025-08-07T10:00:00",
        "method": "enhanced_table_extraction",
        "bin_schedule": {
            "general_waste": {
                "frequency": "Every 2 weeks on Tuesday",
                "next_collection": "19/08/2025",
                "last_collection": "05/08/2025",
            }
        },
    }
