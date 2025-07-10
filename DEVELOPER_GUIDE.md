# 🔧 Constellation Python SDK - Developer Guide

Advanced usage patterns, best practices, and contribution guidelines for the Constellation Network Python SDK.

## 📋 Table of Contents

- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Testing Guide](#testing-guide)
- [Performance Optimization](#performance-optimization)
- [Error Handling Best Practices](#error-handling-best-practices)
- [Contributing Guidelines](#contributing-guidelines)
- [Development Setup](#development-setup)

## 🚀 Advanced Usage Patterns

### Custom Network Configuration

```python
from constellation_sdk import (
    NetworkConfig, AsyncConfig, CacheConfig, LoggingConfig, 
    SDKConfig, ConfigManager
)

# Create custom network configuration
custom_network = NetworkConfig(
    network_version="2.0",
    be_url="https://custom-block-explorer.com",
    l0_url="https://custom-l0-node.com",
    l1_url="https://custom-l1-node.com",
    name="CustomNet",
    timeout=45,
    max_retries=5,
    rate_limit_requests=50
)

# Advanced async configuration
async_config = AsyncConfig(
    connector_limit=200,
    max_concurrent_requests=100,
    total_timeout=60,
    verify_ssl=True
)

# Cache optimization
cache_config = CacheConfig(
    enable_caching=True,
    cache_ttl=600,  # 10 minutes
    max_cache_size=2000,
    cache_balances=True,
    cache_node_info=True
)

# Structured logging
logging_config = LoggingConfig(
    level="INFO",
    enable_console=True,
    enable_file=True,
    log_file="constellation.log",
    structured_logging=True,
    log_performance=True
)

# Complete SDK configuration
sdk_config = SDKConfig(
    network=custom_network,
    async_config=async_config,
    cache=cache_config,
    logging=logging_config,
    debug_mode=False,
    enable_performance_tracking=True
)

# Apply configuration
config_manager = ConfigManager()
config_manager.set_config(sdk_config)
```

### Advanced Async Patterns

```python
import asyncio
from typing import List, Dict, Any
from constellation_sdk import AsyncNetwork, AsyncMetagraphClient

class ConstellationManager:
    """Advanced async operations manager."""
    
    def __init__(self, max_concurrent: int = 50):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.async_network = None
    
    async def __aenter__(self):
        self.async_network = AsyncNetwork()
        await self.async_network.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.async_network:
            await self.async_network.__aexit__(exc_type, exc_val, exc_tb)
    
    async def batch_balance_check(self, addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check balances for multiple addresses with concurrency control."""
        async def get_balance_with_semaphore(address: str):
            async with self.semaphore:
                try:
                    return address, await self.async_network.get_balance(address)
                except Exception as e:
                    return address, {"error": str(e)}
        
        tasks = [get_balance_with_semaphore(addr) for addr in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            address: balance_info 
            for address, balance_info in results 
            if not isinstance(balance_info, Exception)
        }
    
    async def monitor_multiple_accounts(
        self, 
        addresses: List[str], 
        callback, 
        interval: int = 30
    ):
        """Monitor multiple accounts for balance changes."""
        last_ordinals = {addr: 0 for addr in addresses}
        
        while True:
            try:
                balances = await self.batch_balance_check(addresses)
                
                for address, balance_info in balances.items():
                    if "error" in balance_info:
                        continue
                        
                    current_ordinal = balance_info.get('ordinal', 0)
                    if current_ordinal > last_ordinals[address]:
                        await callback(address, balance_info)
                        last_ordinals[address] = current_ordinal
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(interval)

# Usage example
async def balance_change_handler(address: str, balance_info: Dict[str, Any]):
    print(f"🔄 Balance change detected for {address[:12]}...")
    print(f"💰 New balance: {balance_info.get('balance', 'N/A')} DAG")

async def advanced_monitoring_example():
    addresses = ["DAG123...", "DAG456...", "DAG789..."]
    
    async with ConstellationManager(max_concurrent=25) as manager:
        # Check all balances once
        balances = await manager.batch_balance_check(addresses)
        print("Initial balances:", balances)
        
        # Start monitoring (in practice, you'd run this as a background task)
        try:
            await asyncio.wait_for(
                manager.monitor_multiple_accounts(
                    addresses, 
                    balance_change_handler,
                    interval=10
                ),
                timeout=60  # Monitor for 1 minute
            )
        except asyncio.TimeoutError:
            print("Monitoring completed")

# Run the example
# asyncio.run(advanced_monitoring_example())
```

### Custom Validation and Error Handling

```python
from constellation_sdk import (
    ValidationError, NetworkError, ConstellationError,
    AddressValidator, AmountValidator
)
from typing import Optional, Dict, Any
import logging

class RobustTransactionManager:
    """Production-ready transaction manager with comprehensive error handling."""
    
    def __init__(self, network, account):
        self.network = network
        self.account = account
        self.logger = logging.getLogger(__name__)
        self.address_validator = AddressValidator()
        self.amount_validator = AmountValidator()
    
    def validate_transaction_params(
        self, 
        to_address: str, 
        amount: float, 
        fee: float = 0
    ) -> Dict[str, Any]:
        """Comprehensive transaction parameter validation."""
        errors = []
        
        # Validate recipient address
        try:
            self.address_validator.validate(to_address)
        except ValidationError as e:
            errors.append(f"Invalid recipient address: {e}")
        
        # Validate amount
        try:
            self.amount_validator.validate(amount)
            if amount <= 0:
                errors.append("Amount must be positive")
        except ValidationError as e:
            errors.append(f"Invalid amount: {e}")
        
        # Validate fee
        try:
            self.amount_validator.validate(fee)
            if fee < 0:
                errors.append("Fee cannot be negative")
        except ValidationError as e:
            errors.append(f"Invalid fee: {e}")
        
        # Check sender is not recipient
        if to_address == self.account.address:
            errors.append("Cannot send to self")
        
        if errors:
            raise ValidationError(f"Transaction validation failed: {'; '.join(errors)}")
        
        return {"valid": True, "to_address": to_address, "amount": amount, "fee": fee}
    
    def check_sufficient_balance(self, required_amount: float) -> Dict[str, Any]:
        """Check if account has sufficient balance for transaction."""
        try:
            balance_info = self.network.get_balance(self.account.address)
            current_balance = float(balance_info.get('balance', 0))
            
            if current_balance < required_amount:
                raise ValidationError(
                    f"Insufficient balance. Required: {required_amount}, "
                    f"Available: {current_balance}"
                )
            
            return {
                "sufficient": True,
                "current_balance": current_balance,
                "required": required_amount,
                "remaining": current_balance - required_amount,
                "balance_info": balance_info
            }
            
        except NetworkError as e:
            self.logger.error(f"Network error checking balance: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error checking balance: {e}")
            raise ConstellationError(f"Balance check failed: {e}")
    
    def create_safe_transaction(
        self,
        to_address: str,
        amount: float,
        fee: float = 0,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Create transaction with comprehensive error handling and retries."""
        from constellation_sdk import Transactions
        
        # Validate parameters
        validation_result = self.validate_transaction_params(to_address, amount, fee)
        total_amount = amount + fee
        
        # Check balance with retries
        for attempt in range(max_retries):
            try:
                balance_check = self.check_sufficient_balance(total_amount)
                break
            except NetworkError as e:
                self.logger.warning(f"Balance check attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # Create transaction
        try:
            transactions = Transactions()
            balance_info = balance_check["balance_info"]
            
            tx_data = transactions.create_dag_transaction(
                account=self.account,
                to_address=to_address,
                amount=amount,
                fee=fee,
                last_ref_hash=balance_info.get('lastTransactionRef', {}).get('hash', ''),
                last_ref_ordinal=balance_info.get('ordinal', 0)
            )
            
            self.logger.info(
                f"Transaction created: {amount} DAG to {to_address[:12]}... "
                f"(fee: {fee})"
            )
            
            return {
                "transaction": tx_data,
                "balance_before": balance_check["current_balance"],
                "amount": amount,
                "fee": fee,
                "recipient": to_address
            }
            
        except Exception as e:
            self.logger.error(f"Transaction creation failed: {e}")
            raise ConstellationError(f"Failed to create transaction: {e}")
    
    def submit_with_monitoring(
        self,
        tx_data: Dict[str, Any],
        timeout: int = 300,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """Submit transaction and monitor for confirmation."""
        import time
        
        try:
            # Submit transaction
            result = self.network.submit_transaction(tx_data)
            tx_hash = result.get('hash')
            
            if not tx_hash:
                raise ConstellationError("No transaction hash returned")
            
            self.logger.info(f"Transaction submitted: {tx_hash}")
            
            # Monitor for confirmation (simplified - in practice you'd check the ledger)
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Check if transaction appears in balance history
                    # This is a simplified check - real implementation would be more sophisticated
                    balance_info = self.network.get_balance(self.account.address)
                    
                    # If ordinal increased, transaction likely confirmed
                    # (This is simplified logic for demonstration)
                    if balance_info.get('ordinal', 0) > 0:
                        self.logger.info(f"Transaction confirmed: {tx_hash}")
                        return {
                            "confirmed": True,
                            "hash": tx_hash,
                            "confirmation_time": time.time() - start_time
                        }
                
                except Exception as e:
                    self.logger.warning(f"Confirmation check failed: {e}")
                
                time.sleep(poll_interval)
            
            # Timeout reached
            self.logger.warning(f"Transaction confirmation timeout: {tx_hash}")
            return {
                "confirmed": False,
                "hash": tx_hash,
                "timeout": True,
                "message": "Confirmation timeout - transaction may still be processing"
            }
            
        except Exception as e:
            self.logger.error(f"Transaction submission failed: {e}")
            raise

# Usage example
from constellation_sdk import Account, Network

def robust_transaction_example():
    account = Account()  # or load existing account
    network = Network('testnet')
    
    tx_manager = RobustTransactionManager(network, account)
    
    try:
        # Create transaction with validation
        tx_result = tx_manager.create_safe_transaction(
            to_address="DAG123RecipientAddress...",
            amount=10.5,
            fee=0
        )
        
        if tx_result:
            # Submit and monitor
            confirmation = tx_manager.submit_with_monitoring(
                tx_result["transaction"],
                timeout=180
            )
            
            if confirmation["confirmed"]:
                print(f"✅ Transaction confirmed: {confirmation['hash']}")
            else:
                print(f"⏳ Transaction pending: {confirmation['hash']}")
    
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
    except NetworkError as e:
        print(f"❌ Network error: {e}")
    except ConstellationError as e:
        print(f"❌ Constellation error: {e}")
```

## 🧪 Testing Guide

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch
from constellation_sdk import Account, Network, ValidationError

class TestAccountOperations:
    """Comprehensive account testing."""
    
    def test_account_creation(self):
        """Test account creation and properties."""
        account = Account()
        
        assert account.address.startswith('DAG')
        assert len(account.address) == 40  # DAG + 37 characters
        assert len(account.private_key) == 32
        assert len(account.public_key) == 33
    
    def test_account_from_private_key(self):
        """Test account creation from existing private key."""
        # Use a test private key (never use this in production!)
        test_private_key = bytes.fromhex(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        )
        
        account = Account(private_key=test_private_key)
        
        assert account.private_key == test_private_key
        assert account.address.startswith('DAG')
    
    @patch('constellation_sdk.network.requests.get')
    def test_balance_retrieval(self, mock_get):
        """Test balance retrieval with mocked network."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'balance': '100.5',
            'ordinal': 42
        }
        mock_get.return_value = mock_response
        
        network = Network('testnet')
        account = Account()
        
        balance_info = network.get_balance(account.address)
        
        assert balance_info['balance'] == '100.5'
        assert balance_info['ordinal'] == 42
        mock_get.assert_called_once()
    
    @patch('constellation_sdk.network.requests.get')
    def test_network_error_handling(self, mock_get):
        """Test network error handling."""
        # Mock network error
        mock_get.side_effect = Exception("Network connection failed")
        
        network = Network('testnet')
        account = Account()
        
        with pytest.raises(Exception):
            network.get_balance(account.address)

@pytest.mark.asyncio
async def test_async_operations():
    """Test async functionality."""
    from constellation_sdk import AsyncNetwork, ASYNC_AVAILABLE
    
    if not ASYNC_AVAILABLE:
        pytest.skip("Async not available")
    
    async with AsyncNetwork() as client:
        # Test that client initializes properly
        assert client is not None
        
        # Mock test for async balance retrieval
        with patch.object(client, 'get_balance') as mock_balance:
            mock_balance.return_value = {'balance': '50.0', 'ordinal': 10}
            
            result = await client.get_balance("DAG123TestAddress...")
            assert result['balance'] == '50.0'

def test_validation_functions():
    """Test validation components."""
    from constellation_sdk import is_valid_dag_address, is_valid_amount
    
    # Test valid addresses
    assert is_valid_dag_address("DAG123ValidAddressExample123456789012")
    
    # Test invalid addresses
    assert not is_valid_dag_address("InvalidAddress")
    assert not is_valid_dag_address("DAG")  # Too short
    
    # Test valid amounts
    assert is_valid_amount(10.5)
    assert is_valid_amount(0)
    
    # Test invalid amounts
    assert not is_valid_amount(-5)
    assert not is_valid_amount("not_a_number")

# Run tests with: pytest -v test_constellation.py
```

### Integration Testing

```python
import pytest
import asyncio
from constellation_sdk import Network, Account, ASYNC_AVAILABLE

class TestIntegration:
    """Integration tests (require network connectivity)."""
    
    @pytest.mark.integration
    def test_network_connectivity(self):
        """Test actual network connectivity."""
        network = Network('testnet')
        
        try:
            node_info = network.get_node_info()
            assert 'id' in node_info
            assert 'state' in node_info
        except Exception as e:
            pytest.skip(f"Network not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_network_connectivity(self):
        """Test async network connectivity."""
        if not ASYNC_AVAILABLE:
            pytest.skip("Async not available")
        
        from constellation_sdk import AsyncNetwork
        
        try:
            async with AsyncNetwork() as client:
                node_info = await client.get_node_info()
                assert 'id' in node_info
        except Exception as e:
            pytest.skip(f"Async network not available: {e}")

# Run integration tests with: pytest -v -m integration
```

### CLI Testing

```bash
#!/bin/bash
# cli_tests.sh - CLI testing script

echo "🧪 Testing CLI functionality..."

# Test basic CLI
echo "Testing CLI help..."
constellation --help || exit 1

# Test account creation
echo "Testing account creation..."
constellation account create --save-key || exit 1

# Test configuration
echo "Testing configuration..."
constellation config show || exit 1

# Test network commands (may fail in CI)
echo "Testing network commands..."
constellation network health || echo "⚠️  Network health check failed (expected in CI)"

echo "✅ CLI tests completed"
```

## ⚡ Performance Optimization

### Connection Pooling and Caching

```python
from constellation_sdk import get_config, set_config

# Optimize for high-throughput applications
config = get_config()

# Network optimizations
config.network.timeout = 30
config.network.max_retries = 3
config.network.max_connections = 200
config.network.keepalive = True

# Async optimizations
config.async_config.connector_limit = 500
config.async_config.max_concurrent_requests = 100
config.async_config.enable_compression = True

# Cache optimizations
config.cache.enable_caching = True
config.cache.cache_ttl = 300  # 5 minutes
config.cache.max_cache_size = 5000
config.cache.cache_balances = True
config.cache.cache_node_info = True

set_config(config)
```

### Batch Operations

```python
import asyncio
from constellation_sdk import AsyncNetwork

async def efficient_balance_checking():
    """Efficiently check many balances using batching."""
    addresses = [f"DAG{i:037d}" for i in range(1000)]  # 1000 addresses
    
    async with AsyncNetwork() as client:
        # Process in batches to avoid overwhelming the server
        batch_size = 50
        all_results = {}
        
        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [client.get_balance(addr) for addr in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            for addr, result in zip(batch, results):
                if not isinstance(result, Exception):
                    all_results[addr] = result
            
            # Rate limiting - small delay between batches
            await asyncio.sleep(0.1)
        
        return all_results

# Usage
# results = asyncio.run(efficient_balance_checking())
```

## 🔥 Error Handling Best Practices

### Comprehensive Error Handling

```python
from constellation_sdk import (
    ValidationError, NetworkError, HTTPError, APIError,
    ConstellationError, TimeoutError
)
import logging
import time
from typing import Optional, Callable, Any

class ErrorHandler:
    """Centralized error handling for Constellation SDK operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def with_retry(
        self,
        func: Callable,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        retry_on: tuple = (NetworkError, TimeoutError, HTTPError)
    ) -> Callable:
        """Decorator for adding retry logic to functions."""
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    delay = backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                except Exception as e:
                    # Don't retry on non-retryable errors
                    self.logger.error(f"Non-retryable error: {e}")
                    raise
            
            # All retries exhausted
            self.logger.error(f"All {max_retries} retries exhausted")
            raise last_exception
        
        return wrapper
    
    def handle_constellation_errors(self, func: Callable) -> Callable:
        """Decorator for comprehensive Constellation error handling."""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except ValidationError as e:
                self.logger.error(f"Validation error: {e}")
                return {"error": "validation", "message": str(e)}
            
            except NetworkError as e:
                self.logger.error(f"Network error: {e}")
                return {"error": "network", "message": str(e), "retryable": True}
            
            except HTTPError as e:
                self.logger.error(f"HTTP error: {e}")
                return {
                    "error": "http", 
                    "message": str(e),
                    "status_code": getattr(e, 'status_code', None),
                    "retryable": 500 <= getattr(e, 'status_code', 0) < 600
                }
            
            except APIError as e:
                self.logger.error(f"API error: {e}")
                return {"error": "api", "message": str(e)}
            
            except ConstellationError as e:
                self.logger.error(f"Constellation error: {e}")
                return {"error": "constellation", "message": str(e)}
            
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return {"error": "unexpected", "message": str(e)}
        
        return wrapper

# Usage example
error_handler = ErrorHandler()

@error_handler.handle_constellation_errors
@error_handler.with_retry(max_retries=3)
def safe_balance_check(network, address):
    """Safe balance checking with error handling and retries."""
    return network.get_balance(address)

# Usage
from constellation_sdk import Network

network = Network('testnet')
result = safe_balance_check(network, "DAG123SomeAddress...")

if "error" in result:
    print(f"Error: {result['message']}")
    if result.get("retryable"):
        print("This error might be temporary, try again later")
else:
    print(f"Balance: {result.get('balance', 'N/A')} DAG")
```

## 🤝 Contributing Guidelines

### Development Setup

```bash
# Clone the repository
git clone https://github.com/constellation-network/python-sdk.git
cd python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
make dev-install

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### Code Standards

1. **PEP 8 Compliance**: All code must follow PEP 8 style guidelines
2. **Type Hints**: Use type hints for all function parameters and return values
3. **Docstrings**: Comprehensive docstrings for all public functions and classes
4. **Error Handling**: Comprehensive error handling with appropriate exception types
5. **Testing**: Unit tests required for all new features

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Testing Requirements

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=constellation_sdk --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Slow tests only
```

### Documentation Standards

- **API Documentation**: All public APIs must have comprehensive docstrings
- **Examples**: Include practical examples in docstrings
- **Type Information**: Document parameter types and return types
- **Error Conditions**: Document possible exceptions

Example:
```python
def create_transaction(
    account: Account,
    to_address: str,
    amount: float,
    fee: float = 0
) -> Dict[str, Any]:
    """
    Create a DAG transaction.
    
    Args:
        account: The account to send from
        to_address: Valid DAG address to send to
        amount: Amount to send in DAG tokens
        fee: Transaction fee (default: 0)
    
    Returns:
        Dict containing transaction data ready for submission
    
    Raises:
        ValidationError: If parameters are invalid
        ConstellationError: If transaction creation fails
    
    Example:
        >>> account = Account()
        >>> tx_data = create_transaction(
        ...     account=account,
        ...     to_address="DAG123...",
        ...     amount=10.5
        ... )
        >>> print(tx_data['hash'])
    """
```

### Release Process

1. **Update version** in `__init__.py` and `setup.py`
2. **Update CHANGELOG.md** with new features and fixes
3. **Create release** on GitHub with tag `vX.Y.Z`
4. **Automated publishing** will handle PyPI upload

---

## 📚 Additional Resources

- **Architecture Documentation**: See inline code comments for detailed architecture explanations
- **API Reference**: Check the main README.md for complete API documentation
- **Example Applications**: Explore the `examples/` directory
- **Community**: Join Constellation Network community channels for discussions

**Happy developing! 🚀** 