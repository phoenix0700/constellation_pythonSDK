"""
Tests for GraphQL functionality.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from constellation_sdk.exceptions import ConstellationError, NetworkError
from constellation_sdk.graphql import (
    ConstellationSchema,
    GraphQLClient,
    GraphQLOperationType,
    GraphQLQuery,
    GraphQLResponse,
    execute_query,
    execute_query_async,
    get_account_portfolio,
    get_metagraph_overview,
    get_network_status,
)
from constellation_sdk.graphql_builder import (
    QueryBuilder,
    SubscriptionBuilder,
    build_account_query,
    build_balance_subscription,
    build_metagraph_query,
    build_network_status_query,
    build_portfolio_query,
    build_transaction_subscription,
)


class TestGraphQLQuery:
    """Test GraphQLQuery class."""

    def test_query_creation(self):
        """Test GraphQLQuery creation."""
        query = GraphQLQuery(
            query="query { account { balance } }",
            variables={"address": "DAG123"},
            operation_name="GetBalance",
        )

        assert query.query == "query { account { balance } }"
        assert query.variables == {"address": "DAG123"}
        assert query.operation_name == "GetBalance"
        assert query.operation_type == GraphQLOperationType.QUERY

    def test_query_defaults(self):
        """Test GraphQLQuery with defaults."""
        query = GraphQLQuery(query="query { network { status } }")

        assert query.query == "query { network { status } }"
        assert query.variables == {}
        assert query.operation_name is None
        assert query.operation_type == GraphQLOperationType.QUERY


class TestGraphQLResponse:
    """Test GraphQLResponse class."""

    def test_successful_response(self):
        """Test successful GraphQL response."""
        response = GraphQLResponse(
            data={"account": {"balance": 1000000000}}, execution_time=0.123
        )

        assert response.data == {"account": {"balance": 1000000000}}
        assert response.execution_time == 0.123
        assert response.is_successful
        assert not response.has_errors

    def test_error_response(self):
        """Test error GraphQL response."""
        response = GraphQLResponse(
            errors=[
                {"message": "Field not found", "extensions": {"code": "FIELD_ERROR"}}
            ],
            execution_time=0.056,
        )

        assert response.data is None
        assert len(response.errors) == 1
        assert response.errors[0]["message"] == "Field not found"
        assert response.has_errors
        assert not response.is_successful

    def test_mixed_response(self):
        """Test response with both data and errors."""
        response = GraphQLResponse(
            data={"account": {"balance": 1000000000}},
            errors=[{"message": "Warning: deprecated field"}],
            execution_time=0.089,
        )

        assert response.data is not None
        assert len(response.errors) == 1
        assert response.has_errors
        assert not response.is_successful  # Has errors, so not successful


class TestGraphQLClient:
    """Test GraphQLClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = GraphQLClient("testnet")
        self.valid_address = "DAG00000000000000000000000000000000000"
        self.valid_metagraph_id = "DAG11111111111111111111111111111111111"

    def test_client_initialization(self):
        """Test GraphQLClient initialization."""
        assert self.client.network == "testnet"
        assert "graphql" in self.client.graphql_endpoint
        assert "graphql" in self.client.subscription_endpoint
        assert self.client._stats["queries_executed"] == 0

    def test_execute_query_string(self):
        """Test executing a simple query string."""
        query = "query { network { status } }"

        with patch.object(self.client, "_execute_via_rest_translation") as mock_execute:
            mock_execute.return_value = {"network": {"status": "active"}}

            response = self.client.execute(query)

            assert response.is_successful
            assert response.data == {"network": {"status": "active"}}
            assert self.client._stats["queries_executed"] == 1

    def test_execute_query_object(self):
        """Test executing a GraphQLQuery object."""
        query = GraphQLQuery(
            query="query GetAccount($address: String!) { account(address: $address) { balance } }",
            variables={"address": self.valid_address},
        )

        with patch.object(self.client, "_execute_via_rest_translation") as mock_execute:
            mock_execute.return_value = {"account": {"balance": 1000000000}}

            response = self.client.execute(query)

            assert response.is_successful
            assert response.data == {"account": {"balance": 1000000000}}

    def test_execute_query_error(self):
        """Test query execution error handling."""
        query = "invalid query"

        with patch.object(self.client, "_execute_via_rest_translation") as mock_execute:
            mock_execute.side_effect = Exception("Query failed")

            response = self.client.execute(query)

            assert not response.is_successful
            assert response.has_errors
            assert "Query failed" in response.errors[0]["message"]
            assert self.client._stats["errors_encountered"] == 1

    @pytest.mark.asyncio
    async def test_execute_query_async(self):
        """Test async query execution."""
        query = "query { network { status } }"

        with patch.object(
            self.client, "_execute_via_rest_translation_async"
        ) as mock_execute:
            mock_execute.return_value = {"network": {"status": "active"}}

            response = await self.client.execute_async(query)

            assert response.is_successful
            assert response.data == {"network": {"status": "active"}}

    def test_batch_execute(self):
        """Test batch query execution."""
        queries = [
            "query { network { status } }",
            GraphQLQuery(
                query="query { account { balance } }",
                variables={"address": self.valid_address},
            ),
        ]

        with patch.object(self.client, "_execute_via_rest_translation") as mock_execute:
            mock_execute.side_effect = [
                {"network": {"status": "active"}},
                {"account": {"balance": 1000000000}},
            ]

            responses = self.client.batch_execute(queries)

            assert len(responses) == 2
            assert all(r.is_successful for r in responses)
            assert responses[0].data == {"network": {"status": "active"}}
            assert responses[1].data == {"account": {"balance": 1000000000}}

    @pytest.mark.asyncio
    async def test_subscription(self):
        """Test GraphQL subscription."""
        subscription = "subscription { transactionUpdates { hash amount } }"

        with patch.object(self.client, "_simulate_subscription") as mock_sub:
            mock_sub.return_value = asyncio.Queue()

            # Put test data in queue
            test_updates = [
                {"transactionUpdates": {"hash": "tx1", "amount": 100000000}},
                {"transactionUpdates": {"hash": "tx2", "amount": 200000000}},
            ]

            async def mock_subscription_generator(query):
                for update in test_updates:
                    yield update

            mock_sub.return_value = mock_subscription_generator(None)

            updates = []
            async for response in self.client.subscribe(subscription):
                updates.append(response.data)
                if len(updates) >= 2:
                    break

            assert len(updates) == 2
            assert updates[0]["transactionUpdates"]["hash"] == "tx1"
            assert updates[1]["transactionUpdates"]["hash"] == "tx2"

    def test_get_stats(self):
        """Test getting client statistics."""
        # Execute a query to update stats
        self.client._stats["queries_executed"] = 5
        self.client._stats["total_execution_time"] = 1.5

        stats = self.client.get_stats()

        assert stats["queries_executed"] == 5
        assert stats["total_execution_time"] == 1.5
        assert stats["average_execution_time"] == 0.3

    def test_rest_translation_account_query(self):
        """Test REST translation for account queries."""
        query = GraphQLQuery(
            query="query { account { balance } }",
            variables={"address": self.valid_address},
        )

        with patch.object(self.client.network_client, "get_balance") as mock_balance:
            mock_balance.return_value = 1000000000

            result = self.client._execute_via_rest_translation(query)

            assert "account" in result
            assert result["account"]["address"] == self.valid_address
            assert result["account"]["balance"] == 1000000000

    def test_rest_translation_network_query(self):
        """Test REST translation for network queries."""
        query = GraphQLQuery(query="query { network { status info } }")

        with patch.object(self.client.network_client, "get_node_info") as mock_info:
            with patch.object(
                self.client.network_client, "get_cluster_info"
            ) as mock_cluster:
                mock_info.return_value = {"version": "1.0.0"}
                mock_cluster.return_value = [{"id": "node1"}]

                result = self.client._execute_via_rest_translation(query)

                assert "network" in result
                assert result["network"]["status"] == "active"
                assert result["network"]["info"]["version"] == "1.0.0"

    def test_rest_translation_metagraph_query(self):
        """Test REST translation for metagraph queries."""
        query = GraphQLQuery(
            query="query { metagraph { id name } }",
            variables={"id": self.valid_metagraph_id},
        )

        result = self.client._execute_via_rest_translation(query)

        assert "metagraph" in result
        assert result["metagraph"]["id"] == self.valid_metagraph_id
        assert "name" in result["metagraph"]


class TestQueryBuilder:
    """Test QueryBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = QueryBuilder()
        self.valid_address = "DAG00000000000000000000000000000000000"
        self.valid_metagraph_id = "DAG11111111111111111111111111111111111"

    def test_account_query_builder(self):
        """Test building account queries."""
        query = (
            self.builder.account(self.valid_address)
            .with_balance()
            .with_address()
            .with_transactions(limit=10)
            .build()
        )

        assert "query" in query
        assert "account" in query
        assert "balance" in query
        assert "transactions" in query
        assert "first: 10" in query

    def test_metagraph_query_builder(self):
        """Test building metagraph queries."""
        query = (
            self.builder.metagraph(self.valid_metagraph_id)
            .with_info()
            .with_supply_info()
            .with_holders(limit=50)
            .build()
        )

        assert "query" in query
        assert "metagraph" in query
        assert "tokenSymbol" in query
        assert "totalSupply" in query
        assert "holders" in query
        assert "first: 50" in query

    def test_network_query_builder(self):
        """Test building network queries."""
        query = (
            self.builder.network()
            .with_status()
            .with_latest_block()
            .with_metrics()
            .build()
        )

        assert "query" in query
        assert "network" in query
        assert "status" in query
        assert "latestBlock" in query
        assert "metrics" in query

    def test_accounts_query_builder(self):
        """Test building multi-account queries."""
        addresses = [self.valid_address, "DAG22222222222222222222222222222222222"]

        query = (
            self.builder.accounts(addresses)
            .with_balances()
            .with_transactions(limit=5)
            .build()
        )

        assert "query" in query
        assert "accounts" in query
        assert "balance" in query
        assert "transactions" in query
        assert "first: 5" in query

    def test_metagraphs_query_builder(self):
        """Test building metagraphs queries."""
        query = (
            self.builder.metagraphs()
            .with_basic_info()
            .with_metrics()
            .production_only()
            .build()
        )

        assert "query" in query
        assert "metagraphs" in query
        assert "tokenSymbol" in query
        assert "holderCount" in query
        assert "production: True" in query

    def test_query_with_variables(self):
        """Test building queries with variables."""
        query = (
            self.builder.add_variable("address", self.valid_address)
            .set_operation_name("GetAccountInfo")
            .account(self.valid_address)
            .with_balance()
            .build()
        )

        assert "query GetAccountInfo" in query
        assert "$address: String" in query

    def test_empty_query_error(self):
        """Test error when building empty query."""
        with pytest.raises(ValueError, match="No fields added to query"):
            self.builder.build()


class TestSubscriptionBuilder:
    """Test SubscriptionBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = SubscriptionBuilder()
        self.valid_address = "DAG00000000000000000000000000000000000"

    def test_transaction_subscription(self):
        """Test building transaction subscription."""
        subscription = self.builder.transaction_updates([self.valid_address]).build()

        assert "subscription" in subscription
        assert "transactionUpdates" in subscription
        assert "hash" in subscription
        assert "amount" in subscription

    def test_balance_subscription(self):
        """Test building balance subscription."""
        subscription = self.builder.balance_updates([self.valid_address]).build()

        assert "subscription" in subscription
        assert "balanceUpdates" in subscription
        assert "oldBalance" in subscription
        assert "newBalance" in subscription

    def test_metagraph_subscription(self):
        """Test building metagraph subscription."""
        metagraph_ids = ["DAG11111111111111111111111111111111111"]

        subscription = self.builder.metagraph_updates(metagraph_ids).build()

        assert "subscription" in subscription
        assert "metagraphUpdates" in subscription
        assert "updateType" in subscription

    def test_empty_subscription_error(self):
        """Test error when building empty subscription."""
        with pytest.raises(ValueError, match="No fields added to subscription"):
            self.builder.build()


class TestConvenienceFunctions:
    """Test convenience functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_address = "DAG00000000000000000000000000000000000"
        self.valid_metagraph_id = "DAG11111111111111111111111111111111111"

    def test_build_account_query(self):
        """Test build_account_query function."""
        query = build_account_query(self.valid_address)

        assert "query" in query
        assert "account" in query
        assert "balance" in query
        assert "transactions" in query
        assert "metagraphBalances" in query

    def test_build_metagraph_query(self):
        """Test build_metagraph_query function."""
        query = build_metagraph_query(self.valid_metagraph_id)

        assert "query" in query
        assert "metagraph" in query
        assert "tokenSymbol" in query
        assert "holders" in query
        assert "transactions" in query

    def test_build_network_status_query(self):
        """Test build_network_status_query function."""
        query = build_network_status_query()

        assert "query" in query
        assert "network" in query
        assert "status" in query
        assert "latestBlock" in query
        assert "metrics" in query

    def test_build_portfolio_query(self):
        """Test build_portfolio_query function."""
        addresses = [self.valid_address, "DAG22222222222222222222222222222222222"]
        query = build_portfolio_query(addresses)

        assert "query" in query
        assert "accounts" in query
        assert "balance" in query
        assert "transactions" in query

    def test_build_transaction_subscription(self):
        """Test build_transaction_subscription function."""
        subscription = build_transaction_subscription([self.valid_address])

        assert "subscription" in subscription
        assert "transactionUpdates" in subscription
        assert "hash" in subscription

    def test_build_balance_subscription(self):
        """Test build_balance_subscription function."""
        subscription = build_balance_subscription([self.valid_address])

        assert "subscription" in subscription
        assert "balanceUpdates" in subscription
        assert "oldBalance" in subscription


class TestGraphQLIntegration:
    """Integration tests for GraphQL functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_address = "DAG00000000000000000000000000000000000"
        self.valid_metagraph_id = "DAG11111111111111111111111111111111111"

    def test_execute_query_convenience(self):
        """Test execute_query convenience function."""
        query = "query { network { status } }"

        with patch("constellation_sdk.graphql.GraphQLClient") as mock_client_class:
            mock_client = Mock()
            mock_client.execute.return_value = GraphQLResponse(
                data={"network": {"status": "active"}}
            )
            mock_client_class.return_value = mock_client

            response = execute_query("testnet", query)

            assert response.is_successful
            assert response.data == {"network": {"status": "active"}}

    @pytest.mark.asyncio
    async def test_execute_query_async_convenience(self):
        """Test execute_query_async convenience function."""
        query = "query { network { status } }"

        with patch("constellation_sdk.graphql.GraphQLClient") as mock_client_class:
            mock_client = Mock()
            mock_client.execute_async = AsyncMock(
                return_value=GraphQLResponse(data={"network": {"status": "active"}})
            )
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            response = await execute_query_async("testnet", query)

            assert response.is_successful
            assert response.data == {"network": {"status": "active"}}
            mock_client.close.assert_called_once()

    def test_get_account_portfolio_convenience(self):
        """Test get_account_portfolio convenience function."""
        with patch("constellation_sdk.graphql.execute_query") as mock_execute:
            mock_execute.return_value = GraphQLResponse(
                data={"account": {"balance": 1000000000, "transactions": []}}
            )

            response = get_account_portfolio("testnet", self.valid_address)

            assert response.is_successful
            assert response.data["account"]["balance"] == 1000000000
            mock_execute.assert_called_once()

    def test_get_metagraph_overview_convenience(self):
        """Test get_metagraph_overview convenience function."""
        with patch("constellation_sdk.graphql.execute_query") as mock_execute:
            mock_execute.return_value = GraphQLResponse(
                data={
                    "metagraph": {
                        "id": self.valid_metagraph_id,
                        "name": "Test Metagraph",
                    }
                }
            )

            response = get_metagraph_overview("testnet", self.valid_metagraph_id)

            assert response.is_successful
            assert response.data["metagraph"]["id"] == self.valid_metagraph_id
            mock_execute.assert_called_once()

    def test_get_network_status_convenience(self):
        """Test get_network_status convenience function."""
        with patch("constellation_sdk.graphql.execute_query") as mock_execute:
            mock_execute.return_value = GraphQLResponse(
                data={"network": {"status": "active", "nodeCount": 10}}
            )

            response = get_network_status("testnet")

            assert response.is_successful
            assert response.data["network"]["status"] == "active"
            mock_execute.assert_called_once()


class TestConstellationSchema:
    """Test ConstellationSchema pre-built queries."""

    def test_account_portfolio_schema(self):
        """Test account portfolio schema."""
        schema = ConstellationSchema.ACCOUNT_PORTFOLIO

        assert "query AccountPortfolio" in schema
        assert "$address: String!" in schema
        assert "account(address: $address)" in schema
        assert "balance" in schema
        assert "transactions" in schema
        assert "metagraphBalances" in schema

    def test_metagraph_overview_schema(self):
        """Test metagraph overview schema."""
        schema = ConstellationSchema.METAGRAPH_OVERVIEW

        assert "query MetagraphOverview" in schema
        assert "$id: String!" in schema
        assert "metagraph(id: $id)" in schema
        assert "tokenSymbol" in schema
        assert "totalSupply" in schema
        assert "validators" in schema

    def test_network_status_schema(self):
        """Test network status schema."""
        schema = ConstellationSchema.NETWORK_STATUS

        assert "query NetworkStatus" in schema
        assert "network" in schema
        assert "status" in schema
        assert "latestBlock" in schema
        assert "metrics" in schema

    def test_transaction_subscription_schema(self):
        """Test transaction subscription schema."""
        schema = ConstellationSchema.TRANSACTION_SUBSCRIPTION

        assert "subscription TransactionUpdates" in schema
        assert "$addresses: [String!]" in schema
        assert "transactionUpdates" in schema
        assert "hash" in schema
        assert "amount" in schema

    def test_balance_subscription_schema(self):
        """Test balance subscription schema."""
        schema = ConstellationSchema.BALANCE_SUBSCRIPTION

        assert "subscription BalanceUpdates" in schema
        assert "$addresses: [String!]" in schema
        assert "balanceUpdates" in schema
        assert "oldBalance" in schema
        assert "newBalance" in schema


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.unit,
    pytest.mark.graphql,
]
