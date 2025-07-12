#!/usr/bin/env python3
"""
Real-World GraphQL Use Cases for Constellation Network

This module demonstrates practical, real-world applications of the GraphQL API
for common blockchain use cases including portfolio tracking, trading analysis,
DeFi analytics, and monitoring systems.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import sys

from constellation_sdk import (
    Account,
    Network,
    GRAPHQL_AVAILABLE,
)

# GraphQL imports (conditional)
if GRAPHQL_AVAILABLE:
    from constellation_sdk import (
        GraphQLClient,
        GraphQLQuery,
        QueryBuilder,
        SubscriptionBuilder,
        ConstellationSchema,
        execute_query,
        execute_query_async,
        get_account_portfolio,
        get_metagraph_overview,
        get_network_status,
        build_account_query,
        build_portfolio_query,
    )


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"🚀 {title}")
    print(f"{'='*80}")


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n{'─'*60}")
    print(f"✨ {title}")
    print(f"{'─'*60}")


def print_result(success: bool, message: str):
    """Print a formatted result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


class PortfolioTracker:
    """Real-world portfolio tracking using GraphQL."""
    
    def __init__(self, network: str = 'testnet'):
        self.network = network
        self.client = GraphQLClient(network)
        self.tracked_addresses = []
        self.portfolio_data = {}
        
    def add_address(self, address: str, label: str = None):
        """Add an address to track."""
        self.tracked_addresses.append({
            'address': address,
            'label': label or f'Account_{len(self.tracked_addresses)+1}',
            'added_at': datetime.now()
        })
        
    def get_comprehensive_portfolio(self) -> Dict[str, Any]:
        """Get comprehensive portfolio data using GraphQL."""
        if not self.tracked_addresses:
            return {'error': 'No addresses to track'}
        
        # Build comprehensive portfolio query
        addresses = [addr['address'] for addr in self.tracked_addresses]
        
        portfolio_query = f"""
        query ComprehensivePortfolio($addresses: [String!]!) {{
            accounts(addresses: $addresses) {{
                address
                balance
                transactions(first: 10) {{
                    hash
                    amount
                    timestamp
                    destination
                    type
                }}
                metagraphBalances {{
                    metagraphId
                    balance
                    tokenSymbol
                }}
            }}
            network {{
                status
                latestBlock {{
                    height
                    timestamp
                }}
                metrics {{
                    activeAddresses
                    totalTransactions
                }}
            }}
        }}
        """
        
        try:
            response = self.client.execute(portfolio_query, {"addresses": addresses})
            
            if response.is_successful:
                # Process and enrich data
                portfolio_data = {
                    'timestamp': datetime.now().isoformat(),
                    'total_accounts': len(addresses),
                    'total_dag_balance': 0,
                    'total_metagraph_tokens': 0,
                    'accounts': [],
                    'network_status': response.data.get('network', {}),
                    'execution_time': response.execution_time
                }
                
                for account_data in response.data.get('accounts', []):
                    # Find label for this address
                    label = next((
                        addr['label'] for addr in self.tracked_addresses 
                        if addr['address'] == account_data['address']
                    ), 'Unknown')
                    
                    # Calculate metrics
                    balance = account_data.get('balance', 0)
                    transactions = account_data.get('transactions', [])
                    metagraph_balances = account_data.get('metagraphBalances', [])
                    
                    portfolio_data['total_dag_balance'] += balance
                    portfolio_data['total_metagraph_tokens'] += len(metagraph_balances)
                    
                    # Recent activity analysis
                    recent_transactions = [
                        tx for tx in transactions 
                        if tx.get('timestamp', 0) > time.time() - 86400  # Last 24h
                    ]
                    
                    account_info = {
                        'address': account_data['address'],
                        'label': label,
                        'balance_dag': balance / 1e8,  # Convert to DAG
                        'balance_raw': balance,
                        'transaction_count': len(transactions),
                        'recent_activity': len(recent_transactions),
                        'metagraph_tokens': len(metagraph_balances),
                        'metagraph_details': metagraph_balances,
                        'latest_transactions': transactions[:5]
                    }
                    
                    portfolio_data['accounts'].append(account_info)
                
                # Convert totals
                portfolio_data['total_dag_balance'] = portfolio_data['total_dag_balance'] / 1e8
                
                self.portfolio_data = portfolio_data
                return portfolio_data
                
            else:
                return {'error': 'GraphQL query failed', 'details': response.errors}
                
        except Exception as e:
            return {'error': f'Portfolio tracking failed: {e}'}
    
    def get_portfolio_summary(self) -> str:
        """Get a formatted portfolio summary."""
        if not self.portfolio_data:
            self.get_comprehensive_portfolio()
        
        if 'error' in self.portfolio_data:
            return f"❌ Portfolio Error: {self.portfolio_data['error']}"
        
        data = self.portfolio_data
        summary = f"""
📊 Portfolio Summary ({data['timestamp'][:19]})
{'─' * 50}
💰 Total DAG Balance: {data['total_dag_balance']:.8f} DAG
🏛️  Metagraph Tokens: {data['total_metagraph_tokens']} types
📈 Tracked Accounts: {data['total_accounts']}
⏱️  Query Time: {data['execution_time']:.3f}s

📋 Account Details:
"""
        
        for account in data['accounts']:
            summary += f"""
  🏷️  {account['label']} ({account['address'][:12]}...)
  💰 Balance: {account['balance_dag']:.8f} DAG
  📜 Transactions: {account['transaction_count']} total, {account['recent_activity']} recent
  🏛️  Metagraph Tokens: {account['metagraph_tokens']}
"""
        
        network = data['network_status']
        summary += f"""
🌐 Network Status: {network.get('status', 'Unknown')}
📊 Active Addresses: {network.get('metrics', {}).get('activeAddresses', 'N/A')}
"""
        
        return summary


class TradingBotAnalyzer:
    """Trading bot analysis using GraphQL for market intelligence."""
    
    def __init__(self, network: str = 'testnet'):
        self.network = network
        self.client = GraphQLClient(network)
        self.analysis_results = {}
        
    def analyze_market_activity(self, addresses: List[str], timeframe_hours: int = 24) -> Dict[str, Any]:
        """Analyze market activity for trading insights."""
        
        # Build market analysis query
        market_query = f"""
        query MarketAnalysis($addresses: [String!]!) {{
            accounts(addresses: $addresses) {{
                address
                balance
                transactions(first: 50) {{
                    hash
                    amount
                    timestamp
                    destination
                    source
                    type
                }}
            }}
            network {{
                status
                metrics {{
                    transactionRate
                    activeAddresses
                    totalTransactions
                }}
                latestBlock {{
                    height
                    timestamp
                }}
            }}
        }}
        """
        
        try:
            response = self.client.execute(market_query, {"addresses": addresses})
            
            if response.is_successful:
                return self._process_market_data(response.data, timeframe_hours)
            else:
                return {'error': 'Market analysis query failed', 'details': response.errors}
                
        except Exception as e:
            return {'error': f'Market analysis failed: {e}'}
    
    def _process_market_data(self, data: Dict[str, Any], timeframe_hours: int) -> Dict[str, Any]:
        """Process market data for trading insights."""
        cutoff_time = time.time() - (timeframe_hours * 3600)
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'timeframe_hours': timeframe_hours,
            'total_accounts': len(data.get('accounts', [])),
            'network_metrics': data.get('network', {}),
            'account_analysis': [],
            'market_insights': {
                'total_volume': 0,
                'transaction_count': 0,
                'active_traders': 0,
                'avg_transaction_size': 0,
                'largest_transactions': [],
                'trading_patterns': {}
            }
        }
        
        all_transactions = []
        
        for account_data in data.get('accounts', []):
            address = account_data['address']
            balance = account_data.get('balance', 0)
            transactions = account_data.get('transactions', [])
            
            # Filter transactions by timeframe
            recent_transactions = [
                tx for tx in transactions 
                if tx.get('timestamp', 0) > cutoff_time
            ]
            
            # Calculate account metrics
            account_volume = sum(tx.get('amount', 0) for tx in recent_transactions)
            incoming_txs = [tx for tx in recent_transactions if tx.get('destination') == address]
            outgoing_txs = [tx for tx in recent_transactions if tx.get('source') == address]
            
            account_analysis = {
                'address': address,
                'balance': balance / 1e8,
                'recent_transactions': len(recent_transactions),
                'volume': account_volume / 1e8,
                'incoming_count': len(incoming_txs),
                'outgoing_count': len(outgoing_txs),
                'trading_ratio': len(outgoing_txs) / max(len(incoming_txs), 1),
                'avg_transaction_size': (account_volume / len(recent_transactions)) / 1e8 if recent_transactions else 0,
                'is_active_trader': len(recent_transactions) > 5
            }
            
            analysis['account_analysis'].append(account_analysis)
            all_transactions.extend(recent_transactions)
        
        # Calculate market insights
        if all_transactions:
            total_volume = sum(tx.get('amount', 0) for tx in all_transactions)
            analysis['market_insights']['total_volume'] = total_volume / 1e8
            analysis['market_insights']['transaction_count'] = len(all_transactions)
            analysis['market_insights']['active_traders'] = sum(
                1 for acc in analysis['account_analysis'] if acc['is_active_trader']
            )
            analysis['market_insights']['avg_transaction_size'] = (total_volume / len(all_transactions)) / 1e8
            
            # Find largest transactions
            sorted_txs = sorted(all_transactions, key=lambda x: x.get('amount', 0), reverse=True)
            analysis['market_insights']['largest_transactions'] = [
                {
                    'hash': tx['hash'],
                    'amount': tx.get('amount', 0) / 1e8,
                    'timestamp': tx.get('timestamp', 0)
                }
                for tx in sorted_txs[:10]
            ]
        
        return analysis
    
    def get_trading_signals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trading signals from market analysis."""
        signals = []
        
        if 'error' in analysis:
            return [{'type': 'error', 'message': analysis['error']}]
        
        market = analysis['market_insights']
        
        # Volume-based signals
        if market['total_volume'] > 1000:  # High volume threshold
            signals.append({
                'type': 'volume',
                'signal': 'HIGH_VOLUME',
                'confidence': 0.8,
                'message': f"High trading volume detected: {market['total_volume']:.2f} DAG"
            })
        
        # Activity-based signals
        if market['active_traders'] > 0:
            activity_ratio = market['active_traders'] / analysis['total_accounts']
            if activity_ratio > 0.3:
                signals.append({
                    'type': 'activity',
                    'signal': 'HIGH_ACTIVITY',
                    'confidence': 0.7,
                    'message': f"High trader activity: {activity_ratio:.1%} of accounts active"
                })
        
        # Transaction size analysis
        if market['avg_transaction_size'] > 100:
            signals.append({
                'type': 'transaction_size',
                'signal': 'LARGE_TRANSACTIONS',
                'confidence': 0.6,
                'message': f"Large average transaction size: {market['avg_transaction_size']:.2f} DAG"
            })
        
        return signals


class DeFiAnalyticsDashboard:
    """DeFi analytics using GraphQL for ecosystem insights."""
    
    def __init__(self, network: str = 'testnet'):
        self.network = network
        self.client = GraphQLClient(network)
        
    def get_ecosystem_overview(self, metagraph_ids: List[str]) -> Dict[str, Any]:
        """Get comprehensive DeFi ecosystem overview."""
        
        # Build ecosystem query
        ecosystem_query = f"""
        query EcosystemOverview($metagraphIds: [String!]!) {{
            metagraphs(ids: $metagraphIds) {{
                id
                name
                tokenSymbol
                totalSupply
                holderCount
                transactionCount
                status
                validators {{
                    address
                    stake
                }}
                recentTransactions: transactions(first: 20) {{
                    hash
                    amount
                    timestamp
                    type
                }}
            }}
            network {{
                status
                metrics {{
                    totalTransactions
                    activeAddresses
                    transactionRate
                }}
            }}
        }}
        """
        
        try:
            response = self.client.execute(ecosystem_query, {"metagraphIds": metagraph_ids})
            
            if response.is_successful:
                return self._process_ecosystem_data(response.data)
            else:
                return {'error': 'Ecosystem query failed', 'details': response.errors}
                
        except Exception as e:
            return {'error': f'Ecosystem analysis failed: {e}'}
    
    def _process_ecosystem_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process ecosystem data for DeFi insights."""
        metagraphs = data.get('metagraphs', [])
        network = data.get('network', {})
        
        ecosystem = {
            'timestamp': datetime.now().isoformat(),
            'network_status': network,
            'total_metagraphs': len(metagraphs),
            'ecosystem_metrics': {
                'total_supply': 0,
                'total_holders': 0,
                'total_transactions': 0,
                'total_validators': 0,
                'avg_holder_ratio': 0,
                'most_active_metagraph': None,
                'largest_metagraph': None
            },
            'metagraph_details': []
        }
        
        for mg in metagraphs:
            # Calculate metrics
            total_supply = mg.get('totalSupply', 0)
            holder_count = mg.get('holderCount', 0)
            transaction_count = mg.get('transactionCount', 0)
            validator_count = len(mg.get('validators', []))
            
            ecosystem['ecosystem_metrics']['total_supply'] += total_supply
            ecosystem['ecosystem_metrics']['total_holders'] += holder_count
            ecosystem['ecosystem_metrics']['total_transactions'] += transaction_count
            ecosystem['ecosystem_metrics']['total_validators'] += validator_count
            
            # Track most active and largest
            if not ecosystem['ecosystem_metrics']['most_active_metagraph']:
                ecosystem['ecosystem_metrics']['most_active_metagraph'] = mg
            elif transaction_count > ecosystem['ecosystem_metrics']['most_active_metagraph'].get('transactionCount', 0):
                ecosystem['ecosystem_metrics']['most_active_metagraph'] = mg
            
            if not ecosystem['ecosystem_metrics']['largest_metagraph']:
                ecosystem['ecosystem_metrics']['largest_metagraph'] = mg
            elif total_supply > ecosystem['ecosystem_metrics']['largest_metagraph'].get('totalSupply', 0):
                ecosystem['ecosystem_metrics']['largest_metagraph'] = mg
            
            # Process recent transactions
            recent_txs = mg.get('recentTransactions', [])
            recent_volume = sum(tx.get('amount', 0) for tx in recent_txs)
            
            mg_details = {
                'id': mg['id'],
                'name': mg.get('name', 'Unknown'),
                'token_symbol': mg.get('tokenSymbol', 'N/A'),
                'total_supply': total_supply / 1e8,
                'holder_count': holder_count,
                'transaction_count': transaction_count,
                'validator_count': validator_count,
                'recent_volume': recent_volume / 1e8,
                'recent_transaction_count': len(recent_txs),
                'status': mg.get('status', 'Unknown')
            }
            
            ecosystem['metagraph_details'].append(mg_details)
        
        # Calculate averages
        if metagraphs:
            ecosystem['ecosystem_metrics']['avg_holder_ratio'] = (
                ecosystem['ecosystem_metrics']['total_holders'] / len(metagraphs)
            )
        
        return ecosystem


async def run_portfolio_tracking_demo():
    """Demonstrate real-world portfolio tracking."""
    print_header("Real-World Portfolio Tracking Demo")
    
    if not GRAPHQL_AVAILABLE:
        print_result(False, "GraphQL not available. Install aiohttp and websockets.")
        return
    
    print_section("Setting up Portfolio Tracker")
    
    # Create portfolio tracker
    tracker = PortfolioTracker('testnet')
    
    # Add some test addresses (in real world, these would be user's addresses)
    test_accounts = [Account() for _ in range(3)]
    
    for i, account in enumerate(test_accounts):
        tracker.add_address(account.address, f"Test_Wallet_{i+1}")
        print(f"📍 Added {account.address[:12]}... as Test_Wallet_{i+1}")
    
    print_section("Fetching Comprehensive Portfolio Data")
    
    # Get portfolio data
    start_time = time.time()
    portfolio_data = tracker.get_comprehensive_portfolio()
    execution_time = time.time() - start_time
    
    if 'error' in portfolio_data:
        print_result(False, f"Portfolio fetch failed: {portfolio_data['error']}")
        return
    
    print_result(True, f"Portfolio data fetched in {execution_time:.3f}s")
    
    # Display portfolio summary
    print_section("Portfolio Summary")
    print(tracker.get_portfolio_summary())
    
    # Demonstrate real-time monitoring setup
    print_section("Real-time Monitoring Setup")
    print("🔄 In a real application, you would:")
    print("   • Set up periodic portfolio updates")
    print("   • Monitor balance changes")
    print("   • Track new transactions")
    print("   • Send alerts for significant changes")
    print("   • Generate performance reports")
    
    # Show GraphQL efficiency
    print_section("GraphQL Efficiency Benefits")
    print("✅ Single query retrieved:")
    print(f"   • {portfolio_data['total_accounts']} account balances")
    print(f"   • {sum(len(acc['latest_transactions']) for acc in portfolio_data['accounts'])} transactions")
    print(f"   • {portfolio_data['total_metagraph_tokens']} metagraph token balances")
    print(f"   • Network status and metrics")
    print(f"   • All in {portfolio_data['execution_time']:.3f}s!")


async def run_trading_bot_demo():
    """Demonstrate trading bot analysis."""
    print_header("Trading Bot Market Analysis Demo")
    
    if not GRAPHQL_AVAILABLE:
        print_result(False, "GraphQL not available.")
        return
    
    print_section("Setting up Trading Bot Analyzer")
    
    # Create trading bot analyzer
    analyzer = TradingBotAnalyzer('testnet')
    
    # Generate test addresses for market analysis
    test_addresses = [Account().address for _ in range(5)]
    
    print(f"📊 Analyzing market activity for {len(test_addresses)} addresses...")
    
    print_section("Market Activity Analysis")
    
    # Analyze market activity
    start_time = time.time()
    analysis = analyzer.analyze_market_activity(test_addresses, timeframe_hours=24)
    execution_time = time.time() - start_time
    
    if 'error' in analysis:
        print_result(False, f"Market analysis failed: {analysis['error']}")
        return
    
    print_result(True, f"Market analysis completed in {execution_time:.3f}s")
    
    # Display market insights
    print_section("Market Insights")
    market = analysis['market_insights']
    
    print(f"📈 Total Volume (24h): {market['total_volume']:.2f} DAG")
    print(f"🔄 Transaction Count: {market['transaction_count']}")
    print(f"👥 Active Traders: {market['active_traders']}")
    print(f"💰 Average Transaction Size: {market['avg_transaction_size']:.2f} DAG")
    
    # Show account analysis
    print_section("Account Analysis")
    for acc in analysis['account_analysis']:
        print(f"📍 {acc['address'][:12]}...")
        print(f"   💰 Balance: {acc['balance']:.2f} DAG")
        print(f"   🔄 Recent Transactions: {acc['recent_transactions']}")
        print(f"   📊 Volume: {acc['volume']:.2f} DAG")
        print(f"   🔀 Trading Ratio: {acc['trading_ratio']:.2f}")
        print(f"   🎯 Active Trader: {'Yes' if acc['is_active_trader'] else 'No'}")
        print()
    
    # Generate trading signals
    print_section("Trading Signals")
    signals = analyzer.get_trading_signals(analysis)
    
    if signals:
        for signal in signals:
            icon = "🚨" if signal['type'] == 'error' else "💡"
            print(f"{icon} {signal.get('signal', 'SIGNAL')}: {signal.get('message', 'No message')}")
            if 'confidence' in signal:
                print(f"   Confidence: {signal['confidence']:.1%}")
    else:
        print("📊 No significant trading signals detected in current market conditions")


async def run_defi_analytics_demo():
    """Demonstrate DeFi analytics dashboard."""
    print_header("DeFi Analytics Dashboard Demo")
    
    if not GRAPHQL_AVAILABLE:
        print_result(False, "GraphQL not available.")
        return
    
    print_section("Setting up DeFi Analytics Dashboard")
    
    # Create DeFi dashboard
    dashboard = DeFiAnalyticsDashboard('testnet')
    
    # Test metagraph IDs (in real world, these would be actual metagraph IDs)
    test_metagraph_ids = [
        "DAG7Ghth6FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhQs",
        "DAG8Mth7FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhRt",
        "DAG9Nth8FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhRu"
    ]
    
    print(f"🏛️ Analyzing DeFi ecosystem with {len(test_metagraph_ids)} metagraphs...")
    
    print_section("Ecosystem Overview Analysis")
    
    # Get ecosystem overview
    start_time = time.time()
    ecosystem = dashboard.get_ecosystem_overview(test_metagraph_ids)
    execution_time = time.time() - start_time
    
    if 'error' in ecosystem:
        print_result(False, f"Ecosystem analysis failed: {ecosystem['error']}")
        return
    
    print_result(True, f"Ecosystem analysis completed in {execution_time:.3f}s")
    
    # Display ecosystem metrics
    print_section("Ecosystem Metrics")
    metrics = ecosystem['ecosystem_metrics']
    
    print(f"🏛️ Total Metagraphs: {ecosystem['total_metagraphs']}")
    print(f"💰 Total Supply: {metrics['total_supply']:.2f} tokens")
    print(f"👥 Total Holders: {metrics['total_holders']}")
    print(f"🔄 Total Transactions: {metrics['total_transactions']}")
    print(f"🛡️ Total Validators: {metrics['total_validators']}")
    print(f"📊 Avg Holders per Metagraph: {metrics['avg_holder_ratio']:.1f}")
    
    # Show individual metagraph details
    print_section("Metagraph Details")
    for mg in ecosystem['metagraph_details']:
        print(f"🏛️ {mg['name']} ({mg['token_symbol']})")
        print(f"   ID: {mg['id'][:12]}...")
        print(f"   💰 Supply: {mg['total_supply']:.2f} tokens")
        print(f"   👥 Holders: {mg['holder_count']}")
        print(f"   🔄 Transactions: {mg['transaction_count']}")
        print(f"   🛡️ Validators: {mg['validator_count']}")
        print(f"   📈 Recent Volume: {mg['recent_volume']:.2f} tokens")
        print(f"   📊 Status: {mg['status']}")
        print()
    
    # Network status
    print_section("Network Status")
    network = ecosystem['network_status']
    print(f"🌐 Network Status: {network.get('status', 'Unknown')}")
    if 'metrics' in network:
        metrics = network['metrics']
        print(f"📊 Total Transactions: {metrics.get('totalTransactions', 'N/A')}")
        print(f"👥 Active Addresses: {metrics.get('activeAddresses', 'N/A')}")
        print(f"⚡ Transaction Rate: {metrics.get('transactionRate', 'N/A')}")


async def run_comprehensive_demo():
    """Run all real-world use case demos."""
    print_header("Comprehensive Real-World GraphQL Use Cases")
    
    if not GRAPHQL_AVAILABLE:
        print("❌ GraphQL functionality not available!")
        print("Install optional dependencies to run these demos:")
        print("   pip install aiohttp websockets")
        return
    
    print("✅ GraphQL functionality available")
    print("🚀 Running comprehensive real-world use case demonstrations...")
    
    try:
        # Run all demos
        await run_portfolio_tracking_demo()
        await run_trading_bot_demo()
        await run_defi_analytics_demo()
        
        # Summary
        print_header("Demo Summary")
        print("✅ All real-world use cases completed successfully!")
        print()
        print("🎯 Key Takeaways:")
        print("   • GraphQL enables complex, efficient data fetching")
        print("   • Single queries replace multiple REST calls")
        print("   • Real-time capabilities support live applications")
        print("   • Flexible queries adapt to different use cases")
        print("   • Performance benefits scale with complexity")
        print()
        print("📚 Use Case Patterns Demonstrated:")
        print("   • Portfolio tracking and monitoring")
        print("   • Trading bot market analysis")
        print("   • DeFi ecosystem analytics")
        print("   • Real-time data subscriptions")
        print("   • Performance-optimized queries")
        print()
        print("🛠️ Next Steps:")
        print("   • Adapt patterns to your specific use case")
        print("   • Implement real-time monitoring")
        print("   • Add custom analytics and alerts")
        print("   • Scale to production workloads")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to run real-world use case demos."""
    asyncio.run(run_comprehensive_demo())


if __name__ == "__main__":
    main()