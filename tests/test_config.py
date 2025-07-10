"""
Tests for configuration management system.

Tests all configuration classes, environment variable support,
file loading/saving, validation, and the configuration manager.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from constellation_sdk.config import (DEFAULT_CONFIGS, AsyncConfig,
                                      CacheConfig, ConfigManager,
                                      LoggingConfig, NetworkConfig, SDKConfig,
                                      create_custom_config, get_config,
                                      load_config_from_file,
                                      save_config_to_file, set_config,
                                      update_config)
from constellation_sdk.exceptions import ConfigurationError


class TestNetworkConfig:
    """Test NetworkConfig class."""

    def test_network_config_creation(self):
        """Test basic network config creation."""
        config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        assert config.network_version == "2.0"
        assert config.name == "Test"
        assert config.timeout == 30  # Default value
        assert config.max_retries == 3  # Default value

    def test_network_config_validation(self):
        """Test network config validation."""
        # Test invalid timeout
        with pytest.raises(ConfigurationError):
            NetworkConfig(
                network_version="2.0",
                be_url="https://example.com",
                l0_url="https://l0.example.com",
                l1_url="https://l1.example.com",
                name="Test",
                timeout=0,
            )

        # Test invalid max_retries
        with pytest.raises(ConfigurationError):
            NetworkConfig(
                network_version="2.0",
                be_url="https://example.com",
                l0_url="https://l0.example.com",
                l1_url="https://l1.example.com",
                name="Test",
                max_retries=-1,
            )

        # Test missing URLs
        with pytest.raises(ConfigurationError):
            NetworkConfig(
                network_version="2.0",
                be_url="",
                l0_url="https://l0.example.com",
                l1_url="https://l1.example.com",
                name="Test",
            )

    def test_default_network_configs(self):
        """Test that default network configs are valid."""
        for name, config in DEFAULT_CONFIGS.items():
            assert isinstance(config, NetworkConfig)
            assert config.be_url
            assert config.l0_url
            assert config.l1_url
            assert config.name
            assert config.timeout > 0
            assert config.max_retries >= 0


class TestAsyncConfig:
    """Test AsyncConfig class."""

    def test_async_config_creation(self):
        """Test async config creation with defaults."""
        config = AsyncConfig()

        assert config.connector_limit == 100
        assert config.total_timeout == 30
        assert config.verify_ssl is True
        assert config.enable_compression is True

    def test_async_config_validation(self):
        """Test async config validation."""
        # Test invalid connector limit
        with pytest.raises(ConfigurationError):
            AsyncConfig(connector_limit=0)

        # Test invalid timeout
        with pytest.raises(ConfigurationError):
            AsyncConfig(total_timeout=0)

    def test_async_config_custom_values(self):
        """Test async config with custom values."""
        config = AsyncConfig(connector_limit=200, total_timeout=60, verify_ssl=False)

        assert config.connector_limit == 200
        assert config.total_timeout == 60
        assert config.verify_ssl is False


class TestCacheConfig:
    """Test CacheConfig class."""

    def test_cache_config_defaults(self):
        """Test cache config default values."""
        config = CacheConfig()

        assert config.enable_caching is True
        assert config.cache_ttl == 300
        assert config.max_cache_size == 1000
        assert config.cache_balances is True
        assert config.cache_transactions is False


class TestLoggingConfig:
    """Test LoggingConfig class."""

    def test_logging_config_defaults(self):
        """Test logging config default values."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.enable_console is True
        assert config.enable_file is False
        assert config.structured_logging is True


class TestSDKConfig:
    """Test SDKConfig class."""

    def test_sdk_config_creation(self):
        """Test SDK config creation."""
        network = DEFAULT_CONFIGS["testnet"]
        config = SDKConfig(network=network)

        assert config.network == network
        assert isinstance(config.async_config, AsyncConfig)
        assert isinstance(config.cache, CacheConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_sdk_config_validation(self):
        """Test SDK config validation."""
        network = DEFAULT_CONFIGS["testnet"]
        logging_config = LoggingConfig(
            enable_file=True, log_file="/tmp/test_constellation.log"
        )

        config = SDKConfig(network=network, logging=logging_config)

        # Should not raise an exception
        config.validate()

    def test_sdk_config_dict_conversion(self):
        """Test conversion to/from dictionary."""
        network = DEFAULT_CONFIGS["testnet"]
        original_config = SDKConfig(network=network, debug_mode=True)

        # Convert to dict
        config_dict = original_config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["debug_mode"] is True

        # Convert back from dict
        restored_config = SDKConfig.from_dict(config_dict)
        assert restored_config.debug_mode is True
        assert restored_config.network.name == network.name


class TestConfigManager:
    """Test ConfigManager class."""

    def test_config_manager_singleton(self):
        """Test that ConfigManager is a singleton."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()

        assert manager1 is manager2

    @patch.dict(os.environ, {"CONSTELLATION_NETWORK": "mainnet"})
    def test_environment_network_selection(self):
        """Test network selection from environment."""
        # Reset the singleton to pick up environment changes
        ConfigManager._instance = None
        ConfigManager._config = None

        manager = ConfigManager()
        config = manager.get_config()

        assert config.network.name == "MainNet"

    @patch.dict(
        os.environ,
        {
            "CONSTELLATION_NETWORK": "testnet",
            "CONSTELLATION_TIMEOUT": "60",
            "CONSTELLATION_MAX_RETRIES": "5",
        },
    )
    def test_environment_overrides(self):
        """Test environment variable overrides."""
        # Reset the singleton
        ConfigManager._instance = None
        ConfigManager._config = None

        manager = ConfigManager()
        config = manager.get_config()

        assert config.network.timeout == 60
        assert config.network.max_retries == 5

    def test_config_update(self):
        """Test configuration updates."""
        manager = ConfigManager()
        original_debug = manager.get_config().debug_mode

        manager.update_config(debug_mode=not original_debug)

        assert manager.get_config().debug_mode == (not original_debug)

    def test_config_file_operations(self):
        """Test loading and saving configuration files."""
        manager = ConfigManager()
        original_config = manager.get_config()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # Save configuration
            manager.save_to_file(temp_file)

            # Modify configuration
            manager.update_config(debug_mode=True)
            assert manager.get_config().debug_mode is True

            # Load configuration from file
            manager.load_from_file(temp_file)

            # Should restore original debug mode
            assert manager.get_config().debug_mode == original_config.debug_mode

        finally:
            # Clean up
            os.unlink(temp_file)

    def test_invalid_config_file(self):
        """Test handling of invalid configuration files."""
        manager = ConfigManager()

        # Test non-existent file
        with pytest.raises(ConfigurationError):
            manager.load_from_file("/nonexistent/file.json")

        # Test invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            with pytest.raises(ConfigurationError):
                manager.load_from_file(temp_file)
        finally:
            os.unlink(temp_file)


class TestConfigurationFunctions:
    """Test global configuration functions."""

    def test_get_set_config(self):
        """Test global get/set config functions."""
        original_config = get_config()

        # Create new config
        new_network = DEFAULT_CONFIGS["mainnet"]
        new_config = SDKConfig(network=new_network, debug_mode=True)

        # Set new config
        set_config(new_config)

        # Verify it was set
        current_config = get_config()
        assert current_config.debug_mode is True
        assert current_config.network.name == "MainNet"

        # Restore original
        set_config(original_config)

    def test_update_config_function(self):
        """Test global update config function."""
        original_debug = get_config().debug_mode

        update_config(debug_mode=not original_debug)

        assert get_config().debug_mode == (not original_debug)

        # Restore
        update_config(debug_mode=original_debug)

    def test_file_operations(self):
        """Test global file operation functions."""
        original_config = get_config()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # Save config
            save_config_to_file(temp_file)

            # Modify config
            update_config(debug_mode=True)

            # Load config
            load_config_from_file(temp_file)

            # Should restore original
            assert get_config().debug_mode == original_config.debug_mode

        finally:
            os.unlink(temp_file)


class TestCreateCustomConfig:
    """Test custom configuration creation."""

    def test_create_custom_config_basic(self):
        """Test basic custom config creation."""
        config = create_custom_config(
            be_url="https://custom-be.example.com",
            l0_url="https://custom-l0.example.com",
            l1_url="https://custom-l1.example.com",
        )

        assert config.name == "Custom"
        assert config.be_url == "https://custom-be.example.com"
        assert config.network_version == "2.0"

    def test_create_custom_config_with_kwargs(self):
        """Test custom config creation with additional parameters."""
        config = create_custom_config(
            be_url="https://custom-be.example.com",
            l0_url="https://custom-l0.example.com",
            l1_url="https://custom-l1.example.com",
            timeout=60,
            max_retries=5,
        )

        assert config.timeout == 60
        assert config.max_retries == 5


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration system."""

    def test_full_configuration_workflow(self):
        """Test complete configuration workflow."""
        # Start with default config
        original_config = get_config()

        # Create custom network config
        custom_network = create_custom_config(
            be_url="https://test-be.example.com",
            l0_url="https://test-l0.example.com",
            l1_url="https://test-l1.example.com",
            timeout=45,
        )

        # Create full SDK config
        custom_async = AsyncConfig(connector_limit=200)
        custom_cache = CacheConfig(enable_caching=False)
        custom_logging = LoggingConfig(level="DEBUG")

        full_config = SDKConfig(
            network=custom_network,
            async_config=custom_async,
            cache=custom_cache,
            logging=custom_logging,
            debug_mode=True,
        )

        # Set and validate
        set_config(full_config)
        current_config = get_config()

        assert current_config.network.timeout == 45
        assert current_config.async_config.connector_limit == 200
        assert current_config.cache.enable_caching is False
        assert current_config.logging.level == "DEBUG"
        assert current_config.debug_mode is True

        # Test serialization
        config_dict = current_config.to_dict()
        restored_config = SDKConfig.from_dict(config_dict)

        assert restored_config.network.timeout == 45
        assert restored_config.debug_mode is True

        # Restore original
        set_config(original_config)
