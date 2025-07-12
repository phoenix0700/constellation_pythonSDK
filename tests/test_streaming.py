"""
Tests for real-time event streaming functionality.
"""

import asyncio
import json
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock

from constellation_sdk.streaming import (
    NetworkEventStream,
    BalanceTracker,
    EventType,
    StreamEvent,
    EventFilter,
    create_event_stream,
    stream_transactions,
    stream_balance_changes,
)
from constellation_sdk.exceptions import NetworkError, ConstellationError
from constellation_sdk.network import Network


class TestStreamEvent:
    """Test StreamEvent class."""
    
    def test_stream_event_creation(self):
        """Test StreamEvent creation."""
        event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"hash": "test_hash", "amount": 100000000},
            network="testnet",
            source="websocket"
        )
        
        assert event.event_type == EventType.TRANSACTION
        assert event.data["hash"] == "test_hash"
        assert event.data["amount"] == 100000000
        assert event.network == "testnet"
        assert event.source == "websocket"
        assert event.timestamp > 0
    
    def test_stream_event_to_dict(self):
        """Test StreamEvent to_dict method."""
        event = StreamEvent(
            event_type=EventType.BALANCE_CHANGE,
            data={"address": "DAG123", "old_balance": 0, "new_balance": 1000000000},
            network="mainnet"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "balance_change"
        assert event_dict["data"]["address"] == "DAG123"
        assert event_dict["network"] == "mainnet"
        assert "timestamp" in event_dict


class TestEventFilter:
    """Test EventFilter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
        self.valid_metagraph_id = "DAG22222222222222222222222222222222222"
    
    def test_address_filter(self):
        """Test filtering by addresses."""
        event_filter = EventFilter(addresses={self.valid_address1, self.valid_address2})
        
        # Event with matching address should pass
        matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"source": self.valid_address1, "destination": "DAG333..."},
            network="testnet"
        )
        assert event_filter.matches(matching_event)
        
        # Event with non-matching address should be filtered
        non_matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"source": "DAG999...", "destination": "DAG888..."},
            network="testnet"
        )
        assert not event_filter.matches(non_matching_event)
    
    def test_transaction_type_filter(self):
        """Test filtering by transaction types."""
        event_filter = EventFilter(transaction_types={"dag_transfer", "token_transfer"})
        
        # Event with matching transaction type should pass
        matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"transaction_type": "dag_transfer", "amount": 1000000000},
            network="testnet"
        )
        assert event_filter.matches(matching_event)
        
        # Event with non-matching transaction type should be filtered
        non_matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"transaction_type": "data_submission", "data": {}},
            network="testnet"
        )
        assert not event_filter.matches(non_matching_event)
    
    def test_metagraph_filter(self):
        """Test filtering by metagraph IDs."""
        event_filter = EventFilter(metagraph_ids={self.valid_metagraph_id})
        
        # Event with matching metagraph ID should pass
        matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"metagraph_id": self.valid_metagraph_id, "amount": 1000000000},
            network="testnet"
        )
        assert event_filter.matches(matching_event)
        
        # Event with non-matching metagraph ID should be filtered
        non_matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"metagraph_id": "DAG999...", "amount": 1000000000},
            network="testnet"
        )
        assert not event_filter.matches(non_matching_event)
    
    def test_amount_range_filter(self):
        """Test filtering by amount range."""
        event_filter = EventFilter(amount_range=(100000000, 1000000000))  # 1-10 DAG
        
        # Event with amount in range should pass
        matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"amount": 500000000},  # 5 DAG
            network="testnet"
        )
        assert event_filter.matches(matching_event)
        
        # Event with amount outside range should be filtered
        non_matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"amount": 50000000},  # 0.5 DAG
            network="testnet"
        )
        assert not event_filter.matches(non_matching_event)
    
    def test_custom_filter(self):
        """Test custom filter function."""
        def custom_filter_func(event):
            return event.data.get("priority", "normal") == "high"
        
        event_filter = EventFilter(custom_filter=custom_filter_func)
        
        # Event with high priority should pass
        high_priority_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"priority": "high", "amount": 1000000000},
            network="testnet"
        )
        assert event_filter.matches(high_priority_event)
        
        # Event with normal priority should be filtered
        normal_priority_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"priority": "normal", "amount": 1000000000},
            network="testnet"
        )
        assert not event_filter.matches(normal_priority_event)


class TestNetworkEventStream:
    """Test NetworkEventStream class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
        
        # Mock network and config
        self.mock_network = Mock(spec=Network)
        self.mock_network.get_balance.return_value = 1000000000
        
        with patch('constellation_sdk.streaming.Network', return_value=self.mock_network):
            with patch('constellation_sdk.config.get_config') as mock_get_config:
                mock_get_config.return_value.network.l0_url = 'http://localhost:8080'
                self.stream = NetworkEventStream('testnet')
    
    def test_stream_initialization(self):
        """Test NetworkEventStream initialization."""
        assert self.stream.network == 'testnet'
        assert not self.stream._connected
        assert self.stream._running == False
        assert len(self.stream._event_handlers) == len(EventType)
    
    def test_event_handler_registration(self):
        """Test event handler registration."""
        handler_called = False
        
        def test_handler(event):
            nonlocal handler_called
            handler_called = True
        
        # Register handler
        self.stream.on(EventType.TRANSACTION, test_handler)
        
        # Verify handler was registered
        assert test_handler in self.stream._event_handlers[EventType.TRANSACTION]
        
        # Remove handler
        self.stream.off(EventType.TRANSACTION, test_handler)
        
        # Verify handler was removed
        assert test_handler not in self.stream._event_handlers[EventType.TRANSACTION]
    
    def test_custom_event_handler_registration(self):
        """Test custom event handler registration."""
        handler_called = False
        
        def custom_handler(event):
            nonlocal handler_called
            handler_called = True
        
        # Register custom handler
        self.stream.on('custom:my_event', custom_handler)
        
        # Verify handler was registered
        assert custom_handler in self.stream._custom_handlers['my_event']
        
        # Remove handler
        self.stream.off('custom:my_event', custom_handler)
        
        # Verify handler was removed
        assert custom_handler not in self.stream._custom_handlers['my_event']
    
    def test_filter_management(self):
        """Test event filter management."""
        event_filter = EventFilter(addresses={self.valid_address1})
        
        # Add filter
        self.stream.add_filter('test_filter', event_filter)
        assert 'test_filter' in self.stream._filters
        
        # Remove filter
        self.stream.remove_filter('test_filter')
        assert 'test_filter' not in self.stream._filters
    
    def test_get_stats(self):
        """Test getting stream statistics."""
        stats = self.stream.get_stats()
        
        assert 'connected' in stats
        assert 'handlers_registered' in stats
        assert 'custom_handlers' in stats
        assert 'filters_active' in stats
        assert 'events_received' in stats
        assert 'events_filtered' in stats
        assert 'uptime' in stats
    
    @patch('constellation_sdk.streaming.websockets')
    async def test_websocket_connection_success(self, mock_websockets):
        """Test successful WebSocket connection."""
        mock_websocket = AsyncMock()
        mock_websockets.connect = AsyncMock(return_value=mock_websocket)
        
        # Mock message handling
        mock_websocket.recv.side_effect = [
            json.dumps({"type": "transaction", "transaction": {"hash": "test_hash"}}),
            asyncio.CancelledError()  # Simulate task cancellation
        ]
        
        try:
            await self.stream.connect()
            assert self.stream._connected
            assert self.stream._websocket is not None
        finally:
            await self.stream.disconnect()
    
    @patch('constellation_sdk.streaming.websockets')
    async def test_websocket_connection_failure(self, mock_websockets):
        """Test WebSocket connection failure with fallback to polling."""
        mock_websockets.connect.side_effect = Exception("Connection failed")
        
        # Mock polling behavior
        with patch.object(self.stream, '_start_polling', new_callable=AsyncMock) as mock_start_polling:
            await self.stream.connect()
            
            # Should have attempted WebSocket connection and fallen back to polling
            assert self.stream._connected
            mock_start_polling.assert_called_once()
    
    async def test_event_emission(self):
        """Test event emission to handlers."""
        events_received = []
        
        def test_handler(event):
            events_received.append(event)
        
        # Register handler
        self.stream.on(EventType.TRANSACTION, test_handler)
        
        # Create and emit test event
        test_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"hash": "test_hash", "amount": 1000000000},
            network="testnet"
        )
        
        await self.stream._emit_event(test_event)
        
        # Verify handler was called
        assert len(events_received) == 1
        assert events_received[0] == test_event
    
    async def test_event_filtering(self):
        """Test event filtering."""
        events_received = []
        
        def test_handler(event):
            events_received.append(event)
        
        # Register handler
        self.stream.on(EventType.TRANSACTION, test_handler)
        
        # Add filter
        event_filter = EventFilter(addresses={self.valid_address1})
        self.stream.add_filter('test_filter', event_filter)
        
        # Create events - one matching, one not
        matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"source": self.valid_address1, "amount": 1000000000},
            network="testnet"
        )
        
        non_matching_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"source": "DAG999...", "amount": 1000000000},
            network="testnet"
        )
        
        # Emit both events
        await self.stream._emit_event(matching_event)
        await self.stream._emit_event(non_matching_event)
        
        # Only matching event should have triggered handler
        assert len(events_received) == 1
        assert events_received[0] == matching_event
    
    async def test_async_event_handler(self):
        """Test async event handler."""
        events_received = []
        
        async def async_handler(event):
            await asyncio.sleep(0.01)  # Simulate async work
            events_received.append(event)
        
        # Register async handler
        self.stream.on(EventType.TRANSACTION, async_handler)
        
        # Create and emit test event
        test_event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data={"hash": "test_hash"},
            network="testnet"
        )
        
        await self.stream._emit_event(test_event)
        
        # Verify handler was called
        assert len(events_received) == 1
        assert events_received[0] == test_event


class TestBalanceTracker:
    """Test BalanceTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
        
        # Mock network
        self.mock_network = Mock(spec=Network)
        self.mock_network.get_balance.return_value = 1000000000
        
        with patch('constellation_sdk.streaming.Network', return_value=self.mock_network):
            self.tracker = BalanceTracker('testnet')
    
    def test_tracker_initialization(self):
        """Test BalanceTracker initialization."""
        assert self.tracker.network == 'testnet'
        assert len(self.tracker.tracked_addresses) == 0
        assert len(self.tracker.last_balances) == 0
        assert not self.tracker._running
    
    def test_track_address(self):
        """Test tracking address."""
        self.tracker.track_address(self.valid_address1)
        
        assert self.valid_address1 in self.tracker.tracked_addresses
        
        # Test invalid address
        with pytest.raises(ValueError):
            self.tracker.track_address("invalid_address")
    
    def test_untrack_address(self):
        """Test untracking address."""
        # First track an address
        self.tracker.track_address(self.valid_address1)
        self.tracker.last_balances[self.valid_address1] = 1000000000
        
        # Then untrack it
        self.tracker.untrack_address(self.valid_address1)
        
        assert self.valid_address1 not in self.tracker.tracked_addresses
        assert self.valid_address1 not in self.tracker.last_balances
    
    async def test_balance_change_detection(self):
        """Test balance change detection."""
        # Track an address
        self.tracker.track_address(self.valid_address1)
        
        # Set up initial balance
        self.tracker.last_balances[self.valid_address1] = 1000000000
        
        # Change balance
        self.mock_network.get_balance.return_value = 2000000000
        
        # Mock event stream
        mock_stream = Mock()
        mock_stream._emit_event = AsyncMock()
        
        # Check for balance change
        await self.tracker._check_balance_change(self.valid_address1)
        
        # Verify balance was updated
        assert self.tracker.last_balances[self.valid_address1] == 2000000000
    
    async def test_balance_tracker_lifecycle(self):
        """Test starting and stopping balance tracker."""
        # Mock event stream
        mock_stream = Mock()
        mock_stream._emit_event = AsyncMock()
        
        # Start tracker
        await self.tracker.start(mock_stream)
        assert self.tracker._running
        assert self.tracker.event_stream == mock_stream
        
        # Stop tracker
        await self.tracker.stop()
        assert not self.tracker._running


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
    
    def test_create_event_stream(self):
        """Test create_event_stream function."""
        with patch('constellation_sdk.streaming.NetworkEventStream') as mock_stream_class:
            mock_stream = Mock()
            mock_stream_class.return_value = mock_stream
            
            stream = create_event_stream('mainnet')
            
            mock_stream_class.assert_called_once_with('mainnet')
            assert stream == mock_stream
    
    @pytest.mark.asyncio
    async def test_stream_transactions(self):
        """Test stream_transactions convenience function."""
        mock_callback = Mock()
        
        with patch('constellation_sdk.streaming.NetworkEventStream') as mock_stream_class:
            mock_stream = Mock()
            mock_stream.on = Mock()
            mock_stream.add_filter = Mock()
            mock_stream.connect = AsyncMock()
            mock_stream_class.return_value = mock_stream
            
            stream = await stream_transactions(
                network='testnet',
                callback=mock_callback,
                addresses=[self.valid_address1],
                transaction_types=['dag_transfer']
            )
            
            # Verify stream was configured correctly
            mock_stream.on.assert_called_once_with(EventType.TRANSACTION, mock_callback)
            mock_stream.add_filter.assert_called_once()
            mock_stream.connect.assert_called_once()
            
            assert stream == mock_stream
    
    @pytest.mark.asyncio
    async def test_stream_balance_changes(self):
        """Test stream_balance_changes convenience function."""
        mock_callback = Mock()
        
        with patch('constellation_sdk.streaming.NetworkEventStream') as mock_stream_class:
            with patch('constellation_sdk.streaming.BalanceTracker') as mock_tracker_class:
                mock_stream = Mock()
                mock_stream.on = Mock()
                mock_stream.connect = AsyncMock()
                mock_stream_class.return_value = mock_stream
                
                mock_tracker = Mock()
                mock_tracker.track_address = Mock()
                mock_tracker.start = AsyncMock()
                mock_tracker_class.return_value = mock_tracker
                
                stream, tracker = await stream_balance_changes(
                    network='testnet',
                    addresses=[self.valid_address1, self.valid_address2],
                    callback=mock_callback
                )
                
                # Verify stream was configured correctly
                mock_stream.on.assert_called_once_with(EventType.BALANCE_CHANGE, mock_callback)
                mock_stream.connect.assert_called_once()
                
                # Verify tracker was configured correctly
                assert mock_tracker.track_address.call_count == 2
                mock_tracker.start.assert_called_once_with(mock_stream)
                
                assert stream == mock_stream
                assert tracker == mock_tracker


class TestStreamingIntegration:
    """Integration tests for streaming functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_address1 = "DAG00000000000000000000000000000000000"
        self.valid_address2 = "DAG11111111111111111111111111111111111"
        
        # Mock network
        self.mock_network = Mock(spec=Network)
        self.mock_network.get_balance.return_value = 1000000000
    
    @pytest.mark.asyncio
    async def test_end_to_end_streaming(self):
        """Test end-to-end streaming functionality."""
        events_received = []
        
        def event_handler(event):
            events_received.append(event)
        
        with patch('constellation_sdk.streaming.Network', return_value=self.mock_network):
            with patch('constellation_sdk.config.get_config') as mock_get_config:
                mock_get_config.return_value.network.l0_url = 'http://localhost:8080'
                # Create stream
                stream = NetworkEventStream('testnet')
                
                # Register handler
                stream.on(EventType.TRANSACTION, event_handler)
                
                # Add filter
                event_filter = EventFilter(addresses={self.valid_address1})
                stream.add_filter('test_filter', event_filter)
                
                # Mock polling mode (since WebSocket will fail in tests)
                with patch.object(stream, '_start_polling', new_callable=AsyncMock):
                    await stream.connect()
                    
                    # Emit a test event
                    test_event = StreamEvent(
                        event_type=EventType.TRANSACTION,
                        data={"source": self.valid_address1, "amount": 1000000000},
                        network="testnet"
                    )
                    
                    await stream._emit_event(test_event)
                    
                    # Verify event was received
                    assert len(events_received) == 1
                    assert events_received[0] == test_event
                    
                    # Test statistics
                    stats = stream.get_stats()
                    assert stats['events_received'] == 1
                    assert stats['connected'] == True
                    
                    await stream.disconnect()
    
    @pytest.mark.asyncio
    async def test_streaming_with_balance_tracker(self):
        """Test streaming with balance tracker integration."""
        balance_events = []
        
        def balance_handler(event):
            balance_events.append(event)
        
        with patch('constellation_sdk.streaming.Network', return_value=self.mock_network):
            with patch('constellation_sdk.config.get_config') as mock_get_config:
                mock_get_config.return_value.network.l0_url = 'http://localhost:8080'
                # Create stream and tracker
                stream = NetworkEventStream('testnet')
                tracker = BalanceTracker('testnet')
                
                # Register handler
                stream.on(EventType.BALANCE_CHANGE, balance_handler)
                
                # Track address
                tracker.track_address(self.valid_address1)
                
                # Mock polling mode
                with patch.object(stream, '_start_polling', new_callable=AsyncMock):
                    await stream.connect()
                    await tracker.start(stream)
                    
                    # Simulate balance change
                    tracker.last_balances[self.valid_address1] = 1000000000
                    self.mock_network.get_balance.return_value = 2000000000
                    
                    # Trigger balance check
                    await tracker._check_balance_change(self.valid_address1)
                    
                    # Verify balance change was detected
                    assert tracker.last_balances[self.valid_address1] == 2000000000
                    
                    await tracker.stop()
                    await stream.disconnect()


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.unit,
    pytest.mark.streaming,
]


# Mock tests that require WebSocket dependencies
@pytest.mark.skipif(not pytest.importorskip("websockets", reason="websockets not available"), 
                   reason="WebSocket tests require websockets package")
class TestStreamingWithWebSockets:
    """Tests that require actual WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_message_parsing(self):
        """Test WebSocket message parsing."""
        with patch('constellation_sdk.streaming.Network') as mock_network_class:
            with patch('constellation_sdk.config.get_config') as mock_get_config:
                mock_get_config.return_value.network.l0_url = 'ws://localhost:8080'
                mock_network = Mock()
                mock_network_class.return_value = mock_network
                
                stream = NetworkEventStream('testnet')
                
                # Test transaction message
                tx_message = {
                    "type": "transaction",
                    "transaction": {
                        "hash": "test_hash",
                        "source": "DAG123...",
                        "destination": "DAG456...",
                        "amount": 1000000000
                    }
                }
                
                event = stream._create_event_from_message(tx_message)
                
                assert event is not None
                assert event.event_type == EventType.TRANSACTION
                assert event.data["hash"] == "test_hash"
                assert event.data["amount"] == 1000000000
                
                # Test balance change message
                balance_message = {
                    "type": "balance_change",
                    "balance_data": {
                        "address": "DAG123...",
                        "old_balance": 1000000000,
                        "new_balance": 2000000000
                    }
                }
                
                event = stream._create_event_from_message(balance_message)
                
                assert event is not None
                assert event.event_type == EventType.BALANCE_CHANGE
                assert event.data["address"] == "DAG123..."
                assert event.data["old_balance"] == 1000000000
                assert event.data["new_balance"] == 2000000000


# Network-dependent tests (require actual network connection)
@pytest.mark.network
class TestStreamingWithRealNetwork:
    """Tests that require actual network connection."""
    
    @pytest.mark.asyncio
    async def test_real_network_streaming(self):
        """Test streaming with real network connection."""
        try:
            # This test would use real network connections
            # Skip for now as it requires actual Constellation WebSocket endpoints
            pytest.skip("Real network streaming test requires live WebSocket endpoints")
            
            # Example of how this would work:
            # stream = NetworkEventStream('testnet')
            # await stream.connect()
            # # ... test real streaming
            # await stream.disconnect()
            
        except Exception as e:
            pytest.skip(f"Real network streaming test skipped: {e}")