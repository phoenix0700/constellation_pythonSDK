"""
Comprehensive integration tests for Network functionality.
"""

import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from constellation_sdk.network import Network
from constellation_sdk import ConstellationError
from constellation_sdk.config import NetworkConfig


@pytest.mark.integration
@pytest.mark.mock
class TestNetworkInitialization:
    """Test network initialization and configuration."""
    
    def test_network_creation_with_config(self, test_network_config):
        """Test creating network with custom configuration."""
        network = Network(test_network_config)
        
        assert network.config == test_network_config
        assert network.config.name == "test"
        assert network.config.be_url == "https://test-be.constellation.io"
    
    def test_network_creation_with_string(self):
        """Test creating network with network name string."""
        network = Network("testnet")
        
        assert network.config.name == "testnet"
        assert "testnet" in network.config.be_url.lower()
    
    def test_network_creation_invalid_name(self):
        """Test creating network with invalid name."""
        with pytest.raises(ConstellationError):
            Network("invalid_network_name")


@pytest.mark.integration
@pytest.mark.mock
class TestNetworkInfo:
    """Test network information retrieval."""
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_node_info_success(self, mock_get, test_network_config, mock_network_responses):
        """Test successful node info retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses['node_info']
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        node_info = network.get_node_info()
        
        # Validate request
        mock_get.assert_called_once()
        assert test_network_config.be_url in str(mock_get.call_args)
        
        # Validate response
        assert node_info['version'] == '3.2.1-test'
        assert node_info['id'] == 'test_node_id'
        assert node_info['state'] == 'Ready'
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_node_info_http_error(self, mock_get, test_network_config, network_error_scenarios):
        """Test node info retrieval with HTTP error."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'error': 'Server error'}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        
        with pytest.raises(ConstellationError, match="HTTP 500"):
            network.get_node_info()
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_node_info_connection_error(self, mock_get, test_network_config):
        """Test node info retrieval with connection error."""
        # Setup mock connection error
        mock_get.side_effect = ConnectionError("Network unreachable")
        
        network = Network(test_network_config)
        
        with pytest.raises(ConstellationError, match="Network unreachable"):
            network.get_node_info()
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_cluster_info_success(self, mock_get, test_network_config, mock_network_responses):
        """Test successful cluster info retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses['cluster_info']
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        cluster_info = network.get_cluster_info()
        
        # Validate response
        assert isinstance(cluster_info, list)
        assert len(cluster_info) == 3
        assert cluster_info[0]['id'] == 'node1'
        assert cluster_info[0]['state'] == 'Ready'
        assert cluster_info[0]['ip'] == '192.168.1.1'


@pytest.mark.integration
@pytest.mark.mock
class TestBalanceOperations:
    """Test balance retrieval operations."""
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_balance_success(self, mock_get, test_network_config, mock_network_responses, alice_account):
        """Test successful balance retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses['balance_response']
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        balance = network.get_balance(alice_account.address)
        
        # Validate request
        mock_get.assert_called_once()
        assert alice_account.address in str(mock_get.call_args)
        
        # Validate response
        assert balance == 100000000
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_balance_address_not_found(self, mock_get, test_network_config):
        """Test balance retrieval for non-existent address."""
        # Setup mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': 'Address not found'}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        balance = network.get_balance("DAG_NON_EXISTENT_ADDRESS")
        
        # Should return 0 for non-existent addresses
        assert balance == 0
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_balance_invalid_address(self, test_network_config, invalid_dag_addresses):
        """Test balance retrieval with invalid address format."""
        network = Network(test_network_config)
        
        for invalid_address in invalid_dag_addresses[:5]:  # Test subset to avoid long test
            if invalid_address is not None and invalid_address != 123:
                with pytest.raises(ConstellationError):
                    network.get_balance(invalid_address)


@pytest.mark.integration
@pytest.mark.mock  
class TestTransactionOperations:
    """Test transaction submission and retrieval."""
    
    @patch('constellation_sdk.network.requests.post')
    def test_submit_transaction_success(self, mock_post, test_network_config, alice_account, valid_dag_transaction_data, signature_validator):
        """Test successful transaction submission."""
        # Setup signed transaction
        signed_tx = alice_account.sign_transaction(valid_dag_transaction_data)
        
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'hash': 'tx_hash_123'}
        mock_post.return_value = mock_response
        
        network = Network(test_network_config)
        result = network.submit_transaction(signed_tx)
        
        # Validate request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert test_network_config.l1_url in str(call_args)
        
        # Validate request data
        request_data = call_args[1]['json']
        assert signature_validator(request_data)
        
        # Validate response
        assert result['hash'] == 'tx_hash_123'
    
    @patch('constellation_sdk.network.requests.post')
    def test_submit_transaction_rejection(self, mock_post, test_network_config, alice_account, valid_dag_transaction_data):
        """Test transaction submission rejection."""
        # Setup signed transaction
        signed_tx = alice_account.sign_transaction(valid_dag_transaction_data)
        
        # Setup mock rejection response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Insufficient balance'}
        mock_post.return_value = mock_response
        
        network = Network(test_network_config)
        
        with pytest.raises(ConstellationError, match="Transaction rejected"):
            network.submit_transaction(signed_tx)
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_transactions_success(self, mock_get, test_network_config, mock_network_responses, alice_account):
        """Test successful transaction history retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses['transactions_response']
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        transactions = network.get_transactions(alice_account.address)
        
        # Validate request
        mock_get.assert_called_once()
        assert alice_account.address in str(mock_get.call_args)
        
        # Validate response
        assert isinstance(transactions, list)
        assert len(transactions) == 2
        assert transactions[0]['source'] == 'DAG123test'
        assert transactions[0]['destination'] == 'DAG456test'
        assert transactions[0]['amount'] == 50000000
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_transactions_with_limit(self, mock_get, test_network_config, alice_account):
        """Test transaction history retrieval with limit."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        network.get_transactions(alice_account.address, limit=10)
        
        # Validate limit parameter in request
        call_args = str(mock_get.call_args)
        assert 'limit=10' in call_args or '10' in call_args
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_last_transaction_reference_success(self, mock_get, test_network_config, alice_account):
        """Test successful last transaction reference retrieval."""
        # Setup mock response with transaction data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'hash': 'last_tx_hash_123'}]
        }
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        last_ref = network.get_last_transaction_reference(alice_account.address)
        
        # Validate response
        assert last_ref == 'last_tx_hash_123'
    
    @patch('constellation_sdk.network.requests.get')
    def test_get_last_transaction_reference_no_transactions(self, mock_get, test_network_config, alice_account):
        """Test last transaction reference for address with no transactions."""
        # Setup mock response with empty data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        last_ref = network.get_last_transaction_reference(alice_account.address)
        
        # Should return None for addresses with no transactions
        assert last_ref is None


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphOperations:
    """Test metagraph transaction operations."""
    
    @patch('constellation_sdk.network.requests.post')
    def test_submit_metagraph_transaction_success(self, mock_post, test_network_config, alice_account, valid_token_transfer_data):
        """Test successful metagraph transaction submission."""
        # Setup signed metagraph transaction
        signed_tx = alice_account.sign_metagraph_transaction(valid_token_transfer_data)
        
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'hash': 'metagraph_tx_hash_123'}
        mock_post.return_value = mock_response
        
        network = Network(test_network_config)
        result = network.submit_metagraph_transaction(signed_tx)
        
        # Validate request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Validate response
        assert result['hash'] == 'metagraph_tx_hash_123'
    
    @patch('constellation_sdk.network.requests.post')
    def test_submit_metagraph_transaction_rejection(self, mock_post, test_network_config, alice_account, valid_data_submission_data):
        """Test metagraph transaction submission rejection."""
        # Setup signed metagraph transaction
        signed_tx = alice_account.sign_metagraph_transaction(valid_data_submission_data)
        
        # Setup mock rejection response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Invalid data format'}
        mock_post.return_value = mock_response
        
        network = Network(test_network_config)
        
        with pytest.raises(ConstellationError, match="Metagraph transaction rejected"):
            network.submit_metagraph_transaction(signed_tx)


@pytest.mark.integration
@pytest.mark.mock
class TestNetworkErrorHandling:
    """Test network error handling and resilience."""
    
    @patch('constellation_sdk.network.requests.get')
    def test_timeout_error_handling(self, mock_get, test_network_config, alice_account):
        """Test handling of request timeouts."""
        # Setup mock timeout
        mock_get.side_effect = Exception("Request timeout")
        
        network = Network(test_network_config)
        
        with pytest.raises(ConstellationError, match="Request timeout"):
            network.get_balance(alice_account.address)
    
    @patch('constellation_sdk.network.requests.get')
    def test_malformed_json_response(self, mock_get, test_network_config, alice_account):
        """Test handling of malformed JSON responses."""
        # Setup mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        
        with pytest.raises(ConstellationError, match="Invalid JSON"):
            network.get_balance(alice_account.address)
    
    @patch('constellation_sdk.network.requests.get')
    def test_unexpected_response_format(self, mock_get, test_network_config, alice_account):
        """Test handling of unexpected response formats."""
        # Setup mock response with unexpected structure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'unexpected': 'format'}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        
        # Should handle gracefully and return appropriate default
        balance = network.get_balance(alice_account.address)
        assert balance == 0  # Default for missing balance data
    
    @patch('constellation_sdk.network.requests.post')
    def test_network_connection_lost(self, mock_post, test_network_config, alice_account, valid_dag_transaction_data):
        """Test handling of network connection loss during transaction."""
        # Setup signed transaction
        signed_tx = alice_account.sign_transaction(valid_dag_transaction_data)
        
        # Setup mock connection error
        mock_post.side_effect = ConnectionError("Network is unreachable")
        
        network = Network(test_network_config)
        
        with pytest.raises(ConstellationError, match="Network is unreachable"):
            network.submit_transaction(signed_tx)


@pytest.mark.integration
@pytest.mark.mock
class TestNetworkRetries:
    """Test network retry logic."""
    
    @patch('constellation_sdk.network.requests.get')
    def test_retry_on_temporary_failure(self, mock_get, test_network_config, alice_account):
        """Test retry logic on temporary failures."""
        # Setup mock responses: first fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.json.return_value = {'error': 'Service temporarily unavailable'}
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'data': {'balance': 50000000}}
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        network = Network(test_network_config)
        
        # Should retry and eventually succeed
        balance = network.get_balance(alice_account.address)
        assert balance == 50000000
        assert mock_get.call_count == 2


@pytest.mark.integration
@pytest.mark.mock
class TestNetworkPerformance:
    """Test network performance and optimization."""
    
    @patch('constellation_sdk.network.requests.get')
    def test_concurrent_balance_requests(self, mock_get, test_network_config, test_accounts):
        """Test handling of concurrent balance requests."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'balance': 100000000}}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        
        # Make multiple balance requests
        addresses = [account.address for account in test_accounts.values()]
        balances = []
        
        for address in addresses:
            balance = network.get_balance(address)
            balances.append(balance)
        
        # All should succeed
        assert all(balance == 100000000 for balance in balances)
        assert mock_get.call_count == len(addresses)
    
    @patch('constellation_sdk.network.requests.post')
    def test_batch_transaction_submission(self, mock_post, test_network_config, alice_account, valid_dag_addresses):
        """Test batch transaction submission performance."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'hash': 'batch_tx_hash'}
        mock_post.return_value = mock_response
        
        network = Network(test_network_config)
        
        # Create multiple transactions
        transactions = []
        for i, destination in enumerate(valid_dag_addresses):
            tx_data = {
                'source': alice_account.address,
                'destination': destination,
                'amount': (i + 1) * 10000000,
                'fee': 0,
                'salt': 1000 + i
            }
            signed_tx = alice_account.sign_transaction(tx_data)
            transactions.append(signed_tx)
        
        # Submit all transactions
        results = []
        for tx in transactions:
            result = network.submit_transaction(tx)
            results.append(result)
        
        # All should succeed
        assert len(results) == len(transactions)
        assert all(result['hash'] == 'batch_tx_hash' for result in results)


@pytest.mark.integration
@pytest.mark.mock
class TestNetworkEdgeCases:
    """Test network edge cases and boundary conditions."""
    
    @patch('constellation_sdk.network.requests.get')
    def test_empty_transaction_history(self, mock_get, test_network_config, alice_account):
        """Test handling of empty transaction history."""
        # Setup mock response with empty data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        transactions = network.get_transactions(alice_account.address)
        
        # Should return empty list
        assert transactions == []
    
    @patch('constellation_sdk.network.requests.get')
    def test_very_large_balance(self, mock_get, test_network_config, alice_account):
        """Test handling of very large balance values."""
        # Setup mock response with large balance
        large_balance = 2**53 - 1  # JavaScript safe integer
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'balance': large_balance}}
        mock_get.return_value = mock_response
        
        network = Network(test_network_config)
        balance = network.get_balance(alice_account.address)
        
        # Should handle large numbers correctly
        assert balance == large_balance
        assert isinstance(balance, int)
    
    def test_network_configuration_validation(self):
        """Test network configuration validation."""
        # Invalid configuration should raise error
        with pytest.raises(ConstellationError):
            Network(None)
        
        with pytest.raises(ConstellationError):
            Network("")
        
        with pytest.raises(ConstellationError):
            Network(123)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 