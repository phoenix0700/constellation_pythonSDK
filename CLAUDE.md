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

### Key Design Principles
1. **Centralized Transaction Creation**: All transaction types are created through the `Transactions` class
2. **Clean API Consistency**: Same patterns for DAG and metagraph operations
3. **Account Security**: Private key management separated from transaction logic
4. **Network Flexibility**: Support for MainNet, TestNet, IntegrationNet, and custom nodes
5. **Async Performance**: Optional async support for high-throughput applications
6. **Comprehensive Validation**: Input validation at all layers
7. **Structured Error Handling**: Specific exceptions for different error types

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
└── logging.py           # Logging framework

examples/                # Usage examples and demos
├── basic_usage.py       # Core SDK functionality
├── metagraph_demo.py    # Metagraph operations
├── simple_metagraph_usage.py
├── new_architecture_demo.py
└── offline_usage.py     # Offline transaction signing

tests/                   # Unit tests with pytest markers
├── test_account.py      # Account functionality tests
├── test_transactions.py # Transaction creation tests
├── test_network.py      # Network operations tests
├── test_metagraph.py    # Metagraph functionality tests
├── test_async_network.py # Async network tests
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