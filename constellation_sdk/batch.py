"""
Enhanced REST batch operations for Constellation Network SDK.

This module provides enhanced REST capabilities for executing multiple operations
in a single API call, improving performance and reducing network round trips.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class BatchOperationType(Enum):
    """Supported batch operation types."""

    GET_BALANCE = "get_balance"
    GET_ORDINAL = "get_ordinal"
    GET_TRANSACTIONS = "get_transactions"
    GET_RECENT_TRANSACTIONS = "get_recent_transactions"
    GET_NODE_INFO = "get_node_info"
    GET_CLUSTER_INFO = "get_cluster_info"
    SUBMIT_TRANSACTION = "submit_transaction"


@dataclass
class BatchOperation:
    """
    Represents a single operation in a batch request.

    Args:
        operation: Type of operation to perform
        params: Parameters for the operation
        id: Optional identifier for tracking this operation
    """

    operation: BatchOperationType
    params: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class BatchResult:
    """
    Result of a single batch operation.

    Args:
        operation: The original operation
        success: Whether the operation succeeded
        data: Operation result data (if successful)
        error: Error information (if failed)
        id: Operation identifier (if provided)
    """

    operation: BatchOperationType
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    id: Optional[str] = None


@dataclass
class BatchResponse:
    """
    Complete batch request response.

    Args:
        results: List of individual operation results
        summary: Summary statistics
        execution_time: Total execution time in seconds
    """

    results: List[BatchResult]
    summary: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None

    def get_result(self, operation_id: str) -> Optional[BatchResult]:
        """Get result by operation ID."""
        for result in self.results:
            if result.id == operation_id:
                return result
        return None

    def get_successful_results(self) -> List[BatchResult]:
        """Get only successful results."""
        return [r for r in self.results if r.success]

    def get_failed_results(self) -> List[BatchResult]:
        """Get only failed results."""
        return [r for r in self.results if not r.success]

    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if not self.results:
            return 0.0
        return (len(self.get_successful_results()) / len(self.results)) * 100


class BatchValidator:
    """Validates batch operations before execution."""

    @staticmethod
    def validate_operation(operation: BatchOperation) -> List[str]:
        """
        Validate a single batch operation.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate operation type
        if not isinstance(operation.operation, BatchOperationType):
            errors.append(f"Invalid operation type: {operation.operation}")
            return errors

        # Validate parameters based on operation type
        if operation.operation == BatchOperationType.GET_BALANCE:
            if "address" not in operation.params:
                errors.append("get_balance requires 'address' parameter")
            elif not isinstance(operation.params["address"], str):
                errors.append("'address' must be a string")

        elif operation.operation == BatchOperationType.GET_ORDINAL:
            if "address" not in operation.params:
                errors.append("get_ordinal requires 'address' parameter")
            elif not isinstance(operation.params["address"], str):
                errors.append("'address' must be a string")

        elif operation.operation == BatchOperationType.GET_TRANSACTIONS:
            if "address" not in operation.params:
                errors.append("get_transactions requires 'address' parameter")
            elif not isinstance(operation.params["address"], str):
                errors.append("'address' must be a string")

            # Validate optional parameters
            if "limit" in operation.params:
                limit = operation.params["limit"]
                if not isinstance(limit, int) or limit <= 0 or limit > 1000:
                    errors.append("'limit' must be an integer between 1 and 1000")

        elif operation.operation == BatchOperationType.GET_RECENT_TRANSACTIONS:
            if "limit" in operation.params:
                limit = operation.params["limit"]
                if not isinstance(limit, int) or limit <= 0 or limit > 1000:
                    errors.append("'limit' must be an integer between 1 and 1000")

        elif operation.operation == BatchOperationType.SUBMIT_TRANSACTION:
            if "transaction" not in operation.params:
                errors.append("submit_transaction requires 'transaction' parameter")
            elif not isinstance(operation.params["transaction"], dict):
                errors.append("'transaction' must be a dictionary")

        return errors

    @staticmethod
    def validate_batch(operations: List[BatchOperation]) -> List[str]:
        """
        Validate a batch of operations.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not operations:
            errors.append("Batch cannot be empty")
            return errors

        if len(operations) > 100:
            errors.append("Batch cannot exceed 100 operations")

        # Validate each operation
        for i, operation in enumerate(operations):
            operation_errors = BatchValidator.validate_operation(operation)
            for error in operation_errors:
                errors.append(f"Operation {i}: {error}")

        # Check for duplicate IDs
        ids = [op.id for op in operations if op.id is not None]
        if len(ids) != len(set(ids)):
            errors.append("Operation IDs must be unique")

        return errors


def create_batch_operation(
    operation: Union[str, BatchOperationType],
    params: Dict[str, Any],
    operation_id: Optional[str] = None,
) -> BatchOperation:
    """
    Create a batch operation with validation.

    Args:
        operation: Operation type (string or enum)
        params: Operation parameters
        operation_id: Optional operation identifier

    Returns:
        BatchOperation instance

    Raises:
        ValueError: If operation type is invalid
    """
    if isinstance(operation, str):
        try:
            operation = BatchOperationType(operation)
        except ValueError:
            raise ValueError(f"Invalid operation type: {operation}")

    return BatchOperation(operation=operation, params=params, id=operation_id)


# Convenience functions for common batch operations
def batch_get_balances(addresses: List[str]) -> List[BatchOperation]:
    """Create batch operations to get balances for multiple addresses."""
    return [
        create_batch_operation(
            BatchOperationType.GET_BALANCE,
            {"address": address},
            operation_id=f"balance_{i}",
        )
        for i, address in enumerate(addresses)
    ]


def batch_get_transactions(
    addresses: List[str], limit: int = 10
) -> List[BatchOperation]:
    """Create batch operations to get transactions for multiple addresses."""
    return [
        create_batch_operation(
            BatchOperationType.GET_TRANSACTIONS,
            {"address": address, "limit": limit},
            operation_id=f"transactions_{i}",
        )
        for i, address in enumerate(addresses)
    ]


def batch_get_ordinals(addresses: List[str]) -> List[BatchOperation]:
    """Create batch operations to get ordinals for multiple addresses."""
    return [
        create_batch_operation(
            BatchOperationType.GET_ORDINAL,
            {"address": address},
            operation_id=f"ordinal_{i}",
        )
        for i, address in enumerate(addresses)
    ]
