"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        "name": "test",
        "value": 42,
        "items": ["a", "b", "c"]
    }


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent
