"""
Async Network client for Constellation Network operations.

Provides non-blocking HTTP operations using aiohttp for improved performance
and scalability. Supports connection pooling, retries, caching, and
comprehensive error handling.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

try:
    import aiohttp
    from aiohttp import ClientResponse, ClientSession, ClientTimeout

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    # Fallback types for when aiohttp is not available
    ClientSession = None
    ClientTimeout = None
    ClientResponse = None

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
from .config import AsyncConfig, NetworkConfig, get_config
from .exceptions import (
    APIError,
    ConnectionError,
    ConstellationError,
    HTTPError,
    NetworkError,
    TimeoutError,
)
from .logging import get_network_logger, get_performance_tracker
from .validation import AddressValidator, AmountValidator


class AsyncHTTPClient:
    """
    High-performance async HTTP client with connection pooling and retry logic.
    """

    def __init__(self, config: Optional[AsyncConfig] = None):
        """
        Initialize async HTTP client.

        Args:
            config: Optional async configuration. Uses global config if not provided.
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp is required for async operations. "
                "Install it with: pip install aiohttp"
            )

        self.config = config or get_config().async_config
        self.logger = get_network_logger()
        self.perf_tracker = get_performance_tracker()

        self._session: Optional[ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

        # Rate limiting
        self._last_request_time = 0.0
        self._request_count = 0
        self._rate_limit_window_start = 0.0

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created and configured."""
        if self._session is None or self._session.closed:
            # Create TCP connector with connection pooling
            self._connector = aiohttp.TCPConnector(
                limit=self.config.connector_limit,
                limit_per_host=self.config.connector_limit_per_host,
                ttl_dns_cache=self.config.connector_ttl_dns_cache,
                use_dns_cache=self.config.connector_use_dns_cache,
                ssl=False if not self.config.verify_ssl else None,
                enable_cleanup_closed=True,
            )

            # Create timeout configuration
            timeout = ClientTimeout(
                total=self.config.total_timeout,
                connect=self.config.connect_timeout,
                sock_read=self.config.read_timeout,
            )

            # Create session with all configurations
            self._session = ClientSession(
                connector=self._connector,
                timeout=timeout,
                auto_decompress=self.config.auto_decompress,
                trust_env=self.config.trust_env,
                headers={"User-Agent": "Constellation-Python-SDK/1.2.0"},
            )

            # Create concurrency semaphore
            self._semaphore = asyncio.Semaphore(self.config.semaphore_limit)

    async def close(self):
        """Close the HTTP client and clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()

        if self._connector:
            await self._connector.close()

    async def _check_rate_limit(self, network_config: NetworkConfig):
        """Check and enforce rate limiting."""
        current_time = time.time()

        # Reset rate limit window if needed
        if (
            current_time - self._rate_limit_window_start
            >= network_config.rate_limit_window
        ):
            self._rate_limit_window_start = current_time
            self._request_count = 0

        # Check if we've exceeded the rate limit
        if self._request_count >= network_config.rate_limit_requests:
            sleep_time = network_config.rate_limit_window - (
                current_time - self._rate_limit_window_start
            )
            if sleep_time > 0:
                self.logger.logger.warning(
                    f"Rate limit exceeded, sleeping for {sleep_time:.2f}s"
                )
                await asyncio.sleep(sleep_time)
                self._rate_limit_window_start = time.time()
                self._request_count = 0

        self._request_count += 1

    async def request(
        self, method: str, url: str, network_config: NetworkConfig, **kwargs
    ) -> Dict[str, Any]:
        """
        Make an async HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            network_config: Network configuration for timeouts and retries
            **kwargs: Additional arguments for the request

        Returns:
            JSON response data

        Raises:
            NetworkError: For network-related errors
            TimeoutError: For timeout errors
            HTTPError: For HTTP errors
            APIError: For API-specific errors
        """
        await self._ensure_session()

        # Check rate limiting
        await self._check_rate_limit(network_config)

        # Acquire semaphore for concurrency control
        async with self._semaphore:
            return await self._make_request_with_retries(
                method, url, network_config, **kwargs
            )

    async def _make_request_with_retries(
        self, method: str, url: str, network_config: NetworkConfig, **kwargs
    ) -> Dict[str, Any]:
        """Make request with retry logic."""
        last_exception = None

        for attempt in range(network_config.max_retries + 1):
            try:
                start_time = time.time()

                self.logger.logger.debug(
                    f"Making {method} request to {url} (attempt {attempt + 1})"
                )

                async with self._session.request(method, url, **kwargs) as response:
                    # Log performance
                    elapsed = time.time() - start_time
                    self.perf_tracker.end_operation(
                        f"http_{method.lower()}", success=True
                    )

                    # Check for HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise HTTPError(
                            f"HTTP {response.status}: {error_text}",
                            status_code=response.status,
                            response_text=error_text,
                        )

                    # Parse JSON response
                    try:
                        data = await response.json()
                        self.logger.logger.debug(f"Request successful: {method} {url}")
                        return data
                    except json.JSONDecodeError as e:
                        text = await response.text()
                        raise APIError(
                            f"Invalid JSON response: {e}", response_text=text
                        )

            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(f"Request timeout: {url}")
                self.logger.logger.warning(f"Timeout on attempt {attempt + 1}: {url}")

            except aiohttp.ClientConnectionError as e:
                last_exception = ConnectionError(f"Connection error: {e}")
                self.logger.logger.warning(
                    f"Connection error on attempt {attempt + 1}: {e}"
                )

            except HTTPError:
                # Don't retry HTTP errors (4xx, 5xx)
                raise

            except Exception as e:
                last_exception = NetworkError(f"Network error: {e}")
                self.logger.logger.warning(
                    f"Network error on attempt {attempt + 1}: {e}"
                )

            # Wait before retry (with exponential backoff)
            if attempt < network_config.max_retries:
                delay = network_config.retry_delay * (2**attempt)
                self.logger.logger.debug(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)

        # All retries exhausted
        raise last_exception


class AsyncNetwork:
    """
    Async network client for Constellation Network operations.

    Provides high-performance async operations for balance queries,
    transaction submission, and node information retrieval.
    """

    def __init__(self, network_config: Optional[NetworkConfig] = None):
        """
        Initialize async network client.

        Args:
            network_config: Optional network configuration. Uses global config if not provided.
        """
        self.config = network_config or get_config().network
        self.http_client = AsyncHTTPClient()
        self.logger = get_network_logger()
        self.perf_tracker = get_performance_tracker()

        # Cache for responses (simple in-memory cache)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_times: Dict[str, float] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.__aexit__(exc_type, exc_val, exc_tb)

    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key for requests."""
        key = endpoint
        if params:
            # Sort params for consistent keys
            sorted_params = sorted(params.items())
            key += "?" + "&".join(f"{k}={v}" for k, v in sorted_params)
        return key

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid."""
        if cache_key not in self._cache:
            return False

        cache_config = get_config().cache
        if not cache_config.enable_caching:
            return False

        cache_time = self._cache_times.get(cache_key, 0)
        return (time.time() - cache_time) < cache_config.cache_ttl

    def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache a response."""
        cache_config = get_config().cache
        if not cache_config.enable_caching:
            return

        # Simple cache size management
        if len(self._cache) >= cache_config.max_cache_size:
            # Remove oldest entry
            oldest_key = min(
                self._cache_times.keys(), key=lambda k: self._cache_times[k]
            )
            del self._cache[oldest_key]
            del self._cache_times[oldest_key]

        self._cache[cache_key] = response
        self._cache_times[cache_key] = time.time()

    async def get_node_info(self) -> Dict[str, Any]:
        """
        Get node information asynchronously.

        Returns:
            Dictionary containing node information
        """
        cache_key = self._get_cache_key("/node/info")

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug("Returning cached node info")
            return self._cache[cache_key]

        url = urljoin(self.config.l0_url, "/node/info")

        try:
            response = await self.http_client.request("GET", url, self.config)
            self._cache_response(cache_key, response)
            return response
        except Exception as e:
            raise NetworkError(f"Failed to get node info: {e}") from e

    async def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get balance for a DAG address asynchronously.

        Args:
            address: DAG address to query

        Returns:
            Dictionary containing balance information
        """
        # Validate address
        AddressValidator.validate(address)

        cache_key = self._get_cache_key(f"/addresses/{address}/balance")

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug(f"Returning cached balance for {address}")
            return self._cache[cache_key]

        url = urljoin(self.config.l0_url, f"/addresses/{address}/balance")

        try:
            response = await self.http_client.request("GET", url, self.config)
            self._cache_response(cache_key, response)
            return response
        except Exception as e:
            raise NetworkError(f"Failed to get balance for {address}: {e}") from e

    async def get_transaction_info(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction information asynchronously.

        Args:
            tx_hash: Transaction hash to query

        Returns:
            Dictionary containing transaction information
        """
        url = urljoin(self.config.l0_url, f"/transactions/{tx_hash}")

        try:
            return await self.http_client.request("GET", url, self.config)
        except Exception as e:
            raise NetworkError(
                f"Failed to get transaction info for {tx_hash}: {e}"
            ) from e

    async def submit_transaction(
        self, transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit a transaction asynchronously.

        Args:
            transaction_data: Transaction data to submit

        Returns:
            Dictionary containing submission response
        """
        url = urljoin(self.config.l1_url, "/transactions")

        try:
            return await self.http_client.request(
                "POST",
                url,
                self.config,
                json=transaction_data,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            raise NetworkError(f"Failed to submit transaction: {e}") from e

    async def get_latest_snapshot(self) -> Dict[str, Any]:
        """
        Get latest snapshot information asynchronously.

        Returns:
            Dictionary containing latest snapshot data
        """
        cache_key = self._get_cache_key("/snapshots/latest")

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug("Returning cached latest snapshot")
            return self._cache[cache_key]

        url = urljoin(self.config.l0_url, "/snapshots/latest")

        try:
            response = await self.http_client.request("GET", url, self.config)
            self._cache_response(cache_key, response)
            return response
        except Exception as e:
            raise NetworkError(f"Failed to get latest snapshot: {e}") from e

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
            raise NetworkError(f"Failed to get batch balances: {e}") from e

    async def health_check(self) -> bool:
        """
        Perform async health check on the network.

        Returns:
            True if network is healthy, False otherwise
        """
        try:
            self.perf_tracker.start_operation("health_check")
            start_time = time.time()
            await self.get_node_info()
            elapsed = time.time() - start_time

            self.perf_tracker.end_operation("health_check", success=True)
            self.logger.logger.info(f"Health check passed in {elapsed:.2f}s")
            return True

        except Exception as e:
            self.logger.logger.error(f"Health check failed: {e}")
            return False

    def clear_cache(self):
        """Clear all cached responses."""
        self._cache.clear()
        self._cache_times.clear()
        self.logger.logger.debug("Cache cleared")

    # ========================================
    # Batch Operations (Enhanced REST Phase 1)
    # ========================================

    async def batch_request(self, operations: List[BatchOperation]) -> BatchResponse:
        """
        Execute multiple operations in a single batch request asynchronously.

        This method provides enhanced REST capabilities by executing multiple
        operations efficiently and concurrently, providing superior performance
        compared to the synchronous batch_request method.

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
            >>> response = await network.batch_request(operations)
            >>> print(f"Success rate: {response.success_rate()}%")
        """
        start_time = time.time()

        # Validate batch operations
        validation_errors = BatchValidator.validate_batch(operations)
        if validation_errors:
            raise NetworkError(
                f"Batch validation failed: {'; '.join(validation_errors)}"
            )

        # Create concurrent tasks for all operations
        tasks = [
            self._execute_single_operation_async(operation) for operation in operations
        ]

        try:
            # Execute all operations concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            batch_results = []
            for operation, result in zip(operations, results):
                if isinstance(result, Exception):
                    batch_results.append(
                        BatchResult(
                            operation=operation.operation,
                            success=False,
                            error=str(result),
                            id=operation.id,
                        )
                    )
                else:
                    batch_results.append(
                        BatchResult(
                            operation=operation.operation,
                            success=True,
                            data=result,
                            id=operation.id,
                        )
                    )

        except Exception as e:
            # If gather itself fails, create error results for all operations
            batch_results = [
                BatchResult(
                    operation=operation.operation,
                    success=False,
                    error=str(e),
                    id=operation.id,
                )
                for operation in operations
            ]

        execution_time = time.time() - start_time

        # Create summary statistics
        successful_ops = [r for r in batch_results if r.success]
        failed_ops = [r for r in batch_results if not r.success]

        summary = {
            "total_operations": len(operations),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate": len(successful_ops) / len(operations) * 100,
            "execution_time": execution_time,
            "concurrent_execution": True,
        }

        return BatchResponse(
            results=batch_results, summary=summary, execution_time=execution_time
        )

    async def _execute_single_operation_async(self, operation: BatchOperation) -> Any:
        """
        Execute a single batch operation asynchronously.

        Args:
            operation: Batch operation to execute

        Returns:
            Operation result

        Raises:
            NetworkError: If operation fails
        """
        if operation.operation == BatchOperationType.GET_BALANCE:
            return await self.get_balance(operation.params["address"])

        elif operation.operation == BatchOperationType.GET_ORDINAL:
            return await self.get_ordinal(operation.params["address"])

        elif operation.operation == BatchOperationType.GET_TRANSACTIONS:
            address = operation.params["address"]
            limit = operation.params.get("limit", 10)
            return await self.get_transactions(address, limit)

        elif operation.operation == BatchOperationType.GET_RECENT_TRANSACTIONS:
            limit = operation.params.get("limit", 50)
            return await self.get_recent_transactions(limit)

        elif operation.operation == BatchOperationType.GET_NODE_INFO:
            return await self.get_node_info()

        elif operation.operation == BatchOperationType.GET_CLUSTER_INFO:
            return await self.get_cluster_info()

        elif operation.operation == BatchOperationType.SUBMIT_TRANSACTION:
            return await self.submit_transaction(operation.params["transaction"])

        else:
            raise NetworkError(f"Unsupported batch operation: {operation.operation}")

    async def get_multi_balance_enhanced(self, addresses: List[str]) -> Dict[str, int]:
        """
        Get balances for multiple addresses using enhanced batch operations.

        This method uses the new batch operations system and provides better
        error handling and performance tracking compared to the existing
        batch_get_balances method.

        Args:
            addresses: List of DAG addresses

        Returns:
            Dictionary mapping addresses to balances
        """
        operations = batch_get_balances(addresses)
        response = await self.batch_request(operations)

        result = {}
        for i, address in enumerate(addresses):
            operation_result = response.get_result(f"balance_{i}")
            if operation_result and operation_result.success:
                # Extract balance from response data
                balance_data = operation_result.data
                if isinstance(balance_data, dict):
                    result[address] = balance_data.get("data", {}).get("balance", 0)
                else:
                    result[address] = balance_data
            else:
                result[address] = 0  # Default to 0 if operation failed

        return result

    async def get_multi_ordinal(self, addresses: List[str]) -> Dict[str, int]:
        """
        Get ordinals for multiple addresses in a single batch request.

        Args:
            addresses: List of DAG addresses

        Returns:
            Dictionary mapping addresses to ordinals
        """
        operations = batch_get_ordinals(addresses)
        response = await self.batch_request(operations)

        result = {}
        for i, address in enumerate(addresses):
            operation_result = response.get_result(f"ordinal_{i}")
            if operation_result and operation_result.success:
                result[address] = operation_result.data
            else:
                result[address] = 0  # Default to 0 if operation failed

        return result

    async def get_multi_transactions(
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
        response = await self.batch_request(operations)

        result = {}
        for i, address in enumerate(addresses):
            operation_result = response.get_result(f"transactions_{i}")
            if operation_result and operation_result.success:
                result[address] = operation_result.data
            else:
                result[address] = []  # Default to empty list if operation failed

        return result

    async def get_address_overview(self, address: str) -> Dict[str, Any]:
        """
        Get comprehensive address overview in a single batch request.

        Args:
            address: DAG address

        Returns:
            Dictionary with balance, ordinal, and recent transactions
        """
        operations = [
            create_batch_operation("get_balance", {"address": address}, "balance"),
            create_batch_operation("get_ordinal", {"address": address}, "ordinal"),
            create_batch_operation(
                "get_transactions", {"address": address, "limit": 10}, "transactions"
            ),
        ]

        response = await self.batch_request(operations)

        # Extract results
        balance_result = response.get_result("balance")
        ordinal_result = response.get_result("ordinal")
        transactions_result = response.get_result("transactions")

        # Extract balance from response data
        balance_value = 0
        if balance_result and balance_result.success:
            balance_data = balance_result.data
            if isinstance(balance_data, dict):
                balance_value = balance_data.get("data", {}).get("balance", 0)
            else:
                balance_value = balance_data

        return {
            "address": address,
            "balance": balance_value,
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

    async def get_ordinal(self, address: str) -> int:
        """
        Get address ordinal (transaction count) asynchronously.

        Args:
            address: DAG address

        Returns:
            Address ordinal (transaction count)
        """
        cache_key = self._get_cache_key(f"/addresses/{address}/ordinal")

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug(f"Returning cached ordinal for {address}")
            return self._cache[cache_key]

        url = urljoin(self.config.be_url, f"/addresses/{address}/ordinal")

        try:
            response = await self.http_client.request("GET", url, self.config)
            ordinal = response.get("data", {}).get("ordinal", 0)
            self._cache_response(cache_key, ordinal)
            return ordinal
        except Exception as e:
            self.logger.logger.warning(f"Failed to get ordinal for {address}: {e}")
            return 0  # Default to 0 if operation failed

    async def get_transactions(
        self, address: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific address asynchronously.

        Args:
            address: DAG address
            limit: Maximum number of transactions to return

        Returns:
            List of transaction data
        """
        cache_key = self._get_cache_key(
            f"/addresses/{address}/transactions", {"limit": limit}
        )

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug(f"Returning cached transactions for {address}")
            return self._cache[cache_key]

        url = urljoin(self.config.be_url, f"/addresses/{address}/transactions")

        try:
            response = await self.http_client.request(
                "GET", url, self.config, params={"limit": limit}
            )
            transactions = response.get("data", [])
            self._cache_response(cache_key, transactions)
            return transactions
        except Exception as e:
            self.logger.logger.warning(f"Failed to get transactions for {address}: {e}")
            return []  # Default to empty list if operation failed

    async def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent transactions from the network asynchronously.

        Args:
            limit: Maximum number of transactions to return

        Returns:
            List of transaction data
        """
        cache_key = self._get_cache_key("/transactions", {"limit": limit})

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug("Returning cached recent transactions")
            return self._cache[cache_key]

        url = urljoin(self.config.be_url, "/transactions")

        try:
            response = await self.http_client.request(
                "GET", url, self.config, params={"limit": limit}
            )
            transactions = response.get("data", [])
            self._cache_response(cache_key, transactions)
            return transactions
        except Exception as e:
            self.logger.logger.warning(f"Failed to get recent transactions: {e}")
            return []  # Default to empty list if operation failed

    async def get_cluster_info(self) -> List[Dict[str, Any]]:
        """
        Get cluster information asynchronously.

        Returns:
            List of cluster node information
        """
        cache_key = self._get_cache_key("/cluster/info")

        if self._is_cache_valid(cache_key):
            self.logger.logger.debug("Returning cached cluster info")
            return self._cache[cache_key]

        url = urljoin(self.config.l0_url, "/cluster/info")

        try:
            response = await self.http_client.request("GET", url, self.config)
            cluster_info = response.get("data", [])
            self._cache_response(cache_key, cluster_info)
            return cluster_info
        except Exception as e:
            self.logger.logger.warning(f"Failed to get cluster info: {e}")
            return []  # Default to empty list if operation failed


# Utility functions for async operations
async def create_async_network(
    network_config: Optional[NetworkConfig] = None,
) -> AsyncNetwork:
    """
    Create and initialize an async network client.

    Args:
        network_config: Optional network configuration

    Returns:
        Initialized AsyncNetwork instance
    """
    network = AsyncNetwork(network_config)
    await network.__aenter__()
    return network


async def get_multiple_balances_concurrent(
    addresses: List[str], network_config: Optional[NetworkConfig] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to get multiple balances concurrently.

    Args:
        addresses: List of DAG addresses
        network_config: Optional network configuration

    Returns:
        Dictionary mapping addresses to balance information
    """
    async with AsyncNetwork(network_config) as network:
        return await network.batch_get_balances(addresses)
