"""
Constellation Network Python SDK

A comprehensive Python SDK for interacting with the Constellation Network (Hypergraph),
supporting DAG token transactions, metagraph operations, and network queries.

Enhanced with comprehensive validation, error handling, structured logging,
performance optimizations, async support, and configuration management.

Architecture:
- Account: Key management and transaction signing
- Transactions: Centralized transaction creation for all types
- MetagraphClient: Metagraph discovery and queries  
- Network: Core DAG network operations
- AsyncNetwork: High-performance async network operations (Phase 2)
- AsyncMetagraphClient: Async metagraph operations (Phase 2)
- Configuration: Centralized configuration management (Phase 2)
- Validation: Comprehensive input validation system
- Logging: Structured logging with performance tracking
- Exceptions: Hierarchical error handling
"""

from .account import Account, ConstellationError
from .config import (
    DEFAULT_CONFIGS,
    AsyncConfig,
    CacheConfig,
    ConfigManager,
    LoggingConfig,
    NetworkConfig,
    SDKConfig,
    create_custom_config,
    get_config,
    load_config_from_file,
    save_config_to_file,
    set_config,
    update_config,
)
from .metagraph import get_metagraph_summary  # Legacy functions
from .metagraph import (
    MetagraphClient,
    MetagraphError,
    discover_all_metagraphs,
    discover_production_metagraphs,
    get_realistic_metagraph_summary,
)
from .network import Network, NetworkError
from .transactions import create_metagraph_data_transaction  # Convenience functions
from .transactions import (
    Transactions,
    create_dag_transaction,
    create_metagraph_token_transaction,
)

# Async support (Phase 2) - Optional import to handle missing aiohttp
try:
    from .async_metagraph import (
        AsyncMetagraphClient,
        AsyncMetagraphDiscovery,
        batch_get_balances_from_multiple_metagraphs,
        create_async_metagraph_client,
        discover_metagraphs_async,
    )
    from .async_network import (
        AsyncHTTPClient,
        AsyncNetwork,
        create_async_network,
        get_multiple_balances_concurrent,
    )

    ASYNC_AVAILABLE = True
except ImportError:
    # aiohttp not available, async components won't be available
    AsyncNetwork = None
    AsyncHTTPClient = None
    AsyncMetagraphClient = None
    AsyncMetagraphDiscovery = None
    create_async_network = None
    get_multiple_balances_concurrent = None
    discover_metagraphs_async = None
    create_async_metagraph_client = None
    batch_get_balances_from_multiple_metagraphs = None
    ASYNC_AVAILABLE = False

# Enhanced validation and error handling (Phase 1)
from .exceptions import (
    AddressValidationError,
    AmountValidationError,
    APIError,
    ConfigurationError,
    HTTPError,
    InvalidDataError,
    MetagraphIdValidationError,
    TransactionError,
    TransactionValidationError,
    ValidationError,
)

# Logging framework (Phase 1)
from .logging import (
    configure_logging,
    get_logger,
    get_network_logger,
    get_performance_tracker,
    get_transaction_logger,
    log_operation,
)
from .validation import (
    AddressValidator,
    AmountValidator,
    DataValidator,
    MetagraphIdValidator,
    TransactionValidator,
    is_valid_amount,
    is_valid_dag_address,
    is_valid_metagraph_id,
)

__version__ = "1.2.0"
__author__ = "Constellation Network Community"
__license__ = "MIT"

# Core exports
__all__ = [
    # Core classes
    "Account",
    "Transactions",
    "Network",
    "MetagraphClient",
    # Configuration management (Phase 2)
    "NetworkConfig",
    "AsyncConfig",
    "CacheConfig",
    "LoggingConfig",
    "SDKConfig",
    "ConfigManager",
    "get_config",
    "set_config",
    "update_config",
    "load_config_from_file",
    "save_config_to_file",
    "create_custom_config",
    "DEFAULT_CONFIGS",
    # Metagraph functions
    "discover_production_metagraphs",
    "get_realistic_metagraph_summary",
    "discover_all_metagraphs",  # Legacy
    "get_metagraph_summary",  # Legacy
    # Convenience transaction functions
    "create_dag_transaction",
    "create_metagraph_token_transaction",
    "create_metagraph_data_transaction",
    # Core exceptions
    "ConstellationError",
    "TransactionError",
    "NetworkError",
    "MetagraphError",
    # Enhanced validation exceptions (Phase 1)
    "ValidationError",
    "AddressValidationError",
    "AmountValidationError",
    "MetagraphIdValidationError",
    "TransactionValidationError",
    "HTTPError",
    "APIError",
    "InvalidDataError",
    "ConfigurationError",
    # Validation components (Phase 1)
    "AddressValidator",
    "AmountValidator",
    "MetagraphIdValidator",
    "TransactionValidator",
    "DataValidator",
    "is_valid_dag_address",
    "is_valid_amount",
    "is_valid_metagraph_id",
    # Logging framework (Phase 1)
    "configure_logging",
    "get_logger",
    "get_performance_tracker",
    "get_network_logger",
    "get_transaction_logger",
    "log_operation",
    # Async availability flag
    "ASYNC_AVAILABLE",
]

# Add async components to exports if available (Phase 2)
if ASYNC_AVAILABLE:
    __all__.extend(
        [
            # Async network components
            "AsyncNetwork",
            "AsyncHTTPClient",
            "create_async_network",
            "get_multiple_balances_concurrent",
            # Async metagraph components
            "AsyncMetagraphClient",
            "AsyncMetagraphDiscovery",
            "discover_metagraphs_async",
            "create_async_metagraph_client",
            "batch_get_balances_from_multiple_metagraphs",
        ]
    )
