"""
GraphQL query builder for programmatic GraphQL construction.

This module provides a fluent API for building GraphQL queries programmatically,
making it easier to construct complex queries without string concatenation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class SortOrder(Enum):
    """Sort order for GraphQL queries."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass
class GraphQLField:
    """
    Represents a GraphQL field with optional arguments and sub-fields.

    Args:
        name: Field name
        arguments: Field arguments
        fields: Sub-fields for nested queries
        alias: Field alias
    """

    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    fields: List["GraphQLField"] = field(default_factory=list)
    alias: Optional[str] = None

    def to_string(self, indent: int = 0) -> str:
        """Convert field to GraphQL string representation."""
        spaces = "  " * indent

        # Build field name with alias
        field_str = (
            f"{spaces}{self.alias}: {self.name}"
            if self.alias
            else f"{spaces}{self.name}"
        )

        # Add arguments
        if self.arguments:
            args = []
            for key, value in self.arguments.items():
                if isinstance(value, str):
                    args.append(f'{key}: "{value}"')
                elif isinstance(value, list):
                    formatted_list = (
                        "["
                        + ", ".join(
                            f'"{item}"' if isinstance(item, str) else str(item)
                            for item in value
                        )
                        + "]"
                    )
                    args.append(f"{key}: {formatted_list}")
                else:
                    args.append(f"{key}: {value}")
            field_str += f"({', '.join(args)})"

        # Add sub-fields
        if self.fields:
            field_str += " {\n"
            for field in self.fields:
                field_str += field.to_string(indent + 1) + "\n"
            field_str += f"{spaces}}}"

        return field_str


class QueryBuilder:
    """
    Fluent API for building GraphQL queries programmatically.

    Example:
        builder = QueryBuilder()
        query = (builder
                .account("DAG123...")
                .with_balance()
                .with_transactions(limit=10)
                .build())
    """

    def __init__(self):
        self.fields: List[GraphQLField] = []
        self.variables: Dict[str, Any] = {}
        self.operation_name: Optional[str] = None

    def account(self, address: str) -> "AccountQueryBuilder":
        """
        Start building an account query.

        Args:
            address: Account address to query

        Returns:
            AccountQueryBuilder for fluent API
        """
        return AccountQueryBuilder(self, address)

    def metagraph(self, metagraph_id: str) -> "MetagraphQueryBuilder":
        """
        Start building a metagraph query.

        Args:
            metagraph_id: Metagraph ID to query

        Returns:
            MetagraphQueryBuilder for fluent API
        """
        return MetagraphQueryBuilder(self, metagraph_id)

    def network(self) -> "NetworkQueryBuilder":
        """
        Start building a network query.

        Returns:
            NetworkQueryBuilder for fluent API
        """
        return NetworkQueryBuilder(self)

    def accounts(self, addresses: List[str]) -> "AccountsQueryBuilder":
        """
        Start building a multi-account query.

        Args:
            addresses: List of account addresses

        Returns:
            AccountsQueryBuilder for fluent API
        """
        return AccountsQueryBuilder(self, addresses)

    def metagraphs(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> "MetagraphsQueryBuilder":
        """
        Start building a metagraphs query.

        Args:
            filters: Optional filters for metagraphs

        Returns:
            MetagraphsQueryBuilder for fluent API
        """
        return MetagraphsQueryBuilder(self, filters or {})

    def set_operation_name(self, name: str) -> "QueryBuilder":
        """Set operation name for the query."""
        self.operation_name = name
        return self

    def add_variable(self, name: str, value: Any) -> "QueryBuilder":
        """Add a variable to the query."""
        self.variables[name] = value
        return self

    def build(self) -> str:
        """
        Build the final GraphQL query string.

        Returns:
            GraphQL query string
        """
        if not self.fields:
            raise ValueError("No fields added to query")

        # Build query header
        query_parts = ["query"]

        if self.operation_name:
            query_parts.append(self.operation_name)

        # Add variables if any
        if self.variables:
            var_parts = []
            for name, value in self.variables.items():
                var_type = self._infer_graphql_type(value)
                var_parts.append(f"${name}: {var_type}")
            query_parts.append(f"({', '.join(var_parts)})")

        # Build query body
        query_body = " {\n"
        for field in self.fields:
            query_body += field.to_string(1) + "\n"
        query_body += "}"

        return " ".join(query_parts) + query_body

    def _infer_graphql_type(self, value: Any) -> str:
        """Infer GraphQL type from Python value."""
        if isinstance(value, str):
            return "String"
        elif isinstance(value, int):
            return "Int"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, list):
            if value and isinstance(value[0], str):
                return "[String]"
            return "[String]"  # Default to string array
        else:
            return "String"  # Default fallback


class AccountQueryBuilder:
    """Builder for account-specific queries."""

    def __init__(self, parent: QueryBuilder, address: str):
        self.parent = parent
        self.address = address
        self.account_field = GraphQLField("account", {"address": address})
        self.parent.fields.append(self.account_field)

    def with_balance(self) -> "AccountQueryBuilder":
        """Include balance in the query."""
        self.account_field.fields.append(GraphQLField("balance"))
        return self

    def with_address(self) -> "AccountQueryBuilder":
        """Include address in the query."""
        self.account_field.fields.append(GraphQLField("address"))
        return self

    def with_transactions(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> "AccountQueryBuilder":
        """
        Include transactions in the query.

        Args:
            limit: Maximum number of transactions
            offset: Offset for pagination
        """
        args = {}
        if limit is not None:
            args["first"] = limit
        if offset is not None:
            args["offset"] = offset

        tx_field = GraphQLField("transactions", args)
        tx_field.fields.extend(
            [
                GraphQLField("hash"),
                GraphQLField("amount"),
                GraphQLField("timestamp"),
                GraphQLField("destination"),
                GraphQLField("source"),
                GraphQLField("type"),
            ]
        )

        self.account_field.fields.append(tx_field)
        return self

    def with_metagraph_balances(self) -> "AccountQueryBuilder":
        """Include metagraph balances in the query."""
        mg_field = GraphQLField("metagraphBalances")
        mg_field.fields.extend(
            [
                GraphQLField("metagraphId"),
                GraphQLField("balance"),
                GraphQLField("tokenSymbol"),
                GraphQLField("tokenName"),
            ]
        )

        self.account_field.fields.append(mg_field)
        return self

    def build(self) -> str:
        """Build the GraphQL query string."""
        return self.parent.build()


class AccountsQueryBuilder:
    """Builder for multi-account queries."""

    def __init__(self, parent: QueryBuilder, addresses: List[str]):
        self.parent = parent
        self.addresses = addresses
        self.accounts_field = GraphQLField("accounts", {"addresses": addresses})
        self.parent.fields.append(self.accounts_field)

    def with_balances(self) -> "AccountsQueryBuilder":
        """Include balances for all accounts."""
        self.accounts_field.fields.extend(
            [GraphQLField("address"), GraphQLField("balance")]
        )
        return self

    def with_transactions(self, limit: Optional[int] = None) -> "AccountsQueryBuilder":
        """Include transactions for all accounts."""
        args = {}
        if limit is not None:
            args["first"] = limit

        tx_field = GraphQLField("transactions", args)
        tx_field.fields.extend(
            [
                GraphQLField("hash"),
                GraphQLField("amount"),
                GraphQLField("timestamp"),
                GraphQLField("destination"),
            ]
        )

        self.accounts_field.fields.append(tx_field)
        return self

    def build(self) -> str:
        """Build the GraphQL query string."""
        return self.parent.build()


class MetagraphQueryBuilder:
    """Builder for metagraph-specific queries."""

    def __init__(self, parent: QueryBuilder, metagraph_id: str):
        self.parent = parent
        self.metagraph_id = metagraph_id
        self.metagraph_field = GraphQLField("metagraph", {"id": metagraph_id})
        self.parent.fields.append(self.metagraph_field)

    def with_info(self) -> "MetagraphQueryBuilder":
        """Include basic metagraph information."""
        self.metagraph_field.fields.extend(
            [
                GraphQLField("id"),
                GraphQLField("name"),
                GraphQLField("tokenSymbol"),
                GraphQLField("tokenName"),
                GraphQLField("status"),
            ]
        )
        return self

    def with_supply_info(self) -> "MetagraphQueryBuilder":
        """Include token supply information."""
        self.metagraph_field.fields.extend(
            [
                GraphQLField("totalSupply"),
                GraphQLField("circulatingSupply"),
                GraphQLField("maxSupply"),
            ]
        )
        return self

    def with_holders(self, limit: Optional[int] = None) -> "MetagraphQueryBuilder":
        """Include token holders information."""
        args = {}
        if limit is not None:
            args["first"] = limit

        holders_field = GraphQLField("holders", args)
        holders_field.fields.extend(
            [
                GraphQLField("address"),
                GraphQLField("balance"),
                GraphQLField("percentage"),
            ]
        )

        self.metagraph_field.fields.append(holders_field)
        return self

    def with_transactions(self, limit: Optional[int] = None) -> "MetagraphQueryBuilder":
        """Include metagraph transactions."""
        args = {}
        if limit is not None:
            args["first"] = limit

        tx_field = GraphQLField("transactions", args)
        tx_field.fields.extend(
            [
                GraphQLField("hash"),
                GraphQLField("amount"),
                GraphQLField("timestamp"),
                GraphQLField("type"),
                GraphQLField("source"),
                GraphQLField("destination"),
            ]
        )

        self.metagraph_field.fields.append(tx_field)
        return self

    def with_validators(self) -> "MetagraphQueryBuilder":
        """Include validator information."""
        validators_field = GraphQLField("validators")
        validators_field.fields.extend(
            [GraphQLField("address"), GraphQLField("stake"), GraphQLField("status")]
        )

        self.metagraph_field.fields.append(validators_field)
        return self

    def build(self) -> str:
        """Build the GraphQL query string."""
        return self.parent.build()


class MetagraphsQueryBuilder:
    """Builder for multi-metagraph queries."""

    def __init__(self, parent: QueryBuilder, filters: Dict[str, Any]):
        self.parent = parent
        self.filters = filters
        self.metagraphs_field = GraphQLField("metagraphs", filters)
        self.parent.fields.append(self.metagraphs_field)

    def with_basic_info(self) -> "MetagraphsQueryBuilder":
        """Include basic information for all metagraphs."""
        self.metagraphs_field.fields.extend(
            [
                GraphQLField("id"),
                GraphQLField("name"),
                GraphQLField("tokenSymbol"),
                GraphQLField("status"),
            ]
        )
        return self

    def with_metrics(self) -> "MetagraphsQueryBuilder":
        """Include metrics for all metagraphs."""
        self.metagraphs_field.fields.extend(
            [
                GraphQLField("holderCount"),
                GraphQLField("transactionCount"),
                GraphQLField("totalSupply"),
            ]
        )
        return self

    def production_only(self) -> "MetagraphsQueryBuilder":
        """Filter to production metagraphs only."""
        self.metagraphs_field.arguments["production"] = True
        return self

    def build(self) -> str:
        """Build the GraphQL query string."""
        return self.parent.build()


class NetworkQueryBuilder:
    """Builder for network-specific queries."""

    def __init__(self, parent: QueryBuilder):
        self.parent = parent
        self.network_field = GraphQLField("network")
        self.parent.fields.append(self.network_field)

    def with_status(self) -> "NetworkQueryBuilder":
        """Include network status."""
        self.network_field.fields.extend(
            [GraphQLField("status"), GraphQLField("version"), GraphQLField("nodeCount")]
        )
        return self

    def with_latest_block(self) -> "NetworkQueryBuilder":
        """Include latest block information."""
        block_field = GraphQLField("latestBlock")
        block_field.fields.extend(
            [GraphQLField("hash"), GraphQLField("height"), GraphQLField("timestamp")]
        )

        self.network_field.fields.append(block_field)
        return self

    def with_metrics(self) -> "NetworkQueryBuilder":
        """Include network metrics."""
        metrics_field = GraphQLField("metrics")
        metrics_field.fields.extend(
            [
                GraphQLField("transactionRate"),
                GraphQLField("totalTransactions"),
                GraphQLField("activeAddresses"),
                GraphQLField("networkHashRate"),
            ]
        )

        self.network_field.fields.append(metrics_field)
        return self

    def build(self) -> str:
        """Build the GraphQL query string."""
        return self.parent.build()


class SubscriptionBuilder:
    """Builder for GraphQL subscriptions."""

    def __init__(self):
        self.fields: List[GraphQLField] = []
        self.variables: Dict[str, Any] = {}
        self.operation_name: Optional[str] = None

    def transaction_updates(
        self, addresses: Optional[List[str]] = None
    ) -> "SubscriptionBuilder":
        """Subscribe to transaction updates."""
        args = {}
        if addresses:
            args["addresses"] = addresses

        tx_field = GraphQLField("transactionUpdates", args)
        tx_field.fields.extend(
            [
                GraphQLField("hash"),
                GraphQLField("amount"),
                GraphQLField("source"),
                GraphQLField("destination"),
                GraphQLField("timestamp"),
                GraphQLField("type"),
            ]
        )

        self.fields.append(tx_field)
        return self

    def balance_updates(self, addresses: List[str]) -> "SubscriptionBuilder":
        """Subscribe to balance updates."""
        balance_field = GraphQLField("balanceUpdates", {"addresses": addresses})
        balance_field.fields.extend(
            [
                GraphQLField("address"),
                GraphQLField("oldBalance"),
                GraphQLField("newBalance"),
                GraphQLField("change"),
                GraphQLField("timestamp"),
            ]
        )

        self.fields.append(balance_field)
        return self

    def metagraph_updates(self, metagraph_ids: List[str]) -> "SubscriptionBuilder":
        """Subscribe to metagraph updates."""
        mg_field = GraphQLField("metagraphUpdates", {"metagraphIds": metagraph_ids})
        mg_field.fields.extend(
            [
                GraphQLField("metagraphId"),
                GraphQLField("updateType"),
                GraphQLField("data"),
                GraphQLField("timestamp"),
            ]
        )

        self.fields.append(mg_field)
        return self

    def build(self) -> str:
        """Build the GraphQL subscription string."""
        if not self.fields:
            raise ValueError("No fields added to subscription")

        # Build subscription header
        subscription_parts = ["subscription"]

        if self.operation_name:
            subscription_parts.append(self.operation_name)

        # Add variables if any
        if self.variables:
            var_parts = []
            for name, value in self.variables.items():
                var_type = self._infer_graphql_type(value)
                var_parts.append(f"${name}: {var_type}")
            subscription_parts.append(f"({', '.join(var_parts)})")

        # Build subscription body
        subscription_body = " {\n"
        for field in self.fields:
            subscription_body += field.to_string(1) + "\n"
        subscription_body += "}"

        return " ".join(subscription_parts) + subscription_body

    def _infer_graphql_type(self, value: Any) -> str:
        """Infer GraphQL type from Python value."""
        if isinstance(value, str):
            return "String"
        elif isinstance(value, int):
            return "Int"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, list):
            if value and isinstance(value[0], str):
                return "[String]"
            return "[String]"  # Default to string array
        else:
            return "String"  # Default fallback


# Convenience functions for quick query building
def build_account_query(
    address: str, include_transactions: bool = True, include_balances: bool = True
) -> str:
    """
    Build a comprehensive account query.

    Args:
        address: Account address
        include_transactions: Whether to include transactions
        include_balances: Whether to include metagraph balances

    Returns:
        GraphQL query string
    """
    builder = QueryBuilder().account(address).with_balance().with_address()

    if include_transactions:
        builder = builder.with_transactions(limit=20)

    if include_balances:
        builder = builder.with_metagraph_balances()

    return builder.build()


def build_metagraph_query(
    metagraph_id: str, include_holders: bool = True, include_transactions: bool = True
) -> str:
    """
    Build a comprehensive metagraph query.

    Args:
        metagraph_id: Metagraph ID
        include_holders: Whether to include holders
        include_transactions: Whether to include transactions

    Returns:
        GraphQL query string
    """
    builder = QueryBuilder().metagraph(metagraph_id).with_info().with_supply_info()

    if include_holders:
        builder = builder.with_holders(limit=100)

    if include_transactions:
        builder = builder.with_transactions(limit=50)

    return builder.build()


def build_network_status_query() -> str:
    """
    Build a comprehensive network status query.

    Returns:
        GraphQL query string
    """
    return (
        QueryBuilder()
        .network()
        .with_status()
        .with_latest_block()
        .with_metrics()
        .build()
    )


def build_portfolio_query(addresses: List[str]) -> str:
    """
    Build a portfolio query for multiple addresses.

    Args:
        addresses: List of addresses

    Returns:
        GraphQL query string
    """
    return (
        QueryBuilder()
        .accounts(addresses)
        .with_balances()
        .with_transactions(limit=10)
        .build()
    )


def build_transaction_subscription(addresses: List[str]) -> str:
    """
    Build a transaction subscription for specific addresses.

    Args:
        addresses: List of addresses to monitor

    Returns:
        GraphQL subscription string
    """
    return SubscriptionBuilder().transaction_updates(addresses).build()


def build_balance_subscription(addresses: List[str]) -> str:
    """
    Build a balance subscription for specific addresses.

    Args:
        addresses: List of addresses to monitor

    Returns:
        GraphQL subscription string
    """
    return SubscriptionBuilder().balance_updates(addresses).build()
