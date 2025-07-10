"""
Comprehensive configuration management for Constellation SDK.

Supports network configurations, performance settings, async configurations,
environment variables, and validation. Provides centralized settings
management for optimal performance and flexibility.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .exceptions import ConfigurationError, ValidationError
from .validation import is_valid_dag_address


@dataclass
class NetworkConfig:
    """Enhanced configuration for a Constellation network environment."""

    # Core network settings
    network_version: str
    be_url: str  # Block Explorer
    l0_url: str  # Global L0 (Hypergraph layer)
    l1_url: str  # L1 (DAG token layer)
    name: str

    # Performance settings
    timeout: int = 30  # Request timeout in seconds
    max_retries: int = 3  # Maximum retry attempts
    retry_delay: float = 1.0  # Initial retry delay in seconds
    max_connections: int = 100  # Max connections in pool
    keepalive: bool = True  # Keep connections alive

    # Rate limiting
    rate_limit_requests: int = 100  # Requests per minute
    rate_limit_window: int = 60  # Rate limit window in seconds

    # Validation settings
    validate_addresses: bool = True  # Validate DAG addresses
    validate_amounts: bool = True  # Validate transaction amounts
    strict_validation: bool = False  # Strict validation mode

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ConfigurationError(
                "Timeout must be positive", "timeout", self.timeout
            )
        if self.max_retries < 0:
            raise ConfigurationError(
                "Max retries cannot be negative", "max_retries", self.max_retries
            )
        if not self.be_url or not self.l0_url or not self.l1_url:
            raise ConfigurationError("All URLs must be provided")


@dataclass
class AsyncConfig:
    """Configuration for async operations."""

    # Connection settings
    connector_limit: int = 100  # Total connection pool size
    connector_limit_per_host: int = 30  # Connections per host
    connector_ttl_dns_cache: int = 300  # DNS cache TTL
    connector_use_dns_cache: bool = True  # Use DNS caching

    # Timeout settings
    total_timeout: int = 30  # Total request timeout
    connect_timeout: int = 10  # Connection timeout
    read_timeout: int = 20  # Read timeout

    # SSL and security
    verify_ssl: bool = True  # Verify SSL certificates
    ssl_context: Optional[Any] = None  # Custom SSL context

    # Performance settings
    enable_compression: bool = True  # Enable gzip compression
    auto_decompress: bool = True  # Auto decompress responses
    trust_env: bool = True  # Trust environment proxy settings

    # Concurrency settings
    max_concurrent_requests: int = 50  # Max concurrent requests
    semaphore_limit: int = 20  # Semaphore limit for concurrency control

    def __post_init__(self):
        """Validate async configuration."""
        if self.connector_limit <= 0:
            raise ConfigurationError("Connector limit must be positive")
        if self.total_timeout <= 0:
            raise ConfigurationError("Total timeout must be positive")


@dataclass
class CacheConfig:
    """Configuration for caching mechanisms."""

    # Cache settings
    enable_caching: bool = True  # Enable response caching
    cache_ttl: int = 300  # Cache TTL in seconds (5 minutes)
    max_cache_size: int = 1000  # Maximum cache entries

    # Cache types
    cache_balances: bool = True  # Cache balance queries
    cache_node_info: bool = True  # Cache node information
    cache_metagraphs: bool = True  # Cache metagraph discovery
    cache_transactions: bool = False  # Don't cache transactions by default

    # Cache invalidation
    auto_invalidate: bool = True  # Auto invalidate expired entries
    invalidate_on_error: bool = True  # Invalidate on errors


@dataclass
class LoggingConfig:
    """Configuration for logging system."""

    # Logging levels
    level: str = "INFO"  # Default log level
    console_level: str = "INFO"  # Console log level
    file_level: str = "DEBUG"  # File log level

    # Output settings
    enable_console: bool = True  # Log to console
    enable_file: bool = False  # Log to file
    log_file: Optional[str] = None  # Log file path

    # Format settings
    structured_logging: bool = True  # Use structured JSON logging
    include_timestamp: bool = True  # Include timestamps
    include_thread_id: bool = False  # Include thread IDs

    # Performance logging
    log_performance: bool = True  # Log performance metrics
    log_network_requests: bool = False  # Log all network requests
    log_transactions: bool = True  # Log transaction operations


@dataclass
class SDKConfig:
    """Main SDK configuration combining all settings."""

    # Core components
    network: NetworkConfig
    async_config: AsyncConfig = field(default_factory=AsyncConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # SDK behavior
    auto_configure_logging: bool = True  # Auto-configure logging on import
    enable_async: bool = True  # Enable async support
    enable_performance_tracking: bool = True  # Enable performance tracking

    # Development settings
    debug_mode: bool = False  # Enable debug mode
    development_mode: bool = False  # Enable development features

    def validate(self) -> None:
        """Validate the complete configuration."""
        # Network config validates itself in __post_init__
        # Async config validates itself in __post_init__

        if self.logging.log_file and self.logging.enable_file:
            # Ensure log directory exists
            log_path = Path(self.logging.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SDKConfig":
        """Create configuration from dictionary."""
        # Extract nested configs
        network_data = data.pop("network")
        async_data = data.pop("async_config", {})
        cache_data = data.pop("cache", {})
        logging_data = data.pop("logging", {})

        return cls(
            network=NetworkConfig(**network_data),
            async_config=AsyncConfig(**async_data),
            cache=CacheConfig(**cache_data),
            logging=LoggingConfig(**logging_data),
            **data,
        )


# Enhanced default network configurations
DEFAULT_CONFIGS: Dict[str, NetworkConfig] = {
    "mainnet": NetworkConfig(
        network_version="2.0",
        be_url="https://be-mainnet.constellationnetwork.io",
        l0_url="https://l0-lb-mainnet.constellationnetwork.io",
        l1_url="https://l1-lb-mainnet.constellationnetwork.io",
        name="MainNet",
        timeout=30,
        max_retries=3,
        max_connections=100,
        rate_limit_requests=100,
    ),
    "testnet": NetworkConfig(
        network_version="2.0",
        be_url="https://be-testnet.constellationnetwork.io",
        l0_url="https://l0-lb-testnet.constellationnetwork.io",
        l1_url="https://l1-lb-testnet.constellationnetwork.io",
        name="TestNet",
        timeout=30,
        max_retries=3,
        max_connections=50,
        rate_limit_requests=50,
    ),
    "integrationnet": NetworkConfig(
        network_version="2.0",
        be_url="https://be-integrationnet.constellationnetwork.io",
        l0_url="https://l0-lb-integrationnet.constellationnetwork.io",
        l1_url="https://l1-lb-integrationnet.constellationnetwork.io",
        name="IntegrationNet",
        timeout=15,
        max_retries=2,
        max_connections=20,
        rate_limit_requests=20,
    ),
}


# Configuration Manager
class ConfigManager:
    """
    Centralized configuration management with environment support.
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[SDKConfig] = None

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern for global configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._create_default_config()

    def _create_default_config(self) -> SDKConfig:
        """Create default configuration."""
        # Determine network from environment
        network_name = os.getenv("CONSTELLATION_NETWORK", "testnet").lower()

        if network_name not in DEFAULT_CONFIGS:
            raise ConfigurationError(
                f"Invalid network: {network_name}", "network", network_name
            )

        network_config = DEFAULT_CONFIGS[network_name]

        # Override with environment variables
        network_config = self._apply_env_overrides(network_config)

        return SDKConfig(
            network=network_config,
            debug_mode=os.getenv("CONSTELLATION_DEBUG", "false").lower() == "true",
            development_mode=os.getenv("CONSTELLATION_DEV", "false").lower() == "true",
        )

    def _apply_env_overrides(self, config: NetworkConfig) -> NetworkConfig:
        """Apply environment variable overrides to network config."""
        # URL overrides
        config.be_url = os.getenv("CONSTELLATION_BE_URL", config.be_url)
        config.l0_url = os.getenv("CONSTELLATION_L0_URL", config.l0_url)
        config.l1_url = os.getenv("CONSTELLATION_L1_URL", config.l1_url)

        # Performance overrides
        if timeout := os.getenv("CONSTELLATION_TIMEOUT"):
            config.timeout = int(timeout)

        if max_retries := os.getenv("CONSTELLATION_MAX_RETRIES"):
            config.max_retries = int(max_retries)

        if max_connections := os.getenv("CONSTELLATION_MAX_CONNECTIONS"):
            config.max_connections = int(max_connections)

        return config

    def get_config(self) -> SDKConfig:
        """Get current configuration."""
        return self._config

    def set_config(self, config: SDKConfig) -> None:
        """Set new configuration."""
        config.validate()
        self._config = config

    def update_config(self, **kwargs) -> None:
        """Update configuration with partial changes."""
        current_dict = self._config.to_dict()
        current_dict.update(kwargs)
        new_config = SDKConfig.from_dict(current_dict)
        self.set_config(new_config)

    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load configuration from JSON file."""
        path = Path(file_path)

        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")

        try:
            with open(path, "r") as f:
                data = json.load(f)

            config = SDKConfig.from_dict(data)
            self.set_config(config)

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save current configuration to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w") as f:
                json.dump(self._config.to_dict(), f, indent=2)
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration: {e}")

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self._config = self._create_default_config()


# Global configuration instance
_config_manager = ConfigManager()


def get_config() -> SDKConfig:
    """Get the global SDK configuration."""
    return _config_manager.get_config()


def set_config(config: SDKConfig) -> None:
    """Set the global SDK configuration."""
    _config_manager.set_config(config)


def update_config(**kwargs) -> None:
    """Update global configuration with partial changes."""
    _config_manager.update_config(**kwargs)


def load_config_from_file(file_path: Union[str, Path]) -> None:
    """Load configuration from file."""
    _config_manager.load_from_file(file_path)


def save_config_to_file(file_path: Union[str, Path]) -> None:
    """Save configuration to file."""
    _config_manager.save_to_file(file_path)


def create_custom_config(
    be_url: str, l0_url: str, l1_url: str, network_version: str = "2.0", **kwargs
) -> NetworkConfig:
    """Create a custom network configuration for direct node connections."""
    return NetworkConfig(
        network_version=network_version,
        be_url=be_url,
        l0_url=l0_url,
        l1_url=l1_url,
        name="Custom",
        **kwargs,
    )


# Metagraph-specific endpoints are constructed as:
# {base_url}/metagraph/{metagraph_id}/{endpoint}
METAGRAPH_ENDPOINTS = {
    "balances": "/balances",
    "transactions": "/transactions",
    "data": "/data",
    "snapshots": "/snapshots",
    "currency": "/currency",  # For metagraph discovery
    "cluster": "/cluster",  # For cluster information
}
