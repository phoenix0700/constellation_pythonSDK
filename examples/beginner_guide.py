#!/usr/bin/env python3
"""
Constellation Python SDK - Complete Beginner's Guide
===================================================

This example walks you through everything you need to know to start building
with the Constellation Python SDK, from basic setup to advanced features.

Perfect for developers new to Constellation or blockchain development.
"""

from constellation_sdk import (
    Account, 
    Network, 
    Transactions, 
    MetagraphClient, 
    discover_production_metagraphs
)


def step_1_create_accounts():
    """Step 1: Create and manage accounts"""
    print("🔐 STEP 1: Account Management")
    print("=" * 40)
    
    # Create a new account (generates random private key)
    alice = Account()
    print(f"✅ Created Alice's account:")
    print(f"   Address: {alice.address}")
    print(f"   Private Key: {alice.private_key_hex[:20]}...{alice.private_key_hex[-10:]}")
    
    # Create another account
    bob = Account()
    print(f"✅ Created Bob's account:")
    print(f"   Address: {bob.address}")
    
    # 💡 Pro tip: Save private keys securely!
    print("\n💡 Important: Save your private keys securely!")
    print("   - Never share them publicly")
    print("   - Store them in environment variables or secure vaults")
    print("   - You can recreate accounts from private keys")
    
    return alice, bob


def step_2_connect_to_network():
    """Step 2: Connect to Constellation networks"""
    print("\n🌐 STEP 2: Network Connection")
    print("=" * 40)
    
    # Connect to TestNet (best for learning)
    testnet = Network('testnet')
    print(f"✅ Connected to TestNet")
    
    # Get network information
    node_info = testnet.get_node_info()
    cluster_info = testnet.get_cluster_info()
    
    print(f"   Network Version: {node_info.get('version', 'Unknown')}")
    print(f"   Active Nodes: {len(cluster_info)}")
    print(f"   Node State: {node_info.get('state', 'Unknown')}")
    
    # 💡 Network options
    print("\n💡 Available Networks:")
    print("   - 'testnet': For development and learning (FREE tokens)")
    print("   - 'mainnet': Production network (REAL tokens)")
    print("   - 'integrationnet': Internal testing")
    
    return testnet


def step_3_check_balances(network, alice, bob):
    """Step 3: Check account balances"""
    print("\n💰 STEP 3: Balance Checking")
    print("=" * 40)
    
    # Check Alice's balance
    alice_balance = network.get_balance(alice.address)
    print(f"✅ Alice's balance: {alice_balance / 1e8:.8f} DAG")
    
    # Check Bob's balance
    bob_balance = network.get_balance(bob.address)
    print(f"✅ Bob's balance: {bob_balance / 1e8:.8f} DAG")
    
    # 💡 Understanding DAG units
    print("\n💡 Understanding DAG Units:")
    print("   - 1 DAG = 100,000,000 Datolites (smallest unit)")
    print("   - SDK returns balances in Datolites")
    print("   - Divide by 1e8 to get DAG amount")
    
    if alice_balance == 0:
        print("\n🚰 Need TestNet tokens? Visit the TestNet faucet!")
        print("   - Join Constellation Discord")
        print("   - Ask for TestNet tokens in #testnet-faucet")
        print("   - Provide your address: " + alice.address)


def step_4_create_transactions(network, alice, bob):
    """Step 4: Create and sign transactions"""
    print("\n📝 STEP 4: Transaction Creation")
    print("=" * 40)
    
    # Create a DAG transfer transaction
    print("Creating DAG transfer transaction...")
    
    # Step 4a: Create transaction data
    transaction_data = Transactions.create_dag_transfer(
        source=alice.address,
        destination=bob.address,
        amount=100000000,  # 1 DAG in Datolites
        fee=0  # Constellation is feeless!
    )
    print(f"✅ Transaction data created")
    print(f"   Amount: {transaction_data['amount'] / 1e8} DAG")
    print(f"   Fee: {transaction_data['fee']} DAG (feeless!)")
    
    # Step 4b: Sign the transaction
    signed_tx = alice.sign_transaction(transaction_data)
    print(f"✅ Transaction signed")
    print(f"   Structure: {list(signed_tx.keys())}")
    
    # 💡 Clean Architecture
    print("\n💡 Clean Architecture:")
    print("   - Transactions class: Creates transaction data")
    print("   - Account class: Signs transactions")
    print("   - Network class: Submits transactions")
    print("   - Clear separation of concerns!")
    
    return signed_tx


def step_5_metagraph_operations():
    """Step 5: Work with metagraphs (custom blockchains)"""
    print("\n🏛️ STEP 5: Metagraph Operations")
    print("=" * 40)
    
    # Discover production metagraphs
    print("Discovering production metagraphs...")
    metagraphs = discover_production_metagraphs('mainnet')
    print(f"✅ Found {len(metagraphs)} production metagraphs")
    
    if metagraphs:
        # Work with the first metagraph
        metagraph_id = metagraphs[0]['id']
        print(f"   Working with: {metagraph_id[:30]}...")
        
        # Create metagraph client
        client = MetagraphClient('mainnet')
        
        # Create a token transaction
        alice = Account()  # New account for demo
        bob = Account()
        
        token_tx = Transactions.create_token_transfer(
            source=alice.address,
            destination=bob.address,
            amount=1000000000,  # 10 tokens (8 decimals)
            metagraph_id=metagraph_id
        )
        print(f"✅ Token transaction created")
        
        # Create a data transaction
        data_tx = Transactions.create_data_submission(
            source=alice.address,
            data={
                'sensor_type': 'temperature',
                'value': 25.7,
                'location': 'warehouse_a',
                'timestamp': '2024-01-15T10:30:00Z'
            },
            metagraph_id=metagraph_id
        )
        print(f"✅ Data transaction created")
        
        # 💡 Metagraph possibilities
        print("\n💡 What can you build with metagraphs?")
        print("   - Custom tokens and DeFi applications")
        print("   - IoT sensor data verification")
        print("   - Supply chain tracking")
        print("   - Gaming economies")
        print("   - Social media platforms")
        print("   - Any custom blockchain application!")
    else:
        print("   No production metagraphs found (normal for new networks)")


def step_6_advanced_features():
    """Step 6: Advanced features"""
    print("\n🚀 STEP 6: Advanced Features")
    print("=" * 40)
    
    # Transaction simulation
    print("🔮 Transaction Simulation:")
    print("   - Validate transactions before submitting")
    print("   - Save TestNet tokens")
    print("   - Prevent failed transactions")
    
    # CLI tools
    print("\n⚙️ CLI Tools:")
    print("   - constellation --help")
    print("   - constellation account create")
    print("   - constellation balance <address>")
    print("   - constellation send <amount> <address>")
    
    # Async operations
    print("\n⚡ Async Operations:")
    print("   - High-performance concurrent requests")
    print("   - Batch balance checking")
    print("   - Real-time streaming")
    
    # Real-time streaming
    print("\n📡 Real-time Streaming:")
    print("   - Monitor live transactions")
    print("   - Track balance changes")
    print("   - WebSocket connections")


def step_7_next_steps():
    """Step 7: What to do next"""
    print("\n🎯 STEP 7: Next Steps")
    print("=" * 40)
    
    print("🎓 Learning Resources:")
    print("   1. README.md - Complete SDK documentation")
    print("   2. README_METAGRAPH.md - Metagraph guide")
    print("   3. QUICK_START.md - Quick reference")
    print("   4. examples/ directory - More examples")
    
    print("\n🛠️ Practice Projects:")
    print("   1. Build a simple wallet application")
    print("   2. Create a balance tracker")
    print("   3. Build a transaction monitor")
    print("   4. Create a custom metagraph application")
    
    print("\n🌍 Community:")
    print("   - Constellation Discord: Get help and TestNet tokens")
    print("   - GitHub: Contribute to the SDK")
    print("   - Documentation: https://docs.constellationnetwork.io/")
    
    print("\n💡 Pro Tips:")
    print("   - Start with TestNet for learning")
    print("   - Use transaction simulation")
    print("   - Join the Discord community")
    print("   - Explore the examples directory")


def main():
    """Complete beginner's walkthrough"""
    print("🌟 CONSTELLATION PYTHON SDK - BEGINNER'S GUIDE")
    print("=" * 60)
    print("Welcome to Constellation Network! Let's build something amazing.\n")
    
    try:
        # Step 1: Create accounts
        alice, bob = step_1_create_accounts()
        
        # Step 2: Connect to network
        network = step_2_connect_to_network()
        
        # Step 3: Check balances
        step_3_check_balances(network, alice, bob)
        
        # Step 4: Create transactions
        signed_tx = step_4_create_transactions(network, alice, bob)
        
        # Step 5: Metagraph operations
        step_5_metagraph_operations()
        
        # Step 6: Advanced features
        step_6_advanced_features()
        
        # Step 7: Next steps
        step_7_next_steps()
        
        print("\n🎉 CONGRATULATIONS!")
        print("You've completed the beginner's guide to Constellation Python SDK!")
        print("You're now ready to build amazing applications on Constellation Network!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Don't worry! This is part of learning.")
        print("Check the error message and try again.")
        print("Join the Discord community for help!")


if __name__ == "__main__":
    main() 