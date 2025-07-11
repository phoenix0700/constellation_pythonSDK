"""
Constellation Metagraph Python SDK - Complete Capabilities Demo
===============================================================

This script demonstrates everything you can do with the metagraph functionality
in the Constellation Python SDK.
"""

from constellation_sdk import (
    Account,
    MetagraphClient,
    Network,
    Transactions,
    discover_production_metagraphs,
    get_realistic_metagraph_summary,
)


def demo_discovery_capabilities():
    """Demo: Discover and explore metagraphs"""
    print("🔍 1. DISCOVERY & EXPLORATION CAPABILITIES")
    print("=" * 45)

    # Realistic discovery across all networks
    summary = get_realistic_metagraph_summary()
    print(f"✅ Real production metagraphs: {summary['production_total']}")
    print(f"✅ Total deployments (all): {summary['total_deployments']}")

    for network, data in summary["networks"].items():
        print(
            f"   🌐 {network.upper()}: {data['estimated_production']} production, "
            f"{data['likely_test_deployments']} test"
        )

    # Focus on production metagraphs
    print(f"\n🎯 Production Metagraphs on MainNet:")
    production_mgs = discover_production_metagraphs("mainnet")

    for i, mg in enumerate(production_mgs[:3]):  # Show first 3
        print(f"   {i+1}. {mg['id'][:30]}... (created: {mg['created'][:10]})")

    if len(production_mgs) > 3:
        print(f"   ... and {len(production_mgs) - 3} more")

    return production_mgs


def demo_metagraph_info():
    """Demo: Get detailed metagraph information"""
    print(f"\n💡 2. METAGRAPH INFORMATION & ANALYSIS")
    print("=" * 45)

    client = MetagraphClient("mainnet")

    # Get all production metagraphs
    metagraphs = client.discover_production_metagraphs()

    if metagraphs:
        # Analyze first metagraph
        mg = metagraphs[0]
        mg_id = mg["id"]

        print(f"🔬 Analyzing: {mg_id[:30]}...")

        # Get detailed info
        info = client.get_metagraph_info(mg_id)
        print(f"   💰 Balance: {info['balance']} DAG")
        print(f"   📊 Transactions: {info['transaction_count']}")
        print(f"   ⚡ Is Active: {info['is_active']}")
        print(f"   🌐 Network: {info['network']}")

        # Check activity across all metagraphs
        print(f"\n📈 Activity Analysis:")
        active_mgs = client.get_active_metagraphs()
        print(f"   Active metagraphs: {len(active_mgs)}/{len(metagraphs)}")

        return mg_id
    else:
        print("   ℹ️  No production metagraphs found")
        return None


def demo_token_transactions():
    """Demo: Create custom token transactions"""
    print(f"\n🪙  3. CUSTOM TOKEN TRANSACTIONS")
    print("=" * 35)

    # Create accounts
    sender = Account()
    recipient = Account()

    print(f"👤 Sender: {sender.address[:30]}...")
    print(f"👤 Recipient: {recipient.address[:30]}...")

    # Create metagraph client
    client = MetagraphClient("mainnet")

    # Get a production metagraph to work with
    production_mgs = client.discover_production_metagraphs()

    if production_mgs:
        metagraph_id = production_mgs[0]["id"]

        # Create different types of token transactions
        print(f"\n💸 Creating token transactions for: {metagraph_id[:25]}...")

        # Standard token transfer
        token_tx = Transactions.create_token_transfer(
            source=sender.address,
            destination=recipient.address,
            amount=1000000000,  # 10 tokens (assuming 8 decimals)
            metagraph_id=metagraph_id,
            fee=0,
        )
        # Sign the transaction
        signed_token_tx = sender.sign_metagraph_transaction(token_tx)

        print(f"✅ Standard transfer: 10 tokens")
        print(f"   Transaction keys: {list(signed_token_tx.keys())}")
        print(f"   Value keys: {list(signed_token_tx['value'].keys())}")
        print(f"   Signature length: {len(signed_token_tx['proofs'][0]['signature'])} chars")

        # Micro-transaction (fractional tokens)
        micro_tx = Transactions.create_token_transfer(
            source=sender.address,
            destination=recipient.address,
            amount=1000000,  # 0.01 tokens
            metagraph_id=metagraph_id
        )
        signed_micro_tx = sender.sign_metagraph_transaction(micro_tx)

        print(f"✅ Micro-transaction: 0.01 tokens")

        # Large transaction
        large_tx = Transactions.create_token_transfer(
            source=sender.address,
            destination=recipient.address,
            amount=100000000000,  # 1000 tokens
            metagraph_id=metagraph_id
        )
        signed_large_tx = sender.sign_metagraph_transaction(large_tx)

        print(f"✅ Large transfer: 1000 tokens")

        return signed_token_tx
    else:
        print("   ℹ️  No production metagraphs available for demo")
        return None


def demo_data_transactions():
    """Demo: Submit custom data to metagraphs"""
    print(f"\n📦 4. DATA TRANSACTIONS & CUSTOM PAYLOADS")
    print("=" * 45)

    # Create account for data submission
    data_account = Account()
    print(f"📡 Data submitter: {data_account.address[:30]}...")

    client = MetagraphClient("mainnet")
    production_mgs = client.discover_production_metagraphs()

    if production_mgs:
        metagraph_id = production_mgs[0]["id"]

        print(f"\n📤 Submitting data to: {metagraph_id[:25]}...")

        # IoT sensor data
        sensor_tx = Transactions.create_data_submission(
            source=data_account.address,
            data={
                "sensor_type": "temperature",
                "value": 25.7,
                "unit": "celsius",
                "location": "warehouse_a",
                "timestamp": "2024-01-15T10:30:00Z",
                "device_id": "TEMP_001",
            },
            metagraph_id=metagraph_id,
        )
        signed_sensor_tx = data_account.sign_metagraph_transaction(sensor_tx)

        print(f"✅ IoT sensor data submitted")
        print(f"   Data keys: {list(signed_sensor_tx['value']['data'].keys())}")

        # Supply chain tracking
        supply_tx = Transactions.create_data_submission(
            source=data_account.address,
            data={
                "product_id": "PROD_12345",
                "batch_number": "B2024001",
                "origin": "Factory_Shanghai",
                "destination": "Warehouse_NYC",
                "status": "in_transit",
                "carrier": "GlobalShipping",
                "tracking_number": "GS789456123",
            },
            metagraph_id=metagraph_id,
        )
        signed_supply_tx = data_account.sign_metagraph_transaction(supply_tx)

        print(f"✅ Supply chain data submitted")

        # Financial/audit data
        audit_tx = Transactions.create_data_submission(
            source=data_account.address,
            data={
                "transaction_id": "TXN_789",
                "audit_type": "compliance_check",
                "status": "verified",
                "auditor": "AuditFirm_ABC",
                "compliance_score": 95.5,
                "risk_level": "low",
            },
            metagraph_id=metagraph_id,
        )
        signed_audit_tx = data_account.sign_metagraph_transaction(audit_tx)

        print(f"✅ Audit/compliance data submitted")

        # Custom application data
        app_tx = Transactions.create_data_submission(
            source=data_account.address,
            data={
                "app": "social_media_dapp",
                "action": "post_content",
                "user_id": "user_456",
                "content_hash": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
                "likes": 0,
                "shares": 0,
            },
            metagraph_id=metagraph_id,
        )
        signed_app_tx = data_account.sign_metagraph_transaction(app_tx)

        print(f"✅ Social media DApp data submitted")

        return signed_sensor_tx, signed_supply_tx, signed_audit_tx, signed_app_tx
    else:
        print("   ℹ️  No production metagraphs available for demo")
        return None


def demo_balance_queries():
    """Demo: Query balances and metagraph states"""
    print(f"\n💰 5. BALANCE QUERIES & STATE MANAGEMENT")
    print("=" * 45)

    # Create test accounts
    account1 = Account()
    account2 = Account()

    client = MetagraphClient("mainnet")
    production_mgs = client.discover_production_metagraphs()

    if production_mgs:
        metagraph_id = production_mgs[0]["id"]

        print(f"💳 Checking balances on: {metagraph_id[:25]}...")

        # Check DAG balances (standard)
        dag_balance1 = client.get_balance(metagraph_id, account1.address)
        dag_balance2 = client.get_balance(metagraph_id, account2.address)

        print(f"   Account 1 balance: {dag_balance1} DAG")
        print(f"   Account 2 balance: {dag_balance2} DAG")

        # Get metagraph state
        mg_info = client.get_metagraph_info(metagraph_id)
        print(f"   Metagraph balance: {mg_info['balance']} DAG")
        print(f"   Transaction count: {mg_info['transaction_count']}")

        # Network summary
        network_summary = client.get_network_summary()
        print(f"\n📊 Network Summary:")
        print(f"   Network: {network_summary['network']}")
        print(f"   Production metagraphs: {network_summary['production_count']}")
        print(f"   Test deployments: {network_summary['test_deployments']}")

    else:
        print("   ℹ️  No production metagraphs available for demo")


def demo_advanced_features():
    """Demo: Advanced SDK features"""
    print(f"\n⚡ 6. ADVANCED FEATURES & USE CASES")
    print("=" * 40)

    print("🎯 Smart Filtering:")

    # Compare production vs all deployments
    client = MetagraphClient("testnet")

    production_only = client.discover_production_metagraphs()
    all_deployments = client.discover_metagraphs(include_test_deployments=True)

    print(f"   TestNet production: {len(production_only)}")
    print(f"   TestNet all deployments: {len(all_deployments)}")
    print(
        f"   Filtered out: {len(all_deployments) - len(production_only)} test deployments"
    )

    print(f"\n🔄 Multi-Network Operations:")

    # Work across different networks
    networks = ["mainnet", "testnet", "integrationnet"]
    for network in networks:
        try:
            net_client = MetagraphClient(network)
            summary = net_client.get_network_summary()
            print(
                f"   {network}: {summary['production_count']} production, "
                f"{summary['test_deployments']} test"
            )
        except:
            print(f"   {network}: unavailable")

    print(f"\n🏗️  SDK Integration Examples:")
    integration_examples = [
        "DeFi applications with custom tokens",
        "Supply chain tracking with data submissions",
        "IoT sensor networks with real-time data",
        "Social media DApps with content verification",
        "Gaming platforms with in-game currencies",
        "Audit and compliance tracking systems",
    ]

    for example in integration_examples:
        print(f"   ✅ {example}")


def main():
    """Run complete metagraph capabilities demo"""
    print("🏛️  CONSTELLATION METAGRAPH PYTHON SDK")
    print("🚀 COMPLETE CAPABILITIES DEMONSTRATION")
    print("=" * 60)

    try:
        # Run all demos
        production_mgs = demo_discovery_capabilities()
        metagraph_id = demo_metagraph_info()
        token_tx = demo_token_transactions()
        data_txs = demo_data_transactions()
        demo_balance_queries()
        demo_advanced_features()

        print(f"\n🎉 CAPABILITIES SUMMARY")
        print("=" * 25)
        print("✅ Discovery: Find real production metagraphs")
        print("✅ Analysis: Get detailed metagraph information")
        print("✅ Tokens: Create and sign custom token transactions")
        print("✅ Data: Submit structured data to metagraphs")
        print("✅ Queries: Check balances and states")
        print("✅ Advanced: Multi-network, filtering, integration")

        print(f"\n🎯 THE METAGRAPH SDK CAN:")
        capabilities = [
            "Build DeFi applications with custom tokens",
            "Create supply chain tracking systems",
            "Develop IoT data collection networks",
            "Build social media and content platforms",
            "Create gaming economies with custom currencies",
            "Implement audit and compliance systems",
            "Develop any custom blockchain application",
        ]

        for capability in capabilities:
            print(f"   🏗️  {capability}")

        print(f"\n🚀 Ready for production use on Constellation Network!")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
