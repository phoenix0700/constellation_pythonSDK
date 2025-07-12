# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Installation and Setup
```bash
# Install SDK and dependencies
make install

# Install with development tools (pytest, black, flake8, mypy)
make dev-install

# Create virtual environment
make venv
source constellation_env/bin/activate

# Install manually with async support
pip install -r requirements.txt
pip install -e .
```

### Testing
```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test
python -m pytest tests/test_account.py -v

# Run tests with specific markers
python -m pytest -m unit tests/
python -m pytest -m integration tests/
python -m pytest -m network tests/
```

### Code Quality
```bash
# Lint code (flake8 + mypy)
make lint

# Format code (black)
make format

# Additional quality checks (CI/CD uses these)
isort --check-only constellation_sdk/ tests/ examples/
black --check constellation_sdk/ tests/ examples/
mypy constellation_sdk/ --ignore-missing-imports --no-strict-optional
pylint constellation_sdk/ --exit-zero

# Clean build artifacts
make clean
```

### Running Examples
```bash
# Quick demo
make demo

# Run specific examples
python examples/basic_usage.py
python examples/metagraph_demo.py
python examples/simple_metagraph_usage.py
python examples/new_architecture_demo.py
python examples/offline_usage.py
python examples/transaction_simulation_demo.py
python examples/real_time_streaming_demo.py
python examples/batch_operations_demo.py
```

## Architecture Overview

The SDK v1.2.0 follows a clean separation of concerns with enhanced validation, async support, and comprehensive error handling:

### Core Classes
- **`Account`** (`constellation_sdk/account.py`) - Key management and transaction signing using secp256k1 cryptography
- **`Transactions`** (`constellation_sdk/transactions.py`) - Centralized transaction creation for all types (DAG, metagraph token, metagraph data)
- **`Network`** (`constellation_sdk/network.py`) - Core DAG network operations and API calls
- **`MetagraphClient`** (`constellation_sdk/metagraph.py`) - Metagraph discovery and queries
- **`AsyncNetwork`** (`constellation_sdk/async_network.py`) - High-performance async network operations
- **`AsyncMetagraphClient`** (`constellation_sdk/async_metagraph.py`) - Async metagraph operations

### Enhanced Components (v1.2.0)
- **Validation System** (`constellation_sdk/validation.py`) - Comprehensive input validation for addresses, amounts, and data
- **Exception Hierarchy** (`constellation_sdk/exceptions.py`) - Structured error handling with specific exception types
- **Logging Framework** (`constellation_sdk/logging.py`) - Structured logging with performance tracking
- **Configuration Management** (`constellation_sdk/config.py`) - Centralized configuration with async and caching support
- **Transaction Simulation** (`constellation_sdk/simulation.py`) - Pre-flight validation and cost estimation for transactions
- **Real-Time Event Streaming** (`constellation_sdk/streaming.py`) - WebSocket-based event streaming for live network monitoring
- **Batch Operations** (`constellation_sdk/batch.py`) - Enhanced REST operations for executing multiple API calls efficiently

### Key Design Principles
1. **Centralized Transaction Creation**: All transaction types are created through the `Transactions` class
2. **Clean API Consistency**: Same patterns for DAG and metagraph operations
3. **Account Security**: Private key management separated from transaction logic
4. **Network Flexibility**: Support for MainNet, TestNet, IntegrationNet, and custom nodes
5. **Async Performance**: Optional async support for high-throughput applications
6. **Comprehensive Validation**: Input validation at all layers
7. **Structured Error Handling**: Specific exceptions for different error types
8. **Enhanced REST Performance**: Batch operations for efficient multi-operation requests

### Transaction Flow
```python
# 1. Create account
account = Account()

# 2. Create transaction (using Transactions class with validation)
tx_data = Transactions.create_dag_transfer(
    source=account.address,
    destination=destination,
    amount=amount  # Automatically validated
)

# 3. Sign transaction (using Account class)
signed_tx = account.sign_transaction(tx_data)

# 4. Submit transaction (using Network class)
result = network.submit_transaction(signed_tx)
```

### Async Transaction Flow
```python
# For high-performance applications
async def process_transactions():
    async_network = AsyncNetwork('testnet')
    
    # Concurrent operations
    balances = await get_multiple_balances_concurrent(
        async_network, [addr1, addr2, addr3]
    )
    
    # Batch metagraph operations
    mg_balances = await batch_get_balances_from_multiple_metagraphs(
        'mainnet', [mg1, mg2], [addr1, addr2]
    )
```

### Transaction Simulation Flow
```python
# Simulate before creating transactions (saves TestNet funds)
from constellation_sdk import TransactionSimulator

# 1. Simulate transaction
simulation = Transactions.simulate_dag_transfer(
    source=account.address,
    destination=recipient,
    amount=amount,
    network=network,
    detailed_analysis=True
)

# 2. Check if transaction will succeed
if simulation['will_succeed']:
    # 3. Create and submit transaction
    tx_data = Transactions.create_dag_transfer(account.address, recipient, amount)
    signed_tx = account.sign_transaction(tx_data)
    result = network.submit_transaction(signed_tx)
else:
    # Handle validation errors
    print("Transaction would fail:", simulation['validation_errors'])

# Batch simulation
batch_simulation = Transactions.simulate_batch_transfer(
    source=account.address,
    transfers=[
        {'destination': addr1, 'amount': 1000000},
        {'destination': addr2, 'amount': 2000000, 'metagraph_id': mg_id}
    ],
    network=network
)
```

## Network Configuration

Three built-in networks are available in `constellation_sdk/config.py`:
- **mainnet**: Production Constellation Network
- **testnet**: Development and testing network
- **integrationnet**: Integration testing network

Each network has specific endpoints for:
- Block Explorer (`be_url`)
- Global L0 Hypergraph layer (`l0_url`)
- L1 DAG token layer (`l1_url`)

## Testing Requirements

TestNet funding is required for transaction submission testing. Contact the Constellation community (Discord/Telegram) for TestNet tokens.

### CI/CD Testing
The project uses GitHub Actions with extensive test coverage:
- **Unit Tests**: Run on Python 3.8-3.12 across Ubuntu, Windows, macOS
- **Integration Tests**: Test network connectivity on TestNet and IntegrationNet
- **Async Tests**: Verify async functionality when aiohttp is available
- **CLI Tests**: Validate command-line interface functionality
- **Security Scans**: Run safety, bandit, and pip-audit for vulnerability checks
- **Code Quality**: Multiple linting, formatting, and complexity checks

## File Structure

```
constellation_sdk/
├── __init__.py          # Main exports and version info
├── account.py           # Account management and signing
├── transactions.py      # Transaction creation (all types)
├── network.py           # Network interface and API calls
├── metagraph.py         # Metagraph discovery and queries
├── config.py            # Network configurations
├── async_network.py     # Async network operations
├── async_metagraph.py   # Async metagraph operations
├── validation.py        # Input validation system
├── exceptions.py        # Structured error handling
├── logging.py           # Logging framework
├── simulation.py        # Transaction simulation and estimation
├── streaming.py         # Real-time event streaming and WebSocket support
└── batch.py             # Enhanced REST batch operations

examples/                # Usage examples and demos
├── basic_usage.py       # Core SDK functionality
├── metagraph_demo.py    # Metagraph operations
├── simple_metagraph_usage.py
├── new_architecture_demo.py
├── offline_usage.py     # Offline transaction signing
├── transaction_simulation_demo.py  # Transaction simulation examples
├── real_time_streaming_demo.py    # Real-time event streaming examples
└── batch_operations_demo.py       # Enhanced REST batch operations examples

tests/                   # Unit tests with pytest markers
├── test_account.py      # Account functionality tests
├── test_transactions.py # Transaction creation tests
├── test_network.py      # Network operations tests
├── test_metagraph.py    # Metagraph functionality tests
├── test_async_network.py # Async network tests
├── test_simulation.py   # Transaction simulation tests
├── test_streaming.py    # Real-time event streaming tests
├── test_batch.py        # Batch operations tests
└── conftest.py          # Test configuration
```

## Error Handling

The SDK defines a comprehensive exception hierarchy:

### Base Exceptions
- `ConstellationError`: Base SDK error
- `NetworkError`: Network/API related errors
- `TransactionError`: Transaction creation/validation errors
- `MetagraphError`: Metagraph-specific errors

### Validation Exceptions (v1.2.0)
- `ValidationError`: Base validation error
- `AddressValidationError`: Invalid DAG address format
- `AmountValidationError`: Invalid amount values
- `MetagraphIdValidationError`: Invalid metagraph ID format
- `TransactionValidationError`: Invalid transaction structure

### Network Exceptions (v1.2.0)
- `HTTPError`: HTTP request/response errors
- `APIError`: API-specific errors
- `InvalidDataError`: Invalid response data
- `ConfigurationError`: Configuration/setup errors

### Exception Usage
```python
from constellation_sdk import ValidationError, NetworkError

try:
    tx_data = Transactions.create_dag_transfer(
        source="invalid_address",
        destination="DAG123...",
        amount=1000000
    )
except ValidationError as e:
    print(f"Validation error: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
```

## Dependencies

Core dependencies (see `requirements.txt`):
- `requests>=2.28.0` - HTTP client for API calls
- `cryptography>=3.4.8` - secp256k1 cryptography
- `base58>=2.1.0` - Address encoding
- `aiohttp>=3.8.0` - Async HTTP client for async operations
- `websockets>=10.0` - WebSocket client for real-time streaming (optional)

Development dependencies (installed via `make dev-install`):
- `pytest` - Testing framework with markers (unit, integration, network, slow, mock)
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `isort` - Import sorting
- `pylint` - Additional linting
- `safety` - Security vulnerability scanning
- `bandit` - Security linter

### Async Support
The SDK includes optional async support. If `aiohttp` is not installed, async components will be disabled:
```python
from constellation_sdk import ASYNC_AVAILABLE

if ASYNC_AVAILABLE:
    from constellation_sdk import AsyncNetwork, AsyncMetagraphClient
    # Use async operations
else:
    # Fall back to sync operations
    from constellation_sdk import Network, MetagraphClient
```

### Streaming Support
The SDK includes optional real-time streaming support. If `websockets` is not installed, streaming components will be disabled:
```python
from constellation_sdk import STREAMING_AVAILABLE

if STREAMING_AVAILABLE:
    from constellation_sdk import NetworkEventStream, BalanceTracker, EventType
    # Use streaming operations
else:
    # Streaming not available
    print("Install websockets for streaming support: pip install websockets")
```

## Validation System

The SDK includes comprehensive input validation for all operations:

### Validation Components
- **AddressValidator**: Validates DAG address format and checksums
- **AmountValidator**: Validates amount values (positive, within limits)
- **MetagraphIdValidator**: Validates metagraph ID format
- **TransactionValidator**: Validates transaction structure and signatures
- **DataValidator**: Validates data payloads for metagraph submissions

### Validation Usage
```python
from constellation_sdk import (
    is_valid_dag_address, is_valid_amount, is_valid_metagraph_id,
    AddressValidator, ValidationError
)

# Quick validation functions
if is_valid_dag_address("DAG123..."):
    print("Valid address")

if is_valid_amount(1000000):
    print("Valid amount")

# Detailed validation with error messages
try:
    AddressValidator.validate("invalid_address")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## Logging Framework

The SDK provides structured logging with performance tracking:

### Logging Configuration
```python
from constellation_sdk import configure_logging, get_logger

# Configure logging
configure_logging(
    level='INFO',
    format='structured',  # or 'simple'
    enable_performance_tracking=True
)

# Get specialized loggers
logger = get_logger(__name__)
network_logger = get_network_logger()
transaction_logger = get_transaction_logger()
```

### Performance Tracking
```python
from constellation_sdk import get_performance_tracker, log_operation

# Track operation performance
perf_tracker = get_performance_tracker()

# Use decorator for automatic tracking
@log_operation("balance_check")
def check_balance(address):
    return network.get_balance(address)

# Manual tracking
with perf_tracker.track_operation("transaction_creation"):
    tx_data = Transactions.create_dag_transfer(account, destination, amount)
```

## Transaction Simulation System

The SDK includes comprehensive transaction simulation capabilities to validate and estimate transactions before submission.

### Simulation Features
- **Pre-flight Validation**: Validate transaction structure, addresses, and amounts
- **Balance Sufficiency**: Check if source has sufficient balance for transaction
- **Cost Estimation**: Estimate transaction size and processing requirements
- **Success Probability**: Calculate likelihood of transaction success
- **Batch Simulation**: Simulate multiple transactions together
- **Detailed Analysis**: Get comprehensive analysis with optimization suggestions

### Simulation Components
- **`TransactionSimulator`**: Main simulation engine with caching and validation
- **`Transactions.simulate_*`**: Convenient simulation methods integrated into Transactions class
- **`simulate_transaction()`**: Quick simulation function for any transaction type
- **`estimate_transaction_cost()`**: Cost estimation utility

### Simulation Usage
```python
from constellation_sdk import TransactionSimulator, Transactions

# Method 1: Using Transactions class (recommended)
simulation = Transactions.simulate_dag_transfer(
    source=account.address,
    destination=recipient,
    amount=100000000,
    network=network,
    detailed_analysis=True
)

# Method 2: Using TransactionSimulator directly
simulator = TransactionSimulator(network)
result = simulator.simulate_token_transfer(
    account.address, recipient, 1000000000, metagraph_id
)

# Method 3: Convenience function
quick_sim = simulate_transaction(
    network, 'dag', account.address, recipient, 100000000
)

# Production workflow
if simulation['will_succeed']:
    tx = Transactions.create_dag_transfer(account.address, recipient, amount)
    signed_tx = account.sign_transaction(tx)
    result = network.submit_transaction(signed_tx)
else:
    print("Transaction would fail:", simulation['validation_errors'])
```

## Real-Time Event Streaming System

The SDK includes comprehensive real-time event streaming capabilities for monitoring live network activity, building responsive applications, and creating event-driven architectures.

### Streaming Features
- **WebSocket-based Streaming**: Real-time connection to network events
- **Event Filtering**: Filter events by addresses, transaction types, amounts, and custom criteria
- **Balance Change Tracking**: Monitor balance changes for specific addresses
- **Multi-Event Support**: Stream transactions, balance changes, blocks, and custom events
- **Automatic Reconnection**: Resilient connections with automatic reconnection
- **Polling Fallback**: Automatic fallback to polling when WebSocket is unavailable
- **Production-Ready**: Built for high-performance applications with caching and statistics

### Streaming Components
- **`NetworkEventStream`**: Main event streaming class with WebSocket support
- **`BalanceTracker`**: Specialized balance change tracking
- **`EventFilter`**: Flexible event filtering system
- **`StreamEvent`**: Event data structure
- **`create_event_stream()`**: Quick stream creation
- **`stream_transactions()`**: Convenience function for transaction streaming
- **`stream_balance_changes()`**: Convenience function for balance tracking

### Basic Streaming Usage
```python
from constellation_sdk import NetworkEventStream, EventType, EventFilter

# Create event stream
stream = NetworkEventStream('testnet')

# Transaction event handler
def handle_transaction(event):
    print(f"Transaction: {event.data.get('hash')}")
    print(f"From: {event.data.get('source')}")
    print(f"To: {event.data.get('destination')}")
    print(f"Amount: {event.data.get('amount', 0) / 1e8:.8f} DAG")

# Register event handler
stream.on(EventType.TRANSACTION, handle_transaction)

# Connect and start streaming
await stream.connect()

# Stream for 60 seconds
await asyncio.sleep(60)

# Disconnect
await stream.disconnect()
```

### Filtered Streaming
```python
# Create stream with address filter
stream = NetworkEventStream('testnet')

# Filter for specific addresses and transaction types
event_filter = EventFilter(
    addresses={'DAG123...', 'DAG456...'},
    transaction_types={'dag_transfer', 'token_transfer'},
    amount_range=(100000000, 1000000000)  # 1-10 DAG
)
stream.add_filter('my_filter', event_filter)

# Event handler for filtered events
def handle_filtered_event(event):
    print(f"Filtered event: {event.data}")

stream.on(EventType.TRANSACTION, handle_filtered_event)

# Connect and stream
await stream.connect()
await asyncio.sleep(30)
await stream.disconnect()
```

### Balance Change Tracking
```python
from constellation_sdk import BalanceTracker

# Create balance tracker
stream = NetworkEventStream('testnet')
tracker = BalanceTracker('testnet')

# Track specific addresses
tracker.track_address('DAG123...')
tracker.track_address('DAG456...')

# Balance change handler
def handle_balance_change(event):
    data = event.data
    print(f"Balance change for {data['address']}")
    print(f"Old: {data['old_balance'] / 1e8:.8f} DAG")
    print(f"New: {data['new_balance'] / 1e8:.8f} DAG")
    print(f"Change: {data['change'] / 1e8:.8f} DAG")

# Register balance change handler
stream.on(EventType.BALANCE_CHANGE, handle_balance_change)

# Connect and start tracking
await stream.connect()
await tracker.start(stream)

# Track for 300 seconds
await asyncio.sleep(300)

# Stop tracking
await tracker.stop()
await stream.disconnect()
```

### Multi-Event Streaming
```python
# Create stream for all event types
stream = NetworkEventStream('testnet')

# Generic event handler
def handle_any_event(event):
    print(f"{event.event_type.value.upper()} Event:")
    print(f"  Network: {event.network}")
    print(f"  Data: {event.data}")

# Register handlers for all event types
for event_type in EventType:
    stream.on(event_type, handle_any_event)

# Connect and stream
await stream.connect()
await asyncio.sleep(120)
await stream.disconnect()
```

### Custom Event Filters
```python
# Custom filter function
def high_value_filter(event):
    if event.event_type == EventType.TRANSACTION:
        return event.data.get('amount', 0) >= 1000000000  # 10+ DAG
    return True

# Create filter with custom function
custom_filter = EventFilter(
    custom_filter=high_value_filter,
    transaction_types={'dag_transfer', 'token_transfer'}
)

stream = NetworkEventStream('testnet')
stream.add_filter('high_value', custom_filter)

# Handler for high-value transactions
def handle_high_value_tx(event):
    print(f"High-value transaction: {event.data.get('amount', 0) / 1e8:.8f} DAG")

stream.on(EventType.TRANSACTION, handle_high_value_tx)

# Connect and stream
await stream.connect()
await asyncio.sleep(180)
await stream.disconnect()
```

### Convenience Functions
```python
# Quick transaction streaming
stream = await stream_transactions(
    network='testnet',
    callback=handle_transaction,
    addresses=['DAG123...', 'DAG456...'],
    transaction_types=['dag_transfer']
)

# Quick balance tracking
stream, tracker = await stream_balance_changes(
    network='testnet',
    addresses=['DAG123...', 'DAG456...'],
    callback=handle_balance_change
)
```

### Production Streaming Patterns
```python
# Production-ready event processing
class ProductionEventProcessor:
    def __init__(self):
        self.event_buffer = []
        self.alert_threshold = 1000000000  # 10 DAG
        
    async def process_transaction(self, event):
        # Buffer events for batch processing
        self.event_buffer.append(event)
        
        # Process alerts
        if event.data.get('amount', 0) >= self.alert_threshold:
            await self.send_alert(event)
        
        # Batch process every 100 events
        if len(self.event_buffer) >= 100:
            await self.process_batch()
    
    async def send_alert(self, event):
        # Send alert to monitoring system
        print(f"ALERT: High-value transaction {event.data.get('hash')}")
    
    async def process_batch(self):
        # Process buffered events
        print(f"Processing batch of {len(self.event_buffer)} events")
        self.event_buffer.clear()

# Use production processor
processor = ProductionEventProcessor()
stream = NetworkEventStream('mainnet')
stream.on(EventType.TRANSACTION, processor.process_transaction)

# Connect with error handling
try:
    await stream.connect()
    # Stream indefinitely
    while True:
        await asyncio.sleep(10)
        stats = stream.get_stats()
        print(f"Stream stats: {stats['events_received']} events, {stats['uptime']:.1f}s uptime")
except Exception as e:
    print(f"Streaming error: {e}")
finally:
    await stream.disconnect()
```

### CLI Streaming Commands
```bash
# Stream transactions
constellation stream transactions --duration 60 --addresses DAG123... --tx-types dag_transfer

# Stream balance changes
constellation stream balance DAG123... DAG456... --poll-interval 5 --duration 300

# Stream all events with filtering
constellation stream events --event-types transaction --addresses DAG123... --output-file events.json

# Stream with JSON output
constellation --output json stream transactions --duration 30 > transactions.json
```

## Enhanced REST Batch Operations

The SDK includes comprehensive batch operations capabilities for executing multiple API calls efficiently in a single request, reducing network round trips and improving performance for complex queries.

### Batch Operations Features
- **Multiple Operation Types**: Execute different types of operations (balance, transactions, ordinals, etc.) in one request
- **Comprehensive Validation**: Input validation for all batch operations before execution
- **Error Resilience**: Individual operation failures don't affect other operations in the batch
- **Performance Tracking**: Detailed execution statistics and timing information
- **Async Support**: High-performance concurrent execution with AsyncNetwork
- **CLI Integration**: Full command-line interface for batch operations

### Batch Operations Components
- **`BatchOperation`**: Individual operation within a batch request
- **`BatchResponse`**: Complete response with results and statistics
- **`BatchValidator`**: Validation system for batch operations
- **`create_batch_operation()`**: Convenience function for creating operations
- **`batch_get_balances()`**: Create balance operations for multiple addresses
- **`batch_get_transactions()`**: Create transaction operations for multiple addresses
- **`batch_get_ordinals()`**: Create ordinal operations for multiple addresses

### Basic Batch Operations Usage
```python
from constellation_sdk import Network, create_batch_operation

# Create network connection
network = Network('testnet')

# Create batch operations
operations = [
    create_batch_operation('get_balance', {'address': 'DAG123...'}, 'balance'),
    create_batch_operation('get_ordinal', {'address': 'DAG123...'}, 'ordinal'),
    create_batch_operation('get_transactions', {'address': 'DAG123...', 'limit': 10}, 'transactions')
]

# Execute batch request
response = network.batch_request(operations)

# Check results
print(f"Success rate: {response.success_rate()}%")
print(f"Execution time: {response.execution_time:.3f}s")

# Get individual results
balance_result = response.get_result('balance')
if balance_result and balance_result.success:
    print(f"Balance: {balance_result.data / 1e8:.8f} DAG")
```

### Multi-Address Operations
```python
# Get balances for multiple addresses efficiently
addresses = ['DAG123...', 'DAG456...', 'DAG789...']
balances = network.get_multi_balance(addresses)

# Get transactions for multiple addresses
transactions = network.get_multi_transactions(addresses, limit=5)

# Get ordinals for multiple addresses
ordinals = network.get_multi_ordinal(addresses)

# Get comprehensive address overview
overview = network.get_address_overview('DAG123...')
print(f"Balance: {overview['balance'] / 1e8:.8f} DAG")
print(f"Transactions: {len(overview['transactions'])}")
print(f"Execution time: {overview['execution_time']:.3f}s")
```

### Async Batch Operations
```python
from constellation_sdk import AsyncNetwork

async def async_batch_demo():
    async_network = AsyncNetwork('testnet')
    await async_network.__aenter__()
    
    # Execute operations concurrently
    operations = [
        create_batch_operation('get_balance', {'address': addr}, f'balance_{i}')
        for i, addr in enumerate(addresses)
    ]
    
    response = await async_network.batch_request(operations)
    print(f"Concurrent execution: {response.summary['concurrent_execution']}")
    print(f"Success rate: {response.success_rate()}%")
    
    # Enhanced multi-balance with async
    balances = await async_network.get_multi_balance_enhanced(addresses)
    
    await async_network.__aexit__(None, None, None)

# Run async demo
asyncio.run(async_batch_demo())
```

### Convenience Functions
```python
from constellation_sdk import batch_get_balances, batch_get_transactions

# Create batch operations using convenience functions
balance_ops = batch_get_balances(['DAG123...', 'DAG456...'])
transaction_ops = batch_get_transactions(['DAG123...', 'DAG456...'], limit=10)

# Combine different operation types
all_operations = balance_ops + transaction_ops
response = network.batch_request(all_operations)

print(f"Executed {len(all_operations)} operations")
print(f"Success rate: {response.success_rate()}%")
```

### Error Handling and Resilience
```python
# Batch operations handle individual failures gracefully
mixed_operations = [
    create_batch_operation('get_balance', {'address': 'DAG123...'}, 'valid'),
    create_batch_operation('get_balance', {'address': 'INVALID'}, 'invalid'),
]

response = network.batch_request(mixed_operations)

# Check overall results
successful_results = response.get_successful_results()
failed_results = response.get_failed_results()

print(f"Successful: {len(successful_results)}")
print(f"Failed: {len(failed_results)}")

# Process results individually
for result in response.results:
    if result.success:
        print(f"✅ {result.id}: {result.data}")
    else:
        print(f"❌ {result.id}: {result.error}")
```

### CLI Batch Operations Commands
```bash
# Get balances for multiple addresses
constellation batch balances DAG123... DAG456... DAG789...

# Get comprehensive address overview
constellation batch overview DAG123... --include-transactions

# Get transactions for multiple addresses
constellation batch transactions DAG123... DAG456... --limit 5

# Execute custom batch operations from JSON file
constellation batch custom operations.json --output-file results.json

# JSON output format
constellation --output json batch balances DAG123... DAG456...
```

### Custom Batch Operations File Format
```json
[
  {
    "operation": "get_balance",
    "params": {"address": "DAG123..."},
    "id": "alice_balance"
  },
  {
    "operation": "get_transactions",
    "params": {"address": "DAG456...", "limit": 10},
    "id": "bob_transactions"
  },
  {
    "operation": "get_node_info",
    "params": {},
    "id": "network_status"
  }
]
```

### Performance Benefits
- **Reduced Network Calls**: Execute multiple operations in a single HTTP request
- **Lower Latency**: Eliminate multiple round trips for complex queries
- **Improved Throughput**: Async support enables concurrent operation execution
- **Better Resource Usage**: More efficient use of network and API resources
- **Enhanced User Experience**: Faster response times for applications

### Supported Batch Operations
- `get_balance`: Get address balance
- `get_ordinal`: Get address ordinal (transaction count)
- `get_transactions`: Get address transaction history
- `get_recent_transactions`: Get recent network transactions
- `get_node_info`: Get node information
- `get_cluster_info`: Get cluster information
- `submit_transaction`: Submit signed transaction

### Production Usage Patterns
```python
# Portfolio dashboard with batch operations
def get_portfolio_data(addresses):
    operations = []
    
    # Add balance checks for all addresses
    for i, address in enumerate(addresses):
        operations.append(
            create_batch_operation('get_balance', {'address': address}, f'balance_{i}')
        )
    
    # Add transaction history for first few addresses
    for i, address in enumerate(addresses[:3]):
        operations.append(
            create_batch_operation('get_transactions', {'address': address, 'limit': 10}, f'txs_{i}')
        )
    
    # Add network status
    operations.append(
        create_batch_operation('get_node_info', {}, 'network_status')
    )
    
    # Execute portfolio analysis
    response = network.batch_request(operations)
    
    # Process results for dashboard
    portfolio_data = {
        'balances': {},
        'transactions': {},
        'network_status': None,
        'success': response.success_rate() == 100
    }
    
    for result in response.get_successful_results():
        if 'balance_' in result.id:
            idx = int(result.id.split('_')[1])
            portfolio_data['balances'][addresses[idx]] = result.data
        elif 'txs_' in result.id:
            idx = int(result.id.split('_')[1])
            portfolio_data['transactions'][addresses[idx]] = result.data
        elif result.id == 'network_status':
            portfolio_data['network_status'] = result.data
    
    return portfolio_data
```