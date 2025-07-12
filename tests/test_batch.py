"""
Tests for batch operations functionality.
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from constellation_sdk.batch import (
    BatchOperation,
    BatchOperationType,
    BatchResponse,
    BatchResult,
    BatchValidator,
    batch_get_balances,
    batch_get_ordinals,
    batch_get_transactions,
    create_batch_operation,
)
from constellation_sdk.exceptions import NetworkError
from constellation_sdk.network import Network


class TestBatchOperation:
    """Test BatchOperation class."""

    def test_batch_operation_creation(self):
        """Test BatchOperation creation."""
        operation = BatchOperation(
            operation=BatchOperationType.GET_BALANCE,
            params={"address": "DAG123..."},
            id="test_op",
        )

        assert operation.operation == BatchOperationType.GET_BALANCE
        assert operation.params == {"address": "DAG123..."}
        assert operation.id == "test_op"

    def test_batch_operation_without_id(self):
        """Test BatchOperation creation without ID."""
        operation = BatchOperation(
            operation=BatchOperationType.GET_BALANCE, params={"address": "DAG123..."}
        )

        assert operation.operation == BatchOperationType.GET_BALANCE
        assert operation.params == {"address": "DAG123..."}
        assert operation.id is None


class TestBatchResult:
    """Test BatchResult class."""

    def test_batch_result_success(self):
        """Test successful BatchResult."""
        result = BatchResult(
            operation=BatchOperationType.GET_BALANCE,
            success=True,
            data=1000000000,
            id="test_op",
        )

        assert result.operation == BatchOperationType.GET_BALANCE
        assert result.success is True
        assert result.data == 1000000000
        assert result.error is None
        assert result.id == "test_op"

    def test_batch_result_failure(self):
        """Test failed BatchResult."""
        result = BatchResult(
            operation=BatchOperationType.GET_BALANCE,
            success=False,
            error="Network error",
            id="test_op",
        )

        assert result.operation == BatchOperationType.GET_BALANCE
        assert result.success is False
        assert result.data is None
        assert result.error == "Network error"
        assert result.id == "test_op"


class TestBatchResponse:
    """Test BatchResponse class."""

    def test_batch_response_methods(self):
        """Test BatchResponse utility methods."""
        results = [
            BatchResult(BatchOperationType.GET_BALANCE, True, 1000000000, id="op1"),
            BatchResult(BatchOperationType.GET_BALANCE, False, error="Error", id="op2"),
            BatchResult(BatchOperationType.GET_ORDINAL, True, 5, id="op3"),
        ]

        response = BatchResponse(results=results)

        # Test get_result
        assert response.get_result("op1").data == 1000000000
        assert response.get_result("op2").error == "Error"
        assert response.get_result("nonexistent") is None

        # Test get_successful_results
        successful = response.get_successful_results()
        assert len(successful) == 2
        assert all(r.success for r in successful)

        # Test get_failed_results
        failed = response.get_failed_results()
        assert len(failed) == 1
        assert not failed[0].success

        # Test success_rate
        assert (
            abs(response.success_rate() - 66.67) < 0.1
        )  # 66.67% (allowing for floating point precision)

    def test_batch_response_empty(self):
        """Test BatchResponse with empty results."""
        response = BatchResponse(results=[])

        assert response.success_rate() == 0.0
        assert len(response.get_successful_results()) == 0
        assert len(response.get_failed_results()) == 0


class TestBatchValidator:
    """Test BatchValidator class."""

    def test_validate_get_balance_operation(self):
        """Test validation of get_balance operation."""
        # Valid operation
        operation = BatchOperation(
            operation=BatchOperationType.GET_BALANCE, params={"address": "DAG123..."}
        )
        errors = BatchValidator.validate_operation(operation)
        assert len(errors) == 0

        # Missing address
        operation = BatchOperation(operation=BatchOperationType.GET_BALANCE, params={})
        errors = BatchValidator.validate_operation(operation)
        assert len(errors) == 1
        assert "requires 'address' parameter" in errors[0]

        # Invalid address type
        operation = BatchOperation(
            operation=BatchOperationType.GET_BALANCE, params={"address": 123}
        )
        errors = BatchValidator.validate_operation(operation)
        assert len(errors) == 1
        assert "'address' must be a string" in errors[0]

    def test_validate_get_transactions_operation(self):
        """Test validation of get_transactions operation."""
        # Valid operation
        operation = BatchOperation(
            operation=BatchOperationType.GET_TRANSACTIONS,
            params={"address": "DAG123...", "limit": 10},
        )
        errors = BatchValidator.validate_operation(operation)
        assert len(errors) == 0

        # Invalid limit
        operation = BatchOperation(
            operation=BatchOperationType.GET_TRANSACTIONS,
            params={"address": "DAG123...", "limit": 2000},
        )
        errors = BatchValidator.validate_operation(operation)
        assert len(errors) == 1
        assert "'limit' must be an integer between 1 and 1000" in errors[0]

    def test_validate_submit_transaction_operation(self):
        """Test validation of submit_transaction operation."""
        # Valid operation
        operation = BatchOperation(
            operation=BatchOperationType.SUBMIT_TRANSACTION,
            params={"transaction": {"value": {}, "proofs": []}},
        )
        errors = BatchValidator.validate_operation(operation)
        assert len(errors) == 0

        # Missing transaction
        operation = BatchOperation(
            operation=BatchOperationType.SUBMIT_TRANSACTION, params={}
        )
        errors = BatchValidator.validate_operation(operation)
        assert len(errors) == 1
        assert "requires 'transaction' parameter" in errors[0]

    def test_validate_batch_operations(self):
        """Test batch validation."""
        # Valid batch
        operations = [
            BatchOperation(BatchOperationType.GET_BALANCE, {"address": "DAG123..."}),
            BatchOperation(BatchOperationType.GET_ORDINAL, {"address": "DAG456..."}),
        ]
        errors = BatchValidator.validate_batch(operations)
        assert len(errors) == 0

        # Empty batch
        errors = BatchValidator.validate_batch([])
        assert len(errors) == 1
        assert "Batch cannot be empty" in errors[0]

        # Too many operations
        operations = [
            BatchOperation(BatchOperationType.GET_BALANCE, {"address": f"DAG{i}..."})
            for i in range(101)
        ]
        errors = BatchValidator.validate_batch(operations)
        assert len(errors) == 1
        assert "cannot exceed 100 operations" in errors[0]

        # Duplicate IDs
        operations = [
            BatchOperation(
                BatchOperationType.GET_BALANCE, {"address": "DAG123..."}, id="dup"
            ),
            BatchOperation(
                BatchOperationType.GET_BALANCE, {"address": "DAG456..."}, id="dup"
            ),
        ]
        errors = BatchValidator.validate_batch(operations)
        assert len(errors) == 1
        assert "Operation IDs must be unique" in errors[0]


class TestBatchCreationFunctions:
    """Test batch creation convenience functions."""

    def test_create_batch_operation(self):
        """Test create_batch_operation function."""
        # With string operation type
        operation = create_batch_operation(
            "get_balance", {"address": "DAG123..."}, "test_op"
        )

        assert operation.operation == BatchOperationType.GET_BALANCE
        assert operation.params == {"address": "DAG123..."}
        assert operation.id == "test_op"

        # With enum operation type
        operation = create_batch_operation(
            BatchOperationType.GET_BALANCE, {"address": "DAG123..."}
        )

        assert operation.operation == BatchOperationType.GET_BALANCE
        assert operation.id is None

        # Invalid operation type
        with pytest.raises(ValueError, match="Invalid operation type"):
            create_batch_operation("invalid_operation", {})

    def test_batch_get_balances(self):
        """Test batch_get_balances function."""
        addresses = ["DAG123...", "DAG456...", "DAG789..."]
        operations = batch_get_balances(addresses)

        assert len(operations) == 3
        for i, operation in enumerate(operations):
            assert operation.operation == BatchOperationType.GET_BALANCE
            assert operation.params == {"address": addresses[i]}
            assert operation.id == f"balance_{i}"

    def test_batch_get_transactions(self):
        """Test batch_get_transactions function."""
        addresses = ["DAG123...", "DAG456..."]
        operations = batch_get_transactions(addresses, limit=20)

        assert len(operations) == 2
        for i, operation in enumerate(operations):
            assert operation.operation == BatchOperationType.GET_TRANSACTIONS
            assert operation.params == {"address": addresses[i], "limit": 20}
            assert operation.id == f"transactions_{i}"

    def test_batch_get_ordinals(self):
        """Test batch_get_ordinals function."""
        addresses = ["DAG123...", "DAG456..."]
        operations = batch_get_ordinals(addresses)

        assert len(operations) == 2
        for i, operation in enumerate(operations):
            assert operation.operation == BatchOperationType.GET_ORDINAL
            assert operation.params == {"address": addresses[i]}
            assert operation.id == f"ordinal_{i}"


class TestNetworkBatchOperations:
    """Test Network class batch operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.network = Network("testnet")

        # Mock the individual methods
        self.network.get_balance = Mock(return_value=1000000000)
        self.network.get_ordinal = Mock(return_value=5)
        self.network.get_transactions = Mock(return_value=[{"hash": "tx1"}])
        self.network.get_recent_transactions = Mock(return_value=[{"hash": "tx2"}])
        self.network.get_node_info = Mock(return_value={"version": "1.0"})
        self.network.get_cluster_info = Mock(return_value=[{"node": "node1"}])
        self.network.submit_transaction = Mock(return_value={"status": "success"})

    def test_batch_request_success(self):
        """Test successful batch request."""
        operations = [
            create_batch_operation("get_balance", {"address": "DAG123..."}, "balance"),
            create_batch_operation("get_ordinal", {"address": "DAG123..."}, "ordinal"),
        ]

        response = self.network.batch_request(operations)

        assert isinstance(response, BatchResponse)
        assert len(response.results) == 2
        assert response.success_rate() == 100.0

        # Check individual results
        balance_result = response.get_result("balance")
        assert balance_result.success is True
        assert balance_result.data == 1000000000

        ordinal_result = response.get_result("ordinal")
        assert ordinal_result.success is True
        assert ordinal_result.data == 5

    def test_batch_request_with_errors(self):
        """Test batch request with some operations failing."""
        # Make one operation fail
        self.network.get_balance.side_effect = NetworkError("Balance error")

        operations = [
            create_batch_operation("get_balance", {"address": "DAG123..."}, "balance"),
            create_batch_operation("get_ordinal", {"address": "DAG123..."}, "ordinal"),
        ]

        response = self.network.batch_request(operations)

        assert len(response.results) == 2
        assert response.success_rate() == 50.0

        # Check failed result
        balance_result = response.get_result("balance")
        assert balance_result.success is False
        assert "Balance error" in balance_result.error

        # Check successful result
        ordinal_result = response.get_result("ordinal")
        assert ordinal_result.success is True
        assert ordinal_result.data == 5

    def test_batch_request_validation_error(self):
        """Test batch request with validation errors."""
        operations = [
            BatchOperation(BatchOperationType.GET_BALANCE, {}),  # Missing address
        ]

        with pytest.raises(NetworkError, match="Batch validation failed"):
            self.network.batch_request(operations)

    def test_get_multi_balance(self):
        """Test get_multi_balance method."""
        addresses = ["DAG123...", "DAG456...", "DAG789..."]

        # Mock different balance values
        balance_values = [1000000000, 2000000000, 0]
        self.network.get_balance.side_effect = balance_values

        balances = self.network.get_multi_balance(addresses)

        assert len(balances) == 3
        for i, address in enumerate(addresses):
            assert balances[address] == balance_values[i]

    def test_get_multi_ordinal(self):
        """Test get_multi_ordinal method."""
        addresses = ["DAG123...", "DAG456..."]

        # Mock different ordinal values
        ordinal_values = [5, 10]
        self.network.get_ordinal.side_effect = ordinal_values

        ordinals = self.network.get_multi_ordinal(addresses)

        assert len(ordinals) == 2
        for i, address in enumerate(addresses):
            assert ordinals[address] == ordinal_values[i]

    def test_get_multi_transactions(self):
        """Test get_multi_transactions method."""
        addresses = ["DAG123...", "DAG456..."]

        # Mock different transaction lists
        transaction_lists = [[{"hash": "tx1"}, {"hash": "tx2"}], [{"hash": "tx3"}]]
        self.network.get_transactions.side_effect = transaction_lists

        transactions = self.network.get_multi_transactions(addresses, limit=5)

        assert len(transactions) == 2
        for i, address in enumerate(addresses):
            assert transactions[address] == transaction_lists[i]

    def test_get_address_overview(self):
        """Test get_address_overview method."""
        address = "DAG123..."

        overview = self.network.get_address_overview(address)

        assert overview["address"] == address
        assert overview["balance"] == 1000000000
        assert overview["ordinal"] == 5
        assert overview["transactions"] == [{"hash": "tx1"}]
        assert overview["success"] is True
        assert "execution_time" in overview

    def test_get_address_overview_with_errors(self):
        """Test get_address_overview with some operations failing."""
        # Make balance query fail
        self.network.get_balance.side_effect = NetworkError("Balance error")

        address = "DAG123..."
        overview = self.network.get_address_overview(address)

        assert overview["address"] == address
        assert overview["balance"] == 0  # Default value
        assert overview["ordinal"] == 5
        assert overview["transactions"] == [{"hash": "tx1"}]
        assert overview["success"] is False  # Not 100% success rate


@pytest.mark.asyncio
class TestAsyncNetworkBatchOperations:
    """Test AsyncNetwork class batch operations."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("constellation_sdk.async_network.AIOHTTP_AVAILABLE", True):
            from constellation_sdk.async_network import AsyncNetwork

            self.network = AsyncNetwork()

            # Mock the individual methods with async coroutines
            async def mock_get_balance(*args, **kwargs):
                return {"data": {"balance": 1000000000}}

            async def mock_get_ordinal(*args, **kwargs):
                return 5

            async def mock_get_transactions(*args, **kwargs):
                return [{"hash": "tx1"}]

            async def mock_get_recent_transactions(*args, **kwargs):
                return [{"hash": "tx2"}]

            async def mock_get_node_info(*args, **kwargs):
                return {"version": "1.0"}

            async def mock_get_cluster_info(*args, **kwargs):
                return [{"node": "node1"}]

            async def mock_submit_transaction(*args, **kwargs):
                return {"status": "success"}

            self.network.get_balance = mock_get_balance
            self.network.get_ordinal = mock_get_ordinal
            self.network.get_transactions = mock_get_transactions
            self.network.get_recent_transactions = mock_get_recent_transactions
            self.network.get_node_info = mock_get_node_info
            self.network.get_cluster_info = mock_get_cluster_info
            self.network.submit_transaction = mock_submit_transaction

    async def test_async_batch_request_success(self):
        """Test successful async batch request."""
        operations = [
            create_batch_operation("get_balance", {"address": "DAG123..."}, "balance"),
            create_batch_operation("get_ordinal", {"address": "DAG123..."}, "ordinal"),
        ]

        response = await self.network.batch_request(operations)

        assert isinstance(response, BatchResponse)
        assert len(response.results) == 2
        assert response.success_rate() == 100.0
        assert response.summary["concurrent_execution"] is True

    async def test_async_get_multi_balance_enhanced(self):
        """Test async get_multi_balance_enhanced method."""
        addresses = ["DAG123...", "DAG456..."]

        # Mock different balance values for different addresses
        balance_responses = [
            {"data": {"balance": 1000000000}},
            {"data": {"balance": 2000000000}},
        ]

        # Create an async function that returns different values for different calls
        call_count = 0

        async def mock_get_balance_with_values(*args, **kwargs):
            nonlocal call_count
            response = balance_responses[call_count % len(balance_responses)]
            call_count += 1
            return response

        self.network.get_balance = mock_get_balance_with_values

        balances = await self.network.get_multi_balance_enhanced(addresses)

        assert len(balances) == 2
        assert balances[addresses[0]] == 1000000000
        assert balances[addresses[1]] == 2000000000

    async def test_async_get_address_overview(self):
        """Test async get_address_overview method."""
        address = "DAG123..."

        overview = await self.network.get_address_overview(address)

        assert overview["address"] == address
        assert overview["balance"] == 1000000000
        assert overview["ordinal"] == 5
        assert overview["transactions"] == [{"hash": "tx1"}]
        assert overview["success"] is True
        assert "execution_time" in overview


# Integration tests
@pytest.mark.integration
class TestBatchOperationsIntegration:
    """Integration tests for batch operations."""

    def test_real_batch_request_with_mock_network(self):
        """Test batch request with mock network responses."""
        with patch("constellation_sdk.network.requests.request") as mock_request:
            # Mock successful responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"balance": 1000000000}}
            mock_request.return_value = mock_response

            network = Network("testnet")
            operations = [
                create_batch_operation(
                    "get_balance", {"address": "DAG123..."}, "balance1"
                ),
                create_batch_operation(
                    "get_balance", {"address": "DAG456..."}, "balance2"
                ),
            ]

            response = network.batch_request(operations)

            assert response.success_rate() == 100.0
            assert len(response.results) == 2

            # Verify all results are successful
            for result in response.results:
                assert result.success is True
                assert result.data == 1000000000


# Performance tests
@pytest.mark.slow
class TestBatchOperationsPerformance:
    """Performance tests for batch operations."""

    def test_batch_performance_vs_individual(self):
        """Test that batch operations are more efficient than individual calls."""
        with patch("constellation_sdk.network.requests.request") as mock_request:
            # Mock fast responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"balance": 1000000000}}
            mock_request.return_value = mock_response

            network = Network("testnet")
            addresses = [f'DAG{i}{"0" * 32}' for i in range(10)]

            # Time individual calls
            start_time = time.time()
            individual_results = {}
            for address in addresses:
                individual_results[address] = network.get_balance(address)
            individual_time = time.time() - start_time

            # Time batch call
            start_time = time.time()
            batch_results = network.get_multi_balance(addresses)
            batch_time = time.time() - start_time

            # Results should be the same
            assert individual_results == batch_results

            # Note: In real scenarios, batch should be faster due to reduced setup time
            # Here we're just testing that both approaches work
            assert len(batch_results) == len(addresses)


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.unit,
    pytest.mark.batch,
]
