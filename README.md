# 🏛️ Constellation Network Python SDK

**The complete Python SDK for building applications on the Constellation Network (Hypergraph)**

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/constellation-network/python-sdk)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)

---

## 🚀 What is This?

The **Constellation Python SDK** is your complete toolkit for building on the Constellation Network - a feeless, infinitely scalable, and cross-chain interoperable Web3 infrastructure. This SDK provides everything you need to:

### 🏛️ **Metagraph Applications** (New!)
- **Build custom blockchain apps** with token economies and data storage
- **Create DeFi platforms** with custom tokens and smart contracts
- **Develop IoT networks** with on-chain sensor data verification
- **Build supply chain solutions** with immutable tracking
- **Create social media DApps** with decentralized content verification

### 🔐 **Core Functionality**
- **Create and manage DAG accounts** with secp256k1 cryptography
- **Query balances and network data** across MainNet, TestNet, and IntegrationNet
- **Sign and submit transactions** using the HGTP (Hypergraph Transfer Protocol)
- **Monitor live network activity** and analyze transaction flows
- **Build Web3 applications** on Constellation's DAG-based architecture

**Why Constellation?** Unlike traditional blockchains that slow down as they grow, Constellation's Hypergraph gets **faster** with more users. No gas fees, no congestion, just pure scalability.

## 🌟 **What's New in v1.1.0**

✅ **Complete Metagraph Support** - Build custom blockchain applications  
✅ **Centralized Transaction Architecture** - Clean separation of concerns with unified API  
✅ **Production-First Design** - Smart filtering separates real from test deployments  
✅ **Multi-Network Operations** - Seamless MainNet/TestNet/IntegrationNet support  
✅ **Token & Data Transactions** - Full support for custom tokens and data storage  
✅ **Comprehensive Documentation** - Complete guides and real-world examples

### 🏗️ **New Architecture (v1.1.0)**

The SDK now features a clean, maintainable architecture:

- **`Account`** - Pure key management and transaction signing
- **`Transactions`** - Centralized creation for all transaction types  
- **`MetagraphClient`** - Discovery and queries only
- **`Network`** - Core DAG operations

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your App     │    │  Python SDK      │    │ Constellation   │
│                │    │                  │    │   Network       │
│  ┌───────────┐ │    │ ┌──────────────┐ │    │                 │
│  │ Accounts  │◄┼────┼►│   Account    │ │    │  ┌─────────────┐│
│  │ Balances  │ │    │ │  Management  │ │    │  │  MainNet    ││
│  │Transactions│ │    │ │              │ │    │  │  TestNet    ││
│  └───────────┘ │    │ ├──────────────┤ │    │  │ Integration ││
│                │    │ │   Network    │◄┼────┼─►│   Net       ││
│                │    │ │  Interface   │ │    │  └─────────────┘│
│                │    │ │              │ │    │                 │
└─────────────────┘    │ └──────────────┘ │    └─────────────────┘
                       └──────────────────┘
```

This approach is perfect because:

✅ **Industry Standard**: README.md is what every developer expects  
✅ **GitHub Integration**: Displays automatically on repository homepage  
✅ **Searchable**: Easy to find and index  
✅ **Version Controlled**: Changes tracked with the code  
✅ **Markdown Format**: Universally supported and readable  

The comprehensive documentation is now the main README.md file that will greet users when they visit your repository. This is exactly how major Python projects like `requests`, `flask`, and `django` structure their documentation! 🎯

---

## 📦 Installation

### Requirements
- **Python 3.8+**
- **requests** (HTTP client)
- **cryptography** (secp256k1 & Ed25519)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/constellation-network/python-sdk
cd python-sdk

# Install dependencies
pip install -r requirements.txt

# Install the SDK
pip install -e .
```

### Verify Installation

```python
from constellation_sdk import Account, Network
print("🎉 Constellation SDK ready!")

# Create account and check network
account = Account()
network = Network('testnet')
print(f"Account: {account.address}")
print(f"Network: {network.get_node_info()['version']}")
```

---

## ⚡ Quick Start

### 🏛️ **Metagraph Applications** (New Architecture!)

Build custom blockchain applications with token economies and data storage:

```python
from constellation_sdk import Account, MetagraphClient, Transactions, discover_production_metagraphs

# Create accounts
alice = Account()
bob = Account()

# Connect to MainNet (production network) - Discovery only
client = MetagraphClient('mainnet')

# Discover production metagraphs
metagraphs = discover_production_metagraphs('mainnet')
metagraph_id = metagraphs[0]['id']

# Create custom token transaction (New Architecture)
token_tx = Transactions.create_token_transfer(
    sender=alice,           # sender account
    destination=bob.address, # recipient
    amount=1000000000,      # 10 tokens (8 decimals)
    metagraph_id=metagraph_id
)

# Create data transaction (IoT, supply chain, etc.)
data_tx = Transactions.create_data_submission(
    sender=alice,
    data={
        'sensor_type': 'temperature',
        'value': 25.7,
        'location': 'warehouse_a',
        'timestamp': '2024-01-15T10:30:00Z'
    },
    metagraph_id=metagraph_id
)

print("✅ Custom blockchain transactions created with clean API!")
```

### 🔐 **Traditional DAG Operations**

### 1. Create Your First Account

```python
from constellation_sdk import Account

# Generate new account
alice = Account()
print(f"Address: {alice.address}")
print(f"Private Key: {alice.private_key_hex}")

# Import existing account
bob = Account("your_64_char_private_key_hex")
```

### 2. Connect to Networks

```python
from constellation_sdk import Network

# Connect to different networks
mainnet = Network('mainnet')      # Production network
testnet = Network('testnet')      # Development network  
integrationnet = Network('integrationnet')  # Testing network

# Check network status
print(f"TestNet Version: {testnet.get_node_info()['version']}")
print(f"Active Nodes: {len(testnet.get_cluster_info())}")
```

### 3. Check Balances

```python
# Check account balance (returns Datolites: 1 DAG = 100,000,000 Datolites)
balance = testnet.get_balance(alice.address)
print(f"Balance: {balance / 1e8} DAG")

# Check any address
whale_balance = testnet.get_balance("DAG4J6gixVGKYmcZs9Wmkyrv8ERp39vxtjwbjV5Q")
print(f"Whale Balance: {whale_balance / 1e8} DAG")
```

### 4. Create and Sign Transactions (New Architecture)

```python
from constellation_sdk import Transactions

# Step 1: Create transaction with Transactions class
transaction_data = Transactions.create_dag_transfer(
    sender=alice,
    destination=bob.address,
    amount=100000000,  # 1 DAG in Datolites
    fee=0  # Constellation is feeless!
)

# Step 2: Sign transaction with Account
signed_tx = alice.sign_transaction(transaction_data)
print("✅ Transaction created and signed with clean separation!")

# Step 3: Submit transaction (requires funded address)
try:
    result = testnet.submit_transaction(signed_tx)
    print(f"🎉 Transaction submitted: {result}")
except Exception as e:
    print(f"⚠️ Need funding: {e}")
    
# 💡 Clean Architecture Benefits:
# - Transactions class handles creation
# - Account class handles signing
# - Clear separation of concerns
```

---

## 📖 Documentation

### 🚀 **Getting Started**
- **[Quick Start Guide](QUICK_START.md)** - Get up and running in minutes with practical examples
- **[CLI Tool Documentation](#cli-tool)** - Command-line interface for easy SDK operations
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Advanced patterns, testing, and contribution guidelines

### 📚 **Comprehensive Guides**

- **[Metagraph Documentation](README_METAGRAPH.md)** - Complete guide to building custom blockchain applications
- **Main README** (this file) - Core SDK functionality and DAG operations

### 🎯 **Examples & Demos**

Quick start with examples in the `examples/` directory:

| Example | Best For | What It Shows |
|---------|----------|---------------|
| `simple_metagraph_usage.py` | Beginners | Basic metagraph operations |
| `metagraph_demo.py` | Feature exploration | All metagraph capabilities |
| `basic_usage.py` | Core SDK | Account & network operations |
| `offline_usage.py` | Security | Offline transaction signing |
| `example_usage.py` | Production | Real-world integration patterns |

```bash
# Try the simple metagraph example
python3 examples/simple_metagraph_usage.py

# Explore all metagraph features
python3 examples/metagraph_demo.py

# Test basic SDK functionality
python3 examples/basic_usage.py
```

### 🏗️ **Real-World Applications** (New Architecture)

**DeFi Applications**
```python
# Build custom token economies with clean API
token_tx = Transactions.create_token_transfer(sender, recipient_addr, amount, metagraph_id)
```

**IoT Networks**
```python
# Store sensor data on-chain
data_tx = Transactions.create_data_submission(device, sensor_data, metagraph_id)
```

**Supply Chain Tracking**
```python
# Track products from origin to destination
tracking_tx = Transactions.create_data_submission(shipper, shipment_data, metagraph_id)
```

**Gaming Economies**
```python
# In-game currencies and achievements
game_tx = Transactions.create_token_transfer(player1, player2_addr, tokens, metagraph_id)
```

**Batch Operations**
```python
# Process multiple transactions efficiently
transfers = [{'destination': addr1, 'amount': amt1}, {'destination': addr2, 'amount': amt2}]
batch_txs = Transactions.create_batch_transfer(sender, transfers, 'token')
```

---

## 📚 Complete Feature Guide

### 🔐 Account Management

The `Account` class handles all cryptographic operations using secp256k1 (same as Bitcoin/Ethereum).

```python
from constellation_sdk import Account

# Generate new account
account = Account()

# Account properties
print(f"Address: {account.address}")           # DAG + 35 hex chars
print(f"Private Key: {account.private_key_hex}") # 64 hex chars
print(f"Public Key: {account.public_key_hex}")   # 130 hex chars (uncompressed)

# Import from private key
imported = Account("a1b2c3d4...")

# Sign messages
message = "Hello Constellation!"
signature = account.sign_message(message)
print(f"Signature: {signature}")

# Export for backup
backup = {
    'address': account.address,
    'private_key': account.private_key_hex
}
```

### 🌐 Network Operations

The `Network` class provides access to all Constellation network APIs.

```python
from constellation_sdk import Network, NetworkConfig

# Built-in networks
network = Network('testnet')  # or 'mainnet', 'integrationnet'

# Custom network configuration
custom_config = NetworkConfig(
    name="MyNode",
    l0_url="http://my-node:9000",
    l1_url="http://my-node:9010", 
    be_url="https://my-explorer.com"
)
custom_network = Network(custom_config)

# Network information
node_info = network.get_node_info()
print(f"Version: {node_info['version']}")
print(f"Node ID: {node_info.get('id', 'unknown')}")

# Cluster discovery
cluster = network.get_cluster_info()
print(f"Total Nodes: {len(cluster)}")
ready_nodes = [n for n in cluster if n.get('state') == 'Ready']
print(f"Ready Nodes: {len(ready_nodes)}")
```

### 💰 Balance and Address Operations

```python
# Balance checking
balance = network.get_balance("DAG...")
dag_amount = balance / 1e8  # Convert to DAG

# Batch balance checking
addresses = ["DAG1...", "DAG2...", "DAG3..."]
balances = {}
for addr in addresses:
    balances[addr] = network.get_balance(addr) / 1e8

# Address validation
valid_addr = "DAG4J6gixVGKYmcZs9Wmkyrv8ERp39vxtjwbjV5Q"
invalid_addr = "INVALID_ADDRESS"

print(f"Valid: {network.validate_address(valid_addr)}")     # True
print(f"Invalid: {network.validate_address(invalid_addr)}") # False

# Zero balance vs non-existent address (both return 0)
new_account_balance = network.get_balance(Account().address)  # 0
```

### 📝 Transaction Operations

#### Transaction Structure

Constellation transactions use a DAG structure where each transaction references a parent transaction:

```python
transaction_structure = {
    'value': {
        'source': 'DAG...',      # Sender address
        'destination': 'DAG...', # Recipient address  
        'amount': 100000000,     # Amount in Datolites
        'fee': 0,                # Always 0 (feeless)
        'salt': 1234567890,      # Random number for uniqueness
        'parent': {              # Reference to last transaction
            'hash': '...',       # Previous transaction hash
            'ordinal': 5         # Previous transaction order
        }
    },
    'proofs': [{
        'id': '04...',          # Public key (130 hex chars)
        'signature': '30...'    # DER-encoded signature
    }]
}
```

#### Creating Transactions

```python
# Simple transaction (Genesis - first from address)
tx = account.create_transaction({
    'destination': 'DAG3Q4LkJWcdw12nzTRE5hpAZgQiAWQSFYFYUJVw',
    'amount': 100000000,  # 1 DAG
    'fee': 0
})

# Transaction with parent reference (subsequent transactions)
tx_with_parent = account.create_transaction({
    'destination': 'DAG...',
    'amount': 50000000,   # 0.5 DAG
    'fee': 0,
    'parent': {
        'hash': 'previous_transaction_hash',
        'ordinal': 5
    }
})

# Custom salt for unique hashing
tx_custom = account.create_transaction({
    'destination': 'DAG...',
    'amount': 25000000,
    'salt': 9876543210,  # Custom random number
    'fee': 0
})
```

#### Signing and Submitting

```python
# Sign transaction
signed_tx = account.sign_transaction(tx)

# Submit to network (requires funded address)
try:
    result = network.submit_transaction(signed_tx)
    print(f"Success: {result}")
except NetworkError as e:
    if "balance" in str(e).lower():
        print("⚠️ Address needs funding")
    else:
        print(f"Error: {e}")
```

### 📊 Network Monitoring

```python
# Get recent transactions
recent_txs = network.get_recent_transactions(limit=10)

for tx in recent_txs:
    amount_dag = tx['amount'] / 1e8
    print(f"{tx['source'][:15]}... -> {tx['destination'][:15]}... ({amount_dag} DAG)")
    print(f"  Hash: {tx['hash']}")
    print(f"  Ordinal: {tx['ordinal']}")
    print(f"  Parent: {tx['parent']['hash'][:15]}...")

# Monitor specific address activity
def monitor_address(address, network, poll_interval=30):
    """Monitor address for incoming transactions."""
    last_balance = network.get_balance(address)
    
    while True:
        current_balance = network.get_balance(address)
        if current_balance != last_balance:
            change = (current_balance - last_balance) / 1e8
            print(f"💰 Balance changed: {change:+.8f} DAG")
            last_balance = current_balance
        
        time.sleep(poll_interval)

# Usage
# monitor_address(alice.address, testnet)
```

---

## 🎯 Real-World Examples

### Portfolio Tracker

```python
from constellation_sdk import Account, Network
import json

class ConstellationPortfolio:
    def __init__(self, network_name='testnet'):
        self.network = Network(network_name)
        self.accounts = []
    
    def add_account(self, private_key_hex=None):
        """Add account to portfolio."""
        account = Account(private_key_hex) if private_key_hex else Account()
        self.accounts.append(account)
        return account
    
    def get_total_balance(self):
        """Get total portfolio balance."""
        total = 0
        for account in self.accounts:
            balance = self.network.get_balance(account.address)
            total += balance
        return total / 1e8  # Return in DAG
    
    def get_account_balances(self):
        """Get individual account balances."""
        balances = {}
        for account in self.accounts:
            balance = self.network.get_balance(account.address)
            balances[account.address] = balance / 1e8
        return balances
    
    def export_backup(self, filename):
        """Export portfolio backup."""
        backup = {
            'network': self.network.config.name,
            'accounts': [
                {
                    'address': acc.address,
                    'private_key': acc.private_key_hex
                }
                for acc in self.accounts
            ]
        }
        with open(filename, 'w') as f:
            json.dump(backup, f, indent=2)

# Usage
portfolio = ConstellationPortfolio('testnet')
portfolio.add_account()  # Generate new
portfolio.add_account("existing_private_key")  # Import existing

print(f"Total Portfolio: {portfolio.get_total_balance()} DAG")
portfolio.export_backup('my_constellation_portfolio.json')
```

### Transaction Batcher

```python
class TransactionBatcher:
    def __init__(self, account, network):
        self.account = account
        self.network = network
        self.pending_transactions = []
    
    def add_payment(self, recipient, amount_dag):
        """Add payment to batch."""
        tx = self.account.create_transaction({
            'destination': recipient,
            'amount': int(amount_dag * 1e8),  # Convert to Datolites
            'fee': 0
        })
        signed_tx = self.account.sign_transaction(tx)
        self.pending_transactions.append(signed_tx)
    
    def submit_batch(self):
        """Submit all pending transactions."""
        results = []
        for tx in self.pending_transactions:
            try:
                result = self.network.submit_transaction(tx)
                results.append({'status': 'success', 'result': result})
            except Exception as e:
                results.append({'status': 'error', 'error': str(e)})
        
        self.pending_transactions.clear()
        return results

# Usage
sender = Account("your_private_key")
network = Network('testnet')
batcher = TransactionBatcher(sender, network)

# Add multiple payments
recipients = [
    ("DAG3Q4LkJWcdw12nzTRE5hpAZgQiAWQSFYFYUJVw", 1.5),
    ("DAG5FM1vv9PWaoVx6n1mBRwuU7Lg5QpwxLS3KJtT", 0.5),
    ("DAG45ZLcgmQeRHY3oV2ZJACrFUjEZwqeXKSfZc75", 2.0)
]

for recipient, amount in recipients:
    batcher.add_payment(recipient, amount)

# Submit all at once
results = batcher.submit_batch()
```

### Live Network Analytics

```python
class NetworkAnalytics:
    def __init__(self, network_name='testnet'):
        self.network = Network(network_name)
    
    def get_network_stats(self):
        """Get comprehensive network statistics."""
        cluster = self.network.get_cluster_info()
        node_info = self.network.get_node_info()
        recent_txs = self.network.get_recent_transactions(100)
        
        # Calculate statistics
        total_nodes = len(cluster)
        ready_nodes = len([n for n in cluster if n.get('state') == 'Ready'])
        
        if recent_txs:
            total_volume = sum(tx['amount'] for tx in recent_txs) / 1e8
            avg_transaction = total_volume / len(recent_txs)
            unique_addresses = len(set(tx['source'] for tx in recent_txs) | 
                                 set(tx['destination'] for tx in recent_txs))
        else:
            total_volume = avg_transaction = unique_addresses = 0
        
        return {
            'network_version': node_info.get('version', 'unknown'),
            'total_nodes': total_nodes,
            'ready_nodes': ready_nodes,
            'node_health': (ready_nodes / total_nodes * 100) if total_nodes > 0 else 0,
            'recent_transactions': len(recent_txs),
            'total_volume_dag': total_volume,
            'avg_transaction_dag': avg_transaction,
            'unique_addresses': unique_addresses
        }
    
    def print_dashboard(self):
        """Print network dashboard."""
        stats = self.get_network_stats()
        print("🌐 Constellation Network Dashboard")
        print("=" * 40)
        print(f"Network Version: {stats['network_version']}")
        print(f"Node Health: {stats['ready_nodes']}/{stats['total_nodes']} ({stats['node_health']:.1f}%)")
        print(f"Recent Activity: {stats['recent_transactions']} transactions")
        print(f"Volume: {stats['total_volume_dag']:.2f} DAG")
        print(f"Average TX: {stats['avg_transaction_dag']:.4f} DAG")
        print(f"Active Addresses: {stats['unique_addresses']}")

# Usage
analytics = NetworkAnalytics('testnet')
analytics.print_dashboard()
```

---

## 🔧 Advanced Configuration

### Custom Network Setup

```python
from constellation_sdk import NetworkConfig, Network

# Connect to your own node
my_node = NetworkConfig(
    name="MyConstellationNode",
    network_version="3.0",
    be_url="http://localhost:9000",     # Block Explorer
    l0_url="http://localhost:9000",     # L0 (Hypergraph) 
    l1_url="http://localhost:9010",     # L1 (DAG)
)

network = Network(my_node)
```

### Error Handling Best Practices

```python
from constellation_sdk import Account, Network, ConstellationError, NetworkError

def safe_transaction(sender, recipient_address, amount_dag, network):
    """Safely create and submit a transaction with proper error handling."""
    try:
        # Validate inputs
        if not network.validate_address(recipient_address):
            raise ValueError(f"Invalid recipient address: {recipient_address}")
        
        if amount_dag <= 0:
            raise ValueError("Amount must be positive")
        
        # Check sender balance
        balance = network.get_balance(sender.address)
        amount_datolites = int(amount_dag * 1e8)
        
        if balance < amount_datolites:
            raise ValueError(f"Insufficient balance: {balance/1e8} DAG < {amount_dag} DAG")
        
        # Create and submit transaction
        tx = sender.create_transaction({
            'destination': recipient_address,
            'amount': amount_datolites,
            'fee': 0
        })
        
        signed_tx = sender.sign_transaction(tx)
        result = network.submit_transaction(signed_tx)
        
        return {'success': True, 'result': result}
        
    except ConstellationError as e:
        return {'success': False, 'error': f"SDK Error: {e}"}
    except NetworkError as e:
        return {'success': False, 'error': f"Network Error: {e}"}
    except ValueError as e:
        return {'success': False, 'error': f"Validation Error: {e}"}
    except Exception as e:
        return {'success': False, 'error': f"Unexpected Error: {e}"}

# Usage
result = safe_transaction(alice, bob.address, 1.5, testnet)
if result['success']:
    print(f"✅ Transaction successful: {result['result']}")
else:
    print(f"❌ Transaction failed: {result['error']}")
```

---

## 🧪 Testing and Development

### Getting TestNet Funds

To test transaction submission, you need TestNet DAG tokens:

1. **Contact Constellation Community**:
   - Discord: [Constellation Official](https://discord.gg/constellation)
   - Telegram: [@constellationcommunity](https://t.me/constellationcommunity)
   
2. **Request TestNet Funding**:
   ```
   Hi! I'm developing with the Python SDK and need TestNet funds for testing.
   My address: DAG[your_address_here]
   ```

3. **Alternative Networks**:
   ```python
   # Try IntegrationNet (may have different funding mechanisms)
   integrationnet = Network('integrationnet')
   balance = integrationnet.get_balance(your_address)
   ```

### Unit Testing Your Integration

```python
import unittest
from constellation_sdk import Account, Network

class TestConstellationSDK(unittest.TestCase):
    def setUp(self):
        self.account = Account()
        self.network = Network('testnet')
    
    def test_account_creation(self):
        """Test account creation and properties."""
        self.assertTrue(self.account.address.startswith('DAG'))
        self.assertEqual(len(self.account.address), 38)
        self.assertEqual(len(self.account.private_key_hex), 64)
    
    def test_network_connectivity(self):
        """Test network connection and basic queries."""
        node_info = self.network.get_node_info()
        self.assertIn('version', node_info)
        
        cluster = self.network.get_cluster_info()
        self.assertIsInstance(cluster, list)
        self.assertGreater(len(cluster), 0)
    
    def test_balance_query(self):
        """Test balance queries."""
        balance = self.network.get_balance(self.account.address)
        self.assertIsInstance(balance, int)
        self.assertGreaterEqual(balance, 0)
    
    def test_transaction_signing(self):
        """Test transaction creation and signing (New Architecture)."""
        from constellation_sdk import Transactions
        
        tx_data = Transactions.create_dag_transfer(
            sender=self.account,
            destination='DAG3Q4LkJWcdw12nzTRE5hpAZgQiAWQSFYFYUJVw',
            amount=100000000,
            fee=0
        )
        
        signed_tx = self.account.sign_transaction(tx_data)
        self.assertIn('value', signed_tx)
        self.assertIn('proofs', signed_tx)

if __name__ == '__main__':
    unittest.main()
```

---

## 🏗️ Architecture & Migration Guide

### New Centralized Transaction Architecture (v1.1.0)

The SDK has been refactored for better maintainability and consistency:

#### Clean Separation of Concerns

```python
# 🎯 Each class has a clear responsibility:

# Account - Pure key management and signing
account = Account()
signature = account.sign_transaction(tx_data)

# Transactions - Centralized transaction creation
tx_data = Transactions.create_dag_transfer(account, address, amount)
token_tx = Transactions.create_token_transfer(account, address, amount, mg_id)
data_tx = Transactions.create_data_submission(account, data, mg_id)

# MetagraphClient - Discovery and queries only  
client = MetagraphClient('mainnet')
metagraphs = client.discover_production_metagraphs()
balance = client.get_balance(mg_id, address)

# Network - Core DAG operations
network = Network('testnet')
dag_balance = network.get_balance(address)
```

#### Migration Examples

**DAG Transactions**
```python
# ❌ Old Way (still works via convenience functions)
tx = account.create_transaction({'destination': addr, 'amount': amt})
signed_tx = account.sign_transaction(tx)

# ✅ New Way (recommended)
tx_data = Transactions.create_dag_transfer(account, addr, amt)
signed_tx = account.sign_transaction(tx_data)
```

**Metagraph Transactions**
```python
# ❌ Old Way
token_tx = client.create_token_transaction(account, addr, amt, mg_id)
data_tx = client.create_data_transaction(account, data, mg_id)

# ✅ New Way (cleaner and consistent)
token_tx = Transactions.create_token_transfer(account, addr, amt, mg_id)
data_tx = Transactions.create_data_submission(account, data, mg_id)
```

#### Benefits of New Architecture

- **🎯 Consistent API**: Same pattern for all transaction types
- **🧹 Clean Code**: Clear separation of concerns
- **🔧 Maintainable**: Easier to add new transaction types
- **📦 Batch Support**: Unified batch operations
- **🔄 Backward Compatible**: Convenience functions for smooth migration

#### Batch Operations

```python
# Create multiple transactions efficiently
transfers = [
    {'destination': addr1, 'amount': 1000000},
    {'destination': addr2, 'amount': 2000000}
]

# All transaction types support batching
dag_batch = Transactions.create_batch_transfer(account, transfers, 'dag')
token_batch = Transactions.create_batch_transfer(account, transfers, 'token')
data_batch = Transactions.create_batch_transfer(account, transfers, 'data')
```

#### Validation and Error Handling

```python
from constellation_sdk import TransactionError

try:
    # All transaction creation includes validation
    tx_data = Transactions.create_dag_transfer(
        sender=account,
        destination="invalid_address",  # Will fail validation
        amount=100000000
    )
except TransactionError as e:
    print(f"Transaction error: {e}")

# Size estimation and structure validation
size = Transactions.estimate_transaction_size(tx_data)
valid = Transactions.validate_transaction_structure(tx_data)
```

---

## 🖥️ CLI Tool

The Constellation SDK now includes a powerful command-line interface for easy interaction with the network.

### Installation & Setup

```bash
# CLI is automatically available after SDK installation
constellation --help

# Create and save a default account for quick operations
constellation account create --save-key

# View current configuration
constellation config show
```

### Common CLI Commands

```bash
# Account Management
constellation account create                    # Create new account
constellation account create --save-key         # Create and save as default
constellation account info                      # Show default account info
constellation account info DAG123...            # Show specific account info

# Balance Operations  
constellation balance DAG123YourAddress...      # Check specific balance
constellation balance DAG123... --watch         # Watch for balance changes

# Send Transactions
constellation send 10.5 DAG456RecipientAddr...  # Send using default account
constellation send 5.0 DAG789... --from-key your_private_key  # Send with specific key
constellation send 1.0 DAG456... --dry-run      # Test transaction without sending

# Network Information
constellation network info                       # Get network status
constellation network health                     # Check network health

# Metagraph Operations
constellation metagraph discover                 # Find all metagraphs
constellation metagraph discover --production    # Production metagraphs only
constellation metagraph discover --async         # Faster async discovery

# Configuration
constellation config show                        # Show all settings
constellation config set default_network mainnet # Update configuration
constellation config reset                       # Reset to defaults

# Global Options
constellation --network mainnet balance DAG...   # Use specific network
constellation --output json account info         # JSON output format
constellation -v network info                    # Verbose output
```

### CLI Configuration

The CLI stores settings in `~/.constellation/cli-config.json`:

```json
{
  "default_network": "testnet",
  "default_private_key": "your_key_here",
  "output_format": "pretty",
  "async_enabled": true
}
```

### Examples

```bash
# Quick portfolio check
constellation account create --save-key
constellation account info

# Monitor account activity
constellation balance DAG123... --watch

# Send transaction with confirmation
constellation send 10.0 DAG456RecipientAddr... --from-key your_key

# Discover production metagraphs
constellation metagraph discover --production --output json

# Network monitoring
constellation network health
constellation network info --verbose
```

---

## 🚨 Troubleshooting

### Common Issues

**1. "NetworkConfig() argument after ** must be a mapping"**
```python
# ❌ Wrong
network = Network('testnet')  # If config is broken

# ✅ Fix - Check config.py
from constellation_sdk.config import DEFAULT_CONFIGS
print(type(DEFAULT_CONFIGS['testnet']))  # Should be dict or NetworkConfig
```

**2. "Transaction failed - check address balance"**
```python
# ❌ Unfunded address
balance = network.get_balance(account.address)
print(f"Balance: {balance}")  # Will be 0

# ✅ Get TestNet funding first
# Contact Constellation community for TestNet tokens
```

**3. "Invalid private key"**
```python
# ❌ Wrong format
account = Account("invalid_key")

# ✅ Correct format (64 hex characters)
account = Account("a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456")
```

**4. "Network request failed"**
```python
# ❌ Network connectivity issues
try:
    balance = network.get_balance(address)
except NetworkError as e:
    print(f"Network issue: {e}")
    # Check internet connection, try different network
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Your SDK code here - will show detailed network requests
```

---

## 📖 API Reference

### Classes

#### `Account`
```python
Account(private_key_hex: Optional[str] = None)
```
- **Methods**: `sign_message()`, `sign_transaction()`, `sign_metagraph_transaction()`
- **Properties**: `address`, `private_key_hex`, `public_key_hex`
- **Focus**: Pure key management and cryptographic signing

#### `Transactions` ⭐ New!
```python
Transactions  # Static methods only
```
- **Methods**: 
  - `create_dag_transfer()` - DAG token transfers
  - `create_token_transfer()` - Metagraph token transfers
  - `create_data_submission()` - Metagraph data submissions
  - `create_batch_transfer()` - Batch operations
  - `validate_transaction_structure()` - Validation
  - `estimate_transaction_size()` - Size estimation
- **Focus**: Centralized transaction creation for all types

#### `MetagraphClient`
```python
MetagraphClient(network: str = 'mainnet')
```
- **Methods**: `discover_metagraphs()`, `discover_production_metagraphs()`, `get_metagraph_info()`, `get_balance()`, `get_active_metagraphs()`
- **Focus**: Metagraph discovery and queries only

#### `Network`
```python
Network(network_or_config: Union[str, NetworkConfig])
```
- **Methods**: `get_balance()`, `get_node_info()`, `get_cluster_info()`, `get_recent_transactions()`, `submit_transaction()`, `validate_address()`
- **Focus**: Core DAG network operations

#### `NetworkConfig`
```python
NetworkConfig(name: str, network_version: str, be_url: str, l0_url: str, l1_url: str)
```

### Constants

```python
DEFAULT_CONFIGS = {
    'mainnet': NetworkConfig(...),
    'testnet': NetworkConfig(...),
    'integrationnet': NetworkConfig(...)
}
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests**: Ensure your code is tested
5. **Submit a pull request**

### Development Setup

```bash
git clone https://github.com/constellation-network/python-sdk
cd python-sdk
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/

# Run examples
python examples/basic_usage.py
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **Constellation Network**: [https://constellationnetwork.io](https://constellationnetwork.io)
- **Documentation**: [https://docs.constellationnetwork.io](https://docs.constellationnetwork.io)
- **Discord**: [Official Constellation Discord](https://discord.gg/constellation)
- **GitHub**: [Constellation Network](https://github.com/constellation-network)

---

## 🎉 What's Next?

Now that you have the Constellation Python SDK, you're ready to build the next generation of Web3 applications! Here are some ideas:

- **🏦 DeFi Applications**: Build lending, trading, or yield farming platforms
- **🎮 Gaming**: Create blockchain games with instant, feeless transactions  
- **📱 Mobile Apps**: Integrate DAG payments into mobile applications
- **🤖 Trading Bots**: Automate DAG trading strategies
- **📊 Analytics**: Build portfolio trackers and network analyzers
- **🌐 Cross-Chain**: Bridge assets between networks

**Happy building on Constellation! 🚀**

---

*Made with ❤️ by the Constellation Community*