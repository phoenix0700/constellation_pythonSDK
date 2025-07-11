"""
New Architecture Demo - Constellation Python SDK
===============================================

Comprehensive demonstration of the new centralized transaction architecture.

Key Architecture Changes:
- Account: Pure key management and signing
- Transactions: Centralized transaction creation for all types
- MetagraphClient: Discovery and queries only
- Network: Core DAG operations

This creates a clean, maintainable, and consistent API.
"""

from constellation_sdk import (
    Account,
    MetagraphClient,
    Network,
    Transactions,
    discover_production_metagraphs,
)


def demonstrate_new_architecture():
    """Comprehensive demo of the new centralized architecture."""

    print("🏗️  Constellation SDK - New Architecture Demo")
    print("=" * 50)

    # ====================
    # PART 1: ACCOUNT MANAGEMENT (Key-focused)
    # ====================
    print("\n🔐 PART 1: Account Management (Pure Key Focus)")
    print("-" * 40)

    # Create accounts - now purely about keys
    alice = Account()
    bob = Account()

    print(f"Alice: {alice.address}")
    print(f"Bob: {bob.address}")
    print(f"✅ Account class focuses on key management only")

    # ====================
    # PART 2: CENTRALIZED TRANSACTIONS
    # ====================
    print("\n📦 PART 2: Centralized Transaction Creation")
    print("-" * 40)

    print("Creating different transaction types with unified API...\n")

    # 2.1 DAG Token Transfer
    print("2.1 DAG Token Transfer:")
    dag_tx_data = Transactions.create_dag_transfer(
        sender=alice, destination=bob.address, amount=100000000, fee=0  # 1 DAG
    )
    print(f"   📄 Transaction data created: {list(dag_tx_data.keys())}")

    # Sign the transaction
    signed_dag_tx = alice.sign_transaction(dag_tx_data)
    print(f"   🔏 Transaction signed: {list(signed_dag_tx.keys())}")

    # 2.2 Batch DAG Transfers
    print("\n2.2 Batch DAG Transfers:")
    transfers = [
        {"destination": bob.address, "amount": 50000000},  # 0.5 DAG
        {"destination": alice.address, "amount": 25000000},  # 0.25 DAG (self)
    ]

    batch_txs = Transactions.create_batch_transfer(
        sender=alice, transfers=transfers, transaction_type="dag"
    )
    print(f"   📦 Batch created: {len(batch_txs)} transactions")
    print(f"   🎯 Consistent API for single and batch operations")

    # ====================
    # PART 3: METAGRAPH DISCOVERY (Query-focused)
    # ====================
    print("\n🔍 PART 3: Metagraph Discovery (Pure Query Focus)")
    print("-" * 40)

    # Create metagraph client - now only for discovery/queries
    mg_client = MetagraphClient("mainnet")

    print("Discovering production metagraphs...")
    production_metagraphs = mg_client.discover_production_metagraphs()
    print(f"   🏛️  Found {len(production_metagraphs)} production metagraphs")

    if production_metagraphs:
        # Get detailed info about first metagraph
        mg_id = production_metagraphs[0]["id"]
        mg_info = mg_client.get_metagraph_info(mg_id)
        print(f"   📊 Metagraph info: {mg_info.get('balance', 0)} DAG balance")
        print(f"   ✅ MetagraphClient focuses on discovery/queries only")

        # ====================
        # PART 4: METAGRAPH TRANSACTIONS
        # ====================
        print(f"\n🌐 PART 4: Metagraph Transactions (Centralized)")
        print("-" * 40)

        # 4.1 Token Transfer
        print("4.1 Metagraph Token Transfer:")
        token_tx = Transactions.create_token_transfer(
            sender=alice,
            destination=bob.address,
            amount=1000000000,  # 10 tokens
            metagraph_id=mg_id,
        )
        print(f"   💰 Token transfer created and signed")
        print(f"   🎯 Same create pattern as DAG transactions")

        # 4.2 Data Submission
        print("\n4.2 Metagraph Data Submission:")
        data_tx = Transactions.create_data_submission(
            sender=alice,
            data={
                "sensor_type": "temperature",
                "value": 25.7,
                "location": "room_1",
                "app_version": "1.2.3",
            },
            metagraph_id=mg_id,
        )
        print(f"   📊 Data submission created and signed")
        print(f"   🎯 Consistent API across all transaction types")

        # 4.3 Mixed Batch Operations
        print("\n4.3 Mixed Batch Operations:")
        mixed_batch = [
            {"destination": bob.address, "amount": 500000000, "metagraph_id": mg_id},
            {
                "data": {"alert": "temperature_high", "value": 35.2},
                "metagraph_id": mg_id,
            },
        ]

        # Create token transfers
        token_batch = Transactions.create_batch_transfer(
            sender=alice,
            transfers=mixed_batch[:1],  # First item (token)
            transaction_type="token",
        )

        # Create data submissions
        data_batch = Transactions.create_batch_transfer(
            sender=alice,
            transfers=mixed_batch[1:],  # Second item (data)
            transaction_type="data",
        )

        print(f"   📦 Token batch: {len(token_batch)} transactions")
        print(f"   📦 Data batch: {len(data_batch)} transactions")
        print(f"   🎯 Flexible batching for different transaction types")

    # ====================
    # PART 5: NETWORK OPERATIONS
    # ====================
    print(f"\n🌐 PART 5: Network Operations (Unchanged)")
    print("-" * 40)

    network = Network("testnet")
    node_info = network.get_node_info()
    print(f"   🖥️  Network: {node_info.get('version', 'Unknown')}")
    print(f"   ✅ Network class unchanged - focuses on DAG operations")

    # ====================
    # PART 6: ARCHITECTURE BENEFITS
    # ====================
    print(f"\n🎯 PART 6: Architecture Benefits")
    print("-" * 40)

    print("✅ Clean Separation of Concerns:")
    print("   - Account: Keys and signing only")
    print("   - Transactions: All transaction creation")
    print("   - MetagraphClient: Discovery and queries")
    print("   - Network: Core DAG operations")

    print("\n✅ Consistent API:")
    print("   - Same pattern for DAG, token, and data transactions")
    print("   - Unified batch operations")
    print("   - Clear parameter naming")

    print("\n✅ Better Maintainability:")
    print("   - Transaction logic centralized")
    print("   - Easier to add new transaction types")
    print("   - Clear responsibilities per class")

    print("\n✅ Backward Compatibility:")
    print("   - Convenience functions available")
    print("   - Old import patterns still work")
    print("   - Gradual migration path")

    # ====================
    # PART 7: MIGRATION GUIDE
    # ====================
    print(f"\n🔄 PART 7: Migration Examples")
    print("-" * 40)

    print("OLD WAY:")
    print("   # account.create_transaction({'destination': addr, 'amount': amt})")
    print("   # signed_tx = account.sign_transaction(tx_data)")

    print("\nNEW WAY:")
    print("   # tx_data = Transactions.create_dag_transfer(account, addr, amt)")
    print("   # signed_tx = account.sign_transaction(tx_data)")

    print("\nOLD WAY (Metagraphs):")
    print("   # client.create_token_transaction(account, addr, amt, mg_id)")

    print("\nNEW WAY (Metagraphs):")
    print("   # Transactions.create_token_transfer(account, addr, amt, mg_id)")

    print(f"\n🎉 New Architecture Demo Complete!")
    print(f"💡 Use this pattern for all new development")


def demonstrate_convenience_functions():
    """Show backward compatibility with convenience functions."""

    print(f"\n🔄 Convenience Functions (Backward Compatibility)")
    print("-" * 50)

    from constellation_sdk import (
        create_dag_transaction,
        create_metagraph_data_transaction,
        create_metagraph_token_transaction,
    )

    alice = Account()
    bob = Account()

    # These work for backward compatibility
    print("Using convenience functions for smooth migration:")

    dag_tx = create_dag_transaction(alice, bob.address, 100000000)
    print(f"✅ create_dag_transaction() works")

    # Note: These would need a real metagraph ID
    print(f"✅ create_metagraph_token_transaction() available")
    print(f"✅ create_metagraph_data_transaction() available")
    print(f"💡 Convenience functions provide smooth migration path")


if __name__ == "__main__":
    demonstrate_new_architecture()
    demonstrate_convenience_functions()
