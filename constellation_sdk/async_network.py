"""
Async Network client for Constellation Network operations.

Provides non-blocking HTTP operations using aiohttp for improved performance
and scalability. Supports connection pooling, retries, caching, and
comprehensive error handling.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urljoin
import json

try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, ClientResponse
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    # Fallback types for when aiohttp is not available
    ClientSession = None
    ClientTimeout = None
    ClientResponse = None

from .config import get_config, NetworkConfig, AsyncConfig
from .exceptions import (
    NetworkError, ConnectionError, TimeoutError, HTTPError, APIError,
    ConstellationError
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
                enable_cleanup_closed=True
            )
            
            # Create timeout configuration
            timeout = ClientTimeout(
                total=self.config.total_timeout,
                connect=self.config.connect_timeout,
                sock_read=self.config.read_timeout
            )
            
            # Create session with all configurations
            self._session = ClientSession(
                connector=self._connector,
                timeout=timeout,
                auto_decompress=self.config.auto_decompress,
                trust_env=self.config.trust_env,
                headers={'User-Agent': 'Constellation-Python-SDK/1.2.0'}
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
        if current_time - self._rate_limit_window_start >= network_config.rate_limit_window:
            self._rate_limit_window_start = current_time
            self._request_count = 0
        
        # Check if we've exceeded the rate limit
        if self._request_count >= network_config.rate_limit_requests:
            sleep_time = network_config.rate_limit_window - (current_time - self._rate_limit_window_start)
            if sleep_time > 0:
                self.logger.logger.warning(f"Rate limit exceeded, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self._rate_limit_window_start = time.time()
                self._request_count = 0
        
        self._request_count += 1
    
    async def request(
        self,
        method: str,
        url: str,
        network_config: NetworkConfig,
        **kwargs
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
            return await self._make_request_with_retries(method, url, network_config, **kwargs)
    
    async def _make_request_with_retries(
        self,
        method: str,
        url: str,
        network_config: NetworkConfig,
        **kwargs
    ) -> Dict[str, Any]:
        """Make request with retry logic."""
        last_exception = None
        
        for attempt in range(network_config.max_retries + 1):
            try:
                start_time = time.time()
                
                self.logger.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                async with self._session.request(method, url, **kwargs) as response:
                    # Log performance
                    elapsed = time.time() - start_time
                    self.perf_tracker.end_operation(f"http_{method.lower()}", success=True)
                    
                    # Check for HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise HTTPError(
                            f"HTTP {response.status}: {error_text}",
                            status_code=response.status,
                            response_text=error_text
                        )
                    
                    # Parse JSON response
                    try:
                        data = await response.json()
                        self.logger.logger.debug(f"Request successful: {method} {url}")
                        return data
                    except json.JSONDecodeError as e:
                        text = await response.text()
                        raise APIError(f"Invalid JSON response: {e}", response_text=text)
            
            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(f"Request timeout: {url}")
                self.logger.logger.warning(f"Timeout on attempt {attempt + 1}: {url}")
            
            except aiohttp.ClientConnectionError as e:
                last_exception = ConnectionError(f"Connection error: {e}")
                self.logger.logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
            
            except HTTPError:
                # Don't retry HTTP errors (4xx, 5xx)
                raise
            
            except Exception as e:
                last_exception = NetworkError(f"Network error: {e}")
                self.logger.logger.warning(f"Network error on attempt {attempt + 1}: {e}")
            
            # Wait before retry (with exponential backoff)
            if attempt < network_config.max_retries:
                delay = network_config.retry_delay * (2 ** attempt)
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
            oldest_key = min(self._cache_times.keys(), key=lambda k: self._cache_times[k])
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
            raise NetworkError(f"Failed to get transaction info for {tx_hash}: {e}") from e
    
    async def submit_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
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
                headers={'Content-Type': 'application/json'}
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
    
    async def batch_get_balances(self, addresses: List[str]) -> Dict[str, Dict[str, Any]]:
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
                    self.logger.logger.warning(f"Failed to get balance for {address}: {result}")
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


# Utility functions for async operations
async def create_async_network(network_config: Optional[NetworkConfig] = None) -> AsyncNetwork:
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
    addresses: List[str],
    network_config: Optional[NetworkConfig] = None
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