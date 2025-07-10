"""
Network interface for Constellation Network.
Handles API calls, balance queries, and transaction submission.
"""

import requests
from typing import Dict, Any, List, Optional
from .config import DEFAULT_CONFIGS, NetworkConfig


class NetworkError(Exception):
    """Exception for network-related errors."""
    pass


class Network:
    """
    Constellation Network interface.
    
    Example:
        >>> network = Network('testnet')
        >>> balance = network.get_balance('DAG4J6gixVGKYmcZs9Wmkyrv8ERp39vxtjwbjV5Q')
        >>> print(f"Balance: {balance/1e8} DAG")
    """
    
    def __init__(self, network_or_config):
        """
        Initialize network connection.
        
        Args:
            network_or_config: Network name ('mainnet', 'testnet', 'integrationnet') 
                             or NetworkConfig object
        """
        if isinstance(network_or_config, str):
            if network_or_config not in DEFAULT_CONFIGS:
                raise NetworkError(f"Unknown network: {network_or_config}")
            # DEFAULT_CONFIGS contains NetworkConfig objects, just use directly
            self.config = DEFAULT_CONFIGS[network_or_config]
        elif isinstance(network_or_config, NetworkConfig):
            self.config = network_or_config
        else:
            raise NetworkError(f"Invalid network configuration type: {type(network_or_config)}")
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            return response
        except requests.RequestException as e:
            raise NetworkError(f"Network request failed: {e}")
    
    def get_balance(self, address: str) -> int:
        """
        Get address balance in Datolites (1 DAG = 1e8 Datolites).
        
        Args:
            address: DAG address
            
        Returns:
            Balance in Datolites
        """
        url = f"{self.config.be_url}/addresses/{address}/balance"
        response = self._make_request(url)
        
        if response.status_code == 200:
            return response.json()['data']['balance']
        elif response.status_code == 404:
            return 0  # Address not found = zero balance
        else:
            raise NetworkError(f"Balance query failed: {response.status_code}")
    
    def get_cluster_info(self) -> List[Dict[str, Any]]:
        """Get information about network cluster nodes."""
        url = f"{self.config.l1_url}/cluster/info"
        response = self._make_request(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise NetworkError(f"Cluster info failed: {response.status_code}")
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about the connected node."""
        url = f"{self.config.l1_url}/node/info"
        response = self._make_request(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise NetworkError(f"Node info failed: {response.status_code}")
    
    def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent transactions from the network.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction data
        """
        url = f"{self.config.be_url}/transactions"
        response = self._make_request(url, params={'limit': limit})
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            raise NetworkError(f"Transaction query failed: {response.status_code}")
    
    def submit_transaction(self, signed_transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a signed transaction to the network.
        
        Args:
            signed_transaction: Signed transaction from Account.sign_transaction()
            
        Returns:
            Transaction submission result
            
        Note:
            Requires funded address. Use TestNet faucet to fund addresses for testing.
        """
        url = f"{self.config.l1_url}/transactions"
        response = self._make_request(
            url, 
            method='POST',
            json=signed_transaction,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise NetworkError(f"Invalid transaction: {response.text}")
        elif response.status_code == 500:
            # Common for unfunded addresses
            raise NetworkError("Transaction failed - check address balance and parent references")
        else:
            raise NetworkError(f"Transaction submission failed: {response.status_code}")
    
    def validate_address(self, address: str) -> bool:
        """Validate DAG address format."""
        return (
            isinstance(address, str) and 
            address.startswith('DAG') and 
            len(address) == 38 and
            all(c in '0123456789ABCDEFabcdef' for c in address[3:])
        ) 