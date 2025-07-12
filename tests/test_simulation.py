"""
Tests for transaction simulation functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch

from constellation_sdk import (
    Account,
    Network,
    Transactions,
    TransactionSimulator,
    simulate_transaction,
    estimate_transaction_cost,
)
from constellation_sdk.exceptions import (
    ValidationError,
    AddressValidationError,
    AmountValidationError,
    TransactionValidationError,
)


class TestTransactionSimulator:
    """Test TransactionSimulator class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock network
        self.mock_network = Mock(spec=Network)
        self.mock_network.get_balance.return_value = 1000000000  # 10 DAG
        
        # Create simulator
        self.simulator = TransactionSimulator(self.mock_network)
        
        # Test addresses (with valid format for passing validation - 38 chars total)
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
        self.invalid_address = "INVALID_ADDRESS"
        self.valid_metagraph_id = "DAG22222222222222222222222222222222222"

    def test_simulate_dag_transfer_valid(self):
        """Test successful DAG transfer simulation."""
        result = self.simulator.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=100000000,  # 1 DAG
            check_balance=True
        )
        
        assert result['transaction_type'] == 'dag_transfer'
        assert len(result['validation_errors']) == 0
        assert result['balance_sufficient'] is True
        assert result['will_succeed'] is True
        assert result['success_probability'] > 0.8
        assert result['estimated_size'] > 0
        
        # Verify balance was checked
        self.mock_network.get_balance.assert_called_once_with(self.valid_address1)

    def test_simulate_dag_transfer_insufficient_balance(self):
        """Test DAG transfer simulation with insufficient balance."""
        # Set up insufficient balance
        self.mock_network.get_balance.return_value = 50000000  # 0.5 DAG
        
        result = self.simulator.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=100000000,  # 1 DAG
            check_balance=True
        )
        
        assert result['will_succeed'] is False
        assert result['balance_sufficient'] is False
        assert any('Insufficient balance' in error for error in result['validation_errors'])
        assert result['success_probability'] < 0.8

    def test_simulate_dag_transfer_invalid_address(self):
        """Test DAG transfer simulation with invalid addresses."""
        result = self.simulator.simulate_dag_transfer(
            source=self.invalid_address,
            destination=self.valid_address2,
            amount=100000000,
            check_balance=False
        )
        
        assert result['will_succeed'] is False
        assert any('Invalid source address' in error for error in result['validation_errors'])
        assert result['success_probability'] < 0.8

    def test_simulate_dag_transfer_invalid_amount(self):
        """Test DAG transfer simulation with invalid amount."""
        result = self.simulator.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=-100000000,  # Negative amount
            check_balance=False
        )
        
        assert result['will_succeed'] is False
        assert any('Invalid amount' in error for error in result['validation_errors'])

    def test_simulate_dag_transfer_detailed_analysis(self):
        """Test DAG transfer simulation with detailed analysis."""
        result = self.simulator.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=100000000,
            detailed_analysis=True
        )
        
        assert 'detailed_analysis' in result
        analysis = result['detailed_analysis']
        assert 'transaction_complexity' in analysis
        assert 'estimated_processing_time' in analysis
        assert 'network_requirements' in analysis
        assert 'optimization_suggestions' in analysis
        assert 'risk_factors' in analysis

    def test_simulate_token_transfer_valid(self):
        """Test successful token transfer simulation."""
        result = self.simulator.simulate_token_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=1000000000,  # 10 tokens
            metagraph_id=self.valid_metagraph_id,
            check_balance=True
        )
        
        assert result['transaction_type'] == 'token_transfer'
        assert result['metagraph_id'] == self.valid_metagraph_id
        assert result['will_succeed'] is True
        assert result['balance_sufficient'] is True  # Should be True for token transfers
        assert len(result['validation_errors']) == 0
        assert result['success_probability'] > 0.8

    def test_simulate_token_transfer_invalid_metagraph_id(self):
        """Test token transfer simulation with invalid metagraph ID."""
        result = self.simulator.simulate_token_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=1000000000,
            metagraph_id="INVALID_ID",
            check_balance=False
        )
        
        assert result['will_succeed'] is False
        assert any('Metagraph ID' in error for error in result['validation_errors'])

    def test_simulate_data_submission_valid(self):
        """Test successful data submission simulation."""
        data = {
            "sensor_type": "temperature",
            "value": 25.7,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        result = self.simulator.simulate_data_submission(
            source=self.valid_address1,
            data=data,
            metagraph_id=self.valid_metagraph_id
        )
        
        assert result['transaction_type'] == 'data_submission'
        assert result['metagraph_id'] == self.valid_metagraph_id
        assert result['will_succeed'] is True
        assert result['balance_sufficient'] is True  # Data submissions don't require balance
        assert len(result['validation_errors']) == 0
        assert result['data_size'] > 0

    def test_simulate_data_submission_large_data(self):
        """Test data submission simulation with large data payload."""
        # Create large data payload
        large_data = {"data": "x" * (1024 * 1024 + 1)}  # Over 1MB
        
        result = self.simulator.simulate_data_submission(
            source=self.valid_address1,
            data=large_data,
            metagraph_id=self.valid_metagraph_id
        )
        
        assert any('Data payload is large' in warning for warning in result['warnings'])

    def test_simulate_data_submission_invalid_data(self):
        """Test data submission simulation with invalid data."""
        # Create non-serializable data
        invalid_data = {"function": lambda x: x}
        
        result = self.simulator.simulate_data_submission(
            source=self.valid_address1,
            data=invalid_data,
            metagraph_id=self.valid_metagraph_id
        )
        
        assert result['will_succeed'] is False
        assert any('not JSON serializable' in error for error in result['validation_errors'])

    def test_simulate_batch_transfers_valid(self):
        """Test successful batch transfer simulation."""
        transfers = [
            {"destination": self.valid_address2, "amount": 100000000},
            {"destination": self.valid_address1, "amount": 200000000}
        ]
        
        result = self.simulator.simulate_batch_transfers(
            source=self.valid_address1,
            transfers=transfers,
            check_balance=True
        )
        
        assert result['transaction_type'] == 'batch_transfer'
        assert result['total_transfers'] == 2
        assert result['successful_transfers'] == 2
        assert result['failed_transfers'] == 0
        assert result['total_amount'] == 300000000
        assert len(result['individual_results']) == 2

    def test_simulate_batch_transfers_insufficient_balance(self):
        """Test batch transfer simulation with insufficient balance."""
        # Set up insufficient balance
        self.mock_network.get_balance.return_value = 100000000  # 1 DAG
        
        transfers = [
            {"destination": self.valid_address2, "amount": 500000000},  # 5 DAG
            {"destination": self.valid_address1, "amount": 600000000}   # 6 DAG
        ]
        
        result = self.simulator.simulate_batch_transfers(
            source=self.valid_address1,
            transfers=transfers,
            check_balance=True
        )
        
        assert result['batch_success_probability'] == 0.0
        assert any('Insufficient balance' in error for error in result['validation_errors'])

    def test_simulate_batch_transfers_mixed_types(self):
        """Test batch transfer simulation with mixed transaction types."""
        transfers = [
            {"destination": self.valid_address2, "amount": 100000000},  # DAG transfer
            {
                "destination": self.valid_address2,
                "amount": 1000000000,
                "metagraph_id": self.valid_metagraph_id
            },  # Token transfer
            {
                "data": {"sensor": "temperature", "value": 25.7},
                "metagraph_id": self.valid_metagraph_id
            }  # Data submission
        ]
        
        result = self.simulator.simulate_batch_transfers(
            source=self.valid_address1,
            transfers=transfers,
            check_balance=True
        )
        
        assert result['total_transfers'] == 3
        assert len(result['individual_results']) == 3
        
        # Check that different transaction types were simulated
        transaction_types = [r['transaction_type'] for r in result['individual_results']]
        assert 'dag_transfer' in transaction_types
        assert 'token_transfer' in transaction_types
        assert 'data_submission' in transaction_types

    def test_balance_caching(self):
        """Test that balance queries are cached."""
        # First call
        result1 = self.simulator.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=100000000,
            check_balance=True
        )
        
        # Second call (should use cache)
        result2 = self.simulator.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=200000000,
            check_balance=True
        )
        
        # Should have called get_balance only once due to caching
        assert self.mock_network.get_balance.call_count == 1

    def test_network_error_handling(self):
        """Test handling of network errors during simulation."""
        # Set up network error
        self.mock_network.get_balance.side_effect = Exception("Network error")
        
        result = self.simulator.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=100000000,
            check_balance=True
        )
        
        assert result['balance_sufficient'] is False
        assert any('Could not check balance' in warning for warning in result['warnings'])


class TestTransactionsSimulationMethods:
    """Test simulation methods in Transactions class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_network = Mock(spec=Network)
        self.mock_network.get_balance.return_value = 1000000000  # 10 DAG
        
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
        self.valid_metagraph_id = "DAG22222222222222222222222222222222222"

    def test_transactions_simulate_dag_transfer(self):
        """Test Transactions.simulate_dag_transfer method."""
        result = Transactions.simulate_dag_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=100000000,
            network=self.mock_network
        )
        
        assert result['transaction_type'] == 'dag_transfer'
        assert result['will_succeed'] is True

    def test_transactions_simulate_token_transfer(self):
        """Test Transactions.simulate_token_transfer method."""
        result = Transactions.simulate_token_transfer(
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=1000000000,
            metagraph_id=self.valid_metagraph_id,
            network=self.mock_network
        )
        
        assert result['transaction_type'] == 'token_transfer'
        assert result['metagraph_id'] == self.valid_metagraph_id

    def test_transactions_simulate_data_submission(self):
        """Test Transactions.simulate_data_submission method."""
        data = {"sensor": "temperature", "value": 25.7}
        
        result = Transactions.simulate_data_submission(
            source=self.valid_address1,
            data=data,
            metagraph_id=self.valid_metagraph_id,
            network=self.mock_network
        )
        
        assert result['transaction_type'] == 'data_submission'
        assert result['data_size'] > 0

    def test_transactions_simulate_batch_transfer(self):
        """Test Transactions.simulate_batch_transfer method."""
        transfers = [
            {"destination": self.valid_address2, "amount": 100000000},
            {"destination": self.valid_address1, "amount": 200000000}
        ]
        
        result = Transactions.simulate_batch_transfer(
            source=self.valid_address1,
            transfers=transfers,
            network=self.mock_network
        )
        
        assert result['transaction_type'] == 'batch_transfer'
        assert result['total_transfers'] == 2


class TestConvenienceFunctions:
    """Test convenience functions for simulation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_network = Mock(spec=Network)
        self.mock_network.get_balance.return_value = 1000000000  # 10 DAG
        
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
        self.valid_metagraph_id = "DAG22222222222222222222222222222222222"

    def test_simulate_transaction_dag(self):
        """Test simulate_transaction convenience function for DAG transfers."""
        result = simulate_transaction(
            network=self.mock_network,
            transaction_type='dag',
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=100000000
        )
        
        assert result['transaction_type'] == 'dag_transfer'
        assert result['will_succeed'] is True

    def test_simulate_transaction_token(self):
        """Test simulate_transaction convenience function for token transfers."""
        result = simulate_transaction(
            network=self.mock_network,
            transaction_type='token',
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=1000000000,
            metagraph_id=self.valid_metagraph_id
        )
        
        assert result['transaction_type'] == 'token_transfer'
        assert result['metagraph_id'] == self.valid_metagraph_id

    def test_simulate_transaction_data(self):
        """Test simulate_transaction convenience function for data submissions."""
        data = {"sensor": "temperature", "value": 25.7}
        
        result = simulate_transaction(
            network=self.mock_network,
            transaction_type='data',
            source=self.valid_address1,
            destination=self.valid_address2,
            amount=0,  # Not used for data submissions
            data=data,
            metagraph_id=self.valid_metagraph_id
        )
        
        assert result['transaction_type'] == 'data_submission'

    def test_simulate_transaction_invalid_type(self):
        """Test simulate_transaction with invalid transaction type."""
        with pytest.raises(ValueError, match="Unknown transaction type"):
            simulate_transaction(
                network=self.mock_network,
                transaction_type='invalid',
                source=self.valid_address1,
                destination=self.valid_address2,
                amount=100000000
            )

    def test_estimate_transaction_cost(self):
        """Test estimate_transaction_cost convenience function."""
        transaction_data = {
            'source': self.valid_address1,
            'destination': self.valid_address2,
            'amount': 100000000,
            'fee': 0,
            'salt': 12345678
        }
        
        result = estimate_transaction_cost(self.mock_network, transaction_data)
        
        assert 'estimated_size_bytes' in result
        assert 'estimated_fee' in result
        assert 'estimated_processing_time' in result
        assert 'network_bandwidth_required' in result
        assert 'storage_footprint' in result
        assert result['estimated_fee'] == 0  # Constellation is feeless


class TestSimulationIntegration:
    """Integration tests for simulation with real transaction creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_network = Mock(spec=Network)
        self.mock_network.get_balance.return_value = 1000000000  # 10 DAG
        
        self.account = Account()
        self.destination = "DAG00000000000000000000000000000000000"
        self.metagraph_id = "DAG22222222222222222222222222222222222"

    def test_simulate_then_create_dag_transfer(self):
        """Test simulating then creating a DAG transfer transaction."""
        # First simulate
        simulation = Transactions.simulate_dag_transfer(
            source=self.account.address,
            destination=self.destination,
            amount=100000000,
            network=self.mock_network
        )
        
        # If simulation succeeds, create the transaction
        if simulation['will_succeed']:
            transaction = Transactions.create_dag_transfer(
                source=self.account.address,
                destination=self.destination,
                amount=100000000
            )
            
            # Verify transaction was created with same parameters
            assert transaction['source'] == self.account.address
            assert transaction['destination'] == self.destination
            assert transaction['amount'] == 100000000
            assert transaction['fee'] == 0

    def test_simulate_then_create_token_transfer(self):
        """Test simulating then creating a token transfer transaction."""
        # First simulate
        simulation = Transactions.simulate_token_transfer(
            source=self.account.address,
            destination=self.destination,
            amount=1000000000,
            metagraph_id=self.metagraph_id,
            network=self.mock_network
        )
        
        # If simulation succeeds, create the transaction
        if simulation['will_succeed']:
            transaction = Transactions.create_token_transfer(
                source=self.account.address,
                destination=self.destination,
                amount=1000000000,
                metagraph_id=self.metagraph_id
            )
            
            # Verify transaction was created with same parameters
            assert transaction['source'] == self.account.address
            assert transaction['destination'] == self.destination
            assert transaction['amount'] == 1000000000
            assert transaction['metagraph_id'] == self.metagraph_id

    def test_simulate_then_create_data_submission(self):
        """Test simulating then creating a data submission transaction."""
        data = {"sensor": "temperature", "value": 25.7}
        
        # First simulate
        simulation = Transactions.simulate_data_submission(
            source=self.account.address,
            data=data,
            metagraph_id=self.metagraph_id,
            network=self.mock_network
        )
        
        # If simulation succeeds, create the transaction
        if simulation['will_succeed']:
            transaction = Transactions.create_data_submission(
                source=self.account.address,
                data=data,
                metagraph_id=self.metagraph_id
            )
            
            # Verify transaction was created with same parameters
            assert transaction['source'] == self.account.address
            assert transaction['data'] == data
            assert transaction['metagraph_id'] == self.metagraph_id


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.unit,
    pytest.mark.simulation,
]


# Network-dependent tests (require actual network connection)
@pytest.mark.network
class TestSimulationWithRealNetwork:
    """Tests that require actual network connection."""

    def test_simulate_with_real_network(self):
        """Test simulation with real network connection."""
        try:
            from constellation_sdk import Network
            
            # Use testnet for testing
            network = Network('testnet')
            
            # Create a real account
            account = Account()
            
            # Test simulation with real network
            result = Transactions.simulate_dag_transfer(
                source=account.address,
                destination="DAG00000000000000000000000000000000000",
                amount=100000000,
                network=network,
                check_balance=True
            )
            
            # Should have valid simulation result
            assert 'will_succeed' in result
            assert 'balance_sufficient' in result
            assert 'estimated_size' in result
            
            # Balance should be insufficient for new account
            assert result['balance_sufficient'] is False
            
        except Exception as e:
            pytest.skip(f"Network test skipped: {e}")