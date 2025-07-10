"""
Shared test fixtures for Constellation SDK tests.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from constellation_sdk import Account, Network, MetagraphClient, Transactions
from constellation_sdk.config import NetworkConfig


# =====================
# Account Fixtures
# =====================

@pytest.fixture
def alice_account():
    """Create a test account for Alice."""
    return Account()

@pytest.fixture  
def bob_account():
    """Create a test account for Bob."""
    return Account()

@pytest.fixture
def test_accounts(alice_account, bob_account):
    """Create multiple test accounts."""
    return {
        'alice': alice_account,
        'bob': bob_account,
        'charlie': Account()
    }

@pytest.fixture
def known_private_key():
    """A known private key for deterministic testing."""
    return "a1b2c3d4e5f67890123456789012345678901234567890abcdef123456789abcdef"

@pytest.fixture
def known_account(known_private_key):
    """Account with known private key for predictable testing."""
    return Account(known_private_key)


# =====================
# Network Configuration Fixtures
# =====================

@pytest.fixture
def test_network_config():
    """Test network configuration."""
    return NetworkConfig(
        name="test",
        network_version="3.0.0",
        be_url="https://test-be.constellation.io",
        l0_url="https://test-l0.constellation.io",
        l1_url="https://test-l1.constellation.io"
    )

@pytest.fixture
def mock_network_responses():
    """Mock network response data."""
    return {
        'node_info': {
            'version': '3.2.1-test',
            'id': 'test_node_id',
            'state': 'Ready'
        },
        'cluster_info': [
            {'id': 'node1', 'state': 'Ready', 'ip': '192.168.1.1'},
            {'id': 'node2', 'state': 'Ready', 'ip': '192.168.1.2'},
            {'id': 'node3', 'state': 'Ready', 'ip': '192.168.1.3'}
        ],
        'balance_response': {
            'data': {'balance': 100000000}
        },
        'transactions_response': {
            'data': [
                {
                    'source': 'DAG123test',
                    'destination': 'DAG456test', 
                    'amount': 50000000,
                    'fee': 0,
                    'timestamp': '2024-01-15T10:30:00Z'
                },
                {
                    'source': 'DAG789test',
                    'destination': 'DAG123test',
                    'amount': 25000000,
                    'fee': 0,
                    'timestamp': '2024-01-15T10:31:00Z'
                }
            ]
        }
    }


# =====================
# Metagraph Fixtures
# =====================

@pytest.fixture
def mock_metagraph_responses():
    """Mock metagraph response data."""
    return {
        'currency_response': {
            'data': [
                {
                    'id': 'DAG7Ghth1WhWK83SB3MtXnnHYZbCsm1234567890',
                    'timestamp': '2024-01-15T08:00:00Z'
                },
                {
                    'id': 'DAG8Ijui2XiXL94TC4OuYZcDtn2345678901',
                    'timestamp': '2024-01-15T09:00:00Z'
                }
            ]
        },
        'metagraph_balance': {
            'data': {'balance': 0}
        }
    }

@pytest.fixture
def test_metagraph_id():
    """Test metagraph ID."""
    return "DAG7Ghth1WhWK83SB3MtXnnHYZbCsm1234567890"

@pytest.fixture
def test_sensor_data():
    """Test sensor data for metagraph transactions."""
    return {
        'sensor_type': 'temperature',
        'value': 25.7,
        'location': 'warehouse_a',
        'timestamp': '2024-01-15T10:30:00Z',
        'device_id': 'sensor_001'
    }


# =====================
# Transaction Fixtures  
# =====================

@pytest.fixture
def valid_dag_transaction_data(alice_account, bob_account):
    """Valid DAG transaction data."""
    return {
        'source': alice_account.address,
        'destination': bob_account.address,
        'amount': 100000000,  # 1 DAG
        'fee': 0,
        'salt': 12345
    }

@pytest.fixture
def valid_token_transfer_data(alice_account, bob_account, test_metagraph_id):
    """Valid metagraph token transfer data."""
    return {
        'source': alice_account.address,
        'destination': bob_account.address,
        'amount': 1000000000,  # 10 tokens
        'fee': 0,
        'metagraph_id': test_metagraph_id,
        'salt': 54321
    }

@pytest.fixture
def valid_data_submission_data(alice_account, test_metagraph_id, test_sensor_data):
    """Valid metagraph data submission data."""
    return {
        'source': alice_account.address,
        'destination': alice_account.address,
        'data': test_sensor_data,
        'metagraph_id': test_metagraph_id,
        'timestamp': 1642248600,
        'salt': 98765
    }


# =====================
# Mock Network Objects
# =====================

@pytest.fixture
def mock_network(test_network_config, mock_network_responses):
    """Mock Network object with patched requests."""
    with patch('constellation_sdk.network.requests') as mock_requests:
        network = Network(test_network_config)
        
        # Configure mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_network_responses['node_info']
        mock_requests.get.return_value = mock_response
        
        yield network, mock_requests

@pytest.fixture
def mock_metagraph_client(mock_metagraph_responses):
    """Mock MetagraphClient with patched requests."""
    with patch('constellation_sdk.metagraph.requests') as mock_requests:
        client = MetagraphClient('testnet')
        
        # Configure mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_metagraph_responses['currency_response']
        mock_requests.get.return_value = mock_response
        
        yield client, mock_requests


# =====================
# Address Fixtures
# =====================

@pytest.fixture
def valid_dag_addresses():
    """Valid DAG addresses for testing."""
    return [
        "DAG4J6gixVGKYmcZs9Wmkyrv8ERp39vxtjwbjV5Q",
        "DAG3Q4LkJWcdw12nzTRE5hpAZgQiAWQSFYFYUJVw",
        "DAG7Ghth1WhWK83SB3MtXnnHYZbCsm89LdZMzBw2"
    ]

@pytest.fixture
def invalid_dag_addresses():
    """Invalid DAG addresses for testing."""
    return [
        "DAG",  # Too short
        "INVALID_ADDRESS",  # Wrong format
        "DAG123",  # Too short
        "DAG" + "x" * 40,  # Too long
        "BTC4J6gixVGKYmcZs9Wmkyrv8ERp39vxtjwbjV5Q",  # Wrong prefix
        "",  # Empty string
        None,  # None value
        123,  # Wrong type
    ]


# =====================
# Error Testing Fixtures
# =====================

@pytest.fixture
def network_error_scenarios():
    """Network error scenarios for testing."""
    return {
        'timeout': {'side_effect': Exception('Connection timeout')},
        'http_404': {'status_code': 404, 'json': lambda: {'error': 'Not found'}},
        'http_500': {'status_code': 500, 'json': lambda: {'error': 'Server error'}},
        'malformed_json': {'status_code': 200, 'json': lambda: None},
        'connection_error': {'side_effect': ConnectionError('Network unreachable')}
    }


# =====================
# Performance Testing Fixtures
# =====================

@pytest.fixture
def large_batch_transfers(test_accounts, valid_dag_addresses):
    """Large batch of transfers for performance testing."""
    transfers = []
    for i in range(100):
        transfers.append({
            'destination': valid_dag_addresses[i % len(valid_dag_addresses)],
            'amount': (i + 1) * 1000000  # Varying amounts
        })
    return transfers


# =====================
# Utility Fixtures
# =====================

@pytest.fixture
def transaction_validator():
    """Helper for transaction validation testing."""
    def validate_transaction_structure(tx, tx_type='dag'):
        """Validate transaction has required structure."""
        if tx_type == 'dag':
            required_fields = ['source', 'destination', 'amount', 'fee', 'salt']
        elif tx_type == 'token':
            required_fields = ['source', 'destination', 'amount', 'fee', 'salt', 'metagraph_id']
        elif tx_type == 'data':
            required_fields = ['source', 'destination', 'data', 'metagraph_id', 'timestamp', 'salt']
        else:
            raise ValueError(f"Unknown transaction type: {tx_type}")
        
        return all(field in tx for field in required_fields)
    
    return validate_transaction_structure

@pytest.fixture
def signature_validator():
    """Helper for signature validation testing."""
    def validate_signature_structure(signed_tx):
        """Validate signed transaction has required structure."""
        return (
            'value' in signed_tx and
            'proofs' in signed_tx and
            isinstance(signed_tx['proofs'], list) and
            len(signed_tx['proofs']) > 0 and
            'id' in signed_tx['proofs'][0] and
            'signature' in signed_tx['proofs'][0]
        )
    
    return validate_signature_structure


# =====================
# Test Categories
# =====================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network connectivity"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "mock: mark test as using mock objects"
    ) 