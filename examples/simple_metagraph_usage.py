"""
Simple Metagraph Usage Example
============================

A beginner-friendly example showing basic metagraph operations
with the Constellation Python SDK using the new centralized architecture.
"""

from constellation_sdk import Account, MetagraphClient, Transactions, discover_production_metagraphs

def simple_metagraph_example():
    """Simple example showing core metagraph functionality."""
    
    print("🏛️  Simple Metagraph Example")
    print("=" * 30)
    
    # 1. Create accounts
    print("1. Creating accounts...")
    alice = Account()
    bob = Account()
    print(f"   Alice: {alice.address[:30]}...")
    print(f"   Bob: {bob.address[:30]}...")
    
    # 2. Connect to MainNet (production network)
    print("\n2. Connecting to MainNet...")
    client = MetagraphClient('mainnet')
    
    # 3. Discover production metagraphs
    print("\n3. Finding production metagraphs...")
    metagraphs = discover_production_metagraphs('mainnet')
    print(f"   Found {len(metagraphs)} production metagraphs")
    
    if metagraphs:
        # 4. Work with first metagraph
        metagraph_id = metagraphs[0]['id']
        print(f"\n4. Working with: {metagraph_id[:25]}...")
        
        # 5. Check balance
        print("\n5. Checking Alice's balance...")
        balance = client.get_balance(metagraph_id, alice.address)
        print(f"   Alice's balance: {balance} DAG")
        
        # 6. Create a token transaction (New Architecture)
        print("\n6. Creating token transaction with Transactions class...")
        token_tx = Transactions.create_token_transfer(
            sender=alice,           # sender account
            destination=bob.address, # recipient address  
            amount=1000000000,      # 10 tokens (assuming 8 decimals)
            metagraph_id=metagraph_id
        )
        print(f"   ✅ Token transaction created and signed")
        print(f"   Transaction type: {list(token_tx.keys())}")
        print(f"   🎯 Clean API: Transactions.create_token_transfer()")
        
        # 7. Create a data transaction (New Architecture)
        print("\n7. Creating data transaction with Transactions class...")
        data_tx = Transactions.create_data_submission(
            sender=alice,
            data={
                'message': 'Hello Constellation!',
                'timestamp': '2024-01-15T10:30:00Z',
                'app': 'simple_example'
            },
            metagraph_id=metagraph_id
        )
        print(f"   ✅ Data transaction created and signed")
        print(f"   Data keys: {list(data_tx['value']['data'].keys())}")
        print(f"   🎯 Clean API: Transactions.create_data_submission()")
        
        print(f"\n🎉 Simple metagraph operations completed!")
        print(f"💡 Tip: Use example_usage.py for more advanced features")
        
    else:
        print("   ℹ️  No production metagraphs available for demo")

if __name__ == "__main__":
    simple_metagraph_example() 