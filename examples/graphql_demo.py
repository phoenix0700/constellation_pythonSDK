#!/usr/bin/env python3
"""
Constellation Network GraphQL API Demo

Demonstrates the GraphQL functionality added to the Constellation Python SDK,
including flexible queries, real-time subscriptions, and complex data relationships.

This example shows how to use GraphQL to build sophisticated applications that
require complex data fetching and real-time updates.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List

from constellation_sdk import (
    GRAPHQL_AVAILABLE,
    Account,
)

# GraphQL imports (conditional)
if GRAPHQL_AVAILABLE:
    from constellation_sdk import (
        ConstellationSchema,
        GraphQLClient,
        GraphQLQuery,
        QueryBuilder,
        SubscriptionBuilder,
        build_account_query,
        build_metagraph_query,
        build_network_status_query,
        build_portfolio_query,
        execute_query,
        execute_query_async,
        get_account_portfolio,
        get_metagraph_overview,
        get_network_status,
    )


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🌌 {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n{'─'*40}")
    print(f"✨ {title}")
    print(f"{'─'*40}")


def basic_graphql_demo():
    """Demonstrate basic GraphQL query execution."""
    print_section("Basic GraphQL Demo")

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available. Install optional dependencies:")
        print("   pip install aiohttp websockets")
        return

    # Initialize GraphQL client
    client = GraphQLClient("testnet")
    print(f"📡 Connected to GraphQL endpoint: {client.graphql_endpoint}")

    print_subsection("Network Status Query")

    # Simple network status query
    network_query = """
    query NetworkStatus {
        network {
            status
            nodeCount
            version
            latestBlock {
                hash
                height
                timestamp
            }
            metrics {
                transactionRate
                totalTransactions
                activeAddresses
            }
        }
    }
    """

    try:
        response = client.execute(network_query)

        if response.is_successful:
            print("✅ Network status query executed successfully")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")
            print("\n📊 Network Data:")
            print(json.dumps(response.data, indent=2))
        else:
            print("❌ Network status query failed")
            for error in response.errors:
                print(f"  Error: {error}")

    except Exception as e:
        print(f"❌ Error executing network query: {e}")

    print_subsection("Account Portfolio Query")

    # Create a test account for demonstration
    account = Account()
    print(f"📍 Demo account: {account.address}")

    # Account portfolio query with variables
    account_query = GraphQLQuery(
        query=ConstellationSchema.ACCOUNT_PORTFOLIO,
        variables={"address": account.address},
    )

    try:
        response = client.execute(account_query)

        if response.is_successful:
            print("✅ Account portfolio query executed successfully")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")

            account_data = response.data.get("account", {})
            balance = account_data.get("balance", 0)
            transactions = account_data.get("transactions", [])
            metagraph_balances = account_data.get("metagraphBalances", [])

            print(f"\n💰 Account Balance: {balance / 1e8:.8f} DAG")
            print(f"📜 Recent Transactions: {len(transactions)}")
            print(f"🏛️  Metagraph Balances: {len(metagraph_balances)}")
        else:
            print("❌ Account portfolio query failed")
            for error in response.errors:
                print(f"  Error: {error}")

    except Exception as e:
        print(f"❌ Error executing account query: {e}")

    # Show client statistics
    print_subsection("Client Statistics")
    stats = client.get_stats()
    print(f"📊 Queries executed: {stats['queries_executed']}")
    print(f"📊 Average execution time: {stats['average_execution_time']:.3f}s")
    print(f"📊 Errors encountered: {stats['errors_encountered']}")


def query_builder_demo():
    """Demonstrate the GraphQL query builder."""
    print_section("Query Builder Demo")

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available.")
        return

    print_subsection("Programmatic Query Construction")

    # Create test account
    account = Account()
    addresses = [account.address, Account().address, Account().address]

    print(f"🏗️  Building queries for {len(addresses)} addresses...")

    # Build comprehensive account query
    print("\n1️⃣ Building Account Query:")
    account_query = (
        QueryBuilder()
        .account(addresses[0])
        .with_balance()
        .with_address()
        .with_transactions(limit=10)
        .with_metagraph_balances()
        .build()
    )

    print("Generated Query:")
    print(account_query)

    # Build multi-account portfolio query
    print("\n2️⃣ Building Portfolio Query:")
    portfolio_query = (
        QueryBuilder()
        .accounts(addresses)
        .with_balances()
        .with_transactions(limit=5)
        .build()
    )

    print("Generated Query:")
    print(portfolio_query)

    # Build network status query
    print("\n3️⃣ Building Network Query:")
    network_query = (
        QueryBuilder()
        .network()
        .with_status()
        .with_latest_block()
        .with_metrics()
        .build()
    )

    print("Generated Query:")
    print(network_query)

    # Build metagraph query (hypothetical metagraph ID)
    print("\n4️⃣ Building Metagraph Query:")
    metagraph_id = "DAG7Ghth6FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhQs"
    metagraph_query = (
        QueryBuilder()
        .metagraph(metagraph_id)
        .with_info()
        .with_supply_info()
        .with_holders(limit=20)
        .with_transactions(limit=15)
        .with_validators()
        .build()
    )

    print("Generated Query:")
    print(metagraph_query)

    print_subsection("Execute Built Queries")

    # Execute one of the built queries
    client = GraphQLClient("testnet")

    try:
        print("🔄 Executing network status query...")
        response = client.execute(network_query)

        if response.is_successful:
            print("✅ Network query executed successfully")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")

            network_data = response.data.get("network", {})
            print(f"📊 Network Status: {network_data.get('status', 'Unknown')}")
            print(f"🏢 Node Count: {network_data.get('nodeCount', 'N/A')}")
            print(f"🔧 Version: {network_data.get('version', 'N/A')}")
        else:
            print("❌ Network query failed")
            for error in response.errors:
                print(f"  Error: {error}")

    except Exception as e:
        print(f"❌ Error executing built query: {e}")


def subscription_demo():
    """Demonstrate GraphQL subscriptions."""
    print_section("GraphQL Subscriptions Demo")

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available.")
        return

    print_subsection("Real-time Subscription Building")

    # Create test accounts for monitoring
    addresses = [Account().address, Account().address]
    metagraph_ids = ["DAG7Ghth6FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhQs"]

    print(f"📡 Building subscriptions for {len(addresses)} addresses...")

    # Build transaction subscription
    print("\n1️⃣ Transaction Updates Subscription:")
    tx_subscription = SubscriptionBuilder().transaction_updates(addresses).build()

    print("Generated Subscription:")
    print(tx_subscription)

    # Build balance subscription
    print("\n2️⃣ Balance Updates Subscription:")
    balance_subscription = SubscriptionBuilder().balance_updates(addresses).build()

    print("Generated Subscription:")
    print(balance_subscription)

    # Build metagraph subscription
    print("\n3️⃣ Metagraph Updates Subscription:")
    metagraph_subscription = (
        SubscriptionBuilder().metagraph_updates(metagraph_ids).build()
    )

    print("Generated Subscription:")
    print(metagraph_subscription)

    print_subsection("Subscription Simulation")
    print("💡 In a real application, these subscriptions would provide live updates:")
    print("   • Transaction events as they occur")
    print("   • Balance changes in real-time")
    print("   • Metagraph state updates")
    print("   • Custom event filtering")


async def async_graphql_demo():
    """Demonstrate async GraphQL operations."""
    print_section("Async GraphQL Demo")

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available.")
        return

    print_subsection("Async Query Execution")

    # Multiple accounts for concurrent operations
    accounts = [Account() for _ in range(3)]
    addresses = [acc.address for acc in accounts]

    print(f"🚀 Executing async queries for {len(addresses)} accounts...")

    # Convenience function for async queries
    try:
        print("\n1️⃣ Network Status (Async):")
        network_response = await execute_query_async(
            "testnet", ConstellationSchema.NETWORK_STATUS
        )

        if network_response.is_successful:
            print("✅ Network status retrieved successfully")
            print(f"⏱️  Execution time: {network_response.execution_time:.3f}s")

            network_data = network_response.data.get("network", {})
            print(f"📊 Status: {network_data.get('status', 'Unknown')}")
        else:
            print("❌ Network status query failed")

    except Exception as e:
        print(f"❌ Error in async network query: {e}")

    # Multiple account queries concurrently
    try:
        print("\n2️⃣ Multiple Account Queries (Concurrent):")

        async def get_account_data(address: str) -> Dict[str, Any]:
            return await execute_query_async(
                "testnet", ConstellationSchema.ACCOUNT_PORTFOLIO, {"address": address}
            )

        # Execute multiple queries concurrently
        tasks = [
            get_account_data(addr) for addr in addresses[:2]
        ]  # Limit to 2 for demo
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        print(f"✅ Executed {len(responses)} concurrent queries")

        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"  Account {i+1}: ❌ {response}")
            else:
                if response.is_successful:
                    account_data = response.data.get("account", {})
                    balance = account_data.get("balance", 0)
                    print(f"  Account {i+1}: 💰 {balance / 1e8:.8f} DAG")
                else:
                    print(f"  Account {i+1}: ❌ Query failed")

    except Exception as e:
        print(f"❌ Error in concurrent queries: {e}")

    print_subsection("Async Subscription Simulation")

    # Simulate subscription handling
    client = GraphQLClient("testnet")

    try:
        print("🔄 Starting subscription simulation...")
        subscription_query = ConstellationSchema.TRANSACTION_SUBSCRIPTION

        # Simulate subscription for a short time
        print("📡 Simulating transaction updates for 10 seconds...")

        event_count = 0
        async for response in client.subscribe(
            subscription_query, {"addresses": addresses[:1]}
        ):
            if response.is_successful:
                event_count += 1
                tx_data = response.data.get("transactionUpdates", {})
                print(
                    f"  📝 Event {event_count}: Transaction {tx_data.get('hash', 'N/A')[:12]}..."
                )

                # Limit simulation
                if event_count >= 5:
                    break
            else:
                print(f"  ❌ Subscription error: {response.errors}")
                break

        print(f"✅ Subscription simulation completed ({event_count} events)")

    except Exception as e:
        print(f"❌ Error in subscription simulation: {e}")

    finally:
        await client.close()


def convenience_functions_demo():
    """Demonstrate GraphQL convenience functions."""
    print_section("Convenience Functions Demo")

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available.")
        return

    print_subsection("Quick GraphQL Operations")

    # Create test data
    account = Account()
    metagraph_id = "DAG7Ghth6FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhQs"

    print(f"🎯 Using convenience functions for quick operations...")

    # Network status convenience function
    try:
        print("\n1️⃣ Network Status (Convenience Function):")
        response = get_network_status("testnet")

        if response.is_successful:
            print("✅ Network status retrieved")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")

            network_data = response.data.get("network", {})
            print(f"📊 Status: {network_data.get('status', 'Unknown')}")
            print(f"🏢 Nodes: {network_data.get('nodeCount', 'N/A')}")
        else:
            print("❌ Network status failed")
            for error in response.errors:
                print(f"  Error: {error}")

    except Exception as e:
        print(f"❌ Error in network status: {e}")

    # Account portfolio convenience function
    try:
        print("\n2️⃣ Account Portfolio (Convenience Function):")
        response = get_account_portfolio("testnet", account.address)

        if response.is_successful:
            print("✅ Account portfolio retrieved")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")

            account_data = response.data.get("account", {})
            balance = account_data.get("balance", 0)
            transactions = account_data.get("transactions", [])

            print(f"💰 Balance: {balance / 1e8:.8f} DAG")
            print(f"📜 Transactions: {len(transactions)}")
        else:
            print("❌ Account portfolio failed")
            for error in response.errors:
                print(f"  Error: {error}")

    except Exception as e:
        print(f"❌ Error in account portfolio: {e}")

    # Metagraph overview convenience function
    try:
        print("\n3️⃣ Metagraph Overview (Convenience Function):")
        response = get_metagraph_overview("testnet", metagraph_id)

        if response.is_successful:
            print("✅ Metagraph overview retrieved")
            print(f"⏱️  Execution time: {response.execution_time:.3f}s")

            metagraph_data = response.data.get("metagraph", {})
            print(f"🏛️  Name: {metagraph_data.get('name', 'Unknown')}")
            print(f"🪙 Token: {metagraph_data.get('tokenSymbol', 'N/A')}")
            print(f"📊 Supply: {metagraph_data.get('totalSupply', 0) / 1e8:.8f}")
        else:
            print("❌ Metagraph overview failed")
            for error in response.errors:
                print(f"  Error: {error}")

    except Exception as e:
        print(f"❌ Error in metagraph overview: {e}")

    print_subsection("Convenience Query Builders")

    # Show pre-built query generators
    addresses = [account.address, Account().address]

    print("🔧 Generated queries using convenience builders:")

    print("\n• Account Query:")
    account_query = build_account_query(
        account.address, include_transactions=True, include_balances=True
    )
    print(f"  Length: {len(account_query)} characters")

    print("\n• Metagraph Query:")
    metagraph_query = build_metagraph_query(
        metagraph_id, include_holders=True, include_transactions=True
    )
    print(f"  Length: {len(metagraph_query)} characters")

    print("\n• Network Status Query:")
    network_query = build_network_status_query()
    print(f"  Length: {len(network_query)} characters")

    print("\n• Portfolio Query:")
    portfolio_query = build_portfolio_query(addresses)
    print(f"  Length: {len(portfolio_query)} characters")


def error_handling_demo():
    """Demonstrate GraphQL error handling."""
    print_section("GraphQL Error Handling Demo")

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available.")
        return

    print_subsection("Error Scenarios")

    client = GraphQLClient("testnet")

    # Invalid query syntax
    print("\n1️⃣ Invalid Query Syntax:")
    invalid_query = "query { invalid syntax here }"

    try:
        response = client.execute(invalid_query)

        if response.has_errors:
            print("✅ Error handling working correctly")
            print(f"📊 {len(response.errors)} error(s) detected")
            for error in response.errors:
                print(f"  ❌ {error.get('message', 'Unknown error')}")
        else:
            print("⚠️  Expected error not detected")

    except Exception as e:
        print(f"✅ Exception caught: {e}")

    # Non-existent field
    print("\n2️⃣ Non-existent Field:")
    field_query = """
    query {
        network {
            nonExistentField
        }
    }
    """

    try:
        response = client.execute(field_query)

        if response.has_errors:
            print("✅ Field validation working")
            for error in response.errors:
                print(f"  ❌ {error.get('message', 'Unknown error')}")
        else:
            print("⚠️  Field error not detected")

    except Exception as e:
        print(f"✅ Exception caught: {e}")

    # Invalid variables
    print("\n3️⃣ Invalid Variables:")
    var_query = GraphQLQuery(
        query=ConstellationSchema.ACCOUNT_PORTFOLIO,
        variables={"address": "INVALID_ADDRESS_FORMAT"},
    )

    try:
        response = client.execute(var_query)

        if response.has_errors:
            print("✅ Variable validation working")
            for error in response.errors:
                print(f"  ❌ {error.get('message', 'Unknown error')}")
        else:
            print("⚠️  Variable error not detected")

    except Exception as e:
        print(f"✅ Exception caught: {e}")

    print_subsection("Graceful Degradation")

    # Show how GraphQL queries can partially succeed
    print("💡 GraphQL supports partial results:")
    print("   • Some fields may succeed while others fail")
    print("   • Errors are collected alongside successful data")
    print("   • Applications can handle partial responses gracefully")


def performance_demo():
    """Demonstrate GraphQL performance benefits."""
    print_section("GraphQL Performance Demo")

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available.")
        return

    print_subsection("Performance Comparison")

    client = GraphQLClient("testnet")
    accounts = [Account() for _ in range(3)]
    addresses = [acc.address for acc in accounts]

    print(f"⚡ Comparing performance for {len(addresses)} accounts...")

    # Single comprehensive query vs multiple REST calls
    print("\n1️⃣ Single GraphQL Query (Multiple Data Points):")

    comprehensive_query = """
    query ComprehensiveData($addresses: [String!]!) {
        accounts(addresses: $addresses) {
            address
            balance
            transactions(first: 5) {
                hash
                amount
            }
        }
        network {
            status
            nodeCount
            version
        }
    }
    """

    try:
        start_time = time.time()
        response = client.execute(comprehensive_query, {"addresses": addresses})
        execution_time = time.time() - start_time

        if response.is_successful:
            print("✅ Comprehensive query executed")
            print(f"⏱️  Total time: {execution_time:.3f}s")
            print(f"📊 Data points retrieved:")

            accounts_data = response.data.get("accounts", [])
            network_data = response.data.get("network", {})

            print(f"   • {len(accounts_data)} account balances")
            total_transactions = sum(
                len(acc.get("transactions", [])) for acc in accounts_data
            )
            print(f"   • {total_transactions} transactions")
            print(f"   • 1 network status")
            print(f"   • All in a single request!")
        else:
            print("❌ Comprehensive query failed")

    except Exception as e:
        print(f"❌ Error in comprehensive query: {e}")

    print("\n2️⃣ GraphQL vs REST Benefits:")
    print("📈 GraphQL Advantages:")
    print("   • Single request for complex data")
    print("   • Precise field selection (no over-fetching)")
    print("   • Reduced network round trips")
    print("   • Type-safe queries with validation")
    print("   • Real-time subscriptions")
    print("   • Flexible relationship queries")

    print("\n📊 Performance Metrics:")
    stats = client.get_stats()
    print(f"   • Queries executed: {stats['queries_executed']}")
    print(f"   • Average execution time: {stats['average_execution_time']:.3f}s")
    print(
        f"   • Error rate: {stats['errors_encountered'] / max(stats['queries_executed'], 1) * 100:.1f}%"
    )


def main():
    """Run all GraphQL demos."""
    print("🌌 Constellation Network GraphQL API Demo")
    print("=" * 60)

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available!")
        print("Install optional dependencies to enable GraphQL:")
        print("   pip install aiohttp websockets")
        print("\nThis demo requires GraphQL support to run.")
        sys.exit(1)

    print("✅ GraphQL functionality available")
    print("🚀 Starting comprehensive GraphQL demonstration...")

    try:
        # Run synchronous demos
        basic_graphql_demo()
        query_builder_demo()
        subscription_demo()
        convenience_functions_demo()
        error_handling_demo()
        performance_demo()

        # Run async demo
        print_section("Running Async Demo")
        asyncio.run(async_graphql_demo())

        print_section("Demo Complete")
        print("✅ All GraphQL demos completed successfully!")
        print("\n🎯 Next Steps:")
        print("   • Explore the CLI: constellation graphql --help")
        print("   • Try the playground: constellation graphql playground")
        print("   • Build custom queries for your application")
        print("   • Use real-time subscriptions for live updates")

    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Add time import for performance demo
    import time

    main()
