"""
Network interface for Constellation Network.
Handles API calls, balance queries, transaction submission, and batch operations.
"""

import time
from typing import Any, Dict, List, Optional

import requests

from .batch import (
    BatchOperation,
    BatchOperationType,
    BatchResponse,
    BatchResult,
    BatchValidator,
    batch_get_balances,
    batch_get_ordinals,
    batch_get_transactions,
    create_batch_operation,
)
from .config import DEFAULT_CONFIGS, NetworkConfig
from .exceptions import NetworkError


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
            raise NetworkError(
                f"Invalid network configuration type: {type(network_or_config)}"
            )

    def _make_request(
        self, url: str, method: str = "GET", **kwargs
    ) -> requests.Response:
        """Make HTTP request with error handling."""
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            return response
        except (requests.RequestException, ConnectionError) as e:
            raise NetworkError(f"Network request failed: {e}") from e

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
            return response.json()["data"]["balance"]
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
        response = self._make_request(url, params={"limit": limit})

        if response.status_code == 200:
            return response.json()["data"]
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
            method="POST",
            json=signed_transaction,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise NetworkError(f"Invalid transaction: {response.text}")
        elif response.status_code == 500:
            # Common for unfunded addresses
            raise NetworkError(
                "Transaction failed - check address balance and parent references"
            )
        else:
            raise NetworkError(f"Transaction submission failed: {response.status_code}")

    def validate_address(self, address: str) -> bool:
        """Validate DAG address format."""
        return (
            isinstance(address, str)
            and address.startswith("DAG")
            and len(address) == 38
            and all(c in "0123456789ABCDEFabcdef" for c in address[3:])
        )

    def get_ordinal(self, address: str) -> int:
        """
        Get address ordinal (transaction count).

        Args:
            address: DAG address

        Returns:
            Address ordinal (transaction count)
        """
        url = f"{self.config.be_url}/addresses/{address}/ordinal"
        response = self._make_request(url)

        if response.status_code == 200:
            return response.json()["data"]["ordinal"]
        elif response.status_code == 404:
            return 0  # Address not found = zero ordinal
        else:
            raise NetworkError(f"Ordinal query failed: {response.status_code}")

    def get_transactions(self, address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific address.

        Args:
            address: DAG address
            limit: Maximum number of transactions to return

        Returns:
            List of transaction data
        """
        url = f"{self.config.be_url}/addresses/{address}/transactions"
        response = self._make_request(url, params={"limit": limit})

        if response.status_code == 200:
            return response.json()["data"]
        elif response.status_code == 404:
            return []  # Address not found = no transactions
        else:
            raise NetworkError(f"Transactions query failed: {response.status_code}")

    # ========================================
    # Batch Operations (Enhanced REST Phase 1)
    # ========================================

    def batch_request(self, operations: List[BatchOperation]) -> BatchResponse:
        """
        Execute multiple operations in a single batch request.

        This method provides enhanced REST capabilities by executing multiple
        operations efficiently, reducing network round trips and improving
        performance for complex queries.

        Args:
            operations: List of batch operations to execute

        Returns:
            BatchResponse containing results of all operations

        Raises:
            NetworkError: If validation fails or network issues occur

        Example:
            >>> operations = [
            ...     create_batch_operation('get_balance', {'address': 'DAG123...'}),
            ...     create_batch_operation('get_ordinal', {'address': 'DAG123...'}),
            ...     create_batch_operation('get_transactions', {'address': 'DAG123...', 'limit': 5})
            ... ]
            >>> response = network.batch_request(operations)
            >>> print(f"Success rate: {response.success_rate()}%")
        """
        start_time = time.time()

        # Validate batch operations
        validation_errors = BatchValidator.validate_batch(operations)
        if validation_errors:
            raise NetworkError(
                f"Batch validation failed: {'; '.join(validation_errors)}"
            )

        results = []

        # Execute operations sequentially (can be optimized with threading/async later)
        for operation in operations:
            try:
                result = self._execute_single_operation(operation)
                results.append(
                    BatchResult(
                        operation=operation.operation,
                        success=True,
                        data=result,
                        id=operation.id,
                    )
                )
            except Exception as e:
                results.append(
                    BatchResult(
                        operation=operation.operation,
                        success=False,
                        error=str(e),
                        id=operation.id,
                    )
                )

        execution_time = time.time() - start_time

        # Create summary statistics
        successful_ops = [r for r in results if r.success]
        failed_ops = [r for r in results if not r.success]

        summary = {
            "total_operations": len(operations),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate": len(successful_ops) / len(operations) * 100,
            "execution_time": execution_time,
        }

        return BatchResponse(
            results=results, summary=summary, execution_time=execution_time
        )

    def _execute_single_operation(self, operation: BatchOperation) -> Any:
        """
        Execute a single batch operation.

        Args:
            operation: Batch operation to execute

        Returns:
            Operation result

        Raises:
            NetworkError: If operation fails
        """
        if operation.operation == BatchOperationType.GET_BALANCE:
            return self.get_balance(operation.params["address"])

        elif operation.operation == BatchOperationType.GET_ORDINAL:
            return self.get_ordinal(operation.params["address"])

        elif operation.operation == BatchOperationType.GET_TRANSACTIONS:
            address = operation.params["address"]
            limit = operation.params.get("limit", 10)
            return self.get_transactions(address, limit)

        elif operation.operation == BatchOperationType.GET_RECENT_TRANSACTIONS:
            limit = operation.params.get("limit", 50)
            return self.get_recent_transactions(limit)

        elif operation.operation == BatchOperationType.GET_NODE_INFO:
            return self.get_node_info()

        elif operation.operation == BatchOperationType.GET_CLUSTER_INFO:
            return self.get_cluster_info()

        elif operation.operation == BatchOperationType.SUBMIT_TRANSACTION:
            return self.submit_transaction(operation.params["transaction"])

        else:
            raise NetworkError(f"Unsupported batch operation: {operation.operation}")

    def get_multi_balance(self, addresses: List[str]) -> Dict[str, int]:
        """
        Get balances for multiple addresses in a single batch request.

        Args:
            addresses: List of DAG addresses

        Returns:
            Dictionary mapping addresses to balances

        Example:
            >>> balances = network.get_multi_balance(['DAG123...', 'DAG456...'])
            >>> print(f"Total balance: {sum(balances.values()) / 1e8} DAG")
        """
        operations = batch_get_balances(addresses)
        response = self.batch_request(operations)

        result = {}
        for i, address in enumerate(addresses):
            operation_result = response.get_result(f"balance_{i}")
            if operation_result and operation_result.success:
                result[address] = operation_result.data
            else:
                result[address] = 0  # Default to 0 if operation failed

        return result

    def get_multi_ordinal(self, addresses: List[str]) -> Dict[str, int]:
        """
        Get ordinals for multiple addresses in a single batch request.

        Args:
            addresses: List of DAG addresses

        Returns:
            Dictionary mapping addresses to ordinals
        """
        operations = batch_get_ordinals(addresses)
        response = self.batch_request(operations)

        result = {}
        for i, address in enumerate(addresses):
            operation_result = response.get_result(f"ordinal_{i}")
            if operation_result and operation_result.success:
                result[address] = operation_result.data
            else:
                result[address] = 0  # Default to 0 if operation failed

        return result

    def get_multi_transactions(
        self, addresses: List[str], limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get transactions for multiple addresses in a single batch request.

        Args:
            addresses: List of DAG addresses
            limit: Maximum number of transactions per address

        Returns:
            Dictionary mapping addresses to transaction lists
        """
        operations = batch_get_transactions(addresses, limit)
        response = self.batch_request(operations)

        result = {}
        for i, address in enumerate(addresses):
            operation_result = response.get_result(f"transactions_{i}")
            if operation_result and operation_result.success:
                result[address] = operation_result.data
            else:
                result[address] = []  # Default to empty list if operation failed

        return result

    def get_address_overview(self, address: str) -> Dict[str, Any]:
        """
        Get comprehensive address overview in a single batch request.

        Args:
            address: DAG address

        Returns:
            Dictionary with balance, ordinal, and recent transactions

        Example:
            >>> overview = network.get_address_overview('DAG123...')
            >>> print(f"Balance: {overview['balance'] / 1e8} DAG")
            >>> print(f"Transactions: {len(overview['transactions'])}")
        """
        operations = [
            create_batch_operation("get_balance", {"address": address}, "balance"),
            create_batch_operation("get_ordinal", {"address": address}, "ordinal"),
            create_batch_operation(
                "get_transactions", {"address": address, "limit": 10}, "transactions"
            ),
        ]

        response = self.batch_request(operations)

        # Extract results
        balance_result = response.get_result("balance")
        ordinal_result = response.get_result("ordinal")
        transactions_result = response.get_result("transactions")

        return {
            "address": address,
            "balance": (
                balance_result.data if balance_result and balance_result.success else 0
            ),
            "ordinal": (
                ordinal_result.data if ordinal_result and ordinal_result.success else 0
            ),
            "transactions": (
                transactions_result.data
                if transactions_result and transactions_result.success
                else []
            ),
            "success": response.success_rate() == 100,
            "execution_time": response.execution_time,
        }

    def get_snapshot_holders(self) -> List[Dict[str, Any]]:
        """
        Get a list of all wallet balances from the latest global snapshot.

        This method fetches the latest combined snapshot from the Global L0 API,
        extracts the wallet balances, and returns a list of all holders with
        their respective balances in DAG.

        Returns:
            A list of dictionaries, each containing 'wallet' and 'amount'.
            Returns an empty list if the snapshot format is unexpected.

        Example:
            >>> # Get all holders from the latest snapshot
            >>> holders = network.get_snapshot_holders()
        """
        url_to_fetch = "http://l0-lb-mainnet.constellationnetwork.io/global-snapshots/latest/combined"

        response = self._make_request(
            url_to_fetch, headers={"Accept": "application/json"}
        )

        if response.status_code != 200:
            raise NetworkError(
                f"Failed to fetch snapshot from {url_to_fetch}: {response.status_code}"
            )

        try:
            json_data = response.json()
            balances = json_data[1]["balances"]
        except (KeyError, IndexError, TypeError):
            # Handle cases where the snapshot format is not as expected
            return []

        holders = []
        for wallet, amount in balances.items():
            if wallet == "0000000000000000000000000000000000000000":
                continue
            holders.append({"wallet": wallet, "amount": amount / 1e8})

        return holders
