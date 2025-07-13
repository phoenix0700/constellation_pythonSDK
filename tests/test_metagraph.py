"""
Comprehensive integration tests for MetagraphClient functionality.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from constellation_sdk import ConstellationError
from constellation_sdk.metagraph import MetagraphClient
import time


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphClientInitialization:
    """Test metagraph client initialization."""

    def test_client_creation_mainnet(self):
        """Test creating client for mainnet."""
        client = MetagraphClient("mainnet")

        assert client.network_name == "mainnet"
        assert (
            "mainnet" in client.base_url.lower()
            or "constellation.io" in client.base_url
        )

    def test_client_creation_testnet(self):
        """Test creating client for testnet."""
        client = MetagraphClient("testnet")

        assert client.network_name == "testnet"
        assert "testnet" in client.base_url.lower()

    def test_client_creation_invalid_network(self):
        """Test creating client with invalid network."""
        with pytest.raises(ConstellationError):
            MetagraphClient("invalid_network")


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphDiscovery:
    """Test metagraph discovery functionality."""

    @patch("constellation_sdk.metagraph.requests.get")
    def test_discover_metagraphs_success(self, mock_get, mock_metagraph_responses):
        """Test successful metagraph discovery."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metagraph_responses["currency_response"]
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        metagraphs = client.discover_metagraphs()

        # Validate request
        mock_get.assert_called_once()
        call_args = str(mock_get.call_args)
        assert "currency" in call_args.lower()

        # Validate specific metagraph in response
        assert len(metagraphs) == 2
        assert metagraphs[0]["id"] == "DAG31fddd28e278f8086f52cbd40abe08a8692"
        assert metagraphs[0]["network"] == "testnet"

    @patch("constellation_sdk.metagraph.requests.get")
    def test_discover_metagraphs_empty_result(self, mock_get):
        """Test metagraph discovery with no results."""
        # Setup mock response with empty data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        metagraphs = client.discover_metagraphs()

        # Should return empty list
        assert isinstance(metagraphs, list)
        assert len(metagraphs) == 0

    @patch("constellation_sdk.metagraph.requests.get")
    def test_discover_metagraphs_http_error(self, mock_get):
        """Test metagraph discovery with HTTP error."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server error"}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        with pytest.raises(ConstellationError, match="Error discovering metagraphs"):
            client.discover_metagraphs()

    @patch("constellation_sdk.metagraph.requests.get")
    def test_discover_metagraphs_connection_error(self, mock_get):
        """Test metagraph discovery with connection error."""
        # Setup mock connection error
        mock_get.side_effect = ConnectionError("Network unreachable")

        client = MetagraphClient("testnet")

        with pytest.raises(ConstellationError, match="Network unreachable"):
            client.discover_metagraphs()

    @patch("constellation_sdk.metagraph.requests.get")
    def test_discover_metagraphs_with_limit(self, mock_get, mock_metagraph_responses):
        """Test metagraph discovery with limit parameter."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metagraph_responses["currency_response"]
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        metagraphs = client.discover_metagraphs(limit=10)

        # Validate limit parameter in request
        call_args = str(mock_get.call_args)
        assert "limit=10" in call_args or "10" in call_args


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphBalanceOperations:
    """Test metagraph balance operations."""

    @patch("constellation_sdk.metagraph.requests.get")
    def test_get_metagraph_balance_success(
        self, mock_get, alice_account, test_metagraph_id
    ):
        """Test successful metagraph balance retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"balance": 1500000000}}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        balance = client.get_balance(alice_account.address, test_metagraph_id)

        # Validate request
        mock_get.assert_called_once()
        call_args = str(mock_get.call_args)
        assert alice_account.address in call_args
        assert test_metagraph_id in call_args

        # Validate response
        assert balance == 1500000000

    @patch("constellation_sdk.metagraph.requests.get")
    def test_get_metagraph_balance_address_not_found(self, mock_get, test_metagraph_id):
        """Test metagraph balance for non-existent address."""
        # Setup mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Address not found"}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        balance = client.get_balance("DAG_NON_EXISTENT_ADDRESS", test_metagraph_id)

        # Should return 0 for non-existent addresses
        assert balance == 0

    @patch("constellation_sdk.metagraph.requests.get")
    def test_get_metagraph_balance_invalid_metagraph(self, mock_get, alice_account):
        """Test metagraph balance with invalid metagraph ID."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid metagraph ID"}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        with pytest.raises(ConstellationError, match="Invalid metagraph ID"):
            client.get_balance(alice_account.address, "INVALID_METAGRAPH_ID")

    @patch("constellation_sdk.metagraph.requests.get")
    def test_get_metagraph_balance_validation_errors(
        self, alice_account, test_metagraph_id, invalid_dag_addresses
    ):
        """Test metagraph balance with invalid inputs."""
        client = MetagraphClient("testnet")

        # Test invalid address formats
        for invalid_address in invalid_dag_addresses[:3]:  # Test subset
            if invalid_address is not None and invalid_address != 123:
                with pytest.raises(ConstellationError):
                    client.get_balance(invalid_address, test_metagraph_id)

        # Test invalid metagraph ID formats
        invalid_metagraph_ids = ["", "INVALID", "DAG123", None, 123]
        for invalid_id in invalid_metagraph_ids:
            if invalid_id is not None and invalid_id != 123:
                with pytest.raises(ConstellationError):
                    client.get_balance(alice_account.address, invalid_id)


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphTransactionHistory:
    """Test metagraph transaction history operations."""

    @patch("constellation_sdk.metagraph.requests.get")
    def test_get_metagraph_transactions_success(
        self, mock_get, alice_account, test_metagraph_id
    ):
        """Test successful metagraph transaction history retrieval."""
        # Setup mock response with transaction data
        mock_transactions = {
            "data": [
                {
                    "source": alice_account.address,
                    "destination": "DAG456test",
                    "amount": 1000000000,
                    "metagraph_id": test_metagraph_id,
                    "timestamp": "2024-01-15T10:30:00Z",
                    "type": "token_transfer",
                },
                {
                    "source": alice_account.address,
                    "destination": alice_account.address,
                    "data": {"sensor": "temp", "value": 25.5},
                    "metagraph_id": test_metagraph_id,
                    "timestamp": "2024-01-15T10:31:00Z",
                    "type": "data_submission",
                },
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_transactions
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        transactions = client.get_transactions(alice_account.address, test_metagraph_id)

        # Validate request
        mock_get.assert_called_once()
        call_args = str(mock_get.call_args)
        assert alice_account.address in call_args
        assert test_metagraph_id in call_args

        # Validate response
        assert isinstance(transactions, list)
        assert len(transactions) == 2
        assert transactions[0]["source"] == alice_account.address
        assert transactions[0]["type"] == "token_transfer"
        assert transactions[1]["type"] == "data_submission"
        assert "data" in transactions[1]

    @patch("constellation_sdk.metagraph.requests.get")
    def test_get_metagraph_transactions_with_limit(
        self, mock_get, alice_account, test_metagraph_id
    ):
        """Test metagraph transaction history with limit."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        client.get_transactions(alice_account.address, test_metagraph_id, limit=5)

        # Validate limit parameter in request
        call_args = str(mock_get.call_args)
        assert "limit=5" in call_args or "5" in call_args

    @patch("constellation_sdk.metagraph.requests.get")
    def test_get_metagraph_transactions_empty_history(
        self, mock_get, alice_account, test_metagraph_id
    ):
        """Test metagraph transaction history for address with no transactions."""
        # Setup mock response with empty data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        transactions = client.get_transactions(alice_account.address, test_metagraph_id)

        # Should return empty list
        assert transactions == []


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphDataQueries:
    """Test metagraph data query operations."""

    @patch("constellation_sdk.metagraph.requests.get")
    def test_query_metagraph_data_success(self, mock_get, test_metagraph_id):
        """Test successful metagraph data query."""
        # Setup mock response with data
        mock_data = {
            "data": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "data": {"sensor_type": "temperature", "value": 25.7},
                    "source": "DAG123sensor",
                },
                {
                    "timestamp": "2024-01-15T10:31:00Z",
                    "data": {"sensor_type": "humidity", "value": 65.2},
                    "source": "DAG456sensor",
                },
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        data = client.query_data(test_metagraph_id)

        # Validate request
        mock_get.assert_called_once()
        call_args = str(mock_get.call_args)
        assert test_metagraph_id in call_args

        # Validate response
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["data"]["sensor_type"] == "temperature"
        assert data[1]["data"]["sensor_type"] == "humidity"

    @patch("constellation_sdk.metagraph.requests.get")
    def test_query_metagraph_data_with_filters(self, mock_get, test_metagraph_id):
        """Test metagraph data query with filters."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        # Query with various filters
        filters = {
            "start_time": "2024-01-15T00:00:00Z",
            "end_time": "2024-01-15T23:59:59Z",
            "source": "DAG123sensor",
            "limit": 10,
        }

        client.query_data(test_metagraph_id, **filters)

        # Validate filters in request
        call_args = str(mock_get.call_args)
        assert "start_time" in call_args
        assert "end_time" in call_args
        assert "DAG123sensor" in call_args
        assert "limit=10" in call_args or "10" in call_args

    @patch("constellation_sdk.metagraph.requests.get")
    def test_query_metagraph_data_no_results(self, mock_get, test_metagraph_id):
        """Test metagraph data query with no results."""
        # Setup mock response with empty data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        data = client.query_data(test_metagraph_id)

        # Should return empty list
        assert data == []


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphErrorHandling:
    """Test metagraph client error handling."""

    @patch("constellation_sdk.metagraph.requests.get")
    def test_timeout_error_handling(self, mock_get, alice_account, test_metagraph_id):
        """Test handling of request timeouts."""
        # Setup mock timeout
        mock_get.side_effect = Exception("Request timeout")

        client = MetagraphClient("testnet")

        with pytest.raises(ConstellationError, match="Request timeout"):
            client.get_balance(alice_account.address, test_metagraph_id)

    @patch("constellation_sdk.metagraph.requests.get")
    def test_malformed_json_response(self, mock_get, alice_account, test_metagraph_id):
        """Test handling of malformed JSON responses."""
        # Setup mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        with pytest.raises(ConstellationError, match="Invalid JSON"):
            client.get_balance(alice_account.address, test_metagraph_id)

    @patch("constellation_sdk.metagraph.requests.get")
    def test_unexpected_response_structure(
        self, mock_get, alice_account, test_metagraph_id
    ):
        """Test handling of unexpected response structures."""
        # Setup mock response with unexpected structure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "structure"}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        # Should handle gracefully and return appropriate default
        balance = client.get_balance(alice_account.address, test_metagraph_id)
        assert balance == 0  # Default for missing balance data

    @patch("constellation_sdk.metagraph.requests.get")
    def test_metagraph_not_found(self, mock_get, alice_account):
        """Test handling of non-existent metagraph."""
        # Setup mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Metagraph not found"}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        with pytest.raises(ConstellationError, match="Metagraph not found"):
            client.get_balance(alice_account.address, "DAG_NONEXISTENT_METAGRAPH")


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphPerformance:
    """Test metagraph client performance."""

    @patch("constellation_sdk.metagraph.requests.get")
    def test_concurrent_balance_requests(
        self, mock_get, test_accounts, test_metagraph_id
    ):
        """Test handling of concurrent balance requests."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"balance": 500000000}}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        # Make multiple balance requests
        addresses = [account.address for account in test_accounts.values()]
        balances = []

        for address in addresses:
            balance = client.get_balance(address, test_metagraph_id)
            balances.append(balance)

        # All should succeed
        assert all(balance == 500000000 for balance in balances)
        assert mock_get.call_count == len(addresses)

    @patch("constellation_sdk.metagraph.requests.get")
    def test_multiple_metagraph_discovery(self, mock_get, mock_metagraph_responses):
        """Test multiple metagraph discovery requests."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metagraph_responses["currency_response"]
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")

        # Make multiple discovery requests
        results = []
        for _ in range(3):
            metagraphs = client.discover_metagraphs()
            results.append(metagraphs)

        # All should return consistent results
        assert all(len(result) == 2 for result in results)
        assert mock_get.call_count == 3


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphEdgeCases:
    """Test metagraph client edge cases."""

    @patch("constellation_sdk.metagraph.requests.get")
    def test_very_large_metagraph_balance(
        self, mock_get, alice_account, test_metagraph_id
    ):
        """Test handling of very large metagraph balance values."""
        # Setup mock response with large balance
        large_balance = 2**53 - 1  # JavaScript safe integer
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"balance": large_balance}}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        balance = client.get_balance(alice_account.address, test_metagraph_id)

        # Should handle large numbers correctly
        assert balance == large_balance
        assert isinstance(balance, int)

    @patch("constellation_sdk.metagraph.requests.get")
    def test_large_data_query_result(self, mock_get, test_metagraph_id):
        """Test handling of large data query results."""
        # Setup mock response with large data set
        large_data = {
            "data": [
                {
                    "timestamp": f"2024-01-15T{i:02d}:00:00Z",
                    "data": {"sensor_id": i, "value": i * 1.5},
                    "source": f"DAG{i}sensor",
                }
                for i in range(1000)  # Large number of entries
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = large_data
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        data = client.query_data(test_metagraph_id)

        # Should handle large data sets
        assert len(data) == 1000
        assert data[0]["data"]["sensor_id"] == 0
        assert data[999]["data"]["sensor_id"] == 999

    def test_metagraph_client_string_representation(self):
        """Test string representation of metagraph client."""
        client = MetagraphClient("testnet")
        client_str = str(client)

        # Should contain useful information
        assert "testnet" in client_str.lower() or "MetagraphClient" in client_str

    def test_invalid_method_calls(self):
        """Test calling methods with invalid parameters."""
        client = MetagraphClient("testnet")

        # Test with None parameters
        with pytest.raises(ConstellationError):
            client.get_balance(None, "DAG123")

        with pytest.raises(ConstellationError):
            client.get_balance("DAG123", None)

        with pytest.raises(ConstellationError):
            client.query_data(None)


@pytest.mark.integration
@pytest.mark.mock
class TestMetagraphSubmissions:
    """Tests for new submission and status features."""

    @pytest.fixture
    def client(self):
        """Fixture for a MetagraphClient with a mocked network object."""
        with patch("constellation_sdk.metagraph.Network") as MockNetwork:
            client = MetagraphClient("testnet")
            client.network = MockNetwork()
            return client

    def test_submit_transaction_success(self, client):
        """Test successful transaction submission."""
        signed_tx = {"value": "some_tx_data", "proofs": []}
        expected_hash = {"hash": "tx_hash_abc"}
        client.network.submit_transaction.return_value = expected_hash

        result = client.submit_transaction(signed_tx)

        client.network.submit_transaction.assert_called_once_with(signed_tx)
        assert result == expected_hash

    def test_get_transaction_status_confirmed(self, client):
        """Test confirmed transaction status."""
        tx_hash = "confirmed_hash"
        client.network.get_transaction.return_value = {"blockHash": "some_block_hash"}

        status = client.get_transaction_status(tx_hash)

        client.network.get_transaction.assert_called_once_with(tx_hash)
        assert status == "confirmed"

    def test_get_transaction_status_pending(self, client):
        """Test pending transaction status."""
        tx_hash = "pending_hash"
        client.network.get_transaction.return_value = {"blockHash": None}

        status = client.get_transaction_status(tx_hash)
        assert status == "pending"

    def test_get_transaction_status_not_found(self, client):
        """Test not_found transaction status."""
        tx_hash = "not_found_hash"
        client.network.get_transaction.return_value = None

        status = client.get_transaction_status(tx_hash)
        assert status == "not_found"

    @patch("time.sleep", return_value=None)
    def test_wait_for_confirmation_success(self, mock_sleep, client):
        """Test successful wait for transaction confirmation."""
        tx_hash = "wait_success_hash"
        pending_tx = {"blockHash": None}
        confirmed_tx = {"blockHash": "block_hash_xyz"}

        # Simulate transaction being pending then confirmed
        client.network.get_transaction.side_effect = [pending_tx, confirmed_tx]

        result = client.wait_for_confirmation(tx_hash, poll_interval=0)

        assert client.network.get_transaction.call_count == 2
        assert result == confirmed_tx

    @patch("time.sleep", return_value=None)
    def test_wait_for_confirmation_timeout(self, mock_sleep, client):
        """Test timeout during wait for confirmation."""
        tx_hash = "wait_timeout_hash"
        client.network.get_transaction.return_value = {"blockHash": None}

        with pytest.raises(ConstellationError, match="not confirmed after"):
            client.wait_for_confirmation(tx_hash, timeout=0.1, poll_interval=0.05)

    @patch("requests.get")
    def test_get_custom_state_success(self, mock_get):
        """Test successful custom state retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"my_key": "my_value"}}
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        state = client.get_custom_state("metagraph123", "my_key")

        assert state == {"my_key": "my_value"}
        mock_get.assert_called_once()
        assert "state/my_key" in mock_get.call_args[0][0]

    @patch("requests.get")
    def test_get_custom_state_not_found(self, mock_get):
        """Test custom state retrieval when key not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = MetagraphClient("testnet")
        state = client.get_custom_state("metagraph123", "not_found_key")

        assert state is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
