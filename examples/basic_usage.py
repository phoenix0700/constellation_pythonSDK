"""
Basic usage examples for Constellation Python SDK.
Demonstrates the new centralized transaction architecture.
"""

from constellation_sdk import Account, Network, Transactions

def main():
    print("🚀 Constellation Python SDK - Basic Usage")
    print("=" * 50)
    
    # 1. Create accounts
    print("\n1. 🔐 Account Management:")
    alice = Account()
    bob = Account()
    
    print(f"   Alice: {alice.address}")
    print(f"   Bob: {bob.address}")
    
    # 2. Connect to network
    print("\n2. 🌐 Network Connection:")
    network = Network('testnet')
    
    # Get network info
    node_info = network.get_node_info()
    print(f"   Network: {node_info.get('version', 'Unknown')}")
    
    # 3. Check balances
    print("\n3. 💰 Balance Checking:")
    alice_balance = network.get_balance(alice.address)
    print(f"   Alice balance: {alice_balance/1e8} DAG")
    
    # 4. Analyze recent transactions
    print("\n4. 📊 Recent Network Activity:")
    transactions = network.get_recent_transactions(5)
    for i, tx in enumerate(transactions, 1):
        amount_dag = tx['amount'] / 1e8
        print(f"   {i}. {tx['source'][:15]}... -> {tx['destination'][:15]}... ({amount_dag:.2f} DAG)")
    
    # 5. Create and sign transaction (demo - needs funding)
    print("\n5. 📝 Transaction Creation (New Architecture):")
    print("   📦 Step 1: Create transaction with Transactions class")
    transaction_data = Transactions.create_dag_transfer(
        sender=alice,
        destination=bob.address,
        amount=100000000,  # 1 DAG in Datolites
        fee=0
    )
    
    print("   🔏 Step 2: Sign transaction with Account")
    signed_tx = alice.sign_transaction(transaction_data)
    print(f"   ✅ Transaction signed successfully")
    print(f"   📋 Structure: {list(signed_tx.keys())}")
    print(f"   🎯 Clean separation: Transactions creates, Account signs")
    
    # Note: To submit, address needs funding
    print(f"\n💡 To submit transactions:")
    print(f"   1. Fund address via TestNet faucet")
    print(f"   2. Use: network.submit_transaction(signed_tx)")
    
    print(f"\n🎉 SDK fully functional! Ready for funded addresses.")

if __name__ == "__main__":
    main() 