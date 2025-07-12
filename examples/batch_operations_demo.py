"""
Batch Operations Demo - Constellation Network Python SDK

This example demonstrates the Enhanced REST Phase 1 batch operations feature,
which allows multiple API operations to be executed efficiently in a single request,
reducing network round trips and improving performance for complex queries.
"""

import asyncio
import json
import time

from constellation_sdk import (
    ASYNC_AVAILABLE,
    Account,
    AsyncNetwork,
    BatchOperation,
    BatchOperationType,
    Network,
    batch_get_balances,
    batch_get_ordinals,
    batch_get_transactions,
    create_batch_operation,
)


def main():
    """Demonstrate batch operations capabilities."""
    print("📦 Batch Operations Demo - Constellation Network Python SDK")
    print("=" * 70)
    print()

    # Create sample accounts
    alice = Account()
    bob = Account()
    charlie = Account()
    dave = Account()

    addresses = [alice.address, bob.address, charlie.address, dave.address]

    print("👥 Sample Addresses:")
    for i, address in enumerate(addresses, 1):
        print(f"   {i}. {address}")
    print()

    # Connect to network
    network = Network("testnet")
    print(f"🌐 Connected to {network.config.name}")
    print()

    # ========================================
    # 1. Basic Batch Operations
    # ========================================

    print("📋 1. Basic Batch Operations")
    print("-" * 40)

    # Create individual batch operations
    operations = [
        create_batch_operation(
            "get_balance", {"address": alice.address}, "alice_balance"
        ),
        create_batch_operation(
            "get_ordinal", {"address": alice.address}, "alice_ordinal"
        ),
        create_batch_operation(
            "get_transactions", {"address": alice.address, "limit": 5}, "alice_txs"
        ),
        create_batch_operation("get_recent_transactions", {"limit": 10}, "recent_txs"),
        create_batch_operation("get_node_info", {}, "node_info"),
    ]

    print(f"🔄 Executing {len(operations)} operations in a single batch...")
    start_time = time.time()

    try:
        response = network.batch_request(operations)
        execution_time = time.time() - start_time

        print(f"✅ Batch completed in {execution_time:.3f}s")
        print(f"📊 Summary:")
        print(f"   Total operations: {response.summary['total_operations']}")
        print(f"   Successful: {response.summary['successful_operations']}")
        print(f"   Failed: {response.summary['failed_operations']}")
        print(f"   Success rate: {response.summary['success_rate']:.1f}%")
        print()

        # Display individual results
        print("📋 Individual Results:")
        alice_balance = response.get_result("alice_balance")
        if alice_balance and alice_balance.success:
            print(f"   💰 Alice balance: {alice_balance.data / 1e8:.8f} DAG")

        alice_ordinal = response.get_result("alice_ordinal")
        if alice_ordinal and alice_ordinal.success:
            print(f"   🔢 Alice ordinal: {alice_ordinal.data}")

        alice_txs = response.get_result("alice_txs")
        if alice_txs and alice_txs.success:
            print(f"   📤 Alice transactions: {len(alice_txs.data)}")

        recent_txs = response.get_result("recent_txs")
        if recent_txs and recent_txs.success:
            print(f"   🌐 Recent network transactions: {len(recent_txs.data)}")

        node_info = response.get_result("node_info")
        if node_info and node_info.success:
            print(f"   🖥️  Node version: {node_info.data.get('version', 'Unknown')}")

    except Exception as e:
        print(f"❌ Batch request failed: {e}")

    print()

    # ========================================
    # 2. Multi-Address Operations
    # ========================================

    print("👥 2. Multi-Address Operations")
    print("-" * 40)

    print(f"🔄 Getting balances for {len(addresses)} addresses...")

    try:
        # Compare individual vs batch performance

        # Individual calls
        start_time = time.time()
        individual_balances = {}
        for address in addresses:
            try:
                individual_balances[address] = network.get_balance(address)
            except Exception:
                individual_balances[address] = 0
        individual_time = time.time() - start_time

        # Batch call
        start_time = time.time()
        batch_balances = network.get_multi_balance(addresses)
        batch_time = time.time() - start_time

        print(f"⏱️  Performance Comparison:")
        print(
            f"   Individual calls: {individual_time:.3f}s ({len(addresses)} requests)"
        )
        print(f"   Batch call: {batch_time:.3f}s (1 request)")
        print(f"   Efficiency gain: {individual_time / batch_time:.1f}x faster")
        print()

        # Display results
        total_balance = sum(batch_balances.values())
        funded_addresses = [addr for addr, bal in batch_balances.items() if bal > 0]

        print(f"💰 Balance Results:")
        print(f"   Total addresses: {len(addresses)}")
        print(f"   Funded addresses: {len(funded_addresses)}")
        print(f"   Total balance: {total_balance / 1e8:.8f} DAG")
        print()

        for i, (address, balance) in enumerate(batch_balances.items(), 1):
            status = "💰" if balance > 0 else "⚪"
            print(f"   {status} Address {i}: {balance / 1e8:.8f} DAG")

    except Exception as e:
        print(f"❌ Multi-address operation failed: {e}")

    print()

    # ========================================
    # 3. Address Overview
    # ========================================

    print("📊 3. Comprehensive Address Overview")
    print("-" * 40)

    print(f"🔄 Getting complete overview for {alice.address[:15]}...")

    try:
        overview = network.get_address_overview(alice.address)

        print(f"✅ Overview completed in {overview['execution_time']:.3f}s")
        print(f"📊 Address Overview:")
        print(f"   Address: {overview['address']}")
        print(f"   Balance: {overview['balance'] / 1e8:.8f} DAG")
        print(f"   Ordinal: {overview['ordinal']}")
        print(f"   Recent transactions: {len(overview['transactions'])}")
        print(f"   Data complete: {'✅' if overview['success'] else '❌'}")

        if overview["transactions"]:
            print(f"   📤 Recent Transactions:")
            for i, tx in enumerate(overview["transactions"][:3], 1):
                amount = tx.get("amount", 0)
                print(
                    f"      {i}. {tx.get('hash', 'N/A')[:16]}... ({amount / 1e8:.8f} DAG)"
                )

    except Exception as e:
        print(f"❌ Address overview failed: {e}")

    print()

    # ========================================
    # 4. Convenience Functions
    # ========================================

    print("🛠️ 4. Convenience Functions")
    print("-" * 40)

    print("🔄 Using convenience functions for common operations...")

    try:
        # Batch balance operations
        balance_operations = batch_get_balances(addresses[:3])
        print(f"   📊 Created {len(balance_operations)} balance operations")

        # Batch transaction operations
        tx_operations = batch_get_transactions(addresses[:2], limit=5)
        print(f"   📤 Created {len(tx_operations)} transaction operations")

        # Batch ordinal operations
        ordinal_operations = batch_get_ordinals(addresses[:3])
        print(f"   🔢 Created {len(ordinal_operations)} ordinal operations")

        # Execute all convenience operations together
        all_operations = balance_operations + tx_operations + ordinal_operations
        response = network.batch_request(all_operations)

        print(f"✅ Executed {len(all_operations)} operations")
        print(f"   Success rate: {response.success_rate():.1f}%")
        print(f"   Execution time: {response.execution_time:.3f}s")

    except Exception as e:
        print(f"❌ Convenience functions failed: {e}")

    print()

    # ========================================
    # 5. Error Handling and Resilience
    # ========================================

    print("🛡️ 5. Error Handling and Resilience")
    print("-" * 40)

    print("🔄 Testing batch operations with mixed success/failure...")

    try:
        # Create operations with some that will likely fail
        mixed_operations = [
            create_batch_operation(
                "get_balance", {"address": alice.address}, "valid_balance"
            ),
            create_batch_operation(
                "get_balance", {"address": "INVALID_ADDRESS"}, "invalid_balance"
            ),
            create_batch_operation(
                "get_ordinal", {"address": bob.address}, "valid_ordinal"
            ),
            create_batch_operation(
                "get_transactions", {"address": "DAG" + "x" * 35}, "invalid_txs"
            ),
        ]

        response = network.batch_request(mixed_operations)

        print(f"📊 Mixed Results:")
        print(f"   Total operations: {len(mixed_operations)}")
        print(f"   Successful: {len(response.get_successful_results())}")
        print(f"   Failed: {len(response.get_failed_results())}")
        print(f"   Success rate: {response.success_rate():.1f}%")
        print()

        print("📋 Operation Details:")
        for result in response.results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.id}: {result.operation.value}")
            if not result.success:
                print(f"      Error: {result.error}")

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

    print()

    # ========================================
    # 6. Async Batch Operations
    # ========================================

    if ASYNC_AVAILABLE:
        print("⚡ 6. Async Batch Operations")
        print("-" * 40)

        async def async_batch_demo():
            """Demonstrate async batch operations."""
            try:
                async_network = AsyncNetwork(network.config)
                await async_network.__aenter__()

                print("🔄 Running async batch operations...")

                operations = [
                    create_batch_operation(
                        "get_balance", {"address": addr}, f"balance_{i}"
                    )
                    for i, addr in enumerate(addresses)
                ]

                start_time = time.time()
                response = await async_network.batch_request(operations)
                async_time = time.time() - start_time

                print(f"⚡ Async batch completed in {async_time:.3f}s")
                print(
                    f"   Concurrent execution: {response.summary.get('concurrent_execution', False)}"
                )
                print(f"   Success rate: {response.success_rate():.1f}%")
                print()

                # Enhanced multi-balance with async
                balances = await async_network.get_multi_balance_enhanced(addresses[:3])
                print(f"💰 Enhanced async balances:")
                for i, (address, balance) in enumerate(balances.items(), 1):
                    print(f"   {i}. {balance / 1e8:.8f} DAG")

                await async_network.__aexit__(None, None, None)

            except Exception as e:
                print(f"❌ Async batch operations failed: {e}")

        # Run async demo
        asyncio.run(async_batch_demo())
    else:
        print("⚠️ 6. Async Batch Operations")
        print("-" * 40)
        print("   Async support not available (install aiohttp)")

    print()

    # ========================================
    # 7. Custom Batch Operations
    # ========================================

    print("🎨 7. Custom Batch Operations")
    print("-" * 40)

    print("🔄 Creating custom batch operations...")

    try:
        # Create a custom batch for portfolio analysis
        portfolio_operations = []

        # Add balance checks for all addresses
        for i, address in enumerate(addresses):
            portfolio_operations.append(
                create_batch_operation(
                    "get_balance", {"address": address}, f"portfolio_balance_{i}"
                )
            )

        # Add transaction history for active addresses
        for i, address in enumerate(addresses[:2]):
            portfolio_operations.append(
                create_batch_operation(
                    "get_transactions",
                    {"address": address, "limit": 10},
                    f"portfolio_txs_{i}",
                )
            )

        # Add network info
        portfolio_operations.append(
            create_batch_operation("get_node_info", {}, "network_status")
        )

        # Execute portfolio analysis
        print(
            f"📊 Executing portfolio analysis ({len(portfolio_operations)} operations)..."
        )
        response = network.batch_request(portfolio_operations)

        print(f"✅ Portfolio analysis completed")
        print(f"   Execution time: {response.execution_time:.3f}s")
        print(f"   Data completeness: {response.success_rate():.1f}%")

        # Analyze results
        total_portfolio_value = 0
        active_addresses = 0
        total_transactions = 0

        for result in response.get_successful_results():
            if "portfolio_balance_" in result.id:
                total_portfolio_value += result.data
                if result.data > 0:
                    active_addresses += 1
            elif "portfolio_txs_" in result.id:
                total_transactions += len(result.data)

        print(f"📈 Portfolio Summary:")
        print(f"   Total value: {total_portfolio_value / 1e8:.8f} DAG")
        print(f"   Active addresses: {active_addresses}/{len(addresses)}")
        print(f"   Total transactions: {total_transactions}")

    except Exception as e:
        print(f"❌ Custom batch operations failed: {e}")

    print()

    # ========================================
    # Summary
    # ========================================

    print("🎉 Batch Operations Demo Completed!")
    print("=" * 70)
    print("💡 Key Benefits Demonstrated:")
    print("  ✅ Reduced network round trips (1 request vs many)")
    print("  ✅ Improved performance for complex queries")
    print("  ✅ Comprehensive error handling and resilience")
    print("  ✅ Flexible operation composition")
    print("  ✅ Both sync and async support")
    print("  ✅ CLI integration for easy scripting")
    print("  ✅ Enhanced REST capabilities")
    print()
    print("🚀 Enhanced REST Phase 1 is production-ready!")
    print("💡 Build efficient applications with batch operations.")


if __name__ == "__main__":
    main()
