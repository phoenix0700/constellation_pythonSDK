#!/usr/bin/env python3
"""
Constellation Python SDK - Mainnet Usage Examples
==================================================

Complete examples showing how to use the Constellation Python SDK on mainnet
for real-world applications including DeFi, IoT, supply chain, and more.

This script demonstrates:
1. Mainnet network operations
2. Metagraph discovery and analysis  
3. Token transactions on mainnet metagraphs
4. Data submissions for various use cases
5. Balance queries and state management
"""

from constellation_sdk import (
    Account,
    MetagraphClient, 
    Network,
    Transactions,
    discover_production_metagraphs,
    get_realistic_metagraph_summary
)


def mainnet_network_operations():
    """Demonstrate basic mainnet network operations."""
    print("🌐 MAINNET NETWORK OPERATIONS")
    print("=" * 35)
    
    # Connect to mainnet
    mainnet = Network('mainnet')
    
    # Get network information
    node_info = mainnet.get_node_info()
    print(f"✅ Connected to mainnet")
    print(f"   Version: {node_info.get('version', 'Unknown')}")
    
    # Get cluster information
    cluster_info = mainnet.get_cluster_info()
    print(f"   Active nodes: {len(cluster_info)}")
    
    # Create accounts
    alice = Account()
    bob = Account()
    
    print(f"✅ Created accounts:")
    print(f"   Alice: {alice.address}")
    print(f"   Bob: {bob.address}")
    
    # Check balances (will be 0 for new accounts)
    alice_balance = mainnet.get_balance(alice.address)
    bob_balance = mainnet.get_balance(bob.address)
    
    print(f"✅ Account balances:")
    print(f"   Alice: {alice_balance / 1e8:.8f} DAG")
    print(f"   Bob: {bob_balance / 1e8:.8f} DAG")
    
    return alice, bob, mainnet


def mainnet_metagraph_discovery():
    """Discover and analyze production metagraphs on mainnet."""
    print(f"\n🔍 MAINNET METAGRAPH DISCOVERY")
    print("=" * 35)
    
    # Get realistic summary across all networks
    summary = get_realistic_metagraph_summary()
    print(f"✅ Network summary:")
    print(f"   Total production metagraphs: {summary['production_total']}")
    print(f"   Total deployments (all): {summary['total_deployments']}")
    
    # Focus on mainnet production metagraphs
    mainnet_mgs = discover_production_metagraphs('mainnet')
    print(f"✅ Mainnet production metagraphs: {len(mainnet_mgs)}")
    
    if mainnet_mgs:
        print("   Top 3 production metagraphs:")
        for i, mg in enumerate(mainnet_mgs[:3]):
            print(f"   {i+1}. {mg['id'][:30]}... (created: {mg['created'][:10]})")
        
        if len(mainnet_mgs) > 3:
            print(f"   ... and {len(mainnet_mgs) - 3} more")
    
    # Analyze metagraph details
    client = MetagraphClient('mainnet')
    active_mgs = client.get_active_metagraphs()
    
    print(f"✅ Activity analysis:")
    print(f"   Active metagraphs: {len(active_mgs)}/{len(mainnet_mgs)}")
    
    return mainnet_mgs, client


def mainnet_token_transactions(alice, bob, metagraphs):
    """Create token transactions on mainnet metagraphs."""
    print(f"\n💰 MAINNET TOKEN TRANSACTIONS")
    print("=" * 35)
    
    if not metagraphs:
        print("❌ No production metagraphs available for token transactions")
        return
    
    # Use first production metagraph
    metagraph_id = metagraphs[0]['id']
    print(f"✅ Using metagraph: {metagraph_id[:30]}...")
    
    print(f"🔥 Creating token transactions:")
    
    # 1. Standard token transfer (10 tokens)
    print("   1. Standard token transfer (10 tokens)")
    token_tx = Transactions.create_token_transfer(
        source=alice.address,
        destination=bob.address,
        amount=1000000000,  # 10 tokens (8 decimals)
        metagraph_id=metagraph_id
    )
    signed_token_tx = alice.sign_metagraph_transaction(token_tx)
    print(f"      ✅ Transaction created and signed")
    
    # 2. Micro-transaction (0.01 tokens)
    print("   2. Micro-transaction (0.01 tokens)")
    micro_tx = Transactions.create_token_transfer(
        source=alice.address,
        destination=bob.address,
        amount=1000000,  # 0.01 tokens
        metagraph_id=metagraph_id
    )
    signed_micro_tx = alice.sign_metagraph_transaction(micro_tx)
    print(f"      ✅ Micro-transaction created")
    
    # 3. Large transaction (100 tokens)
    print("   3. Large transaction (100 tokens)")
    large_tx = Transactions.create_token_transfer(
        source=alice.address,
        destination=bob.address,
        amount=10000000000,  # 100 tokens
        metagraph_id=metagraph_id
    )
    signed_large_tx = alice.sign_metagraph_transaction(large_tx)
    print(f"      ✅ Large transaction created")
    
    print(f"✅ All token transactions created successfully")
    print(f"   Transaction structure: {list(signed_token_tx.keys())}")
    print(f"   Value fields: {list(signed_token_tx['value'].keys())}")
    
    return signed_token_tx, signed_micro_tx, signed_large_tx


def mainnet_data_transactions(alice, metagraphs):
    """Submit data to mainnet metagraphs for various use cases."""
    print(f"\n📊 MAINNET DATA TRANSACTIONS")
    print("=" * 35)
    
    if not metagraphs:
        print("❌ No production metagraphs available for data transactions")
        return
    
    metagraph_id = metagraphs[0]['id']
    print(f"✅ Submitting data to: {metagraph_id[:30]}...")
    
    transactions = []
    
    # 1. IoT sensor data
    print("   1. IoT sensor data")
    iot_tx = Transactions.create_data_submission(
        source=alice.address,
        data={
            "sensor_type": "temperature_humidity",
            "temperature": 22.5,
            "humidity": 65.2,
            "location": "warehouse_mainnet_01",
            "timestamp": "2024-01-15T14:30:00Z",
            "device_id": "IoT_SENSOR_001",
            "battery_level": 87
        },
        metagraph_id=metagraph_id
    )
    signed_iot_tx = alice.sign_metagraph_transaction(iot_tx)
    transactions.append(signed_iot_tx)
    print(f"      ✅ IoT data transaction created")
    
    # 2. Supply chain tracking
    print("   2. Supply chain tracking")
    supply_tx = Transactions.create_data_submission(
        source=alice.address,
        data={
            "product_id": "PROD_MAINNET_456",
            "batch_number": "BATCH_2024_001",
            "origin": "Factory_Berlin",
            "destination": "Warehouse_London",
            "status": "in_transit",
            "carrier": "GlobalLogistics",
            "tracking_number": "GL987654321",
            "estimated_delivery": "2024-01-20T12:00:00Z"
        },
        metagraph_id=metagraph_id
    )
    signed_supply_tx = alice.sign_metagraph_transaction(supply_tx)
    transactions.append(signed_supply_tx)
    print(f"      ✅ Supply chain transaction created")
    
    # 3. DeFi protocol data
    print("   3. DeFi protocol data")
    defi_tx = Transactions.create_data_submission(
        source=alice.address,
        data={
            "protocol": "ConstellationDeFi",
            "action": "liquidity_provision",
            "pool_id": "DAG-USDC-POOL",
            "amount_dag": 1000.0,
            "amount_usdc": 2500.0,
            "lp_tokens_minted": 1581.13,
            "apy": 12.5,
            "transaction_fee": 0.3
        },
        metagraph_id=metagraph_id
    )
    signed_defi_tx = alice.sign_metagraph_transaction(defi_tx)
    transactions.append(signed_defi_tx)
    print(f"      ✅ DeFi protocol transaction created")
    
    # 4. Carbon credits trading
    print("   4. Carbon credits trading")
    carbon_tx = Transactions.create_data_submission(
        source=alice.address,
        data={
            "credit_type": "VCS_Verified",
            "project_id": "VCS_FOREST_001",
            "credits_amount": 50.0,
            "price_per_credit": 15.75,
            "total_value": 787.50,
            "vintage_year": 2023,
            "verification_standard": "Verra_VCS",
            "buyer": "EcoTech_Corp",
            "retirement_purpose": "carbon_neutrality_2024"
        },
        metagraph_id=metagraph_id
    )
    signed_carbon_tx = alice.sign_metagraph_transaction(carbon_tx)
    transactions.append(signed_carbon_tx)
    print(f"      ✅ Carbon credits transaction created")
    
    print(f"✅ All data transactions created successfully")
    print(f"   Total transactions: {len(transactions)}")
    
    return transactions


def mainnet_balance_queries(alice, bob, client, metagraphs):
    """Query balances and metagraph states on mainnet."""
    print(f"\n💳 MAINNET BALANCE QUERIES")
    print("=" * 35)
    
    if not metagraphs:
        print("❌ No production metagraphs available for balance queries")
        return
    
    metagraph_id = metagraphs[0]['id']
    print(f"✅ Checking balances on: {metagraph_id[:30]}...")
    
    # Check token balances
    alice_balance = client.get_balance(alice.address, metagraph_id)
    bob_balance = client.get_balance(bob.address, metagraph_id)
    
    print(f"   Alice token balance: {alice_balance:.8f}")
    print(f"   Bob token balance: {bob_balance:.8f}")
    
    # Get metagraph information
    mg_info = client.get_metagraph_info(metagraph_id)
    print(f"✅ Metagraph information:")
    print(f"   Metagraph balance: {mg_info['balance']} DAG")
    print(f"   Transaction count: {mg_info['transaction_count']}")
    print(f"   Is active: {mg_info['is_active']}")
    
    # Network summary
    summary = client.get_network_summary()
    print(f"✅ Network summary:")
    print(f"   Network: {summary['network']}")
    print(f"   Production metagraphs: {summary['production_count']}")
    print(f"   Test deployments: {summary['test_deployments']}")


def mainnet_advanced_features():
    """Demonstrate advanced mainnet features."""
    print(f"\n⚡ ADVANCED MAINNET FEATURES")
    print("=" * 35)
    
    # Multi-network comparison
    print("🔄 Multi-network comparison:")
    networks = ['mainnet', 'testnet', 'integrationnet']
    
    for network in networks:
        client = MetagraphClient(network)
        production_mgs = client.discover_production_metagraphs()
        all_mgs = client.discover_metagraphs(include_test_deployments=True)
        
        print(f"   {network.upper()}:")
        print(f"     Production: {len(production_mgs)}")
        print(f"     Total deployments: {len(all_mgs)}")
        print(f"     Test deployments: {len(all_mgs) - len(production_mgs)}")
    
    # Smart filtering demonstration
    print(f"\n🎯 Smart filtering (mainnet vs testnet):")
    mainnet_client = MetagraphClient('mainnet')
    testnet_client = MetagraphClient('testnet')
    
    mainnet_prod = mainnet_client.discover_production_metagraphs()
    testnet_all = testnet_client.discover_metagraphs(include_test_deployments=True)
    testnet_prod = testnet_client.discover_production_metagraphs()
    
    print(f"   Mainnet (production focus): {len(mainnet_prod)} metagraphs")
    print(f"   Testnet (all deployments): {len(testnet_all)} metagraphs")
    print(f"   Testnet (production only): {len(testnet_prod)} metagraphs")
    print(f"   Filtered out: {len(testnet_all) - len(testnet_prod)} test deployments")


def main():
    """Run all mainnet examples."""
    print("🌟 CONSTELLATION PYTHON SDK - MAINNET EXAMPLES")
    print("=" * 55)
    print("Demonstrating real-world usage on Constellation mainnet")
    print("=" * 55)
    
    try:
        # 1. Basic mainnet operations
        alice, bob, mainnet = mainnet_network_operations()
        
        # 2. Metagraph discovery
        metagraphs, client = mainnet_metagraph_discovery()
        
        # 3. Token transactions
        if metagraphs:
            token_txs = mainnet_token_transactions(alice, bob, metagraphs)
            
            # 4. Data transactions
            data_txs = mainnet_data_transactions(alice, metagraphs)
            
            # 5. Balance queries
            mainnet_balance_queries(alice, bob, client, metagraphs)
        
        # 6. Advanced features
        mainnet_advanced_features()
        
        print(f"\n🎉 MAINNET EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 45)
        print("✅ Network operations - Connected to mainnet")
        print("✅ Metagraph discovery - Found production metagraphs")
        print("✅ Token transactions - Created and signed")
        print("✅ Data transactions - Multiple use cases")
        print("✅ Balance queries - Real-time data")
        print("✅ Advanced features - Multi-network operations")
        
        print(f"\n💡 NEXT STEPS:")
        print("- Fund your accounts to submit transactions")
        print("- Build your custom DApp using these patterns")
        print("- Explore specific metagraphs for your use case")
        print("- Use testnet for development and testing")
        
        print(f"\n🚀 Ready for production on Constellation mainnet!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Check your network connection and try again")


if __name__ == "__main__":
    main() 