# 🏛️ Constellation Metagraph Python SDK

Complete guide to using metagraphs with the Constellation Python SDK. Build custom blockchain applications with token economies and data storage on the Constellation Network.

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Discovery & Exploration](#discovery--exploration)
- [Token Transactions](#token-transactions)
- [Data Transactions](#data-transactions)
- [Balance & State Queries](#balance--state-queries)
- [Advanced Features](#advanced-features)
- [Real-World Applications](#real-world-applications)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

## 🌟 Overview

Metagraphs are custom blockchain applications on Constellation Network that enable:

- **Custom Token Economies** - Create and manage your own digital currencies
- **Data Storage** - Store structured data on-chain with cryptographic verification  
- **Smart Applications** - Build DeFi, IoT, supply chain, gaming, and enterprise solutions
- **Scalable Infrastructure** - Leverage Constellation's high-throughput DAG architecture

### Production vs Test Deployments

The SDK intelligently filters metagraphs:
- **Production Metagraphs** (~20 total): Real applications with economic value
- **Test Deployments** (~108): Automated testing, node validation, development experiments

**💡 The SDK defaults to MainNet and production metagraphs for real-world applications.**

## 🚀 Quick Start

### Installation

```bash
# Install the SDK
pip install constellation-sdk

# Or install from source
git clone https://github.com/constellation-network/python-sdk
cd python-sdk
make install
```

### Basic Example

```python
from constellation_sdk import Account, MetagraphClient, discover_production_metagraphs

# Create accounts
alice = Account()
bob = Account()

# Connect to MainNet
client = MetagraphClient('mainnet')

# Find production metagraphs
metagraphs = discover_production_metagraphs('mainnet')
metagraph_id = metagraphs[0]['id']

# Create token transaction
token_tx = client.create_token_transaction(
    alice,              # sender
    bob.address,        # recipient
    1000000000,         # amount (10 tokens, 8 decimals)
    metagraph_id
)

# Create data transaction
data_tx = client.create_data_transaction(
    alice,
    {'message': 'Hello Constellation!', 'app': 'my_dapp'},
    metagraph_id
)

print("✅ Transactions created and signed!")
```

## 🔍 Discovery & Exploration

### Discover Production Metagraphs

```python
from constellation_sdk import discover_production_metagraphs, get_realistic_metagraph_summary

# Get realistic summary across all networks
summary = get_realistic_metagraph_summary()
print(f"Production metagraphs: {summary['production_total']}")
print(f"Total deployments: {summary['total_deployments']}")

# Discover production metagraphs by network
mainnet_mgs = discover_production_metagraphs('mainnet')      # 7 production
testnet_mgs = discover_production_metagraphs('testnet')      # 4 production  
integration_mgs = discover_production_metagraphs('integrationnet')  # 9 production

# Each metagraph contains:
for mg in mainnet_mgs[:3]:
    print(f"ID: {mg['id']}")
    print(f"Created: {mg['created']}")
    print(f"Network: {mg['network']}")
```

### Metagraph Information

```python
client = MetagraphClient('mainnet')

# Get detailed metagraph info
info = client.get_metagraph_info(metagraph_id)
print(f"Balance: {info['balance']} DAG")
print(f"Transactions: {info['transaction_count']}")
print(f"Active: {info['is_active']}")

# Find active metagraphs
active_mgs = client.get_active_metagraphs()
print(f"Active metagraphs: {len(active_mgs)}")

# Network summary
summary = client.get_network_summary()
print(f"Network: {summary['network']}")
print(f"Production count: {summary['production_count']}")
```

## 🪙 Token Transactions

Create custom token transactions for DeFi applications, gaming economies, and token-based systems.

### Basic Token Transfer

```python
from constellation_sdk import Account, MetagraphClient

# Setup
sender = Account()
recipient = Account()
client = MetagraphClient('mainnet')
metagraph_id = "DAG7Ghth1WhWK83SB3MtXnnHYZbCsm..."

# Create token transaction
token_tx = client.create_token_transaction(
    sender,
    recipient.address,
    amount=1000000000,      # 10 tokens (8 decimals)
    metagraph_id=metagraph_id,
    fee=0                   # Usually 0 for Constellation
)

# Transaction structure
print("Transaction keys:", list(token_tx.keys()))
# Output: ['value', 'proofs']

print("Value keys:", list(token_tx['value'].keys()))
# Output: ['source', 'destination', 'amount', 'fee', 'salt', 'metagraph_id']

print("Signature length:", len(token_tx['proofs'][0]['signature']))
# Output: 142-144 characters (secp256k1)
```

### Advanced Token Operations

```python
# Micro-transaction (fractional tokens)
micro_tx = client.create_token_transaction(
    sender, recipient.address, 1000000, metagraph_id  # 0.01 tokens
)

# Large transaction
large_tx = client.create_token_transaction(
    sender, recipient.address, 100000000000, metagraph_id  # 1000 tokens
)

# With custom fee
fee_tx = client.create_token_transaction(
    sender, recipient.address, 1000000000, metagraph_id, fee=1000000
)
```

## 📦 Data Transactions

Submit structured data to metagraphs for IoT, supply chain, social media, and enterprise applications.

### IoT Sensor Data

```python
# Temperature sensor data
sensor_tx = client.create_data_transaction(
    account,
    {
        'sensor_type': 'temperature',
        'value': 25.7,
        'unit': 'celsius',
        'location': 'warehouse_a',
        'timestamp': '2024-01-15T10:30:00Z',
        'device_id': 'TEMP_001'
    },
    metagraph_id
)
```

### Supply Chain Tracking

```python
# Product tracking
supply_tx = client.create_data_transaction(
    account,
    {
        'product_id': 'PROD_12345',
        'batch_number': 'B2024001',
        'origin': 'Factory_Shanghai',
        'destination': 'Warehouse_NYC',
        'status': 'in_transit',
        'carrier': 'GlobalShipping',
        'tracking_number': 'GS789456123'
    },
    metagraph_id
)
```

### Financial/Audit Data

```python
# Compliance tracking
audit_tx = client.create_data_transaction(
    account,
    {
        'transaction_id': 'TXN_789',
        'audit_type': 'compliance_check',
        'status': 'verified',
        'auditor': 'AuditFirm_ABC',
        'compliance_score': 95.5,
        'risk_level': 'low'
    },
    metagraph_id
)
```

### Social Media DApp

```python
# Content submission
social_tx = client.create_data_transaction(
    account,
    {
        'app': 'social_media_dapp',
        'action': 'post_content',
        'user_id': 'user_456',
        'content_hash': 'bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi',
        'likes': 0,
        'shares': 0
    },
    metagraph_id
)
```

## 💰 Balance & State Queries

### Account Balances

```python
# Check DAG balance on metagraph
balance = client.get_balance(metagraph_id, account.address)
print(f"Balance: {balance} DAG")

# Check multiple accounts
accounts = [alice.address, bob.address, charlie.address]
for addr in accounts:
    bal = client.get_balance(metagraph_id, addr)
    print(f"{addr[:10]}...: {bal} DAG")
```

### Metagraph State

```python
# Get comprehensive metagraph information
mg_info = client.get_metagraph_info(metagraph_id)

print(f"Metagraph Balance: {mg_info['balance']} DAG")
print(f"Transaction Count: {mg_info['transaction_count']}")
print(f"Is Active: {mg_info['is_active']}")
print(f"Network: {mg_info['network']}")
```

## ⚡ Advanced Features

### Multi-Network Operations

```python
# Work across different networks
networks = ['mainnet', 'testnet', 'integrationnet']

for network in networks:
    client = MetagraphClient(network)
    summary = client.get_network_summary()
    print(f"{network}: {summary['production_count']} production metagraphs")
```

### Smart Filtering

```python
# Compare production vs all deployments
client = MetagraphClient('testnet')

# Production only (recommended)
production_only = client.discover_production_metagraphs()

# All deployments (including test)
all_deployments = client.discover_metagraphs(include_test_deployments=True)

print(f"Production: {len(production_only)}")
print(f"All deployments: {len(all_deployments)}")
print(f"Test deployments filtered: {len(all_deployments) - len(production_only)}")
```

### Activity Detection

```python
# Find metagraphs with actual usage
active_mgs = client.get_active_metagraphs()
all_mgs = client.discover_production_metagraphs()

print(f"Active: {len(active_mgs)}/{len(all_mgs)} metagraphs")

for mg in active_mgs:
    info = client.get_metagraph_info(mg['id'])
    print(f"  {mg['id'][:25]}... - {info['transaction_count']} transactions")
```

## 🏗️ Real-World Applications

### DeFi Application

```python
class DeFiApp:
    def __init__(self, metagraph_id):
        self.client = MetagraphClient('mainnet')
        self.metagraph_id = metagraph_id
    
    def stake_tokens(self, user_account, amount):
        """Stake tokens in DeFi protocol"""
        return self.client.create_data_transaction(
            user_account,
            {
                'action': 'stake',
                'amount': amount,
                'timestamp': datetime.now().isoformat(),
                'protocol': 'defi_staking_v1'
            },
            self.metagraph_id
        )
    
    def calculate_rewards(self, user_address):
        """Calculate staking rewards"""
        # Implementation would query metagraph state
        pass
```

### IoT Data Collection

```python
class IoTNetwork:
    def __init__(self, metagraph_id):
        self.client = MetagraphClient('mainnet')
        self.metagraph_id = metagraph_id
    
    def submit_sensor_data(self, device_account, sensor_data):
        """Submit IoT sensor data to blockchain"""
        return self.client.create_data_transaction(
            device_account,
            {
                'device_type': sensor_data['type'],
                'measurements': sensor_data['data'],
                'location': sensor_data['location'],
                'timestamp': sensor_data['timestamp'],
                'device_signature': sensor_data['signature']
            },
            self.metagraph_id
        )
```

### Gaming Economy

```python
class GameEconomy:
    def __init__(self, metagraph_id):
        self.client = MetagraphClient('mainnet')
        self.metagraph_id = metagraph_id
    
    def transfer_game_tokens(self, player1, player2, amount):
        """Transfer in-game currency between players"""
        return self.client.create_token_transaction(
            player1, player2.address, amount, self.metagraph_id
        )
    
    def record_achievement(self, player_account, achievement):
        """Record player achievement on-chain"""
        return self.client.create_data_transaction(
            player_account,
            {
                'achievement': achievement['name'],
                'score': achievement['score'],
                'timestamp': achievement['timestamp'],
                'game_session': achievement['session_id']
            },
            self.metagraph_id
        )
```

## 📚 API Reference

### MetagraphClient

Main client for metagraph operations.

```python
client = MetagraphClient(network='mainnet', timeout=30)
```

**Parameters:**
- `network`: 'mainnet', 'testnet', or 'integrationnet'
- `timeout`: Request timeout in seconds

### Discovery Functions

```python
# Discover production metagraphs
metagraphs = discover_production_metagraphs(network='mainnet')

# Get realistic summary
summary = get_realistic_metagraph_summary()
```

### Core Methods

```python
# Token transactions
token_tx = client.create_token_transaction(account, to_address, amount, metagraph_id, fee=0)

# Data transactions  
data_tx = client.create_data_transaction(account, data, metagraph_id)

# Balance queries
balance = client.get_balance(metagraph_id, address)

# Metagraph info
info = client.get_metagraph_info(metagraph_id)

# Discovery
metagraphs = client.discover_production_metagraphs()
active_mgs = client.get_active_metagraphs()
summary = client.get_network_summary()
```

### Legacy Functions

```python
# Legacy functions (still supported)
all_metagraphs = discover_all_metagraphs()  # Includes test deployments
old_summary = get_metagraph_summary()       # Original summary format
```

## 🎯 Best Practices

### 1. Network Selection

```python
# ✅ Good: Use MainNet for production
client = MetagraphClient('mainnet')

# ⚠️  Caution: TestNet for development only
client = MetagraphClient('testnet')
```

### 2. Production Focus

```python
# ✅ Good: Focus on production metagraphs
production_mgs = discover_production_metagraphs('mainnet')

# ❌ Avoid: Including test deployments unnecessarily
all_deployments = client.discover_metagraphs(include_test_deployments=True)
```

### 3. Error Handling

```python
from constellation_sdk import MetagraphError

try:
    transaction = client.create_token_transaction(
        account, recipient, amount, metagraph_id
    )
except MetagraphError as e:
    print(f"Metagraph error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 4. Amount Handling

```python
# ✅ Good: Use smallest units (e.g., nano-DAG)
amount = 1000000000  # 10 tokens with 8 decimals

# ✅ Good: Clear decimal handling
tokens = 10.5
amount = int(tokens * 100000000)  # Convert to nano units

# ❌ Avoid: Floating point for precise amounts
amount = 10.5  # Can cause precision issues
```

### 5. Account Security

```python
# ✅ Good: Generate accounts securely
account = Account()  # Uses cryptographically secure random generation

# ✅ Good: Import existing accounts safely
account = Account(private_key_hex="your_private_key")

# ⚠️  Caution: Protect private keys
# Never log, commit, or expose private keys
```

### 6. Data Structure

```python
# ✅ Good: Well-structured data
data = {
    'action': 'transfer',
    'amount': 1000,
    'timestamp': datetime.now().isoformat(),
    'metadata': {
        'app_version': '1.0.0',
        'session_id': 'abc123'
    }
}

# ❌ Avoid: Poorly structured data
data = {'misc': 'random data without structure'}
```

## 🚀 Getting Started

1. **Install the SDK**: `pip install constellation-sdk`
2. **Try simple example**: `python3 examples/simple_metagraph_usage.py`
3. **Explore comprehensive demo**: `python3 examples/metagraph_demo.py`
4. **Build your application**: Use this documentation as reference
5. **Join the community**: Constellation Network Discord/Telegram

## 📞 Support

- **Documentation**: This file and main README.md
- **Examples**: Check `examples/` directory
- **Source Code**: `constellation_sdk/` directory
- **Community**: Constellation Network official channels

---

🏛️ **Built for the Constellation Network** - Enabling the future of decentralized applications with DAG technology. 