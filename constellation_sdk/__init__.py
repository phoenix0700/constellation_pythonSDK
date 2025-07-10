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
from .network import Network, NetworkError  
from .config import (
    DEFAULT_CONFIGS, NetworkConfig, AsyncConfig, CacheConfig, LoggingConfig, SDKConfig,
    ConfigManager, get_config, set_config, update_config,
    load_config_from_file, save_config_to_file, create_custom_config
)
from .transactions import (
    Transactions,
    create_dag_transaction, create_metagraph_token_transaction, 
    create_metagraph_data_transaction  # Convenience functions
)
from .metagraph import (
    MetagraphClient, MetagraphError, 
    discover_production_metagraphs, get_realistic_metagraph_summary,
    discover_all_metagraphs, get_metagraph_summary  # Legacy functions
)

# Async support (Phase 2) - Optional import to handle missing aiohttp
try:
    from .async_network import AsyncNetwork, AsyncHTTPClient, create_async_network, get_multiple_balances_concurrent
    from .async_metagraph import (
        AsyncMetagraphClient, AsyncMetagraphDiscovery,
        discover_metagraphs_async, create_async_metagraph_client,
        batch_get_balances_from_multiple_metagraphs
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
    ValidationError, AddressValidationError, AmountValidationError,
    MetagraphIdValidationError, TransactionValidationError,
    TransactionError, HTTPError, APIError, InvalidDataError, ConfigurationError
)
from .validation import (
    AddressValidator, AmountValidator, MetagraphIdValidator,
    TransactionValidator, DataValidator,
    is_valid_dag_address, is_valid_amount, is_valid_metagraph_id
)

# Logging framework (Phase 1)
from .logging import (
    configure_logging, get_logger, get_performance_tracker,
    get_network_logger, get_transaction_logger, log_operation
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
    "get_metagraph_summary",   # Legacy
    
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
    "ASYNC_AVAILABLE"
]

# Add async components to exports if available (Phase 2)
if ASYNC_AVAILABLE:
    __all__.extend([
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
        "batch_get_balances_from_multiple_metagraphs"
    ]) 