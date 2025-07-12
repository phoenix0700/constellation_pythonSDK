"""
Real-Time Event Streaming Demo - Constellation Network Python SDK

This example demonstrates how to use the real-time event streaming feature
to monitor live network activity, track balance changes, and build responsive
applications that react to blockchain events in real-time.
"""

import asyncio
import json
from constellation_sdk import (
    Account,
    Network,
    NetworkEventStream,
    BalanceTracker,
    EventType,
    EventFilter,
    create_event_stream,
    stream_transactions,
    stream_balance_changes,
    STREAMING_AVAILABLE,
)


async def main():
    """Demonstrate real-time event streaming capabilities."""
    print("🌊 Real-Time Event Streaming Demo - Constellation Network Python SDK")
    print("=" * 70)
    
    if not STREAMING_AVAILABLE:
        print("❌ Streaming not available. Install with: pip install websockets")
        return
    
    # Create accounts and network
    alice = Account()
    bob = Account()
    charlie = Account()
    network = Network('testnet')
    
    print(f"👤 Alice: {alice.address}")
    print(f"👤 Bob: {bob.address}")
    print(f"👤 Charlie: {charlie.address}")
    print(f"🌐 Network: {network.config.name}")
    print()
    
    # 1. Basic Transaction Streaming
    print("📊 1. Basic Transaction Streaming")
    print("-" * 40)
    
    # Create event stream
    stream = NetworkEventStream('testnet')
    
    # Transaction event handler
    def handle_transaction(event):
        print(f"📤 Transaction Event:")
        print(f"  Hash: {event.data.get('hash', 'N/A')}")
        print(f"  Type: {event.data.get('transaction_type', 'N/A')}")
        print(f"  From: {event.data.get('source', 'N/A')}")
        print(f"  To: {event.data.get('destination', 'N/A')}")
        print(f"  Amount: {event.data.get('amount', 0) / 1e8:.8f} DAG")
        print(f"  Network: {event.network}")
        print()
    
    # Register transaction handler
    stream.on(EventType.TRANSACTION, handle_transaction)
    
    try:
        # Connect to stream
        await stream.connect()
        print("✅ Connected to transaction stream")
        
        # Stream for 10 seconds
        print("⏳ Streaming for 10 seconds...")
        await asyncio.sleep(10)
        
        # Show statistics
        stats = stream.get_stats()
        print(f"📊 Statistics: {stats['events_received']} events received")
        print()
        
    except Exception as e:
        print(f"❌ Streaming error: {e}")
    finally:
        await stream.disconnect()
        print("🔌 Disconnected from stream")
    
    print()
    
    # 2. Filtered Transaction Streaming
    print("🔍 2. Filtered Transaction Streaming")
    print("-" * 40)
    
    # Create new stream with filters
    filtered_stream = NetworkEventStream('testnet')
    
    # Add address filter
    address_filter = EventFilter(
        addresses={alice.address, bob.address},
        transaction_types={'dag_transfer', 'token_transfer'}
    )
    filtered_stream.add_filter('alice_bob_filter', address_filter)
    
    # Filtered transaction handler
    def handle_filtered_transaction(event):
        print(f"🎯 Filtered Transaction (Alice/Bob only):")
        print(f"  Hash: {event.data.get('hash', 'N/A')}")
        print(f"  From: {event.data.get('source', 'N/A')}")
        print(f"  To: {event.data.get('destination', 'N/A')}")
        print(f"  Amount: {event.data.get('amount', 0) / 1e8:.8f} DAG")
        print()
    
    # Register filtered handler
    filtered_stream.on(EventType.TRANSACTION, handle_filtered_transaction)
    
    try:
        # Connect to filtered stream
        await filtered_stream.connect()
        print("✅ Connected to filtered transaction stream")
        
        # Stream for 10 seconds
        print("⏳ Streaming filtered transactions for 10 seconds...")
        await asyncio.sleep(10)
        
        # Show statistics
        stats = filtered_stream.get_stats()
        print(f"📊 Statistics: {stats['events_received']} received, {stats['events_filtered']} filtered")
        print()
        
    except Exception as e:
        print(f"❌ Filtered streaming error: {e}")
    finally:
        await filtered_stream.disconnect()
        print("🔌 Disconnected from filtered stream")
    
    print()
    
    # 3. Balance Change Tracking
    print("💰 3. Balance Change Tracking")
    print("-" * 40)
    
    # Create balance tracker
    balance_stream = NetworkEventStream('testnet')
    balance_tracker = BalanceTracker('testnet')
    
    # Track specific addresses
    addresses_to_track = [alice.address, bob.address, charlie.address]
    for address in addresses_to_track:
        balance_tracker.track_address(address)
    
    # Balance change handler
    def handle_balance_change(event):
        data = event.data
        change = data.get('change', 0)
        change_str = f"+{change / 1e8:.8f}" if change > 0 else f"{change / 1e8:.8f}"
        
        print(f"💰 Balance Change:")
        print(f"  Address: {data.get('address', 'N/A')}")
        print(f"  Old Balance: {data.get('old_balance', 0) / 1e8:.8f} DAG")
        print(f"  New Balance: {data.get('new_balance', 0) / 1e8:.8f} DAG")
        print(f"  Change: {change_str} DAG")
        print()
    
    # Register balance change handler
    balance_stream.on(EventType.BALANCE_CHANGE, handle_balance_change)
    
    try:
        # Connect stream and start tracker
        await balance_stream.connect()
        await balance_tracker.start(balance_stream)
        print("✅ Started balance tracking")
        
        # Track for 15 seconds
        print("⏳ Tracking balance changes for 15 seconds...")
        await asyncio.sleep(15)
        
        # Show statistics
        stats = balance_stream.get_stats()
        print(f"📊 Statistics: {stats['events_received']} balance events received")
        print()
        
    except Exception as e:
        print(f"❌ Balance tracking error: {e}")
    finally:
        await balance_tracker.stop()
        await balance_stream.disconnect()
        print("🔌 Stopped balance tracking")
    
    print()
    
    # 4. Multi-Event Streaming
    print("🎯 4. Multi-Event Streaming")
    print("-" * 40)
    
    # Create multi-event stream
    multi_stream = NetworkEventStream('testnet')
    
    # Generic event handler
    def handle_any_event(event):
        print(f"🌟 {event.event_type.value.upper()} Event:")
        print(f"  Network: {event.network}")
        print(f"  Source: {event.source}")
        print(f"  Timestamp: {event.timestamp}")
        print(f"  Data: {json.dumps(event.data, indent=2)}")
        print()
    
    # Register handlers for all event types
    for event_type in EventType:
        multi_stream.on(event_type, handle_any_event)
    
    try:
        # Connect to multi-event stream
        await multi_stream.connect()
        print("✅ Connected to multi-event stream")
        
        # Stream for 12 seconds
        print("⏳ Streaming all events for 12 seconds...")
        await asyncio.sleep(12)
        
        # Show statistics
        stats = multi_stream.get_stats()
        print(f"📊 Statistics: {stats['events_received']} total events")
        print()
        
    except Exception as e:
        print(f"❌ Multi-event streaming error: {e}")
    finally:
        await multi_stream.disconnect()
        print("🔌 Disconnected from multi-event stream")
    
    print()
    
    # 5. Custom Event Filters
    print("🎨 5. Custom Event Filters")
    print("-" * 40)
    
    # Create stream with custom filter
    custom_stream = NetworkEventStream('testnet')
    
    # Custom filter function for high-value transactions
    def high_value_filter(event):
        if event.event_type == EventType.TRANSACTION:
            amount = event.data.get('amount', 0)
            return amount >= 1000000000  # 10 DAG or more
        return True
    
    # Create custom filter
    custom_filter = EventFilter(
        amount_range=(1000000000, float('inf')),  # 10+ DAG
        custom_filter=high_value_filter
    )
    custom_stream.add_filter('high_value_filter', custom_filter)
    
    # High-value transaction handler
    def handle_high_value_transaction(event):
        print(f"💎 High-Value Transaction:")
        print(f"  Amount: {event.data.get('amount', 0) / 1e8:.8f} DAG")
        print(f"  Hash: {event.data.get('hash', 'N/A')}")
        print(f"  From: {event.data.get('source', 'N/A')}")
        print(f"  To: {event.data.get('destination', 'N/A')}")
        print()
    
    # Register custom handler
    custom_stream.on(EventType.TRANSACTION, handle_high_value_transaction)
    
    try:
        # Connect to custom stream
        await custom_stream.connect()
        print("✅ Connected to high-value transaction stream")
        
        # Stream for 15 seconds
        print("⏳ Streaming high-value transactions for 15 seconds...")
        await asyncio.sleep(15)
        
        # Show statistics
        stats = custom_stream.get_stats()
        print(f"📊 Statistics: {stats['events_received']} received, {stats['events_filtered']} filtered")
        print()
        
    except Exception as e:
        print(f"❌ Custom streaming error: {e}")
    finally:
        await custom_stream.disconnect()
        print("🔌 Disconnected from custom stream")
    
    print()
    
    # 6. Using Convenience Functions
    print("🛠️ 6. Using Convenience Functions")
    print("-" * 40)
    
    # Quick transaction streaming
    def quick_tx_handler(event):
        print(f"⚡ Quick Transaction: {event.data.get('hash', 'N/A')[:8]}...")
    
    try:
        print("🚀 Starting quick transaction stream...")
        quick_stream = await stream_transactions(
            network='testnet',
            callback=quick_tx_handler,
            addresses=[alice.address, bob.address],
            transaction_types=['dag_transfer']
        )
        
        # Stream for 8 seconds
        await asyncio.sleep(8)
        
        # Show statistics
        stats = quick_stream.get_stats()
        print(f"📊 Quick stream: {stats['events_received']} events")
        
        await quick_stream.disconnect()
        print("✅ Quick stream completed")
        
    except Exception as e:
        print(f"❌ Quick stream error: {e}")
    
    print()
    
    # 7. Advanced Event Processing
    print("🔧 7. Advanced Event Processing")
    print("-" * 40)
    
    # Create event processor
    class EventProcessor:
        def __init__(self):
            self.transaction_count = 0
            self.total_volume = 0
            self.addresses_seen = set()
            
        def process_transaction(self, event):
            self.transaction_count += 1
            self.total_volume += event.data.get('amount', 0)
            
            source = event.data.get('source')
            destination = event.data.get('destination')
            if source:
                self.addresses_seen.add(source)
            if destination:
                self.addresses_seen.add(destination)
            
            # Print summary every 5 transactions
            if self.transaction_count % 5 == 0:
                print(f"📈 Processing Summary:")
                print(f"  Transactions: {self.transaction_count}")
                print(f"  Total Volume: {self.total_volume / 1e8:.8f} DAG")
                print(f"  Unique Addresses: {len(self.addresses_seen)}")
                print()
    
    processor = EventProcessor()
    
    # Create processing stream
    processing_stream = NetworkEventStream('testnet')
    processing_stream.on(EventType.TRANSACTION, processor.process_transaction)
    
    try:
        # Connect to processing stream
        await processing_stream.connect()
        print("✅ Connected to processing stream")
        
        # Process for 20 seconds
        print("⏳ Processing transactions for 20 seconds...")
        await asyncio.sleep(20)
        
        # Final summary
        print(f"🎯 Final Summary:")
        print(f"  Total Transactions: {processor.transaction_count}")
        print(f"  Total Volume: {processor.total_volume / 1e8:.8f} DAG")
        print(f"  Unique Addresses: {len(processor.addresses_seen)}")
        print()
        
        # Show stream statistics
        stats = processing_stream.get_stats()
        print(f"📊 Stream Statistics:")
        print(f"  Events Received: {stats['events_received']}")
        print(f"  Uptime: {stats['uptime']:.1f} seconds")
        print(f"  Reconnections: {stats['reconnections']}")
        print()
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
    finally:
        await processing_stream.disconnect()
        print("🔌 Disconnected from processing stream")
    
    print()
    
    # 8. Production-Ready Streaming Application
    print("🏭 8. Production-Ready Streaming Application")
    print("-" * 40)
    
    # Create production-style event handler
    class ProductionEventHandler:
        def __init__(self):
            self.event_log = []
            self.alert_threshold = 1000000000  # 10 DAG
            
        async def handle_transaction(self, event):
            # Log event
            self.event_log.append({
                'timestamp': event.timestamp,
                'hash': event.data.get('hash'),
                'amount': event.data.get('amount', 0),
                'type': event.data.get('transaction_type')
            })
            
            # Check for alerts
            amount = event.data.get('amount', 0)
            if amount >= self.alert_threshold:
                await self.send_alert(event)
            
            # Keep only last 100 events
            if len(self.event_log) > 100:
                self.event_log.pop(0)
        
        async def send_alert(self, event):
            print(f"🚨 ALERT: High-value transaction detected!")
            print(f"  Amount: {event.data.get('amount', 0) / 1e8:.8f} DAG")
            print(f"  Hash: {event.data.get('hash', 'N/A')}")
            print()
        
        def get_statistics(self):
            return {
                'events_logged': len(self.event_log),
                'total_volume': sum(event['amount'] for event in self.event_log),
                'avg_amount': sum(event['amount'] for event in self.event_log) / len(self.event_log) if self.event_log else 0
            }
    
    production_handler = ProductionEventHandler()
    
    # Create production stream
    production_stream = NetworkEventStream('testnet')
    production_stream.on(EventType.TRANSACTION, production_handler.handle_transaction)
    
    try:
        # Connect to production stream
        await production_stream.connect()
        print("✅ Production stream connected")
        
        # Run for 15 seconds
        print("⏳ Running production stream for 15 seconds...")
        await asyncio.sleep(15)
        
        # Show production statistics
        prod_stats = production_handler.get_statistics()
        stream_stats = production_stream.get_stats()
        
        print(f"🏭 Production Statistics:")
        print(f"  Events Logged: {prod_stats['events_logged']}")
        print(f"  Total Volume: {prod_stats['total_volume'] / 1e8:.8f} DAG")
        print(f"  Average Amount: {prod_stats['avg_amount'] / 1e8:.8f} DAG")
        print(f"  Stream Uptime: {stream_stats['uptime']:.1f} seconds")
        print()
        
    except Exception as e:
        print(f"❌ Production streaming error: {e}")
    finally:
        await production_stream.disconnect()
        print("🔌 Production stream disconnected")
    
    print()
    print("🎉 Real-time streaming demo completed!")
    print("💡 Key Features Demonstrated:")
    print("  ✅ Basic transaction streaming")
    print("  ✅ Event filtering and address tracking")
    print("  ✅ Balance change monitoring")
    print("  ✅ Multi-event streaming")
    print("  ✅ Custom filters and processing")
    print("  ✅ Convenience functions")
    print("  ✅ Production-ready patterns")
    print()
    print("🚀 Build real-time DApps with Constellation's streaming capabilities!")


if __name__ == "__main__":
    asyncio.run(main())