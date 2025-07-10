"""
Comprehensive integration tests for Network functionality - FIXED VERSION.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from constellation_sdk import ConstellationError
from constellation_sdk.config import NetworkConfig
from constellation_sdk.network import Network


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

    @patch("constellation_sdk.network.requests.request")
    def test_get_node_info_success(
        self, mock_request, test_network_config, mock_network_responses
    ):
        """Test successful node info retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses["node_info"]
        mock_request.return_value = mock_response

        network = Network(test_network_config)
        node_info = network.get_node_info()

        # Validate request
        mock_request.assert_called_once()
        assert test_network_config.l1_url in str(mock_request.call_args)

        # Validate response
        assert node_info["version"] == "3.2.1-test"
        assert node_info["id"] == "test_node_id"
        assert node_info["state"] == "Ready"

    @patch("constellation_sdk.network.requests.request")
    def test_get_node_info_http_error(
        self, mock_request, test_network_config, network_error_scenarios
    ):
        """Test node info retrieval with HTTP error."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server error"}
        mock_request.return_value = mock_response

        network = Network(test_network_config)

        with pytest.raises(ConstellationError, match="HTTP 500"):
            network.get_node_info()

    @patch("constellation_sdk.network.requests.request")
    def test_get_node_info_connection_error(self, mock_request, test_network_config):
        """Test node info retrieval with connection error."""
        # Setup mock connection error
        mock_request.side_effect = ConnectionError("Network unreachable")

        network = Network(test_network_config)

        with pytest.raises(ConstellationError, match="Network unreachable"):
            network.get_node_info()

    @patch("constellation_sdk.network.requests.request")
    def test_get_cluster_info_success(
        self, mock_request, test_network_config, mock_network_responses
    ):
        """Test successful cluster info retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses["cluster_info"]
        mock_request.return_value = mock_response

        network = Network(test_network_config)
        cluster_info = network.get_cluster_info()

        # Validate response
        assert isinstance(cluster_info, list)
        assert len(cluster_info) == 3
        assert cluster_info[0]["id"] == "node1"
        assert cluster_info[0]["state"] == "Ready"
        assert cluster_info[0]["ip"] == "192.168.1.1"


@pytest.mark.integration
@pytest.mark.mock
class TestBalanceOperations:
    """Test balance retrieval operations."""

    @patch("constellation_sdk.network.requests.request")
    def test_get_balance_success(
        self, mock_request, test_network_config, mock_network_responses, alice_account
    ):
        """Test successful balance retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses["balance_response"]
        mock_request.return_value = mock_response

        network = Network(test_network_config)
        balance = network.get_balance(alice_account.address)

        # Validate request
        mock_request.assert_called_once()
        assert alice_account.address in str(mock_request.call_args)

        # Validate response
        assert balance == 100000000

    @patch("constellation_sdk.network.requests.request")
    def test_get_balance_address_not_found(self, mock_request, test_network_config):
        """Test balance retrieval for non-existent address."""
        # Setup mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Address not found"}
        mock_request.return_value = mock_response

        network = Network(test_network_config)
        balance = network.get_balance("DAG_NON_EXISTENT_ADDRESS")

        # Should return 0 for non-existent addresses
        assert balance == 0

    @patch("constellation_sdk.network.requests.request")
    def test_get_balance_invalid_address(
        self, mock_request, test_network_config, invalid_dag_addresses
    ):
        """Test balance retrieval with invalid address format."""
        network = Network(test_network_config)

        for invalid_address in invalid_dag_addresses[
            :5
        ]:  # Test subset to avoid long test
            if invalid_address is not None and invalid_address != 123:
                with pytest.raises(ConstellationError):
                    network.get_balance(invalid_address)


@pytest.mark.integration
@pytest.mark.mock
class TestTransactionOperations:
    """Test transaction submission and retrieval."""

    @patch("constellation_sdk.network.requests.request")
    def test_submit_transaction_success(
        self,
        mock_request,
        test_network_config,
        alice_account,
        valid_dag_transaction_data,
        signature_validator,
    ):
        """Test successful transaction submission."""
        # Setup signed transaction
        signed_tx = alice_account.sign_transaction(valid_dag_transaction_data)

        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"hash": "tx_hash_123"}
        mock_request.return_value = mock_response

        network = Network(test_network_config)
        result = network.submit_transaction(signed_tx)

        # Validate request
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert test_network_config.l1_url in str(call_args)

        # Validate request data
        request_data = call_args[1]["json"]
        assert signature_validator(request_data)

        # Validate response
        assert result["hash"] == "tx_hash_123"
