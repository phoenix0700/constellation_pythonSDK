"""
Constellation Python SDK - Usage Examples
==========================================

This script demonstrates how to use all the main features of the 
Constellation Python SDK.
"""

from constellation_sdk import (
    Account, Network, 
    MetagraphClient, discover_production_metagraphs, get_realistic_metagraph_summary
)

def main():
    print("🚀 Constellation Python SDK - Usage Examples")
    print("=" * 50)
    
    # 1. Account Management
    print("\n1️⃣  Account Management")
    print("-" * 20)
    
    # Create a new account
    my_account = Account()
    print(f"✅ New account created: {my_account.address}")
    
    # Sign a message
    message = "Hello Constellation!"
    signature = my_account.sign_message(message)
    print(f"✅ Message signed: {len(signature)} character signature")
    
    # 2. Network Operations
    print("\n2️⃣  Network Operations")
    print("-" * 20)
    
    # Connect to TestNet
    network = Network('testnet')
    print(f"✅ Connected to {network.config.name}")
    
    # Check account balance
    balance = network.get_balance(my_account.address)
    print(f"✅ Account balance: {balance} DAG")
    
    # 3. Metagraph Discovery (Realistic Approach)
    print("\n3️⃣  Metagraph Discovery")
    print("-" * 20)
    
    # Get realistic summary across all networks
    summary = get_realistic_metagraph_summary()
    print(f"✅ Real production metagraphs: {summary['production_total']}")
    print(f"✅ Total deployments (includes tests): {summary['total_deployments']}")
    
    # Discover production metagraphs on MainNet
    production_metagraphs = discover_production_metagraphs('mainnet')
    print(f"✅ MainNet production metagraphs: {len(production_metagraphs)}")
    
    # 4. Metagraph Operations (Production Focus)
    print("\n4️⃣  Metagraph Operations")
    print("-" * 20)
    
    # Create metagraph client for MainNet (production)
    mg_client = MetagraphClient('mainnet')
    
    if production_metagraphs:
        # Work with the first production metagraph
        metagraph_id = production_metagraphs[0]['id']
        
        # Get metagraph info
        info = mg_client.get_metagraph_info(metagraph_id)
        print(f"✅ Production metagraph balance: {info['balance']} DAG")
        print(f"✅ Is active: {info.get('is_active', False)}")
        
        # Create a token transaction (example)
        recipient = Account()  # Create recipient account
        token_tx = mg_client.create_token_transaction(
            my_account, 
            recipient.address, 
            1000000000,  # 10 tokens (assuming 8 decimals)
            metagraph_id
        )
        print(f"✅ Token transaction created for production metagraph: {metagraph_id[:25]}...")
        
        # Create a data transaction (example)
        data_tx = mg_client.create_data_transaction(
            my_account,
            {'temperature': 25.5, 'humidity': 60.2, 'timestamp': '2024-01-01T12:00:00Z'},
            metagraph_id
        )
        print(f"✅ Data transaction created for production use")
    else:
        print("ℹ️  No production metagraphs found - this is normal for new networks")
    
    # 5. Transaction Creation
    print("\n5️⃣  DAG Transaction Creation")
    print("-" * 30)
    
    # Create another account for the recipient
    recipient = Account()
    
    # Create transaction data
    transaction_data = {
        'source': my_account.address,
        'destination': recipient.address,
        'amount': 100000000,  # 1 DAG (8 decimals)
        'fee': 0,
        'salt': 12345
    }
    
    # Sign the transaction
    signature = my_account.sign_transaction(transaction_data)
    print(f"✅ DAG transaction signed: {len(signature)} character signature")
    print(f"   Amount: {transaction_data['amount'] / 1e8} DAG")
    
    print("\n🎉 All examples completed successfully!")
    print("\n📚 For more information:")
    print("   - Check the README.md file")
    print("   - Run 'make demo' for interactive examples")
    print("   - Visit the examples/ directory")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have installed the SDK with 'make install'") 