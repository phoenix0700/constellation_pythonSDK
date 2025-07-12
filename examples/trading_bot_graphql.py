#!/usr/bin/env python3
"""
Trading Bot GraphQL Integration Example

This example demonstrates how to build a sophisticated trading bot using GraphQL
for market analysis, portfolio management, and automated trading decisions.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from constellation_sdk import (
    GRAPHQL_AVAILABLE,
    Account,
    Network,
    Transactions,
)

if GRAPHQL_AVAILABLE:
    from constellation_sdk import (
        GraphQLClient,
        GraphQLQuery,
        QueryBuilder,
        execute_query_async,
    )


@dataclass
class TradingSignal:
    """Represents a trading signal with metadata."""

    signal_type: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning: str = ""
    data_source: str = "graphql"


@dataclass
class MarketData:
    """Market data structure from GraphQL."""

    total_volume: float
    transaction_count: int
    active_addresses: int
    avg_transaction_size: float
    price_trend: str
    liquidity_score: float
    timestamp: datetime = field(default_factory=datetime.now)


class GraphQLTradingBot:
    """Advanced trading bot using GraphQL for market intelligence."""

    def __init__(self, network: str = "testnet"):
        self.network = network
        self.client = GraphQLClient(network) if GRAPHQL_AVAILABLE else None
        self.network_client = Network(network)
        self.account = Account()

        # Trading configuration
        self.config = {
            "max_position_size": 1000.0,  # Maximum position size in DAG
            "risk_tolerance": 0.05,  # 5% risk tolerance
            "min_confidence": 0.7,  # Minimum signal confidence
            "analysis_window": 24,  # Hours to analyze
            "rebalance_threshold": 0.1,  # 10% deviation triggers rebalance
        }

        # State tracking
        self.positions = {}
        self.signals_history = []
        self.market_data_cache = {}

    async def analyze_market_conditions(
        self, target_addresses: List[str]
    ) -> MarketData:
        """Comprehensive market analysis using GraphQL."""
        if not GRAPHQL_AVAILABLE:
            raise RuntimeError("GraphQL not available for market analysis")

        # Build comprehensive market analysis query
        market_query = """
        query MarketAnalysis($addresses: [String!]!, $timeframe: Int!) {
            accounts(addresses: $addresses) {
                address
                balance
                transactions(first: 100) {
                    hash
                    amount
                    timestamp
                    destination
                    source
                    type
                }
            }
            network {
                status
                latestBlock {
                    height
                    timestamp
                }
                metrics {
                    transactionRate
                    activeAddresses
                    totalTransactions
                }
            }
        }
        """

        try:
            response = await self.client.execute_async(
                market_query,
                {
                    "addresses": target_addresses,
                    "timeframe": self.config["analysis_window"],
                },
            )

            if response.is_successful:
                return self._process_market_data(response.data)
            else:
                raise RuntimeError(f"Market analysis failed: {response.errors}")

        except Exception as e:
            raise RuntimeError(f"GraphQL market analysis error: {e}")

    def _process_market_data(self, data: Dict[str, Any]) -> MarketData:
        """Process GraphQL response into market data."""
        accounts = data.get("accounts", [])
        network = data.get("network", {})

        # Calculate market metrics
        total_volume = 0
        transaction_count = 0
        all_transactions = []

        cutoff_time = time.time() - (self.config["analysis_window"] * 3600)

        for account in accounts:
            transactions = account.get("transactions", [])
            recent_txs = [
                tx for tx in transactions if tx.get("timestamp", 0) > cutoff_time
            ]

            account_volume = sum(tx.get("amount", 0) for tx in recent_txs)
            total_volume += account_volume
            transaction_count += len(recent_txs)
            all_transactions.extend(recent_txs)

        # Calculate additional metrics
        avg_transaction_size = (
            (total_volume / transaction_count) if transaction_count > 0 else 0
        )
        active_addresses = network.get("metrics", {}).get("activeAddresses", 0)

        # Calculate price trend (simplified)
        price_trend = self._calculate_price_trend(all_transactions)

        # Calculate liquidity score
        liquidity_score = self._calculate_liquidity_score(
            total_volume, transaction_count, active_addresses
        )

        return MarketData(
            total_volume=total_volume / 1e8,  # Convert to DAG
            transaction_count=transaction_count,
            active_addresses=active_addresses,
            avg_transaction_size=avg_transaction_size / 1e8,
            price_trend=price_trend,
            liquidity_score=liquidity_score,
        )

    def _calculate_price_trend(self, transactions: List[Dict]) -> str:
        """Calculate price trend from transaction data."""
        if not transactions:
            return "NEUTRAL"

        # Sort transactions by timestamp
        sorted_txs = sorted(transactions, key=lambda x: x.get("timestamp", 0))

        # Split into two halves for trend analysis
        mid_point = len(sorted_txs) // 2
        first_half = sorted_txs[:mid_point]
        second_half = sorted_txs[mid_point:]

        if not first_half or not second_half:
            return "NEUTRAL"

        # Calculate average transaction size for each half
        first_avg = sum(tx.get("amount", 0) for tx in first_half) / len(first_half)
        second_avg = sum(tx.get("amount", 0) for tx in second_half) / len(second_half)

        # Determine trend
        if second_avg > first_avg * 1.1:
            return "BULLISH"
        elif second_avg < first_avg * 0.9:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_liquidity_score(
        self, volume: float, tx_count: int, active_addresses: int
    ) -> float:
        """Calculate liquidity score from 0 to 1."""
        # Normalize factors
        volume_score = min(volume / 10000, 1.0)  # Normalize to 10,000 DAG
        activity_score = min(tx_count / 1000, 1.0)  # Normalize to 1,000 transactions
        participation_score = min(
            active_addresses / 100, 1.0
        )  # Normalize to 100 addresses

        # Weighted average
        return volume_score * 0.4 + activity_score * 0.3 + participation_score * 0.3

    async def generate_trading_signals(
        self, market_data: MarketData
    ) -> List[TradingSignal]:
        """Generate trading signals based on market analysis."""
        signals = []

        # Volume-based signals
        if market_data.total_volume > 1000:  # High volume
            signals.append(
                TradingSignal(
                    signal_type="VOLUME",
                    action="BUY" if market_data.price_trend == "BULLISH" else "HOLD",
                    confidence=0.8,
                    reasoning=f"High volume ({market_data.total_volume:.2f} DAG) with {market_data.price_trend} trend",
                )
            )

        # Liquidity-based signals
        if market_data.liquidity_score > 0.7:
            signals.append(
                TradingSignal(
                    signal_type="LIQUIDITY",
                    action="BUY",
                    confidence=0.7,
                    reasoning=f"High liquidity score: {market_data.liquidity_score:.2f}",
                )
            )
        elif market_data.liquidity_score < 0.3:
            signals.append(
                TradingSignal(
                    signal_type="LIQUIDITY",
                    action="SELL",
                    confidence=0.6,
                    reasoning=f"Low liquidity score: {market_data.liquidity_score:.2f}",
                )
            )

        # Activity-based signals
        if market_data.transaction_count > 100:
            signals.append(
                TradingSignal(
                    signal_type="ACTIVITY",
                    action="BUY" if market_data.price_trend != "BEARISH" else "HOLD",
                    confidence=0.6,
                    reasoning=f"High activity: {market_data.transaction_count} transactions",
                )
            )

        # Price trend signals
        if market_data.price_trend == "BULLISH":
            signals.append(
                TradingSignal(
                    signal_type="TREND",
                    action="BUY",
                    confidence=0.75,
                    reasoning="Bullish price trend detected",
                )
            )
        elif market_data.price_trend == "BEARISH":
            signals.append(
                TradingSignal(
                    signal_type="TREND",
                    action="SELL",
                    confidence=0.75,
                    reasoning="Bearish price trend detected",
                )
            )

        # Store signals in history
        self.signals_history.extend(signals)

        return signals

    async def execute_trading_strategy(
        self, signals: List[TradingSignal]
    ) -> Dict[str, Any]:
        """Execute trading strategy based on generated signals."""
        if not signals:
            return {"action": "HOLD", "reason": "No signals generated"}

        # Filter signals by confidence
        high_confidence_signals = [
            s for s in signals if s.confidence >= self.config["min_confidence"]
        ]

        if not high_confidence_signals:
            return {"action": "HOLD", "reason": "No high-confidence signals"}

        # Aggregate signals
        buy_signals = [s for s in high_confidence_signals if s.action == "BUY"]
        sell_signals = [s for s in high_confidence_signals if s.action == "SELL"]

        # Decision logic
        if len(buy_signals) > len(sell_signals):
            action = "BUY"
            confidence = sum(s.confidence for s in buy_signals) / len(buy_signals)
        elif len(sell_signals) > len(buy_signals):
            action = "SELL"
            confidence = sum(s.confidence for s in sell_signals) / len(sell_signals)
        else:
            action = "HOLD"
            confidence = 0.5

        # Calculate position size
        position_size = self._calculate_position_size(confidence)

        # Simulate trade execution
        trade_result = await self._simulate_trade(action, position_size)

        return {
            "action": action,
            "confidence": confidence,
            "position_size": position_size,
            "signals_used": len(high_confidence_signals),
            "trade_result": trade_result,
            "reasoning": f"Aggregated {len(high_confidence_signals)} signals",
        }

    def _calculate_position_size(self, confidence: float) -> float:
        """Calculate position size based on confidence and risk tolerance."""
        # Get current balance
        try:
            balance = self.network_client.get_balance(self.account.address)
            balance_dag = balance / 1e8
        except:
            balance_dag = 0

        # Calculate position size
        max_position = min(
            balance_dag * self.config["risk_tolerance"],
            self.config["max_position_size"],
        )

        # Scale by confidence
        position_size = max_position * confidence

        return position_size

    async def _simulate_trade(
        self, action: str, position_size: float
    ) -> Dict[str, Any]:
        """Simulate trade execution (in real bot, this would execute actual trades)."""
        # In a real trading bot, this would:
        # 1. Create actual transactions
        # 2. Submit to network
        # 3. Handle confirmations
        # 4. Update position tracking

        return {
            "simulated": True,
            "action": action,
            "amount": position_size,
            "timestamp": datetime.now().isoformat(),
            "status": "SIMULATED",
            "note": "Real bot would execute actual transaction here",
        }

    async def run_trading_cycle(self, target_addresses: List[str]) -> Dict[str, Any]:
        """Run a complete trading cycle."""
        cycle_start = time.time()

        try:
            # 1. Analyze market conditions
            market_data = await self.analyze_market_conditions(target_addresses)

            # 2. Generate trading signals
            signals = await self.generate_trading_signals(market_data)

            # 3. Execute trading strategy
            execution_result = await self.execute_trading_strategy(signals)

            cycle_time = time.time() - cycle_start

            return {
                "cycle_time": cycle_time,
                "market_data": market_data,
                "signals_generated": len(signals),
                "execution_result": execution_result,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "error": str(e),
                "cycle_time": time.time() - cycle_start,
                "timestamp": datetime.now().isoformat(),
            }

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        return {
            "total_signals_generated": len(self.signals_history),
            "signal_types": {},
            "average_confidence": (
                sum(s.confidence for s in self.signals_history)
                / len(self.signals_history)
                if self.signals_history
                else 0
            ),
            "current_positions": self.positions,
            "bot_config": self.config,
        }


async def demo_trading_bot():
    """Demonstrate the GraphQL trading bot."""
    print("🤖 GraphQL Trading Bot Demo")
    print("=" * 50)

    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL not available. Install aiohttp and websockets.")
        return

    # Create trading bot
    bot = GraphQLTradingBot("testnet")

    # Generate test addresses for analysis
    test_addresses = [Account().address for _ in range(5)]

    print(f"📊 Bot initialized for {len(test_addresses)} target addresses")
    print(f"🏦 Bot account: {bot.account.address}")
    print(f"⚙️  Risk tolerance: {bot.config['risk_tolerance']:.1%}")
    print(f"💰 Max position size: {bot.config['max_position_size']} DAG")

    # Run trading cycle
    print("\n🔄 Running trading cycle...")
    cycle_result = await bot.run_trading_cycle(test_addresses)

    if "error" in cycle_result:
        print(f"❌ Trading cycle failed: {cycle_result['error']}")
        return

    print(f"✅ Trading cycle completed in {cycle_result['cycle_time']:.2f}s")

    # Display market analysis
    print("\n📈 Market Analysis:")
    market_data = cycle_result["market_data"]
    print(f"   Volume: {market_data.total_volume:.2f} DAG")
    print(f"   Transactions: {market_data.transaction_count}")
    print(f"   Active Addresses: {market_data.active_addresses}")
    print(f"   Avg Transaction Size: {market_data.avg_transaction_size:.4f} DAG")
    print(f"   Price Trend: {market_data.price_trend}")
    print(f"   Liquidity Score: {market_data.liquidity_score:.2f}")

    # Display trading decision
    print("\n🎯 Trading Decision:")
    execution = cycle_result["execution_result"]
    print(f"   Action: {execution['action']}")
    print(f"   Confidence: {execution.get('confidence', 0):.1%}")
    print(f"   Position Size: {execution.get('position_size', 0):.4f} DAG")
    print(f"   Signals Used: {execution.get('signals_used', 0)}")
    print(f"   Reasoning: {execution.get('reasoning', 'N/A')}")

    # Display performance report
    print("\n📊 Performance Report:")
    report = bot.get_performance_report()
    print(f"   Total Signals: {report['total_signals_generated']}")
    print(f"   Average Confidence: {report['average_confidence']:.1%}")

    print("\n💡 Trading Bot Benefits:")
    print("   • Real-time market analysis using GraphQL")
    print("   • Multi-signal aggregation for better decisions")
    print("   • Risk management with position sizing")
    print("   • Comprehensive performance tracking")
    print("   • Scalable to multiple trading pairs")


if __name__ == "__main__":
    asyncio.run(demo_trading_bot())
