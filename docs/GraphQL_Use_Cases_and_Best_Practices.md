# GraphQL Use Cases and Best Practices

## Overview

This document provides comprehensive guidance for using the Constellation Network GraphQL API in real-world applications. The examples demonstrate practical patterns for portfolio tracking, trading bots, DeFi analytics, and more.

## Table of Contents

1. [Portfolio Tracking](#portfolio-tracking)
2. [Trading Bot Integration](#trading-bot-integration)
3. [DeFi Analytics Dashboard](#defi-analytics-dashboard)
4. [Real-time Monitoring](#real-time-monitoring)
5. [Performance Optimization](#performance-optimization)
6. [Error Handling](#error-handling)
7. [Security Best Practices](#security-best-practices)
8. [Scaling Considerations](#scaling-considerations)

## Portfolio Tracking

### Use Case: Multi-Address Portfolio Management

Portfolio tracking is one of the most common use cases for blockchain applications. The GraphQL API enables efficient monitoring of multiple addresses with complex data relationships.

#### Basic Pattern

```python
from constellation_sdk import GraphQLClient, QueryBuilder

class PortfolioTracker:
    def __init__(self, network: str = 'testnet'):
        self.client = GraphQLClient(network)
        self.tracked_addresses = []
    
    def add_address(self, address: str, label: str = None):
        self.tracked_addresses.append({
            'address': address,
            'label': label or f'Account_{len(self.tracked_addresses)+1}',
            'added_at': datetime.now()
        })
    
    def get_comprehensive_portfolio(self) -> Dict[str, Any]:
        addresses = [addr['address'] for addr in self.tracked_addresses]
        
        # Single GraphQL query for all portfolio data
        portfolio_query = """
        query ComprehensivePortfolio($addresses: [String!]!) {
            accounts(addresses: $addresses) {
                address
                balance
                transactions(first: 10) {
                    hash
                    amount
                    timestamp
                    destination
                    type
                }
                metagraphBalances {
                    metagraphId
                    balance
                    tokenSymbol
                }
            }
            network {
                status
                latestBlock {
                    height
                    timestamp
                }
            }
        }
        """
        
        response = self.client.execute(portfolio_query, {"addresses": addresses})
        return self._process_portfolio_data(response.data)
```

#### Key Benefits

- **Single Request**: Fetch all portfolio data in one GraphQL query
- **Flexible Data Selection**: Include only needed fields
- **Relationship Queries**: Get account balances, transactions, and metagraph tokens together
- **Network Context**: Include network status for comprehensive view

#### Performance Considerations

- **Batch Addresses**: Query multiple addresses in a single request
- **Limit Transaction History**: Use `first: N` to limit transaction count
- **Cache Results**: Cache portfolio data to reduce API calls
- **Pagination**: Use pagination for large portfolios

## Trading Bot Integration

### Use Case: Automated Trading with Market Analysis

Trading bots require real-time market data, analysis capabilities, and automated decision-making. GraphQL provides the flexibility needed for sophisticated trading strategies.

#### Basic Pattern

```python
from constellation_sdk import GraphQLClient
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class TradingSignal:
    signal_type: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    reasoning: str

class GraphQLTradingBot:
    def __init__(self, network: str = 'testnet'):
        self.client = GraphQLClient(network)
        self.config = {
            'max_position_size': 1000.0,
            'risk_tolerance': 0.05,
            'min_confidence': 0.7,
            'analysis_window': 24,
        }
    
    async def analyze_market_conditions(self, addresses: List[str]) -> Dict[str, Any]:
        market_query = """
        query MarketAnalysis($addresses: [String!]!) {
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
                metrics {
                    transactionRate
                    activeAddresses
                    totalTransactions
                }
            }
        }
        """
        
        response = await self.client.execute_async(market_query, {"addresses": addresses})
        return self._analyze_market_data(response.data)
    
    def generate_trading_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        signals = []
        
        # Volume-based signals
        if market_data['total_volume'] > 1000:
            signals.append(TradingSignal(
                signal_type="VOLUME",
                action="BUY" if market_data['price_trend'] == "BULLISH" else "HOLD",
                confidence=0.8,
                reasoning=f"High volume: {market_data['total_volume']:.2f} DAG"
            ))
        
        # Add more signal logic...
        return signals
```

#### Key Benefits

- **Real-time Analysis**: Continuous market monitoring
- **Multi-signal Aggregation**: Combine multiple indicators
- **Risk Management**: Built-in position sizing and risk controls
- **Performance Tracking**: Monitor bot performance and signals

#### Trading Bot Best Practices

1. **Comprehensive Analysis**: Use multiple data points for decisions
2. **Risk Management**: Always implement position sizing and stop losses
3. **Backtesting**: Test strategies on historical data
4. **Error Handling**: Graceful handling of network issues
5. **Logging**: Comprehensive logging for audit trails

## DeFi Analytics Dashboard

### Use Case: Ecosystem Analysis and Monitoring

DeFi applications require comprehensive ecosystem analysis, including metagraph metrics, validator information, and cross-protocol analytics.

#### Basic Pattern

```python
class DeFiAnalyticsDashboard:
    def __init__(self, network: str = 'testnet'):
        self.client = GraphQLClient(network)
    
    def get_ecosystem_overview(self, metagraph_ids: List[str]) -> Dict[str, Any]:
        ecosystem_query = """
        query EcosystemOverview($metagraphIds: [String!]!) {
            metagraphs(ids: $metagraphIds) {
                id
                name
                tokenSymbol
                totalSupply
                holderCount
                transactionCount
                status
                validators {
                    address
                    stake
                }
                recentTransactions: transactions(first: 20) {
                    hash
                    amount
                    timestamp
                    type
                }
            }
            network {
                status
                metrics {
                    totalTransactions
                    activeAddresses
                    transactionRate
                }
            }
        }
        """
        
        response = self.client.execute(ecosystem_query, {"metagraphIds": metagraph_ids})
        return self._process_ecosystem_data(response.data)
```

#### Key Benefits

- **Ecosystem View**: Complete overview of multiple metagraphs
- **Validator Analytics**: Track validator performance and stakes
- **Cross-protocol Analysis**: Compare metrics across different protocols
- **Historical Trends**: Track ecosystem growth and adoption

## Real-time Monitoring

### Use Case: Live Event Streaming

Real-time monitoring is crucial for responsive applications, alerting systems, and live dashboards.

#### Subscription Pattern

```python
async def monitor_addresses(addresses: List[str]):
    client = GraphQLClient('testnet')
    
    # Transaction monitoring subscription
    subscription = """
    subscription TransactionMonitor($addresses: [String!]!) {
        transactionUpdates(addresses: $addresses) {
            hash
            amount
            source
            destination
            timestamp
            type
        }
    }
    """
    
    async for response in client.subscribe(subscription, {"addresses": addresses}):
        if response.is_successful:
            tx_data = response.data.get('transactionUpdates', {})
            await handle_transaction_event(tx_data)
```

#### Real-time Best Practices

1. **Connection Management**: Handle disconnections gracefully
2. **Event Filtering**: Filter events client-side for efficiency
3. **Batch Processing**: Process multiple events together
4. **Alerting**: Set up alerts for important events
5. **Backpressure**: Handle high-frequency events appropriately

## Performance Optimization

### Query Optimization

#### 1. Field Selection

Only request fields you need:

```python
# Good - specific fields
query = """
query {
    account(address: $address) {
        balance
        transactions(first: 5) {
            hash
            amount
        }
    }
}
"""

# Bad - requesting everything
query = """
query {
    account(address: $address) {
        balance
        address
        transactions {
            hash
            amount
            timestamp
            source
            destination
            type
            metadata
        }
    }
}
"""
```

#### 2. Pagination

Use pagination for large datasets:

```python
# Good - paginated
query = """
query {
    transactions(first: 50, after: $cursor) {
        edges {
            node {
                hash
                amount
            }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}
"""
```

#### 3. Batching

Batch multiple queries:

```python
# Good - batch query
query = """
query BatchQuery($addresses: [String!]!) {
    accounts(addresses: $addresses) {
        address
        balance
    }
    network {
        status
    }
}
"""

# Bad - multiple separate queries
for address in addresses:
    query = f"query {{ account(address: \"{address}\") {{ balance }} }}"
    response = client.execute(query)
```

### Caching Strategies

#### 1. Response Caching

```python
import time
from functools import lru_cache

class CachedGraphQLClient:
    def __init__(self, network: str):
        self.client = GraphQLClient(network)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def execute_with_cache(self, query: str, variables: dict = None):
        cache_key = f"{query}:{hash(str(variables))}"
        
        if cache_key in self.cache:
            cached_response, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_response
        
        response = self.client.execute(query, variables)
        self.cache[cache_key] = (response, time.time())
        return response
```

#### 2. Data Normalization

```python
class NormalizedCache:
    def __init__(self):
        self.entities = {}
        self.queries = {}
    
    def normalize_response(self, response_data):
        # Normalize entities by ID
        for account in response_data.get('accounts', []):
            self.entities[f"Account:{account['address']}"] = account
        
        # Cache query results
        return response_data
```

## Error Handling

### Graceful Degradation

```python
class RobustGraphQLClient:
    def __init__(self, network: str):
        self.client = GraphQLClient(network)
        self.fallback_client = Network(network)  # REST fallback
    
    async def get_account_data(self, address: str):
        try:
            # Try GraphQL first
            response = await self.client.execute_async(
                "query { account(address: $address) { balance } }",
                {"address": address}
            )
            
            if response.is_successful:
                return response.data
            else:
                # Fallback to REST
                return await self._fallback_get_account(address)
                
        except Exception as e:
            # Fallback to REST on any error
            return await self._fallback_get_account(address)
    
    async def _fallback_get_account(self, address: str):
        balance = await self.fallback_client.get_balance(address)
        return {
            'account': {
                'address': address,
                'balance': balance,
                'source': 'rest_fallback'
            }
        }
```

### Retry Logic

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class RetryableGraphQLClient:
    def __init__(self, network: str):
        self.client = GraphQLClient(network)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def execute_with_retry(self, query: str, variables: dict = None):
        response = await self.client.execute_async(query, variables)
        
        if response.has_errors:
            # Determine if error is retryable
            retryable_errors = ['NETWORK_ERROR', 'TIMEOUT', 'RATE_LIMIT']
            for error in response.errors:
                if error.get('extensions', {}).get('code') in retryable_errors:
                    raise Exception(f"Retryable error: {error}")
        
        return response
```

## Security Best Practices

### 1. Query Validation

```python
import re
from typing import Dict, Any

class SecureGraphQLClient:
    def __init__(self, network: str):
        self.client = GraphQLClient(network)
        self.query_whitelist = {
            'account_balance',
            'network_status',
            'transaction_history'
        }
    
    def validate_query(self, query: str) -> bool:
        # Check for malicious patterns
        dangerous_patterns = [
            r'__schema',
            r'__type',
            r'mutation',
            r'subscription.*{.*}.*{.*}',  # Nested subscriptions
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False
        
        return True
    
    def execute_safe(self, query: str, variables: Dict[str, Any] = None):
        if not self.validate_query(query):
            raise ValueError("Query validation failed")
        
        return self.client.execute(query, variables)
```

### 2. Rate Limiting

```python
import time
from collections import defaultdict

class RateLimitedGraphQLClient:
    def __init__(self, network: str, requests_per_minute: int = 60):
        self.client = GraphQLClient(network)
        self.rate_limit = requests_per_minute
        self.request_times = defaultdict(list)
    
    def execute_with_rate_limit(self, query: str, variables: dict = None):
        current_time = time.time()
        client_id = "default"  # Could be user-specific
        
        # Clean old requests
        self.request_times[client_id] = [
            req_time for req_time in self.request_times[client_id]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.request_times[client_id]) >= self.rate_limit:
            raise Exception("Rate limit exceeded")
        
        # Execute query
        self.request_times[client_id].append(current_time)
        return self.client.execute(query, variables)
```

### 3. Input Sanitization

```python
from constellation_sdk.validation import AddressValidator

class SanitizedGraphQLClient:
    def __init__(self, network: str):
        self.client = GraphQLClient(network)
    
    def get_account_portfolio(self, address: str):
        # Validate address format
        AddressValidator.validate(address)
        
        # Sanitize inputs
        safe_address = self._sanitize_address(address)
        
        query = """
        query AccountPortfolio($address: String!) {
            account(address: $address) {
                address
                balance
                transactions(first: 20) {
                    hash
                    amount
                    timestamp
                }
            }
        }
        """
        
        return self.client.execute(query, {"address": safe_address})
    
    def _sanitize_address(self, address: str) -> str:
        # Remove any non-alphanumeric characters except expected ones
        import re
        return re.sub(r'[^a-zA-Z0-9]', '', address)
```

## Scaling Considerations

### 1. Connection Pooling

```python
import asyncio
from aiohttp import ClientSession, TCPConnector

class PooledGraphQLClient:
    def __init__(self, network: str, max_connections: int = 100):
        self.network = network
        self.max_connections = max_connections
        self.session = None
        self.semaphore = asyncio.Semaphore(max_connections)
    
    async def __aenter__(self):
        connector = TCPConnector(
            limit=self.max_connections,
            limit_per_host=30,
            ttl_dns_cache=300
        )
        
        self.session = ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute(self, query: str, variables: dict = None):
        async with self.semaphore:
            # Execute query with connection pooling
            pass
```

### 2. Load Balancing

```python
import random
from typing import List

class LoadBalancedGraphQLClient:
    def __init__(self, endpoints: List[str]):
        self.clients = [GraphQLClient(endpoint) for endpoint in endpoints]
        self.health_status = {i: True for i in range(len(self.clients))}
    
    def get_healthy_client(self) -> GraphQLClient:
        healthy_clients = [
            (i, client) for i, client in enumerate(self.clients)
            if self.health_status[i]
        ]
        
        if not healthy_clients:
            raise Exception("No healthy clients available")
        
        # Round-robin or random selection
        return random.choice(healthy_clients)[1]
    
    async def execute_with_failover(self, query: str, variables: dict = None):
        for attempt in range(len(self.clients)):
            try:
                client = self.get_healthy_client()
                response = await client.execute_async(query, variables)
                return response
            except Exception as e:
                # Mark client as unhealthy and try next
                client_idx = self.clients.index(client)
                self.health_status[client_idx] = False
                
                if attempt == len(self.clients) - 1:
                    raise e
```

### 3. Monitoring and Metrics

```python
import time
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class QueryMetrics:
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    query_types: defaultdict = defaultdict(int)

class MonitoredGraphQLClient:
    def __init__(self, network: str):
        self.client = GraphQLClient(network)
        self.metrics = QueryMetrics()
    
    def execute_with_metrics(self, query: str, variables: dict = None):
        start_time = time.time()
        query_type = self._extract_query_type(query)
        
        try:
            response = self.client.execute(query, variables)
            execution_time = time.time() - start_time
            
            # Update metrics
            self.metrics.total_queries += 1
            self.metrics.total_execution_time += execution_time
            self.metrics.query_types[query_type] += 1
            
            if response.is_successful:
                self.metrics.successful_queries += 1
            else:
                self.metrics.failed_queries += 1
            
            # Calculate average
            self.metrics.average_execution_time = (
                self.metrics.total_execution_time / self.metrics.total_queries
            )
            
            return response
            
        except Exception as e:
            self.metrics.failed_queries += 1
            raise e
    
    def _extract_query_type(self, query: str) -> str:
        # Extract operation type from query
        if 'query' in query.lower():
            return 'query'
        elif 'mutation' in query.lower():
            return 'mutation'
        elif 'subscription' in query.lower():
            return 'subscription'
        else:
            return 'unknown'
    
    def get_metrics_summary(self) -> dict:
        return {
            'total_queries': self.metrics.total_queries,
            'success_rate': self.metrics.successful_queries / max(self.metrics.total_queries, 1),
            'average_execution_time': self.metrics.average_execution_time,
            'query_types': dict(self.metrics.query_types)
        }
```

## Example Applications

### 1. Portfolio Dashboard

```python
# examples/portfolio_dashboard.py
async def run_portfolio_dashboard():
    tracker = PortfolioTracker('testnet')
    
    # Add addresses to track
    addresses = [
        "DAG123...",
        "DAG456...",
        "DAG789..."
    ]
    
    for i, address in enumerate(addresses):
        tracker.add_address(address, f"Wallet_{i+1}")
    
    # Get portfolio data
    portfolio = tracker.get_comprehensive_portfolio()
    
    # Display dashboard
    print("Portfolio Dashboard")
    print("=" * 50)
    print(f"Total Balance: {portfolio['total_dag_balance']:.8f} DAG")
    print(f"Accounts: {portfolio['total_accounts']}")
    print(f"Metagraph Tokens: {portfolio['total_metagraph_tokens']}")
    
    for account in portfolio['accounts']:
        print(f"\n{account['label']}:")
        print(f"  Balance: {account['balance_dag']:.8f} DAG")
        print(f"  Transactions: {account['transaction_count']}")
```

### 2. Trading Bot

```python
# examples/trading_bot.py
async def run_trading_bot():
    bot = GraphQLTradingBot('testnet')
    
    # Target addresses for analysis
    target_addresses = [
        "DAG123...",
        "DAG456...",
        "DAG789..."
    ]
    
    while True:
        # Run trading cycle
        cycle_result = await bot.run_trading_cycle(target_addresses)
        
        if 'error' not in cycle_result:
            execution = cycle_result['execution_result']
            print(f"Action: {execution['action']}")
            print(f"Confidence: {execution.get('confidence', 0):.1%}")
            
            # Execute trade if conditions are met
            if execution['action'] in ['BUY', 'SELL']:
                await execute_trade(execution)
        
        # Wait before next cycle
        await asyncio.sleep(60)
```

### 3. DeFi Analytics

```python
# examples/defi_analytics.py
async def run_defi_analytics():
    dashboard = DeFiAnalyticsDashboard('testnet')
    
    # Metagraphs to analyze
    metagraph_ids = [
        "DAG7Ghth6FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhQs",
        "DAG8Mth7FKMcvfK6A8BGSKvJvBYe4EFKgPvvQPJqhRt"
    ]
    
    # Get ecosystem overview
    ecosystem = dashboard.get_ecosystem_overview(metagraph_ids)
    
    # Display analytics
    print("DeFi Ecosystem Analytics")
    print("=" * 50)
    print(f"Total Metagraphs: {ecosystem['total_metagraphs']}")
    print(f"Total Supply: {ecosystem['ecosystem_metrics']['total_supply']:.2f}")
    print(f"Total Holders: {ecosystem['ecosystem_metrics']['total_holders']}")
    
    for mg in ecosystem['metagraph_details']:
        print(f"\n{mg['name']}:")
        print(f"  Token: {mg['token_symbol']}")
        print(f"  Supply: {mg['total_supply']:.2f}")
        print(f"  Holders: {mg['holder_count']}")
```

## Conclusion

The Constellation Network GraphQL API provides powerful capabilities for building sophisticated blockchain applications. By following these patterns and best practices, you can create efficient, scalable, and maintainable applications that leverage the full potential of GraphQL.

### Key Takeaways

1. **Single Query Efficiency**: Use GraphQL's ability to fetch complex data in single requests
2. **Real-time Capabilities**: Leverage subscriptions for live data updates
3. **Flexible Data Selection**: Request only the data you need
4. **Error Handling**: Implement robust error handling and fallback mechanisms
5. **Performance Optimization**: Use caching, batching, and pagination appropriately
6. **Security**: Validate inputs and implement rate limiting
7. **Monitoring**: Track performance and usage metrics

### Next Steps

1. **Experiment**: Try the example applications in your environment
2. **Customize**: Adapt the patterns to your specific use case
3. **Scale**: Implement the scaling considerations for production use
4. **Monitor**: Set up monitoring and alerting for your applications
5. **Contribute**: Share your patterns and improvements with the community

For more examples and detailed implementation, see the `examples/` directory in the Constellation Python SDK repository.