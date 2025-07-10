# 🚀 Constellation Python SDK - Quick Start Guide

Get up and running with the Constellation Network Python SDK in minutes!

## 📦 Installation

### Method 1: Install from PyPI (Recommended)
```bash
pip install constellation-sdk
```

### Method 2: Install from Source
```bash
git clone https://github.com/constellation-network/python-sdk.git
cd python-sdk
pip install -e .
```

## 🛠️ Quick Setup

### 1. Basic Setup
```python
from constellation_sdk import Account, Network

# Create or load an account
account = Account()  # Creates new account
# OR load existing account:
# account = Account(private_key=bytes.fromhex("your_private_key_here"))

# Connect to network
network = Network('testnet')  # or 'mainnet', 'integrationnet'

print(f"Your address: {account.address}")
```

### 2. CLI Setup (Optional but Recommended)
```bash
# Check installation
constellation --help

# Create and save a default account
constellation account create --save-key

# View configuration
constellation config show
```

## 🔑 Essential Operations

### Check Account Balance
```python
# Using SDK
balance_info = network.get_balance(account.address)
print(f"Balance: {balance_info['balance']} DAG")

# Using CLI
constellation balance DAG123YourAddressHere...
# Or if you have a default account:
constellation account info
```

### Send Transactions
```python
from constellation_sdk import Transactions

# Initialize transaction handler
transactions = Transactions()

# Get current account state
balance_info = network.get_balance(account.address)

# Create transaction
tx_data = transactions.create_dag_transaction(
    account=account,
    to_address="DAG456RecipientAddress...",
    amount=10.5,  # Amount in DAG
    fee=0,
    last_ref_hash=balance_info.get('lastTransactionRef', {}).get('hash', ''),
    last_ref_ordinal=balance_info.get('ordinal', 0)
)

# Submit transaction
result = network.submit_transaction(tx_data)
print(f"Transaction submitted: {result['hash']}")
```

```bash
# Using CLI
constellation send 10.5 DAG456RecipientAddress... --from-key your_private_key
# Or with default account:
constellation send 10.5 DAG456RecipientAddress...
```

### Network Information
```python
# Get node info
node_info = network.get_node_info()
print(f"Node state: {node_info['state']}")

# Get latest snapshot
snapshot = network.get_latest_snapshot()
print(f"Latest ordinal: {snapshot['ordinal']}")
```

```bash
# Using CLI
constellation network info
constellation network health
```

## 🔄 Async Operations (For High Performance)

```python
import asyncio
from constellation_sdk import AsyncNetwork

async def async_example():
    async with AsyncNetwork() as client:
        # Get multiple balances concurrently
        addresses = ["DAG123...", "DAG456...", "DAG789..."]
        balances = await client.batch_get_balances(addresses)
        
        for address, balance_info in balances.items():
            print(f"{address}: {balance_info['balance']} DAG")

# Run async code
asyncio.run(async_example())
```

## 🏗️ Metagraph Operations

### Discover Available Metagraphs
```python
from constellation_sdk import discover_production_metagraphs

# Find production metagraphs
metagraphs = discover_production_metagraphs()
for mg in metagraphs:
    print(f"Metagraph: {mg['metagraph_id']} - {mg.get('name', 'Unknown')}")
```

```bash
# Using CLI
constellation metagraph discover --production
constellation metagraph discover --async  # Faster async discovery
```

### Working with Specific Metagraphs
```python
from constellation_sdk import MetagraphClient

# Connect to a specific metagraph
client = MetagraphClient(metagraph_id="your_metagraph_id")

# Get metagraph token balance
balance = client.get_balance("DAG123YourAddress...")
print(f"Token balance: {balance}")
```

## ⚙️ Configuration

### Environment Variables
```bash
# Set default network
export CONSTELLATION_NETWORK=testnet

# Set custom endpoints
export CONSTELLATION_L0_URL=https://custom-l0-url.com
export CONSTELLATION_L1_URL=https://custom-l1-url.com
```

### Programmatic Configuration
```python
from constellation_sdk import get_config, set_config, create_custom_config

# Get current configuration
config = get_config()

# Create custom network configuration
custom_config = create_custom_config(
    be_url="https://custom-be.com",
    l0_url="https://custom-l0.com", 
    l1_url="https://custom-l1.com",
    network_version="2.0"
)

# Update global configuration
config.network = custom_config
set_config(config)
```

## 🔍 Common Use Cases

### 1. Portfolio Tracker
```python
from constellation_sdk import Network

def track_portfolio(addresses):
    network = Network('mainnet')
    total_balance = 0
    
    for address in addresses:
        try:
            balance_info = network.get_balance(address)
            balance = float(balance_info.get('balance', 0))
            total_balance += balance
            print(f"{address[:12]}...: {balance:.2f} DAG")
        except Exception as e:
            print(f"Error fetching {address}: {e}")
    
    print(f"\nTotal Portfolio: {total_balance:.2f} DAG")

# Usage
my_addresses = ["DAG123...", "DAG456...", "DAG789..."]
track_portfolio(my_addresses)
```

### 2. Automated Transaction Monitoring
```python
import time
from constellation_sdk import Network

def monitor_account(address, interval=30):
    network = Network('mainnet')
    last_ordinal = 0
    
    print(f"📊 Monitoring {address[:12]}... for new transactions")
    
    while True:
        try:
            balance_info = network.get_balance(address)
            current_ordinal = balance_info.get('ordinal', 0)
            
            if current_ordinal > last_ordinal:
                print(f"🔄 New transaction detected! Ordinal: {current_ordinal}")
                print(f"💰 Current balance: {balance_info.get('balance', 'N/A')} DAG")
                last_ordinal = current_ordinal
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("👋 Monitoring stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(interval)

# Usage
monitor_account("DAG123YourAddress...")
```

### 3. Batch Balance Checker
```python
import asyncio
from constellation_sdk import get_multiple_balances_concurrent

async def check_multiple_balances():
    addresses = [
        "DAG123Address1...",
        "DAG456Address2...", 
        "DAG789Address3..."
    ]
    
    balances = await get_multiple_balances_concurrent(addresses)
    
    for address, balance_info in balances.items():
        print(f"{address[:12]}...: {balance_info.get('balance', 'Error')} DAG")

# Run
asyncio.run(check_multiple_balances())
```

## 🐛 Troubleshooting

### Common Issues

**1. Import Error with Async Components**
```python
from constellation_sdk import ASYNC_AVAILABLE

if not ASYNC_AVAILABLE:
    print("Install aiohttp for async support: pip install aiohttp")
```

**2. Network Connection Issues**
```python
# Test network connectivity
from constellation_sdk import Network

try:
    network = Network('testnet')
    info = network.get_node_info()
    print("✅ Network connection successful")
except Exception as e:
    print(f"❌ Network error: {e}")
    print("Try switching networks or checking internet connection")
```

**3. CLI Installation Issues**
```bash
# Reinstall with force
pip uninstall constellation-sdk
pip install constellation-sdk --force-reinstall

# Verify installation
constellation --help
```

### Debug Mode
```python
from constellation_sdk import configure_logging

# Enable debug logging
configure_logging(level="DEBUG", enable_console=True)

# Now all operations will show detailed logs
```

### Performance Tuning
```python
from constellation_sdk import get_config, set_config

config = get_config()

# Increase timeouts for slow networks
config.network.timeout = 60
config.network.max_retries = 5

# Enable caching for better performance
config.cache.enable_caching = True
config.cache.cache_ttl = 300  # 5 minutes

set_config(config)
```

## 📚 Next Steps

- **Full Documentation**: Check [README.md](README.md) for complete API reference
- **Examples**: Explore the [examples/](examples/) directory for more use cases
- **Metagraph Guide**: See [README_METAGRAPH.md](README_METAGRAPH.md) for metagraph development
- **CLI Reference**: Run `constellation --help` for complete CLI documentation

## 🆘 Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/constellation-network/python-sdk/issues)
- **Documentation**: [Official Constellation docs](https://docs.constellationnetwork.io/)
- **Community**: Join the Constellation Network community channels

---

**Happy coding! 🌟**

> This SDK provides production-ready tools for building on the Constellation Network. Always test on testnet before mainnet deployment. 