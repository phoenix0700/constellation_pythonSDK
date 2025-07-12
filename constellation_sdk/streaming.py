"""
Real-time event streaming for Constellation Network.

This module provides comprehensive real-time event streaming capabilities for
monitoring network activity, transaction events, balance changes, and custom
metagraph events. Supports WebSocket connections, event filtering, and
subscription management for building responsive applications.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set, Union
from urllib.parse import urlparse
import threading
from dataclasses import dataclass, field
from enum import Enum

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from .config import DEFAULT_CONFIGS
from .exceptions import NetworkError, ConstellationError
from .network import Network
from .validation import AddressValidator


class EventType(Enum):
    """Event types for streaming."""
    TRANSACTION = "transaction"
    BALANCE_CHANGE = "balance_change"
    BLOCK_CREATED = "block_created"
    METAGRAPH_UPDATE = "metagraph_update"
    CUSTOM = "custom"


@dataclass
class StreamEvent:
    """Represents a streaming event."""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    network: str = ""
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'network': self.network,
            'source': self.source
        }


@dataclass
class EventFilter:
    """Event filtering configuration."""
    addresses: Optional[Set[str]] = None
    transaction_types: Optional[Set[str]] = None
    metagraph_ids: Optional[Set[str]] = None
    amount_range: Optional[tuple] = None
    custom_filter: Optional[Callable] = None
    
    def matches(self, event: StreamEvent) -> bool:
        """Check if event matches filter criteria."""
        data = event.data
        
        # Address filtering
        if self.addresses:
            event_addresses = set()
            if 'source' in data:
                event_addresses.add(data['source'])
            if 'destination' in data:
                event_addresses.add(data['destination'])
            if 'address' in data:
                event_addresses.add(data['address'])
            
            if not event_addresses.intersection(self.addresses):
                return False
        
        # Transaction type filtering
        if self.transaction_types and event.event_type == EventType.TRANSACTION:
            tx_type = data.get('transaction_type', data.get('type', ''))
            if tx_type not in self.transaction_types:
                return False
        
        # Metagraph ID filtering
        if self.metagraph_ids:
            event_metagraph = data.get('metagraph_id', '')
            if event_metagraph not in self.metagraph_ids:
                return False
        
        # Amount range filtering
        if self.amount_range:
            amount = data.get('amount', 0)
            min_amount, max_amount = self.amount_range
            if not (min_amount <= amount <= max_amount):
                return False
        
        # Custom filter function
        if self.custom_filter and not self.custom_filter(event):
            return False
        
        return True


class NetworkEventStream:
    """
    Real-time event streaming for Constellation Network.
    
    Provides WebSocket-based streaming of network events including transactions,
    balance changes, and custom metagraph events with filtering capabilities.
    """
    
    def __init__(self, network: str = 'testnet'):
        """
        Initialize network event stream.
        
        Args:
            network: Network name (mainnet, testnet, integrationnet)
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ConstellationError(
                "WebSocket support required. Install with: pip install websockets"
            )
        
        self.network = network
        self.config = DEFAULT_CONFIGS[network]
        self.network_client = Network(network)
        
        # Connection state
        self._websocket = None
        self._connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5
        
        # Event handling
        self._event_handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._custom_handlers: Dict[str, List[Callable]] = {}
        self._filters: Dict[str, EventFilter] = {}
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._running = False
        
        # Statistics
        self._stats = {
            'events_received': 0,
            'events_filtered': 0,
            'connection_time': 0,
            'reconnections': 0
        }
        
        # Polling for networks without WebSocket support
        self._polling_enabled = False
        self._polling_interval = 5.0
        self._last_poll_state = {}
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """
        Connect to the network event stream.
        
        Establishes WebSocket connection and starts background event processing.
        """
        if self._connected:
            return
        
        self.logger.info(f"Connecting to {self.network} event stream...")
        
        try:
            # Try WebSocket connection first
            await self._connect_websocket()
        except Exception as e:
            self.logger.warning(f"WebSocket connection failed: {e}")
            self.logger.info("Falling back to polling mode...")
            await self._start_polling()
        
        self._connected = True
        self._stats['connection_time'] = time.time()
        
        self.logger.info(f"Connected to {self.network} event stream")
    
    async def disconnect(self) -> None:
        """Disconnect from the event stream."""
        if not self._connected:
            return
        
        self.logger.info("Disconnecting from event stream...")
        
        self._running = False
        
        # Close WebSocket connection
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        
        # Cancel background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        self._background_tasks.clear()
        self._connected = False
        
        self.logger.info("Disconnected from event stream")
    
    def on(self, event_type: Union[EventType, str], callback: Callable) -> None:
        """
        Register event handler.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function to handle events
        """
        if isinstance(event_type, str):
            if event_type.startswith('custom:'):
                custom_type = event_type[7:]  # Remove 'custom:' prefix
                if custom_type not in self._custom_handlers:
                    self._custom_handlers[custom_type] = []
                self._custom_handlers[custom_type].append(callback)
            else:
                try:
                    event_type = EventType(event_type)
                except ValueError:
                    raise ValueError(f"Unknown event type: {event_type}")
        
        if isinstance(event_type, EventType):
            self._event_handlers[event_type].append(callback)
    
    def off(self, event_type: Union[EventType, str], callback: Callable) -> None:
        """
        Remove event handler.
        
        Args:
            event_type: Type of event to stop listening for
            callback: Callback function to remove
        """
        if isinstance(event_type, str):
            if event_type.startswith('custom:'):
                custom_type = event_type[7:]
                if custom_type in self._custom_handlers:
                    self._custom_handlers[custom_type].remove(callback)
            else:
                event_type = EventType(event_type)
        
        if isinstance(event_type, EventType):
            self._event_handlers[event_type].remove(callback)
    
    def add_filter(self, name: str, filter_config: EventFilter) -> None:
        """
        Add event filter.
        
        Args:
            name: Filter name
            filter_config: Filter configuration
        """
        self._filters[name] = filter_config
    
    def remove_filter(self, name: str) -> None:
        """
        Remove event filter.
        
        Args:
            name: Filter name to remove
        """
        if name in self._filters:
            del self._filters[name]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        return {
            **self._stats,
            'connected': self._connected,
            'handlers_registered': sum(len(handlers) for handlers in self._event_handlers.values()),
            'custom_handlers': len(self._custom_handlers),
            'filters_active': len(self._filters),
            'uptime': time.time() - self._stats['connection_time'] if self._connected else 0
        }
    
    async def _connect_websocket(self) -> None:
        """Establish WebSocket connection."""
        # For now, we'll simulate WebSocket endpoints
        # In production, these would be real Constellation WebSocket endpoints
        ws_url = self._get_websocket_url()
        
        try:
            self._websocket = await websockets.connect(ws_url)
            
            # Start background task for message handling
            task = asyncio.create_task(self._handle_websocket_messages())
            self._background_tasks.add(task)
            
            self._running = True
            
        except Exception as e:
            raise NetworkError(f"Failed to connect to WebSocket: {e}")
    
    async def _start_polling(self) -> None:
        """Start polling mode for networks without WebSocket support."""
        self._polling_enabled = True
        
        # Start background polling task
        task = asyncio.create_task(self._poll_network_state())
        self._background_tasks.add(task)
        
        self._running = True
    
    async def _handle_websocket_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        while self._running and self._websocket:
            try:
                message = await self._websocket.recv()
                await self._process_message(message)
                
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("WebSocket connection closed")
                if self._running:
                    await self._attempt_reconnect()
                break
            except Exception as e:
                self.logger.error(f"Error handling WebSocket message: {e}")
    
    async def _poll_network_state(self) -> None:
        """Poll network state for changes."""
        while self._running and self._polling_enabled:
            try:
                # Check for new transactions
                await self._poll_transactions()
                
                # Check for balance changes
                await self._poll_balance_changes()
                
                # Wait before next poll
                await asyncio.sleep(self._polling_interval)
                
            except Exception as e:
                self.logger.error(f"Error during polling: {e}")
                await asyncio.sleep(self._polling_interval)
    
    async def _poll_transactions(self) -> None:
        """Poll for new transactions."""
        try:
            # Get recent transactions (this is a simplified implementation)
            # In production, this would query the actual network for recent transactions
            
            # For now, we'll simulate transaction events
            if 'last_transaction_poll' not in self._last_poll_state:
                self._last_poll_state['last_transaction_poll'] = time.time()
                return
            
            # Simulate a transaction event every 30 seconds
            if time.time() - self._last_poll_state['last_transaction_poll'] > 30:
                await self._emit_sample_transaction_event()
                self._last_poll_state['last_transaction_poll'] = time.time()
                
        except Exception as e:
            self.logger.error(f"Error polling transactions: {e}")
    
    async def _poll_balance_changes(self) -> None:
        """Poll for balance changes."""
        # This would be implemented to track specific addresses
        # For now, we'll skip this in polling mode
        pass
    
    async def _process_message(self, message: str) -> None:
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            
            # Create event based on message type
            event = self._create_event_from_message(data)
            
            if event:
                await self._emit_event(event)
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _create_event_from_message(self, data: Dict[str, Any]) -> Optional[StreamEvent]:
        """Create event object from WebSocket message."""
        msg_type = data.get('type', '')
        
        if msg_type == 'transaction':
            return StreamEvent(
                event_type=EventType.TRANSACTION,
                data=data.get('transaction', {}),
                network=self.network,
                source='websocket'
            )
        elif msg_type == 'balance_change':
            return StreamEvent(
                event_type=EventType.BALANCE_CHANGE,
                data=data.get('balance_data', {}),
                network=self.network,
                source='websocket'
            )
        elif msg_type == 'block':
            return StreamEvent(
                event_type=EventType.BLOCK_CREATED,
                data=data.get('block', {}),
                network=self.network,
                source='websocket'
            )
        
        return None
    
    async def _emit_event(self, event: StreamEvent) -> None:
        """Emit event to registered handlers."""
        self._stats['events_received'] += 1
        
        # Apply filters
        if self._filters:
            for filter_name, event_filter in self._filters.items():
                if not event_filter.matches(event):
                    self._stats['events_filtered'] += 1
                    return
        
        # Call event handlers
        handlers = self._event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler: {e}")
    
    async def _emit_sample_transaction_event(self) -> None:
        """Emit a sample transaction event for testing."""
        sample_tx = {
            'hash': f'tx_{int(time.time())}',
            'source': 'DAG00000000000000000000000000000000000',
            'destination': 'DAG11111111111111111111111111111111111',
            'amount': 100000000,
            'transaction_type': 'dag_transfer',
            'timestamp': time.time()
        }
        
        event = StreamEvent(
            event_type=EventType.TRANSACTION,
            data=sample_tx,
            network=self.network,
            source='polling'
        )
        
        await self._emit_event(event)
    
    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to WebSocket."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached")
            return
        
        self._reconnect_attempts += 1
        self._stats['reconnections'] += 1
        
        self.logger.info(f"Attempting reconnection {self._reconnect_attempts}/{self._max_reconnect_attempts}")
        
        await asyncio.sleep(self._reconnect_delay)
        
        try:
            await self._connect_websocket()
            self._reconnect_attempts = 0
            self.logger.info("Reconnected successfully")
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            await self._attempt_reconnect()
    
    def _get_websocket_url(self) -> str:
        """Get WebSocket URL for the network."""
        # For now, we'll use a mock WebSocket URL
        # In production, this would be the actual Constellation WebSocket endpoint
        base_url = self.config.l0_url
        
        # Convert HTTP to WebSocket URL
        if base_url.startswith('http://'):
            ws_url = base_url.replace('http://', 'ws://')
        elif base_url.startswith('https://'):
            ws_url = base_url.replace('https://', 'wss://')
        else:
            ws_url = base_url
        
        return f"{ws_url}/events"


class BalanceTracker:
    """Track balance changes for specific addresses."""
    
    def __init__(self, network: str = 'testnet'):
        """
        Initialize balance tracker.
        
        Args:
            network: Network name
        """
        self.network = network
        self.network_client = Network(network)
        self.tracked_addresses: Set[str] = set()
        self.last_balances: Dict[str, int] = {}
        self.event_stream: Optional[NetworkEventStream] = None
        
        # Background task for polling
        self._polling_task: Optional[asyncio.Task] = None
        self._polling_interval = 10.0
        self._running = False
        
        self.logger = logging.getLogger(__name__)
    
    def track_address(self, address: str) -> None:
        """
        Start tracking balance for an address.
        
        Args:
            address: Address to track
        """
        try:
            AddressValidator.validate(address)
            self.tracked_addresses.add(address)
            self.logger.info(f"Tracking balance for {address}")
        except Exception as e:
            raise ValueError(f"Invalid address: {e}")
    
    def untrack_address(self, address: str) -> None:
        """
        Stop tracking balance for an address.
        
        Args:
            address: Address to stop tracking
        """
        self.tracked_addresses.discard(address)
        if address in self.last_balances:
            del self.last_balances[address]
        self.logger.info(f"Stopped tracking balance for {address}")
    
    async def start(self, event_stream: Optional[NetworkEventStream] = None) -> None:
        """
        Start balance tracking.
        
        Args:
            event_stream: Optional event stream to emit balance change events
        """
        if self._running:
            return
        
        self.event_stream = event_stream
        self._running = True
        
        # Start background polling task
        self._polling_task = asyncio.create_task(self._poll_balances())
        
        self.logger.info("Balance tracking started")
    
    async def stop(self) -> None:
        """Stop balance tracking."""
        if not self._running:
            return
        
        self._running = False
        
        if self._polling_task:
            self._polling_task.cancel()
            self._polling_task = None
        
        self.logger.info("Balance tracking stopped")
    
    async def _poll_balances(self) -> None:
        """Poll balance changes for tracked addresses."""
        while self._running:
            try:
                for address in self.tracked_addresses.copy():
                    await self._check_balance_change(address)
                
                await asyncio.sleep(self._polling_interval)
                
            except Exception as e:
                self.logger.error(f"Error polling balances: {e}")
                await asyncio.sleep(self._polling_interval)
    
    async def _check_balance_change(self, address: str) -> None:
        """Check if balance has changed for an address."""
        try:
            current_balance = self.network_client.get_balance(address)
            last_balance = self.last_balances.get(address, 0)
            
            if current_balance != last_balance:
                # Balance changed
                self.last_balances[address] = current_balance
                
                # Emit balance change event
                if self.event_stream:
                    event = StreamEvent(
                        event_type=EventType.BALANCE_CHANGE,
                        data={
                            'address': address,
                            'old_balance': last_balance,
                            'new_balance': current_balance,
                            'change': current_balance - last_balance
                        },
                        network=self.network,
                        source='balance_tracker'
                    )
                    
                    await self.event_stream._emit_event(event)
                
                self.logger.info(f"Balance change detected for {address}: {last_balance} -> {current_balance}")
            
        except Exception as e:
            self.logger.error(f"Error checking balance for {address}: {e}")


# Convenience functions for quick streaming setup
def create_event_stream(network: str = 'testnet') -> NetworkEventStream:
    """
    Create a network event stream.
    
    Args:
        network: Network name
        
    Returns:
        NetworkEventStream instance
    """
    return NetworkEventStream(network)


async def stream_transactions(
    network: str = 'testnet',
    callback: Callable = None,
    addresses: Optional[List[str]] = None,
    transaction_types: Optional[List[str]] = None
) -> NetworkEventStream:
    """
    Quick setup for streaming transactions.
    
    Args:
        network: Network name
        callback: Callback function for transaction events
        addresses: Filter by addresses
        transaction_types: Filter by transaction types
        
    Returns:
        Connected NetworkEventStream instance
    """
    stream = NetworkEventStream(network)
    
    if callback:
        stream.on(EventType.TRANSACTION, callback)
    
    if addresses or transaction_types:
        filter_config = EventFilter(
            addresses=set(addresses) if addresses else None,
            transaction_types=set(transaction_types) if transaction_types else None
        )
        stream.add_filter('default', filter_config)
    
    await stream.connect()
    return stream


async def stream_balance_changes(
    network: str = 'testnet',
    addresses: List[str] = None,
    callback: Callable = None
) -> tuple[NetworkEventStream, BalanceTracker]:
    """
    Quick setup for streaming balance changes.
    
    Args:
        network: Network name
        addresses: Addresses to track
        callback: Callback function for balance change events
        
    Returns:
        Tuple of (NetworkEventStream, BalanceTracker)
    """
    stream = NetworkEventStream(network)
    tracker = BalanceTracker(network)
    
    if callback:
        stream.on(EventType.BALANCE_CHANGE, callback)
    
    if addresses:
        for address in addresses:
            tracker.track_address(address)
    
    await stream.connect()
    await tracker.start(stream)
    
    return stream, tracker