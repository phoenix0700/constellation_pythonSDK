"""
Transaction Simulation Demo - Constellation Network Python SDK

This example demonstrates how to use the transaction simulation feature
to validate and estimate transactions before submitting them to the network.
This helps save TestNet funds and prevents failed transactions.
"""

from constellation_sdk import (
    Account,
    Network,
    Transactions,
    TransactionSimulator,
    simulate_transaction,
    estimate_transaction_cost,
)


def main():
    """Demonstrate transaction simulation capabilities."""
    print("🔮 Transaction Simulation Demo - Constellation Network Python SDK")
    print("=" * 60)
    
    # Create accounts and network
    alice = Account()
    bob = Account()
    network = Network('testnet')
    
    print(f"👤 Alice: {alice.address}")
    print(f"👤 Bob: {bob.address}")
    print(f"🌐 Network: {network.config.name}")
    print()
    
    # 1. Basic DAG Transfer Simulation
    print("📊 1. DAG Transfer Simulation")
    print("-" * 30)
    
    # Simulate a DAG transfer
    dag_simulation = Transactions.simulate_dag_transfer(
        source=alice.address,
        destination=bob.address,
        amount=100000000,  # 1 DAG
        network=network,
        detailed_analysis=True
    )
    
    print(f"Transaction Type: {dag_simulation['transaction_type']}")
    print(f"Will Succeed: {dag_simulation['will_succeed']}")
    print(f"Success Probability: {dag_simulation['success_probability']:.1%}")
    print(f"Estimated Size: {dag_simulation['estimated_size']} bytes")
    print(f"Balance Sufficient: {dag_simulation['balance_sufficient']}")
    
    if dag_simulation['validation_errors']:
        print("❌ Validation Errors:")
        for error in dag_simulation['validation_errors']:
            print(f"  - {error}")
    
    if dag_simulation['warnings']:
        print("⚠️  Warnings:")
        for warning in dag_simulation['warnings']:
            print(f"  - {warning}")
    
    # Show detailed analysis
    if 'detailed_analysis' in dag_simulation:
        analysis = dag_simulation['detailed_analysis']
        print(f"📈 Detailed Analysis:")
        print(f"  - Complexity: {analysis['transaction_complexity']}")
        print(f"  - Processing Time: {analysis['estimated_processing_time']}")
        print(f"  - Network Requirements: {', '.join(analysis['network_requirements'])}")
        
        if analysis['optimization_suggestions']:
            print("  - Optimization Suggestions:")
            for suggestion in analysis['optimization_suggestions']:
                print(f"    • {suggestion}")
    
    print()
    
    # 2. Token Transfer Simulation
    print("🪙 2. Token Transfer Simulation")
    print("-" * 30)
    
    # Use a mock metagraph ID
    metagraph_id = "DAG22222222222222222222222222222222222"
    
    token_simulation = Transactions.simulate_token_transfer(
        source=alice.address,
        destination=bob.address,
        amount=1000000000,  # 10 tokens
        metagraph_id=metagraph_id,
        network=network
    )
    
    print(f"Transaction Type: {token_simulation['transaction_type']}")
    print(f"Metagraph ID: {token_simulation['metagraph_id']}")
    print(f"Will Succeed: {token_simulation['will_succeed']}")
    print(f"Success Probability: {token_simulation['success_probability']:.1%}")
    print(f"Estimated Size: {token_simulation['estimated_size']} bytes")
    print()
    
    # 3. Data Submission Simulation
    print("📄 3. Data Submission Simulation")
    print("-" * 30)
    
    sensor_data = {
        "sensor_type": "temperature",
        "value": 25.7,
        "location": "warehouse_a",
        "timestamp": "2024-01-15T10:30:00Z",
        "unit": "celsius"
    }
    
    data_simulation = Transactions.simulate_data_submission(
        source=alice.address,
        data=sensor_data,
        metagraph_id=metagraph_id,
        network=network
    )
    
    print(f"Transaction Type: {data_simulation['transaction_type']}")
    print(f"Data Size: {data_simulation['data_size']} bytes")
    print(f"Will Succeed: {data_simulation['will_succeed']}")
    print(f"Success Probability: {data_simulation['success_probability']:.1%}")
    print(f"Estimated Size: {data_simulation['estimated_size']} bytes")
    print()
    
    # 4. Batch Transfer Simulation
    print("📦 4. Batch Transfer Simulation")
    print("-" * 30)
    
    # Create mixed batch of transfers
    batch_transfers = [
        {"destination": bob.address, "amount": 50000000},  # 0.5 DAG
        {
            "destination": alice.address,
            "amount": 500000000,  # 5 tokens
            "metagraph_id": metagraph_id
        },
        {
            "data": {"sensor": "humidity", "value": 65.2},
            "metagraph_id": metagraph_id
        }
    ]
    
    batch_simulation = Transactions.simulate_batch_transfer(
        source=alice.address,
        transfers=batch_transfers,
        network=network
    )
    
    print(f"Transaction Type: {batch_simulation['transaction_type']}")
    print(f"Total Transfers: {batch_simulation['total_transfers']}")
    print(f"Successful Transfers: {batch_simulation['successful_transfers']}")
    print(f"Failed Transfers: {batch_simulation['failed_transfers']}")
    print(f"Batch Success Probability: {batch_simulation['batch_success_probability']:.1%}")
    print(f"Total Size: {batch_simulation['total_size']} bytes")
    
    print("📋 Individual Results:")
    for i, result in enumerate(batch_simulation['individual_results']):
        print(f"  Transfer {i+1}: {result['transaction_type']} - "
              f"{'✅ Success' if result['will_succeed'] else '❌ Failed'}")
    
    print()
    
    # 5. Using TransactionSimulator directly
    print("⚙️ 5. Using TransactionSimulator Class")
    print("-" * 30)
    
    simulator = TransactionSimulator(network)
    
    # Simulate with caching (balance will be cached)
    print("First simulation (balance query):")
    sim1 = simulator.simulate_dag_transfer(
        alice.address, bob.address, 25000000, check_balance=True
    )
    print(f"  - Will succeed: {sim1['will_succeed']}")
    
    print("Second simulation (uses cached balance):")
    sim2 = simulator.simulate_dag_transfer(
        alice.address, bob.address, 75000000, check_balance=True
    )
    print(f"  - Will succeed: {sim2['will_succeed']}")
    print()
    
    # 6. Convenience Functions
    print("🎯 6. Convenience Functions")
    print("-" * 30)
    
    # Quick simulation
    quick_sim = simulate_transaction(
        network=network,
        transaction_type='dag',
        source=alice.address,
        destination=bob.address,
        amount=10000000  # 0.1 DAG
    )
    print(f"Quick DAG simulation: {'✅ Success' if quick_sim['will_succeed'] else '❌ Failed'}")
    
    # Cost estimation
    sample_tx = {
        'source': alice.address,
        'destination': bob.address,
        'amount': 100000000,
        'fee': 0,
        'salt': 12345678
    }
    
    cost_estimate = estimate_transaction_cost(network, sample_tx)
    print(f"Cost estimate:")
    print(f"  - Size: {cost_estimate['estimated_size_bytes']} bytes")
    print(f"  - Fee: {cost_estimate['estimated_fee']} (Constellation is feeless)")
    print(f"  - Processing time: {cost_estimate['estimated_processing_time']}")
    print(f"  - Network bandwidth: {cost_estimate['network_bandwidth_required']} bytes")
    print()
    
    # 7. Production Workflow Example
    print("🏭 7. Production Workflow Example")
    print("-" * 30)
    
    print("Simulating before creating transaction...")
    
    # Step 1: Simulate
    simulation = Transactions.simulate_dag_transfer(
        source=alice.address,
        destination=bob.address,
        amount=100000000,
        network=network
    )
    
    # Step 2: Check if it will succeed
    if simulation['will_succeed']:
        print("✅ Simulation successful! Creating transaction...")
        
        # Step 3: Create the actual transaction
        transaction = Transactions.create_dag_transfer(
            source=alice.address,
            destination=bob.address,
            amount=100000000
        )
        
        # Step 4: Sign the transaction
        signed_tx = alice.sign_transaction(transaction)
        
        print(f"📝 Transaction created and signed!")
        print(f"   - Source: {signed_tx['value']['source']}")
        print(f"   - Destination: {signed_tx['value']['destination']}")
        print(f"   - Amount: {signed_tx['value']['amount'] / 1e8} DAG")
        print(f"   - Transaction hash: {signed_tx['hash']}")
        
        # In a real application, you would submit it:
        # result = network.submit_transaction(signed_tx)
        print("   - Ready to submit to network!")
        
    else:
        print("❌ Simulation failed. Transaction would not succeed.")
        if simulation['validation_errors']:
            print("   Errors:")
            for error in simulation['validation_errors']:
                print(f"     - {error}")
    
    print()
    print("🎉 Transaction simulation demo completed!")
    print("💡 Use simulation to validate transactions before submission")
    print("💰 Save TestNet funds and prevent failed transactions")


if __name__ == "__main__":
    main()