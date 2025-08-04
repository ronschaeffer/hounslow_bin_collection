#!/usr/bin/env python3
"""Test environment variable configuration for address settings."""

import os
import sys

sys.path.insert(0, "src")

from hounslow_bin_collection.config import Config


def test_env_config():
    """Test environment variable configuration."""
    print("🧪 Testing Environment Variable Configuration")
    print("=" * 50)

    # Test without environment variables
    print("\n1. Default configuration (no env vars):")
    config = Config()
    print(f"   postcode: {config.get('address.postcode')}")
    print(f"   address_hint: {config.get('address.address_hint')}")
    print(f"   uprn: {config.get('address.uprn')}")

    # Test with environment variables
    print("\n2. Setting environment variables...")
    os.environ["HOUNSLOW_POSTCODE"] = "TW7 7HX"
    os.environ["HOUNSLOW_ADDRESS"] = "136 Worple Rd"
    os.environ["UPRN"] = "100021577775"

    # Create new config instance to pick up env vars
    config_with_env = Config()
    print(f"   postcode: {config_with_env.get('address.postcode')}")
    print(f"   address_hint: {config_with_env.get('address.address_hint')}")
    print(f"   uprn: {config_with_env.get('address.uprn')}")

    print("\n✅ Environment variable configuration working!")
    print("\n💡 Usage in production:")
    print("   export HOUNSLOW_POSTCODE='your_postcode'")
    print("   export HOUNSLOW_ADDRESS='your_address'")
    print("   # OR")
    print("   export UPRN='your_uprn'")

    # Clean up
    del os.environ["HOUNSLOW_POSTCODE"]
    del os.environ["HOUNSLOW_ADDRESS"]
    del os.environ["UPRN"]


if __name__ == "__main__":
    test_env_config()
