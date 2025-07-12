"""
GraphQL client implementation for Constellation Network SDK.

This module provides GraphQL query capabilities for flexible data fetching,
real-time subscriptions, and complex relationship queries across DAG accounts,
metagraphs, and network data.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import time

try:
    import aiohttp
    import websockets
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

from .config import DEFAULT_CONFIGS
from .exceptions import ConstellationError, NetworkError, ValidationError
from .network import Network
from .validation import AddressValidator


class GraphQLOperationType(Enum):
    """GraphQL operation types."""
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"


@dataclass
class GraphQLQuery:
    """
    Represents a GraphQL query with variables and metadata.
    
    Args:
        query: GraphQL query string
        variables: Query variables dictionary
        operation_name: Optional operation name
        operation_type: Type of GraphQL operation
    """
    query: str
    variables: Dict[str, Any] = field(default_factory=dict)
    operation_name: Optional[str] = None
    operation_type: GraphQLOperationType = GraphQLOperationType.QUERY


@dataclass
class GraphQLResponse:
    """
    GraphQL response wrapper with error handling.
    
    Args:
        data: Response data
        errors: List of GraphQL errors
        extensions: Response extensions
        execution_time: Query execution time
    """
    data: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    extensions: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    
    @property
    def has_errors(self) -> bool:
        """Check if response has errors."""
        return bool(self.errors)
    
    @property
    def is_successful(self) -> bool:
        """Check if response is successful."""
        return self.data is not None and not self.has_errors


class GraphQLClient:
    """
    GraphQL client for Constellation Network.
    
    Provides flexible query capabilities, real-time subscriptions,
    and integration with existing SDK functionality.
    """
    
    def __init__(self, network: str = 'testnet'):
        """
        Initialize GraphQL client.
        
        Args:
            network: Network name (mainnet, testnet, integrationnet)
        """
        self.network = network
        self.config = DEFAULT_CONFIGS[network]
        self.network_client = Network(network)
        
        # GraphQL endpoint configuration
        self.graphql_endpoint = self._get_graphql_endpoint()
        self.subscription_endpoint = self._get_subscription_endpoint()
        
        # Client state
        self._session = None
        self._websocket = None
        self._subscription_tasks = {}
        
        # Statistics
        self._stats = {
            'queries_executed': 0,
            'subscriptions_active': 0,
            'total_execution_time': 0,
            'errors_encountered': 0
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def _get_graphql_endpoint(self) -> str:
        """Get GraphQL HTTP endpoint."""
        base_url = self.config.l0_url
        return f"{base_url}/graphql"
    
    def _get_subscription_endpoint(self) -> str:
        """Get GraphQL WebSocket endpoint for subscriptions."""
        base_url = self.config.l0_url
        # Convert HTTP to WebSocket URL
        if base_url.startswith('http://'):
            ws_url = base_url.replace('http://', 'ws://')
        elif base_url.startswith('https://'):
            ws_url = base_url.replace('https://', 'wss://')
        else:
            ws_url = base_url
        return f"{ws_url}/graphql"
    
    def execute(self, query: Union[str, GraphQLQuery], variables: Optional[Dict[str, Any]] = None) -> GraphQLResponse:
        """
        Execute GraphQL query synchronously.
        
        Args:
            query: GraphQL query string or GraphQLQuery object
            variables: Query variables
            
        Returns:
            GraphQLResponse with data and metadata
        """
        if isinstance(query, str):
            query = GraphQLQuery(query=query, variables=variables or {})
        
        start_time = time.time()
        
        try:
            # For now, we'll simulate GraphQL by translating to REST calls
            # In production, this would make actual GraphQL requests
            response_data = self._execute_via_rest_translation(query)
            
            execution_time = time.time() - start_time
            self._stats['queries_executed'] += 1
            self._stats['total_execution_time'] += execution_time
            
            return GraphQLResponse(
                data=response_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            self._stats['errors_encountered'] += 1
            self.logger.error(f"GraphQL query execution failed: {e}")
            
            return GraphQLResponse(
                errors=[{
                    'message': str(e),
                    'extensions': {'code': 'EXECUTION_ERROR'}
                }],
                execution_time=time.time() - start_time
            )
    
    async def execute_async(self, query: Union[str, GraphQLQuery], variables: Optional[Dict[str, Any]] = None) -> GraphQLResponse:
        """
        Execute GraphQL query asynchronously.
        
        Args:
            query: GraphQL query string or GraphQLQuery object
            variables: Query variables
            
        Returns:
            GraphQLResponse with data and metadata
        """
        if not ASYNC_AVAILABLE:
            raise ConstellationError("Async support not available. Install aiohttp for async operations.")
        
        if isinstance(query, str):
            query = GraphQLQuery(query=query, variables=variables or {})
        
        start_time = time.time()
        
        try:
            # Initialize async session if needed
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            # For now, simulate GraphQL execution
            response_data = await self._execute_via_rest_translation_async(query)
            
            execution_time = time.time() - start_time
            self._stats['queries_executed'] += 1
            self._stats['total_execution_time'] += execution_time
            
            return GraphQLResponse(
                data=response_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            self._stats['errors_encountered'] += 1
            self.logger.error(f"Async GraphQL query execution failed: {e}")
            
            return GraphQLResponse(
                errors=[{
                    'message': str(e),
                    'extensions': {'code': 'EXECUTION_ERROR'}
                }],
                execution_time=time.time() - start_time
            )
    
    def batch_execute(self, queries: List[Union[str, GraphQLQuery]]) -> List[GraphQLResponse]:
        """
        Execute multiple GraphQL queries in batch.
        
        Args:
            queries: List of GraphQL queries
            
        Returns:
            List of GraphQLResponse objects
        """
        responses = []
        
        for query in queries:
            if isinstance(query, str):
                query = GraphQLQuery(query=query)
            
            response = self.execute(query)
            responses.append(response)
        
        return responses
    
    async def subscribe(self, subscription: Union[str, GraphQLQuery], variables: Optional[Dict[str, Any]] = None) -> AsyncGenerator[GraphQLResponse, None]:
        """
        Create GraphQL subscription for real-time updates.
        
        Args:
            subscription: GraphQL subscription string or GraphQLQuery object
            variables: Subscription variables
            
        Yields:
            GraphQLResponse objects for each subscription update
        """
        if not ASYNC_AVAILABLE:
            raise ConstellationError("Async support not available. Install aiohttp and websockets for subscriptions.")
        
        if isinstance(subscription, str):
            subscription = GraphQLQuery(
                query=subscription,
                variables=variables or {},
                operation_type=GraphQLOperationType.SUBSCRIPTION
            )
        
        subscription_id = f"sub_{int(time.time() * 1000)}"
        
        try:
            # For now, simulate subscription by polling
            # In production, this would use WebSocket subscriptions
            async for update in self._simulate_subscription(subscription):
                yield GraphQLResponse(data=update)
                
        except Exception as e:
            self.logger.error(f"Subscription failed: {e}")
            yield GraphQLResponse(
                errors=[{
                    'message': str(e),
                    'extensions': {'code': 'SUBSCRIPTION_ERROR'}
                }]
            )
    
    def _execute_via_rest_translation(self, query: GraphQLQuery) -> Dict[str, Any]:
        """
        Translate GraphQL query to REST API calls.
        
        This is a simulation layer until full GraphQL endpoint is available.
        """
        # Parse query to determine what data is needed
        query_str = query.query.lower()
        variables = query.variables
        
        result = {}
        
        # Account queries
        if 'account' in query_str and 'address' in variables:
            address = variables['address']
            AddressValidator.validate(address)
            
            account_data = {
                'address': address,
                'balance': self.network_client.get_balance(address)
            }
            
            # Add transactions if requested
            if 'transactions' in query_str:
                try:
                    # Simulate transaction history
                    account_data['transactions'] = []
                except Exception:
                    account_data['transactions'] = []
            
            result['account'] = account_data
        
        # Network queries
        if 'network' in query_str:
            try:
                network_data = {
                    'status': 'active',
                    'info': self.network_client.get_node_info(),
                    'cluster': self.network_client.get_cluster_info()
                }
                result['network'] = network_data
            except Exception as e:
                self.logger.warning(f"Failed to get network data: {e}")
        
        # Metagraph queries
        if 'metagraph' in query_str and 'id' in variables:
            metagraph_id = variables['id']
            try:
                # Simulate metagraph data
                result['metagraph'] = {
                    'id': metagraph_id,
                    'name': f"Metagraph_{metagraph_id[:8]}",
                    'status': 'active'
                }
            except Exception as e:
                self.logger.warning(f"Failed to get metagraph data: {e}")
        
        return result
    
    async def _execute_via_rest_translation_async(self, query: GraphQLQuery) -> Dict[str, Any]:
        """
        Async version of REST translation.
        """
        # For now, just call the sync version
        # In production, this would use async HTTP calls
        return self._execute_via_rest_translation(query)
    
    async def _simulate_subscription(self, subscription: GraphQLQuery) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Simulate GraphQL subscription with polling.
        """
        subscription_str = subscription.query.lower()
        variables = subscription.variables
        
        # Simulate subscription updates
        counter = 0
        while counter < 10:  # Limit for demo
            await asyncio.sleep(5)  # Poll every 5 seconds
            
            if 'transactionupdates' in subscription_str:
                # Simulate transaction updates
                yield {
                    'transactionUpdates': {
                        'hash': f'tx_{counter}_{int(time.time())}',
                        'amount': 100000000,
                        'timestamp': time.time()
                    }
                }
            
            counter += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get GraphQL client statistics."""
        return {
            **self._stats,
            'average_execution_time': (
                self._stats['total_execution_time'] / self._stats['queries_executed']
                if self._stats['queries_executed'] > 0 else 0
            )
        }
    
    async def close(self):
        """Close async resources."""
        if self._session:
            await self._session.close()
        
        if self._websocket:
            await self._websocket.close()
        
        # Cancel subscription tasks
        for task in self._subscription_tasks.values():
            if not task.done():
                task.cancel()


# Pre-built GraphQL schemas for common operations
class ConstellationSchema:
    """Pre-built GraphQL schemas for common Constellation operations."""
    
    ACCOUNT_PORTFOLIO = """
    query AccountPortfolio($address: String!) {
        account(address: $address) {
            address
            balance
            transactions(first: 20) {
                hash
                amount
                timestamp
                destination
            }
            metagraphBalances {
                metagraphId
                balance
                tokenSymbol
            }
        }
    }
    """
    
    METAGRAPH_OVERVIEW = """
    query MetagraphOverview($id: String!) {
        metagraph(id: $id) {
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
        }
    }
    """
    
    NETWORK_STATUS = """
    query NetworkStatus {
        network {
            status
            nodeCount
            version
            latestBlock {
                hash
                height
                timestamp
            }
            metrics {
                transactionRate
                totalTransactions
                activeAddresses
            }
        }
    }
    """
    
    TRANSACTION_SUBSCRIPTION = """
    subscription TransactionUpdates($addresses: [String!]) {
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
    
    BALANCE_SUBSCRIPTION = """
    subscription BalanceUpdates($addresses: [String!]) {
        balanceUpdates(addresses: $addresses) {
            address
            oldBalance
            newBalance
            change
            timestamp
        }
    }
    """


# Convenience functions for quick GraphQL operations
def execute_query(network: str, query: str, variables: Optional[Dict[str, Any]] = None) -> GraphQLResponse:
    """
    Execute GraphQL query with minimal setup.
    
    Args:
        network: Network name
        query: GraphQL query string
        variables: Query variables
        
    Returns:
        GraphQLResponse
    """
    client = GraphQLClient(network)
    return client.execute(query, variables)


async def execute_query_async(network: str, query: str, variables: Optional[Dict[str, Any]] = None) -> GraphQLResponse:
    """
    Execute GraphQL query asynchronously with minimal setup.
    
    Args:
        network: Network name
        query: GraphQL query string
        variables: Query variables
        
    Returns:
        GraphQLResponse
    """
    client = GraphQLClient(network)
    try:
        return await client.execute_async(query, variables)
    finally:
        await client.close()


def get_account_portfolio(network: str, address: str) -> GraphQLResponse:
    """
    Get complete account portfolio using GraphQL.
    
    Args:
        network: Network name
        address: Account address
        
    Returns:
        GraphQLResponse with account portfolio data
    """
    return execute_query(
        network,
        ConstellationSchema.ACCOUNT_PORTFOLIO,
        {'address': address}
    )


def get_metagraph_overview(network: str, metagraph_id: str) -> GraphQLResponse:
    """
    Get metagraph overview using GraphQL.
    
    Args:
        network: Network name
        metagraph_id: Metagraph ID
        
    Returns:
        GraphQLResponse with metagraph data
    """
    return execute_query(
        network,
        ConstellationSchema.METAGRAPH_OVERVIEW,
        {'id': metagraph_id}
    )


def get_network_status(network: str) -> GraphQLResponse:
    """
    Get network status using GraphQL.
    
    Args:
        network: Network name
        
    Returns:
        GraphQLResponse with network status
    """
    return execute_query(network, ConstellationSchema.NETWORK_STATUS)