"""
Async Metagraph client for Constellation Network.

Provides high-performance async operations for metagraph discovery,
balance queries, transaction operations, and data retrieval.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

from .async_network import AsyncNetwork
from .config import METAGRAPH_ENDPOINTS, NetworkConfig, get_config
from .exceptions import (
    ConstellationError,
    MetagraphError,
    NetworkError,
    ValidationError,
)
from .logging import get_logger, get_performance_tracker
from .validation import AddressValidator, AmountValidator


class AsyncMetagraphClient:
    """
    Async client for interacting with Constellation metagraphs.

    Provides high-performance async operations for metagraph-specific
    functionality including balance queries, transaction submission,
    and data operations.
    """

    def __init__(
        self, metagraph_id: str, network_config: Optional[NetworkConfig] = None
    ):
        """
        Initialize async metagraph client.

        Args:
            metagraph_id: Metagraph identifier
            network_config: Optional network configuration
        """
        self.metagraph_id = metagraph_id
        self.config = network_config or get_config().network
        self.network = AsyncNetwork(self.config)
        self.logger = get_logger()
        self.perf_tracker = get_performance_tracker()

        # Metagraph endpoints
        self.base_url = self.config.l0_url
        self.metagraph_base = f"/metagraph/{self.metagraph_id}"

        # Cache for metagraph-specific data
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_times: Dict[str, float] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.network.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.network.__aexit__(exc_type, exc_val, exc_tb)

    def _get_metagraph_url(self, endpoint: str) -> str:
        """Construct metagraph-specific URL."""
        return urljoin(self.base_url, self.metagraph_base + endpoint)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid."""
        if cache_key not in self._cache:
            return False

        cache_config = get_config().cache
        if not cache_config.enable_caching or not cache_config.cache_metagraphs:
            return False

        cache_time = self._cache_times.get(cache_key, 0)
        return (time.time() - cache_time) < cache_config.cache_ttl

    def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache a response."""
        cache_config = get_config().cache
        if not cache_config.enable_caching or not cache_config.cache_metagraphs:
            return

        self._cache[cache_key] = response
        self._cache_times[cache_key] = time.time()

    async def get_info(self) -> Dict[str, Any]:
        """
        Get metagraph information asynchronously.

        Returns:
            Dictionary containing metagraph information
        """
        cache_key = f"metagraph_info_{self.metagraph_id}"

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug(
                f"Returning cached info for metagraph {self.metagraph_id}"
            )
            return self._cache[cache_key]

        url = self._get_metagraph_url("/cluster")

        try:
            response = await self.network.http_client.request("GET", url, self.config)
            self._cache_response(cache_key, response)
            return response
        except Exception as e:
            raise MetagraphError(f"Failed to get metagraph info: {e}") from e

    async def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get balance for an address in this metagraph asynchronously.

        Args:
            address: DAG address to query

        Returns:
            Dictionary containing balance information
        """
        # Validate address
        AddressValidator.validate(address)

        cache_key = f"balance_{self.metagraph_id}_{address}"

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug(
                f"Returning cached balance for {address} in {self.metagraph_id}"
            )
            return self._cache[cache_key]

        url = self._get_metagraph_url(f"/addresses/{address}/balance")

        try:
            response = await self.network.http_client.request("GET", url, self.config)
            self._cache_response(cache_key, response)
            return response
        except Exception as e:
            raise MetagraphError(f"Failed to get balance for {address}: {e}") from e

    async def get_transaction_history(
        self, address: str, limit: int = 20, order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get transaction history for an address asynchronously.

        Args:
            address: DAG address to query
            limit: Maximum number of transactions to return
            order: Sort order (asc or desc)

        Returns:
            Dictionary containing transaction history
        """
        AddressValidator.validate(address)

        url = self._get_metagraph_url("/transactions")
        params = {"address": address, "limit": limit, "order": order}

        try:
            return await self.network.http_client.request(
                "GET", url, self.config, params=params
            )
        except Exception as e:
            raise MetagraphError(f"Failed to get transaction history: {e}") from e

    async def submit_data_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a data transaction to the metagraph asynchronously.

        Args:
            data: Data transaction to submit

        Returns:
            Dictionary containing submission response
        """
        url = self._get_metagraph_url("/data")

        try:
            return await self.network.http_client.request(
                "POST",
                url,
                self.config,
                json=data,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            raise MetagraphError(f"Failed to submit data transaction: {e}") from e

    async def submit_transaction(self, signed_transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a signed transaction to the network asynchronously.
        Args:
            signed_transaction: Signed transaction from Transactions class
        Returns:
            Transaction submission result
        """
        try:
            return await self.network.submit_transaction(signed_transaction)
        except NetworkError as e:
            raise MetagraphError(f"Transaction submission failed: {e}") from e

    async def get_transaction_status(self, transaction_hash: str) -> str:
        """
        Get the status of a transaction asynchronously.
        Args:
            transaction_hash: The hash of the transaction to check.
        Returns:
            The transaction status ('pending', 'confirmed', 'failed', or 'not_found')
        """
        try:
            tx = await self.network.get_transaction(transaction_hash)
            if tx is None:
                return "not_found"
            if tx.get("blockHash"):
                return "confirmed"
            else:
                return "pending"
        except NetworkError as e:
            raise MetagraphError(f"Failed to get transaction status: {e}")

    async def wait_for_confirmation(
        self, transaction_hash: str, timeout: int = 120, poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for a transaction to be confirmed asynchronously.
        Args:
            transaction_hash: The hash of the transaction to wait for.
            timeout: The maximum time to wait in seconds.
            poll_interval: The time to wait between polling for status.
        Returns:
            The confirmed transaction data.
        Raises:
            MetagraphError: If the transaction is not confirmed within the timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                tx = await self.network.get_transaction(transaction_hash)
                if tx and tx.get("blockHash"):
                    return tx
            except NetworkError:
                pass  # Ignore network errors and retry
            await asyncio.sleep(poll_interval)

        raise MetagraphError(
            f"Transaction {transaction_hash} not confirmed after {timeout} seconds."
        )

    async def get_latest_snapshot(self) -> Dict[str, Any]:
        """
        Get latest snapshot for this metagraph asynchronously.

        Returns:
            Dictionary containing latest snapshot data
        """
        cache_key = f"snapshot_{self.metagraph_id}_latest"

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug(
                f"Returning cached snapshot for {self.metagraph_id}"
            )
            return self._cache[cache_key]

        url = self._get_metagraph_url("/snapshots/latest")

        try:
            response = await self.network.http_client.request("GET", url, self.config)
            self._cache_response(cache_key, response)
            return response
        except Exception as e:
            raise MetagraphError(f"Failed to get latest snapshot: {e}") from e

    async def get_data(
        self, hash_value: Optional[str] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get data from the metagraph asynchronously.

        Args:
            hash_value: Optional specific data hash to retrieve
            limit: Maximum number of data entries to return

        Returns:
            Dictionary containing data
        """
        url = self._get_metagraph_url("/data")
        params = {"limit": limit}

        if hash_value:
            params["hash"] = hash_value

        try:
            return await self.network.http_client.request(
                "GET", url, self.config, params=params
            )
        except Exception as e:
            raise MetagraphError(f"Failed to get data: {e}") from e

    async def get_custom_state(self, state_key: str) -> Optional[Any]:
        """
        Query a custom state value from the metagraph by key (async).
        NOTE: Assumes a generic state endpoint exists.
        Args:
            state_key: The key of the state variable to query.
        Returns:
            The value of the state variable, or None if not found.
        """
        if state_key is None:
            raise ConstellationError("State key cannot be None")

        url = self._get_metagraph_url(f"/state/{state_key}")

        try:
            response = await self.network.http_client.request("GET", url, self.config)
            return response.get("data")
        except NetworkError as e:
            # Assuming 404 means the key is not found
            if hasattr(e, "status_code") and e.status_code == 404:
                return None
            raise MetagraphError(f"Failed to query custom state: {e}") from e

    async def batch_get_balances(
        self, addresses: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get balances for multiple addresses concurrently.

        Args:
            addresses: List of DAG addresses

        Returns:
            Dictionary mapping addresses to their balance information
        """
        if not addresses:
            return {}

        # Validate all addresses first
        for address in addresses:
            AddressValidator.validate(address)

        # Create concurrent tasks
        tasks = [self.get_balance(address) for address in addresses]

        try:
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            balances = {}
            for i, (address, result) in enumerate(zip(addresses, results)):
                if isinstance(result, Exception):
                    self.logger.logger.warning(
                        f"Failed to get balance for {address}: {result}"
                    )
                    balances[address] = {"error": str(result)}
                else:
                    balances[address] = result

            return balances

        except Exception as e:
            raise MetagraphError(f"Failed to get batch balances: {e}") from e

    async def health_check(self) -> bool:
        """
        Perform async health check on the metagraph.

        Returns:
            True if metagraph is healthy, False otherwise
        """
        try:
            self.perf_tracker.start_operation("metagraph_health_check")
            start_time = time.time()
            await self.get_info()
            elapsed = time.time() - start_time

            self.perf_tracker.end_operation("metagraph_health_check", success=True)
            self.logger.logger.info(
                f"Metagraph {self.metagraph_id} health check passed in {elapsed:.2f}s"
            )
            return True

        except Exception as e:
            self.logger.logger.error(
                f"Metagraph {self.metagraph_id} health check failed: {e}"
            )
            return False

    def clear_cache(self):
        """Clear all cached responses for this metagraph."""
        self._cache.clear()
        self._cache_times.clear()
        self.logger.logger.debug(f"Cache cleared for metagraph {self.metagraph_id}")


class AsyncMetagraphDiscovery:
    """
    Async metagraph discovery and management.

    Provides methods to discover available metagraphs and create
    AsyncMetagraphClient instances.
    """

    def __init__(self, network_config: Optional[NetworkConfig] = None):
        """
        Initialize async metagraph discovery.

        Args:
            network_config: Optional network configuration
        """
        self.config = network_config or get_config().network
        self.network = AsyncNetwork(self.config)
        self.logger = get_logger()

        # Cache for discovered metagraphs
        self._discovered_metagraphs: Optional[List[Dict[str, Any]]] = None
        self._discovery_time: Optional[float] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.network.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.network.__aexit__(exc_type, exc_val, exc_tb)

    async def discover_metagraphs(
        self, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Discover available metagraphs asynchronously.

        Args:
            force_refresh: Force refresh even if cached data is available

        Returns:
            List of available metagraph information
        """
        # Check cache
        if not force_refresh and self._is_discovery_cache_valid():
            self.logger.logger.debug("Returning cached metagraph discovery")
            return self._discovered_metagraphs

        url = urljoin(self.config.l0_url, "/cluster/info")

        try:
            response = await self.network.http_client.request("GET", url, self.config)

            # Extract metagraph information from cluster info
            metagraphs = []
            if "metagraphs" in response:
                metagraphs = response["metagraphs"]
            elif isinstance(response, list):
                metagraphs = response

            # Cache the results
            self._discovered_metagraphs = metagraphs
            self._discovery_time = time.time()

            self.logger.logger.info(f"Discovered {len(metagraphs)} metagraphs")
            return metagraphs

        except Exception as e:
            raise MetagraphError(f"Failed to discover metagraphs: {e}") from e

    def _is_discovery_cache_valid(self) -> bool:
        """Check if discovery cache is still valid."""
        if self._discovered_metagraphs is None or self._discovery_time is None:
            return False

        cache_config = get_config().cache
        if not cache_config.enable_caching or not cache_config.cache_metagraphs:
            return False

        return (time.time() - self._discovery_time) < cache_config.cache_ttl

    async def get_metagraph_client(self, metagraph_id: str) -> AsyncMetagraphClient:
        """
        Get an async metagraph client for a specific metagraph.

        Args:
            metagraph_id: Metagraph identifier

        Returns:
            Initialized AsyncMetagraphClient
        """
        client = AsyncMetagraphClient(metagraph_id, self.config)
        await client.__aenter__()
        return client

    async def batch_health_check(
        self, metagraph_ids: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Perform health checks on multiple metagraphs concurrently.

        Args:
            metagraph_ids: Optional list of metagraph IDs. If not provided,
                          discovers and checks all available metagraphs.

        Returns:
            Dictionary mapping metagraph IDs to health status
        """
        if metagraph_ids is None:
            # Discover all metagraphs
            try:
                discovered = await self.discover_metagraphs()
                metagraph_ids = [
                    mg.get("id", mg.get("metagraphId", str(i)))
                    for i, mg in enumerate(discovered)
                ]
            except Exception as e:
                self.logger.logger.error(
                    f"Failed to discover metagraphs for health check: {e}"
                )
                return {}

        if not metagraph_ids:
            return {}

        # Create health check tasks
        async def check_metagraph(mg_id):
            try:
                async with AsyncMetagraphClient(mg_id, self.config) as client:
                    return mg_id, await client.health_check()
            except Exception as e:
                self.logger.logger.warning(
                    f"Health check failed for metagraph {mg_id}: {e}"
                )
                return mg_id, False

        tasks = [check_metagraph(mg_id) for mg_id in metagraph_ids]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            health_status = {}
            for result in results:
                if isinstance(result, Exception):
                    self.logger.logger.error(f"Health check task failed: {result}")
                    continue

                mg_id, status = result
                health_status[mg_id] = status

            return health_status

        except Exception as e:
            raise MetagraphError(f"Failed to perform batch health check: {e}") from e


# Utility functions for async metagraph operations
async def discover_metagraphs_async(
    network_config: Optional[NetworkConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to discover metagraphs asynchronously.

    Args:
        network_config: Optional network configuration

    Returns:
        List of available metagraph information
    """
    async with AsyncMetagraphDiscovery(network_config) as discovery:
        return await discovery.discover_metagraphs()


async def create_async_metagraph_client(
    metagraph_id: str, network_config: Optional[NetworkConfig] = None
) -> AsyncMetagraphClient:
    """
    Convenience function to create and initialize an async metagraph client.

    Args:
        metagraph_id: Metagraph identifier
        network_config: Optional network configuration

    Returns:
        Initialized AsyncMetagraphClient
    """
    client = AsyncMetagraphClient(metagraph_id, network_config)
    await client.__aenter__()
    return client


async def batch_get_balances_from_multiple_metagraphs(
    address_metagraph_pairs: List[tuple], network_config: Optional[NetworkConfig] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Get balances from multiple metagraphs concurrently.

    Args:
        address_metagraph_pairs: List of (address, metagraph_id) tuples
        network_config: Optional network configuration

    Returns:
        Dictionary mapping "address_metagraph" to balance information
    """
    if not address_metagraph_pairs:
        return {}

    async def get_balance_from_metagraph(address, metagraph_id):
        try:
            async with AsyncMetagraphClient(metagraph_id, network_config) as client:
                balance = await client.get_balance(address)
                return f"{address}_{metagraph_id}", balance
        except Exception as e:
            return f"{address}_{metagraph_id}", {"error": str(e)}

    tasks = [
        get_balance_from_metagraph(address, mg_id)
        for address, mg_id in address_metagraph_pairs
    ]

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        balances = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            key, balance = result
            balances[key] = balance

        return balances

    except Exception as e:
        raise MetagraphError(
            f"Failed to get batch balances from multiple metagraphs: {e}"
        ) from e
