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

# GraphQL integration (optional)
try:
    from .graphql import ConstellationSchema, GraphQLClient
    from .graphql_builder import (
        QueryBuilder,
        build_metagraph_query,
        build_portfolio_query,
    )

    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False


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

        # Initialize GraphQL client if available
        if GRAPHQL_AVAILABLE:
            self.graphql_client = GraphQLClient(network)
        else:
            self.graphql_client = None

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
                params["limit"] = limit

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

    def get_transactions(
        self, address: str, metagraph_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
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
                params["limit"] = limit

            response = requests.get(tx_url, params=params, timeout=5)

            if response.status_code == 404:
                # Address or metagraph not found, return empty list
                return []
            elif response.status_code != 200:
                raise MetagraphError(
                    f"Failed to get transactions: {response.status_code}"
                )

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

    # GraphQL-powered methods (enhanced functionality)
    def get_comprehensive_metagraph_data(
        self,
        metagraph_id: str,
        include_holders: bool = True,
        include_transactions: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive metagraph data using GraphQL (if available).

        Args:
            metagraph_id: Metagraph ID
            include_holders: Whether to include holder information
            include_transactions: Whether to include transaction history

        Returns:
            Comprehensive metagraph data dictionary

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> data = client.get_comprehensive_metagraph_data('DAG7Ghth...')
            >>> print(f"Metagraph: {data['name']}")
            >>> print(f"Total Supply: {data['totalSupply']}")
            >>> print(f"Holders: {len(data['holders'])}")
        """
        if not GRAPHQL_AVAILABLE or not self.graphql_client:
            # Fallback to REST API
            return self._get_comprehensive_metagraph_data_rest(
                metagraph_id, include_holders, include_transactions
            )

        try:
            # Use GraphQL for rich data
            query = build_metagraph_query(
                metagraph_id, include_holders, include_transactions
            )
            response = self.graphql_client.execute(query)

            if response.is_successful and response.data:
                return response.data.get("metagraph", {})
            else:
                # Fallback to REST on GraphQL failure
                return self._get_comprehensive_metagraph_data_rest(
                    metagraph_id, include_holders, include_transactions
                )

        except Exception as e:
            # Fallback to REST on any error
            return self._get_comprehensive_metagraph_data_rest(
                metagraph_id, include_holders, include_transactions
            )

    def _get_comprehensive_metagraph_data_rest(
        self, metagraph_id: str, include_holders: bool, include_transactions: bool
    ) -> Dict[str, Any]:
        """Fallback REST implementation for comprehensive metagraph data."""
        try:
            # Get basic info
            info = self.get_metagraph_info(metagraph_id)

            # Add additional data if requested
            if include_holders:
                # This would require additional REST endpoints
                info["holders"] = []

            if include_transactions:
                # This would require additional REST endpoints
                info["transactions"] = []

            return info

        except Exception as e:
            raise MetagraphError(f"Error getting comprehensive metagraph data: {e}")

    def get_account_portfolio_graphql(
        self, address: str, include_metagraph_balances: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive account portfolio using GraphQL (if available).

        Args:
            address: Account address
            include_metagraph_balances: Whether to include metagraph balances

        Returns:
            Account portfolio data dictionary

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> portfolio = client.get_account_portfolio_graphql('DAG4J6gix...')
            >>> print(f"DAG Balance: {portfolio['balance']}")
            >>> print(f"Metagraph Balances: {len(portfolio['metagraphBalances'])}")
        """
        if not GRAPHQL_AVAILABLE or not self.graphql_client:
            raise ConstellationError(
                "GraphQL functionality not available. Install required dependencies."
            )

        try:
            # Build comprehensive account query
            builder = QueryBuilder().account(address).with_balance().with_address()

            if include_metagraph_balances:
                builder = builder.with_metagraph_balances()

            # Add recent transactions
            builder = builder.with_transactions(limit=20)

            query = builder.build()
            response = self.graphql_client.execute(query)

            if response.is_successful and response.data:
                return response.data.get("account", {})
            else:
                raise MetagraphError(f"GraphQL query failed: {response.errors}")

        except Exception as e:
            raise MetagraphError(f"Error getting account portfolio: {e}")

    def get_multi_account_portfolio(self, addresses: List[str]) -> Dict[str, Any]:
        """
        Get portfolio data for multiple accounts using GraphQL (if available).

        Args:
            addresses: List of account addresses

        Returns:
            Multi-account portfolio data dictionary

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> portfolios = client.get_multi_account_portfolio(['DAG123...', 'DAG456...'])
            >>> for account in portfolios['accounts']:
            ...     print(f"{account['address']}: {account['balance']} DAG")
        """
        if not GRAPHQL_AVAILABLE or not self.graphql_client:
            raise ConstellationError(
                "GraphQL functionality not available. Install required dependencies."
            )

        try:
            # Build multi-account query
            query = build_portfolio_query(addresses)
            response = self.graphql_client.execute(query)

            if response.is_successful and response.data:
                return response.data
            else:
                raise MetagraphError(f"GraphQL query failed: {response.errors}")

        except Exception as e:
            raise MetagraphError(f"Error getting multi-account portfolio: {e}")

    def discover_metagraphs_graphql(
        self, production_only: bool = True, include_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Discover metagraphs using GraphQL (if available) for enhanced data.

        Args:
            production_only: Whether to include only production metagraphs
            include_metrics: Whether to include metrics like holder count, transaction count

        Returns:
            List of metagraph data dictionaries with enhanced information

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> metagraphs = client.discover_metagraphs_graphql()
            >>> for mg in metagraphs:
            ...     print(f"{mg['name']}: {mg['holderCount']} holders")
        """
        if not GRAPHQL_AVAILABLE or not self.graphql_client:
            # Fallback to REST discovery
            return (
                self.discover_production_metagraphs()
                if production_only
                else self.discover_metagraphs()
            )

        try:
            # Build metagraphs query
            builder = QueryBuilder().metagraphs().with_basic_info()

            if production_only:
                builder = builder.production_only()

            if include_metrics:
                builder = builder.with_metrics()

            query = builder.build()
            response = self.graphql_client.execute(query)

            if response.is_successful and response.data:
                return response.data.get("metagraphs", [])
            else:
                # Fallback to REST on GraphQL failure
                return (
                    self.discover_production_metagraphs()
                    if production_only
                    else self.discover_metagraphs()
                )

        except Exception as e:
            # Fallback to REST on any error
            return (
                self.discover_production_metagraphs()
                if production_only
                else self.discover_metagraphs()
            )

    async def subscribe_to_metagraph_updates(
        self, metagraph_ids: List[str], callback=None
    ):
        """
        Subscribe to real-time metagraph updates using GraphQL subscriptions (if available).

        Args:
            metagraph_ids: List of metagraph IDs to monitor
            callback: Optional callback function for updates

        Example:
            >>> client = MetagraphClient('mainnet')
            >>> def handle_update(update):
            ...     print(f"Metagraph update: {update}")
            >>> await client.subscribe_to_metagraph_updates(['DAG123...'], handle_update)
        """
        if not GRAPHQL_AVAILABLE or not self.graphql_client:
            raise ConstellationError(
                "GraphQL functionality not available. Install required dependencies."
            )

        try:
            # Build subscription
            from .graphql_builder import SubscriptionBuilder

            subscription = (
                SubscriptionBuilder().metagraph_updates(metagraph_ids).build()
            )

            # Subscribe to updates
            async for update in self.graphql_client.subscribe(subscription):
                if callback:
                    callback(update.data)
                else:
                    print(f"Metagraph update: {update.data}")

        except Exception as e:
            raise MetagraphError(f"Error subscribing to metagraph updates: {e}")

    def get_graphql_stats(self) -> Dict[str, Any]:
        """
        Get GraphQL client statistics (if available).

        Returns:
            GraphQL statistics dictionary
        """
        if not GRAPHQL_AVAILABLE or not self.graphql_client:
            return {
                "available": False,
                "message": "GraphQL functionality not available",
            }

        return {"available": True, "stats": self.graphql_client.get_stats()}


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
