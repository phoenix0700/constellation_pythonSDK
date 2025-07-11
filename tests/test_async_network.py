"""
Tests for async network components.

Tests AsyncHTTPClient, AsyncNetwork, and related functionality
with proper async/await patterns and mocking.
"""

import asyncio
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Try to import async components
try:
    from constellation_sdk.async_network import (
        AsyncHTTPClient,
        AsyncNetwork,
        create_async_network,
        get_multiple_balances_concurrent,
    )
    from constellation_sdk.config import AsyncConfig, NetworkConfig
    from constellation_sdk.exceptions import HTTPError, NetworkError, TimeoutError

    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    AsyncHTTPClient = None
    AsyncNetwork = None


# Skip all tests if async components are not available
pytestmark = pytest.mark.skipif(
    not ASYNC_AVAILABLE, reason="aiohttp not available, async components disabled"
)


@pytest.mark.asyncio
class TestAsyncHTTPClient:
    """Test AsyncHTTPClient class."""

    async def test_http_client_creation(self):
        """Test async HTTP client creation."""
        async_config = AsyncConfig()
        client = AsyncHTTPClient(async_config)

        assert client.config == async_config
        assert client._session is None

        await client.close()  # Cleanup

    async def test_context_manager(self):
        """Test async HTTP client as context manager."""
        async_config = AsyncConfig()

        async with AsyncHTTPClient(async_config) as client:
            await client._ensure_session()
            assert client._session is not None
            assert not client._session.closed

        # Session should be closed after context manager
        assert client._session.closed

    @patch("constellation_sdk.async_network.ClientSession")
    async def test_session_creation(self, mock_session_class):
        """Test session creation with proper configuration."""
        mock_session = AsyncMock()
        mock_session.closed = False
        mock_session_class.return_value = mock_session

        async_config = AsyncConfig(
            connector_limit=200, total_timeout=60, verify_ssl=False
        )

        client = AsyncHTTPClient(async_config)
        await client._ensure_session()

        # Verify session was created with correct parameters
        mock_session_class.assert_called_once()
        call_args = mock_session_class.call_args

        # Verify important configuration parameters were passed
        assert "connector" in call_args.kwargs
        assert "timeout" in call_args.kwargs
        assert "headers" in call_args.kwargs
        assert (
            call_args.kwargs["headers"]["User-Agent"]
            == "Constellation-Python-SDK/1.2.0"
        )

        await client.close()

    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
            rate_limit_requests=2,
            rate_limit_window=1,
        )

        client = AsyncHTTPClient()

        # Reset rate limiting state
        client._request_count = 0
        client._rate_limit_window_start = time.time()

        # First two requests should be fast
        start_time = time.time()
        await client._check_rate_limit(network_config)
        await client._check_rate_limit(network_config)
        elapsed = time.time() - start_time

        assert elapsed < 0.1  # Should be very fast
        assert client._request_count == 2

        # Third request should trigger rate limiting (but we won't test the sleep)
        assert client._request_count == 2


@pytest.mark.asyncio
class TestAsyncNetwork:
    """Test AsyncNetwork class."""

    async def test_network_creation(self):
        """Test async network creation."""
        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        network = AsyncNetwork(network_config)

        assert network.config == network_config
        assert isinstance(network.http_client, AsyncHTTPClient)

        await network.__aexit__(None, None, None)

    async def test_context_manager(self):
        """Test async network as context manager."""
        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        async with AsyncNetwork(network_config) as network:
            assert network is not None
            # Context manager should initialize the HTTP client

    def test_cache_key_generation(self):
        """Test cache key generation."""
        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        network = AsyncNetwork(network_config)

        # Test simple cache key
        key1 = network._get_cache_key("/test/endpoint")
        assert key1 == "/test/endpoint"

        # Test cache key with parameters
        params = {"limit": 10, "order": "desc"}
        key2 = network._get_cache_key("/test", params)
        assert "limit=10" in key2
        assert "order=desc" in key2

    def test_cache_validation(self):
        """Test cache validation logic."""
        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        network = AsyncNetwork(network_config)

        # No cache entry
        assert not network._is_cache_valid("nonexistent")

        # Add cache entry
        cache_key = "test_key"
        network._cache_response(cache_key, {"data": "test"})

        # Should be valid immediately
        assert network._is_cache_valid(cache_key)

        # Manually expire cache
        network._cache_times[cache_key] = time.time() - 1000
        assert not network._is_cache_valid(cache_key)

    @patch("constellation_sdk.async_network.AsyncHTTPClient.request")
    async def test_get_node_info(self, mock_request):
        """Test get node info method."""
        mock_request.return_value = {"id": "test_node", "state": "ready"}

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        async with AsyncNetwork(network_config) as network:
            result = await network.get_node_info()

            assert result["id"] == "test_node"
            mock_request.assert_called_once()

            # Test caching - second call should use cache
            result2 = await network.get_node_info()
            assert result2 == result
            # Should still only have one call due to caching
            assert mock_request.call_count == 1

    @patch("constellation_sdk.async_network.AsyncHTTPClient.request")
    async def test_get_balance(self, mock_request):
        """Test get balance method."""
        mock_request.return_value = {"balance": "1000000", "address": "DAG123..."}

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        test_address = "DAG" + "1" * 35  # Valid test address

        async with AsyncNetwork(network_config) as network:
            result = await network.get_balance(test_address)

            assert "balance" in result
            mock_request.assert_called_once()

    @patch("constellation_sdk.async_network.AsyncHTTPClient.request")
    async def test_batch_get_balances(self, mock_request):
        """Test batch balance retrieval."""

        def mock_response(method, url, config):
            if "DAG111" in url:
                return {"balance": "1000", "address": "DAG111..."}
            elif "DAG222" in url:
                return {"balance": "2000", "address": "DAG222..."}
            else:
                raise Exception("Unknown address")

        mock_request.side_effect = mock_response

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        addresses = ["DAG" + "1" * 35, "DAG" + "2" * 35]  # Valid test addresses

        async with AsyncNetwork(network_config) as network:
            results = await network.batch_get_balances(addresses)

            assert len(results) == 2
            assert all(addr in results for addr in addresses)
            assert mock_request.call_count == 2

    @patch("constellation_sdk.async_network.AsyncHTTPClient.request")
    async def test_health_check(self, mock_request):
        """Test health check method."""
        mock_request.return_value = {"status": "healthy"}

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        async with AsyncNetwork(network_config) as network:
            result = await network.health_check()

            assert result is True
            mock_request.assert_called_once()

    @patch("constellation_sdk.async_network.AsyncHTTPClient.request")
    async def test_health_check_failure(self, mock_request):
        """Test health check failure handling."""
        mock_request.side_effect = NetworkError("Connection failed")

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        async with AsyncNetwork(network_config) as network:
            result = await network.health_check()

            assert result is False

    async def test_cache_operations(self):
        """Test cache operations."""
        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        network = AsyncNetwork(network_config)

        # Test cache response
        test_data = {"test": "data"}
        network._cache_response("test_key", test_data)

        assert "test_key" in network._cache
        assert network._cache["test_key"] == test_data

        # Test cache clearing
        network.clear_cache()
        assert len(network._cache) == 0
        assert len(network._cache_times) == 0


@pytest.mark.asyncio
class TestAsyncNetworkUtilities:
    """Test async network utility functions."""

    @patch("constellation_sdk.async_network.AsyncHTTPClient.request")
    async def test_create_async_network(self, mock_request):
        """Test create_async_network utility function."""
        mock_request.return_value = {"status": "ok"}

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        network = await create_async_network(network_config)

        assert isinstance(network, AsyncNetwork)
        # Network should be ready for use
        await network.__aexit__(None, None, None)

    @patch("constellation_sdk.async_network.AsyncNetwork.batch_get_balances")
    async def test_get_multiple_balances_concurrent(self, mock_batch_get):
        """Test get_multiple_balances_concurrent utility function."""
        mock_batch_get.return_value = {
            "DAG111...": {"balance": "1000"},
            "DAG222...": {"balance": "2000"},
        }

        addresses = ["DAG" + "1" * 35, "DAG" + "2" * 35]

        result = await get_multiple_balances_concurrent(addresses)

        assert len(result) == 2
        mock_batch_get.assert_called_once_with(addresses)


@pytest.mark.asyncio
class TestAsyncNetworkErrorHandling:
    """Test error handling in async network components."""

    @patch("constellation_sdk.async_network.AsyncHTTPClient.request")
    async def test_network_error_handling(self, mock_request):
        """Test network error handling."""
        mock_request.side_effect = NetworkError("Connection failed")

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        async with AsyncNetwork(network_config) as network:
            with pytest.raises(NetworkError):
                await network.get_node_info()

    async def test_validation_errors(self):
        """Test validation error handling."""
        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        async with AsyncNetwork(network_config) as network:
            # Invalid address should raise validation error
            with pytest.raises(Exception):  # ValidationError or similar
                await network.get_balance("invalid_address")


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncNetworkIntegration:
    """Integration tests for async network components."""

    async def test_full_async_workflow(self):
        """Test complete async workflow."""
        # This test would require actual network connections
        # For now, we'll just test the basic setup

        network_config = NetworkConfig(
            network_version="2.0",
            be_url="https://example.com",
            l0_url="https://l0.example.com",
            l1_url="https://l1.example.com",
            name="Test",
        )

        async with AsyncNetwork(network_config) as network:
            # Test that all components are properly initialized
            assert network.http_client is not None
            assert network.config == network_config
            assert hasattr(network, "_cache")
            assert hasattr(network, "_cache_times")
