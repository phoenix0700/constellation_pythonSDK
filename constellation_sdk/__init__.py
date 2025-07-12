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

from .account import Account
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
    create_dag_transfer,
    create_data_submission,
    create_metagraph_token_transaction,
    create_token_transfer,
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
    ConstellationError,
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

# Transaction simulation (Phase 1)
from .simulation import (
    TransactionSimulator,
    estimate_transaction_cost,
    simulate_transaction,
)

# Batch operations (Enhanced REST Phase 1)
from .batch import (
    BatchOperation,
    BatchOperationType,
    BatchResult,
    BatchResponse,
    BatchValidator,
    create_batch_operation,
    batch_get_balances,
    batch_get_transactions,
    batch_get_ordinals,
)

# Real-time event streaming (Phase 3)
try:
    from .streaming import (
        NetworkEventStream,
        BalanceTracker,
        EventType,
        StreamEvent,
        EventFilter,
        create_event_stream,
        stream_transactions,
        stream_balance_changes,
    )
    
    STREAMING_AVAILABLE = True
except ImportError:
    # WebSocket dependencies not available
    NetworkEventStream = None
    BalanceTracker = None
    EventType = None
    StreamEvent = None
    EventFilter = None
    create_event_stream = None
    stream_transactions = None
    stream_balance_changes = None
    STREAMING_AVAILABLE = False

# GraphQL API support (Phase 4)
try:
    from .graphql import (
        GraphQLClient,
        GraphQLQuery,
        GraphQLResponse,
        GraphQLOperationType,
        ConstellationSchema,
        execute_query,
        execute_query_async,
        get_account_portfolio,
        get_metagraph_overview,
        get_network_status,
    )
    from .graphql_builder import (
        QueryBuilder,
        SubscriptionBuilder,
        build_account_query,
        build_metagraph_query,
        build_network_status_query,
        build_portfolio_query,
        build_transaction_subscription,
        build_balance_subscription,
    )
    
    GRAPHQL_AVAILABLE = True
except ImportError:
    # GraphQL dependencies not available
    GraphQLClient = None
    GraphQLQuery = None
    GraphQLResponse = None
    GraphQLOperationType = None
    ConstellationSchema = None
    execute_query = None
    execute_query_async = None
    get_account_portfolio = None
    get_metagraph_overview = None
    get_network_status = None
    QueryBuilder = None
    SubscriptionBuilder = None
    build_account_query = None
    build_metagraph_query = None
    build_network_status_query = None
    build_portfolio_query = None
    build_transaction_subscription = None
    build_balance_subscription = None
    GRAPHQL_AVAILABLE = False

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
    "create_dag_transfer",
    "create_token_transfer",
    "create_data_submission",
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
    # Transaction simulation (Phase 1)
    "TransactionSimulator",
    "simulate_transaction",
    "estimate_transaction_cost",
    # Batch operations (Enhanced REST Phase 1)
    "BatchOperation",
    "BatchOperationType",
    "BatchResult",
    "BatchResponse",
    "BatchValidator",
    "create_batch_operation",
    "batch_get_balances",
    "batch_get_transactions",
    "batch_get_ordinals",
    # Async availability flag
    "ASYNC_AVAILABLE",
    # Streaming availability flag
    "STREAMING_AVAILABLE",
    # GraphQL availability flag
    "GRAPHQL_AVAILABLE",
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

# Add streaming components to exports if available (Phase 3)
if STREAMING_AVAILABLE:
    __all__.extend(
        [
            # Streaming components
            "NetworkEventStream",
            "BalanceTracker",
            "EventType",
            "StreamEvent",
            "EventFilter",
            "create_event_stream",
            "stream_transactions",
            "stream_balance_changes",
        ]
    )

# Add GraphQL components to exports if available (Phase 4)
if GRAPHQL_AVAILABLE:
    __all__.extend(
        [
            # GraphQL core components
            "GraphQLClient",
            "GraphQLQuery",
            "GraphQLResponse",
            "GraphQLOperationType",
            "ConstellationSchema",
            "execute_query",
            "execute_query_async",
            "get_account_portfolio",
            "get_metagraph_overview",
            "get_network_status",
            # GraphQL query builder
            "QueryBuilder",
            "SubscriptionBuilder",
            "build_account_query",
            "build_metagraph_query",
            "build_network_status_query",
            "build_portfolio_query",
            "build_transaction_subscription",
            "build_balance_subscription",
        ]
    )
