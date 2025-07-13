"""
Tests for the AsyncMetagraphClient's new submission and status features.
"""

import pytest
from unittest.mock import AsyncMock, patch
import pytest_asyncio

# Try to import async components
try:
    from constellation_sdk.async_metagraph import AsyncMetagraphClient
    from constellation_sdk.exceptions import ConstellationError, NetworkError
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    AsyncMetagraphClient = None
    ConstellationError = None
    NetworkError = None

# Skip all tests if async components are not available
pytestmark = pytest.mark.skipif(
    not ASYNC_AVAILABLE, reason="aiohttp not available, async components disabled"
)


@pytest.mark.asyncio
class TestAsyncMetagraphSubmissions:
    """Tests for new async submission and status features."""

    @pytest.fixture
    def client(self):
        """Fixture for an AsyncMetagraphClient with a mocked network object."""
        # This approach avoids the complexities of async generators in fixtures.
        client = AsyncMetagraphClient("test_metagraph_id")
        client.network = AsyncMock()
        return client

    async def test_submit_transaction_success(self, client):
        """Test successful async transaction submission."""
        signed_tx = {"value": "some_tx_data", "proofs": []}
        expected_hash = {"hash": "tx_hash_abc"}
        client.network.submit_transaction.return_value = expected_hash

        result = await client.submit_transaction(signed_tx)

        client.network.submit_transaction.assert_called_once_with(signed_tx)
        assert result == expected_hash

    async def test_get_transaction_status_confirmed(self, client):
        """Test confirmed async transaction status."""
        tx_hash = "confirmed_hash"
        client.network.get_transaction.return_value = {"blockHash": "some_block_hash"}

        status = await client.get_transaction_status(tx_hash)

        client.network.get_transaction.assert_called_once_with(tx_hash)
        assert status == "confirmed"

    async def test_get_transaction_status_pending(self, client):
        """Test pending async transaction status."""
        tx_hash = "pending_hash"
        client.network.get_transaction.return_value = {"blockHash": None}

        status = await client.get_transaction_status(tx_hash)
        assert status == "pending"

    async def test_get_transaction_status_not_found(self, client):
        """Test not_found async transaction status."""
        tx_hash = "not_found_hash"
        client.network.get_transaction.return_value = None

        status = await client.get_transaction_status(tx_hash)
        assert status == "not_found"

    @patch("asyncio.sleep", return_value=None)
    async def test_wait_for_confirmation_success(self, mock_sleep, client):
        """Test successful async wait for transaction confirmation."""
        tx_hash = "wait_success_hash"
        pending_tx = {"blockHash": None}
        confirmed_tx = {"blockHash": "block_hash_xyz"}

        client.network.get_transaction.side_effect = [pending_tx, confirmed_tx]

        result = await client.wait_for_confirmation(tx_hash, poll_interval=0)

        assert client.network.get_transaction.call_count == 2
        assert result == confirmed_tx

    @patch("asyncio.sleep", return_value=None)
    async def test_wait_for_confirmation_timeout(self, mock_sleep, client):
        """Test timeout during async wait for confirmation."""
        tx_hash = "wait_timeout_hash"
        client.network.get_transaction.return_value = {"blockHash": None}

        with pytest.raises(ConstellationError, match="not confirmed after"):
            await client.wait_for_confirmation(tx_hash, timeout=0.1, poll_interval=0.05)

    async def test_get_custom_state_success(self, client):
        """Test successful async custom state retrieval."""
        client.network.http_client.request.return_value = {"data": {"my_key": "my_value"}}

        state = await client.get_custom_state("my_key")

        assert state == {"my_key": "my_value"}
        client.network.http_client.request.assert_called_once()
        # More specific URL assertion could be added here if needed

    async def test_get_custom_state_not_found(self, client):
        """Test async custom state retrieval when key not found."""
        client.network.http_client.request.side_effect = NetworkError("Not Found", status_code=404)

        state = await client.get_custom_state("not_found_key")

        assert state is None 