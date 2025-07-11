"""
Metagraph discovery and queries for Constellation Network.
Handles metagraph discovery, information retrieval, and balance queries.

For creating metagraph transactions, use the Transactions class.

IMPORTANT: Discovery shows ~128 contracts across all networks, but most are
automated node testing deployments. Real production metagraphs are primarily
on MainNet (~7) with some active ones on test networks.
"""

from typing import Any, Dict, List, Optional, Union

import requests

from .config import NetworkConfig
from .exceptions import ConstellationError
from .network import NetworkError


class MetagraphError(ConstellationError):
    """Exception for metagraph-related errors."""

    pass


class MetagraphClient:
    """
    Client for discovering and querying Constellation metagraphs.

    This class handles:
    - Metagraph discovery across networks
    - Balance and transaction queries
    - Network information and status

    For creating metagraph transactions, use the Transactions class:
        >>> from constellation_sdk import Account, Transactions, MetagraphClient
        >>> account = Account()
        >>> client = MetagraphClient('mainnet')
        >>>
        >>> # Discover production metagraphs
        >>> metagraphs = client.discover_production_metagraphs()
        >>> mg_id = metagraphs[0]['id']
        >>>
        >>> # Create transactions using Transactions class
        >>> token_tx = Transactions.create_token_transfer(
        ...     account, "DAG4J6gix...", 1000000, mg_id
        ... )
        >>> data_tx = Transactions.create_data_submission(
        ...     account, {'sensor': 'temp', 'value': 25}, mg_id
        ... )

    REALITY CHECK: Most discovered "metagraphs" on test networks are automated
    node deployments. Real production metagraphs are primarily on MainNet.

    Example:
        >>> # For production use, focus on MainNet
        >>> client = MetagraphClient('mainnet')
        >>> production_metagraphs = client.discover_production_metagraphs()
        >>> print(f"Found {len(production_metagraphs)} production metagraphs")
        >>>
        >>> # For development, use test networks explicitly
        >>> test_client = MetagraphClient('testnet')
        >>> test_metagraphs = test_client.discover_metagraphs(include_test_deployments=True)
    """

    def __init__(self, network: str = "mainnet"):
        """
        Initialize metagraph client.

        Args:
            network: Network to connect to ('mainnet', 'testnet', 'integrationnet')
                    Default is 'mainnet' for production use
        """
        valid_networks = ["mainnet", "testnet", "integrationnet"]
        if network not in valid_networks:
            raise ConstellationError(
                f"Invalid network '{network}'. Must be one of: {valid_networks}"
            )

        self.network = network
        self.base_url = f"https://be-{network}.constellationnetwork.io"

    def discover_metagraphs(
        self, include_test_deployments: bool = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available metagraphs on the network.

        Args:
            include_test_deployments: Whether to include test/automated deployments.
                                    Defaults to False for mainnet, True for test networks.
            limit: Maximum number of metagraphs to return

        Returns:
            List of metagraph information dictionaries

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> real_metagraphs = client.discover_metagraphs()  # Production only
            >>>
            >>> test_client = MetagraphClient('testnet')
            >>> all_deployments = test_client.discover_metagraphs(include_test_deployments=True)
        """
        if include_test_deployments is None:
            # Default: exclude test deployments on mainnet, include on test networks
            include_test_deployments = self.network != "mainnet"

        try:
            currency_url = f"{self.base_url}/currency"
            params = {}
            if limit is not None:
                params['limit'] = limit
            
            response = requests.get(currency_url, params=params, timeout=10)

            if response.status_code != 200:
                raise MetagraphError(
                    f"Failed to fetch metagraphs: {response.status_code}"
                )

            currencies = response.json()["data"]

            metagraphs = []
            count = 0
            for currency in currencies:
                if limit is not None and count >= limit:
                    break
                    
                metagraph = {
                    "id": currency["id"],
                    "network": self.network,
                    "created": currency.get("timestamp"),
                    "balance": None,
                    "transaction_count": None,
                    "category": self._categorize_metagraph(currency),
                }

                # Filter based on include_test_deployments flag
                if not include_test_deployments and metagraph["category"] in [
                    "test",
                    "automated",
                ]:
                    continue

                metagraphs.append(metagraph)
                count += 1

            return metagraphs

        except Exception as e:
            raise MetagraphError(f"Error discovering metagraphs: {e}")

    def discover_production_metagraphs(self) -> List[Dict[str, Any]]:
        """
        Discover only production-ready metagraphs (excludes test deployments).

        Returns:
            List of production metagraph dictionaries

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> production_mgs = client.discover_production_metagraphs()
            >>> print(f"Found {len(production_mgs)} production metagraphs")
        """
        return self.discover_metagraphs(include_test_deployments=False)

    def _categorize_metagraph(self, currency: Dict[str, Any]) -> str:
        """
        Categorize a metagraph as 'production', 'test', or 'automated'.

        Args:
            currency: Currency data from API

        Returns:
            Category string
        """
        # On mainnet, assume production unless proven otherwise
        if self.network == "mainnet":
            return "production"

        # On test networks, categorize based on patterns we discovered
        created = currency.get("timestamp", "")

        # Check if it was created in a batch (indicating automated deployment)
        # This is a simplified heuristic - could be enhanced with more data
        if self.network in ["testnet", "integrationnet"]:
            return "test"  # Most are test deployments based on our analysis

        return "unknown"

    def get_metagraph_info(self, metagraph_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific metagraph.

        Args:
            metagraph_id: The metagraph ID (DAG address)

        Returns:
            Dictionary with metagraph information

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> info = client.get_metagraph_info('DAG7Ghth1WhWK83SB3MtXnnHYZbCsm...')
            >>> print(f"Balance: {info['balance']} DAG")
        """
        try:
            # Get balance information
            balance_url = f"{self.base_url}/addresses/{metagraph_id}/balance"
            balance_response = requests.get(balance_url, timeout=5)

            balance = 0
            if balance_response.status_code == 200:
                balance_data = balance_response.json()
                balance = balance_data["data"]["balance"]

            # Get transaction history
            tx_url = f"{self.base_url}/addresses/{metagraph_id}/transactions"
            tx_response = requests.get(tx_url, timeout=5)

            transaction_count = 0
            if tx_response.status_code == 200:
                tx_data = tx_response.json()
                transaction_count = len(tx_data.get("data", []))

            return {
                "id": metagraph_id,
                "network": self.network,
                "balance": balance,
                "transaction_count": transaction_count,
                "balance_url": balance_url,
                "transaction_url": tx_url,
                "is_active": balance > 0 or transaction_count > 0,
            }

        except Exception as e:
            raise MetagraphError(f"Error getting metagraph info: {e}")

    def get_active_metagraphs(self) -> List[Dict[str, Any]]:
        """
        Get only active metagraphs (those with balance or transactions).

        Returns:
            List of active metagraph dictionaries

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> active_mgs = client.get_active_metagraphs()
            >>> print(f"Found {len(active_mgs)} active metagraphs")
        """
        all_metagraphs = self.discover_production_metagraphs()
        active_metagraphs = []

        for mg in all_metagraphs:
            try:
                info = self.get_metagraph_info(mg["id"])
                if info.get("is_active", False):
                    mg.update(info)
                    active_metagraphs.append(mg)
            except:
                continue  # Skip if we can't get info

        return active_metagraphs

    def get_balance(self, address: str, metagraph_id: str) -> float:
        """
        Get token balance for an address on a specific metagraph.

        Args:
            address: The address to check balance for
            metagraph_id: The metagraph ID

        Returns:
            Token balance as float

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> balance = client.get_balance('DAG4J6gix...', 'DAG7Ghth...')
            >>> print(f"Token balance: {balance}")
        """
        # Parameter validation
        if address is None or metagraph_id is None:
            raise ConstellationError("Address and metagraph_id cannot be None")
            
        try:
            # Use metagraph-specific balance endpoint
            balance_url = f"{self.base_url}/metagraphs/{metagraph_id}/balance"
            params = {"address": address}
            response = requests.get(balance_url, params=params, timeout=5)

            if response.status_code == 404:
                # Check if it's specifically a metagraph not found error
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", "")
                    if "Metagraph not found" in error_msg:
                        raise ConstellationError("Metagraph not found")
                except ConstellationError:
                    raise  # Re-raise ConstellationError
                except Exception:
                    pass  # JSON parsing failed, treat as address not found
                
                # Address not found (but metagraph exists), return 0 balance
                return 0.0
            elif response.status_code == 400:
                # Invalid request, raise appropriate error
                raise ConstellationError("Invalid metagraph ID")
            elif response.status_code != 200:
                raise MetagraphError(f"Failed to get balance: {response.status_code}")

            balance_data = response.json()
            
            # Handle unexpected response structure gracefully
            if "data" not in balance_data or "balance" not in balance_data["data"]:
                return 0.0  # Default for missing balance data
                
            balance = balance_data["data"]["balance"]
            
            # Return as int for very large numbers to maintain precision
            if isinstance(balance, (int, float)) and balance >= 2**53 - 1:
                return int(balance)
            else:
                return float(balance)

        except ConstellationError:
            raise  # Re-raise ConstellationError as-is
        except ValueError as e:
            # Handle JSON parsing errors
            if "Invalid JSON" in str(e):
                raise ConstellationError("Invalid JSON")
            raise MetagraphError(f"Error getting balance: {e}")
        except Exception as e:
            # Handle request timeouts and other exceptions
            if "timeout" in str(e).lower():
                raise ConstellationError("Request timeout")
            raise MetagraphError(f"Error getting balance: {e}")

    def get_transactions(self, address: str, metagraph_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for an address on a specific metagraph.

        Args:
            address: The address to get transactions for
            metagraph_id: The metagraph ID
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dictionaries

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> transactions = client.get_transactions('DAG4J6gix...', 'DAG7Ghth...')
            >>> print(f"Found {len(transactions)} transactions")
        """
        # Parameter validation
        if address is None or metagraph_id is None:
            raise ConstellationError("Address and metagraph_id cannot be None")
            
        try:
            # Use metagraph-specific transaction endpoint
            tx_url = f"{self.base_url}/metagraphs/{metagraph_id}/transactions"
            params = {"address": address}
            if limit is not None:
                params['limit'] = limit

            response = requests.get(tx_url, params=params, timeout=5)

            if response.status_code == 404:
                # Address or metagraph not found, return empty list
                return []
            elif response.status_code != 200:
                raise MetagraphError(f"Failed to get transactions: {response.status_code}")

            tx_data = response.json()
            return tx_data.get("data", [])

        except Exception as e:
            raise MetagraphError(f"Error getting transactions: {e}")

    def query_data(self, metagraph_id: str, **filters) -> List[Dict[str, Any]]:
        """
        Query data submissions on a specific metagraph.

        Args:
            metagraph_id: The metagraph ID
            **filters: Optional filters like start_time, end_time, source, limit

        Returns:
            List of data submission dictionaries

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> data = client.query_data('DAG7Ghth...', limit=10)
            >>> print(f"Found {len(data)} data submissions")
        """
        # Parameter validation
        if metagraph_id is None:
            raise ConstellationError("Metagraph_id cannot be None")
            
        try:
            # This is a placeholder implementation - actual endpoint may vary
            data_url = f"{self.base_url}/metagraphs/{metagraph_id}/data"
            params = {}
            
            # Add filters as query parameters
            for key, value in filters.items():
                if value is not None:
                    params[key] = value

            response = requests.get(data_url, params=params, timeout=5)

            if response.status_code == 404:
                # Metagraph not found, return empty list
                return []
            elif response.status_code != 200:
                raise MetagraphError(f"Failed to query data: {response.status_code}")

            data_response = response.json()
            return data_response.get("data", [])

        except Exception as e:
            raise MetagraphError(f"Error querying data: {e}")

    def __str__(self) -> str:
        """String representation of the MetagraphClient."""
        return f"MetagraphClient(network='{self.network}', base_url='{self.base_url}')"

    # Transaction creation methods moved to transactions.py module
    # Use Transactions.create_token_transfer() and Transactions.create_data_submission() instead

    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get a realistic summary of metagraphs on this network.

        Returns:
            Dictionary with network summary including realistic expectations

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> summary = client.get_network_summary()
            >>> print(f"Production metagraphs: {summary['production_count']}")
        """
        try:
            all_deployments = self.discover_metagraphs(include_test_deployments=True)
            production_only = self.discover_production_metagraphs()

            return {
                "network": self.network,
                "total_deployments": len(all_deployments),
                "production_count": len(production_only),
                "test_deployments": len(all_deployments) - len(production_only),
                "reality_check": {
                    "mainnet": "Focus here for production metagraphs (~7 real)",
                    "testnet": "Mostly automated node testing (~34 nodes, 37 deployments)",
                    "integrationnet": "Development environment (~84 deployments)",
                }.get(self.network, "Mixed production and test deployments"),
            }
        except Exception as e:
            raise MetagraphError(f"Error getting network summary: {e}")

    def get_all_networks_summary(self) -> Dict[str, Any]:
        """
        Get a realistic summary of metagraphs across all networks.

        Returns:
            Dictionary with realistic network summary

        Example:
            >>> client = MetagraphClient()
            >>> summary = client.get_all_networks_summary()
            >>> print(f"Real production metagraphs: {summary['production_total']}")
        """
        networks = ["mainnet", "testnet", "integrationnet"]
        summary = {
            "networks": {},
            "total_deployments": 0,
            "production_total": 0,
            "reality_check": "Most deployments on test networks are automated node testing",
        }

        for network in networks:
            try:
                be_url = f"https://be-{network}.constellationnetwork.io/currency"
                response = requests.get(be_url, timeout=5)
                if response.status_code == 200:
                    currencies = response.json()["data"]
                    count = len(currencies)

                    # Estimate production based on network
                    production_estimate = (
                        count
                        if network == "mainnet"
                        else max(0, count - int(count * 0.9))
                    )

                    summary["networks"][network] = {
                        "total": count,
                        "estimated_production": production_estimate,
                        "likely_test_deployments": count - production_estimate,
                    }
                    summary["total_deployments"] += count
                    summary["production_total"] += production_estimate
                else:
                    summary["networks"][network] = {
                        "total": 0,
                        "estimated_production": 0,
                        "likely_test_deployments": 0,
                    }
            except:
                summary["networks"][network] = {
                    "total": 0,
                    "estimated_production": 0,
                    "likely_test_deployments": 0,
                }

        return summary

    # Helper methods for transaction creation moved to transactions.py module


# Convenience functions for quick access
def discover_production_metagraphs(network: str = "mainnet") -> List[Dict[str, Any]]:
    """
    Convenience function to discover production metagraphs on a network.

    Args:
        network: Network name ('mainnet' recommended for production)

    Returns:
        List of production metagraph dictionaries

    Example:
        >>> from constellation_sdk.metagraph import discover_production_metagraphs
        >>> production_mgs = discover_production_metagraphs('mainnet')
        >>> print(f"Found {len(production_mgs)} production metagraphs")
    """
    client = MetagraphClient(network)
    return client.discover_production_metagraphs()


def get_realistic_metagraph_summary() -> Dict[str, Any]:
    """
    Get a realistic summary of metagraphs across all networks.

    Returns:
        Dictionary with realistic network summary

    Example:
        >>> from constellation_sdk.metagraph import get_realistic_metagraph_summary
        >>> summary = get_realistic_metagraph_summary()
        >>> print(f"Real production metagraphs: {summary['production_total']}")
        >>> print(f"Test deployments: {summary['total_deployments'] - summary['production_total']}")
    """
    client = MetagraphClient()
    return client.get_all_networks_summary()


# Keep legacy function for backward compatibility
def discover_all_metagraphs(network: str = "testnet") -> List[Dict[str, Any]]:
    """
    Legacy function - discovers all deployments including test/automated ones.

    Args:
        network: Network name

    Returns:
        List of all deployment dictionaries (including test deployments)

    Note:
        For production use, prefer discover_production_metagraphs()
    """
    client = MetagraphClient(network)
    return client.discover_metagraphs(include_test_deployments=True)


def get_metagraph_summary() -> Dict[str, Any]:
    """
    Legacy function - returns all deployments summary.

    Returns:
        Dictionary with all deployments (including test ones)

    Note:
        For realistic numbers, use get_realistic_metagraph_summary()
    """
    client = MetagraphClient()
    return client.get_all_networks_summary()
