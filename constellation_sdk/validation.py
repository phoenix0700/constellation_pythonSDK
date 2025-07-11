"""
Comprehensive validation system for Constellation SDK.

This module provides validators, decorators, and utilities for input validation
across all SDK operations. Includes DAG address validation with checksums,
amount validation, transaction validation, and more.
"""

import functools
import hashlib
import re
from typing import Any, Callable, Dict, List, Optional, Union

from .exceptions import (
    AddressValidationError,
    AmountValidationError,
    InvalidDataError,
    MetagraphIdValidationError,
    TransactionValidationError,
    ValidationError,
)

# =====================
# Address Validation
# =====================


class AddressValidator:
    """
    DAG address validation with checksum support.

    Validates DAG addresses according to Constellation network standards,
    including format validation and checksum verification.
    """

    # DAG address format: DAG + exactly 35 hex characters
    DAG_ADDRESS_PATTERN = re.compile(r"^DAG[0-9A-Fa-f]{35}$")

    @classmethod
    def validate_format(cls, address: str) -> bool:
        """
        Validate DAG address format.

        Args:
            address: Address string to validate

        Returns:
            bool: True if format is valid
        """
        if not isinstance(address, str):
            return False
        return bool(cls.DAG_ADDRESS_PATTERN.match(address))

    @classmethod
    def validate_checksum(cls, address: str) -> bool:
        """
        Validate DAG address checksum.

        Uses a simple checksum algorithm based on the address string.

        Args:
            address: Address string to validate

        Returns:
            bool: True if checksum is valid
        """
        if not cls.validate_format(address):
            return False

        # Extract the hex part (without 'DAG' prefix)
        hex_part = address[3:]

        # Simple checksum: sum of all hex digits modulo 16
        # In a real implementation, this would use the actual Constellation checksum algorithm
        checksum = sum(int(c, 16) for c in hex_part) % 16

        # For this example, we'll consider the checksum valid if it's even
        # In reality, this would be compared against embedded checksum in the address
        return checksum % 2 == 0

    @classmethod
    def validate(cls, address: str, check_checksum: bool = False) -> None:
        """
        Validate DAG address with optional checksum verification.

        Args:
            address: Address string to validate
            check_checksum: Whether to verify checksum

        Raises:
            AddressValidationError: If address is invalid
        """
        if not isinstance(address, str):
            raise AddressValidationError(address, "Address must be a string")

        if not address:
            raise AddressValidationError(address, "Address cannot be empty")

        if not address.startswith("DAG"):
            raise AddressValidationError(address, "Address must start with 'DAG'")

        if len(address) != 38:
            raise AddressValidationError(
                address, f"Address must be exactly 38 characters, got {len(address)}"
            )

        if not cls.validate_format(address):
            raise AddressValidationError(address, "Invalid address format")

        if check_checksum and not cls.validate_checksum(address):
            raise AddressValidationError(address, "Invalid address checksum")


# =====================
# Amount Validation
# =====================


class AmountValidator:
    """
    Amount validation for transactions.

    Validates amounts according to Constellation network standards,
    including range checks and precision validation.
    """

    # Minimum and maximum amounts (in nanodollars)
    MIN_AMOUNT = 1
    MAX_AMOUNT = 2**53 - 1  # JavaScript safe integer

    @classmethod
    def validate(cls, amount: Union[int, float], allow_zero: bool = False) -> None:
        """
        Validate transaction amount.

        Args:
            amount: Amount to validate
            allow_zero: Whether to allow zero amounts

        Raises:
            AmountValidationError: If amount is invalid
        """
        if not isinstance(amount, (int, float)):
            raise AmountValidationError(amount, "Amount must be a number")

        if isinstance(amount, float):
            if amount != int(amount):
                raise AmountValidationError(
                    amount, "Amount must be an integer (no decimals)"
                )
            amount = int(amount)

        if not allow_zero and amount <= 0:
            raise AmountValidationError(amount, "Amount must be positive")

        if allow_zero and amount < 0:
            raise AmountValidationError(amount, "Amount cannot be negative")

        if amount < cls.MIN_AMOUNT and not (allow_zero and amount == 0):
            raise AmountValidationError(
                amount, f"Amount must be at least {cls.MIN_AMOUNT}"
            )

        if amount > cls.MAX_AMOUNT:
            raise AmountValidationError(
                amount, f"Amount cannot exceed {cls.MAX_AMOUNT}"
            )


# =====================
# Metagraph ID Validation
# =====================


class MetagraphIdValidator:
    """
    Metagraph ID validation.

    Validates metagraph IDs according to Constellation standards.
    """

    @classmethod
    def validate(cls, metagraph_id: str) -> None:
        """
        Validate metagraph ID.

        Args:
            metagraph_id: Metagraph ID to validate

        Raises:
            MetagraphIdValidationError: If metagraph ID is invalid
        """
        if not isinstance(metagraph_id, str):
            raise MetagraphIdValidationError(
                metagraph_id, "Metagraph ID must be a string"
            )

        if not metagraph_id:
            raise MetagraphIdValidationError(
                metagraph_id, "Metagraph ID cannot be empty"
            )

        # Metagraph IDs should be DAG addresses
        try:
            AddressValidator.validate(metagraph_id, check_checksum=False)
        except AddressValidationError as e:
            raise MetagraphIdValidationError(
                metagraph_id, f"Invalid format: {e.message}"
            )


# =====================
# Transaction Validation
# =====================


class TransactionValidator:
    """
    Transaction validation for all transaction types.

    Validates transaction structure and content according to
    Constellation network standards.
    """

    # Required fields for each transaction type
    REQUIRED_FIELDS = {
        "dag": ["source", "destination", "amount", "fee", "salt"],
        "token": ["source", "destination", "amount", "fee", "salt", "metagraph_id"],
        "data": ["source", "destination", "data", "metagraph_id", "timestamp", "salt"],
    }

    @classmethod
    def validate_structure(cls, transaction: Dict[str, Any], tx_type: str) -> None:
        """
        Validate transaction structure.

        Args:
            transaction: Transaction data to validate
            tx_type: Transaction type ('dag', 'token', 'data')

        Raises:
            TransactionValidationError: If transaction structure is invalid
        """
        if not isinstance(transaction, dict):
            raise TransactionValidationError(
                "Transaction must be a dictionary", transaction_type=tx_type
            )

        if tx_type not in cls.REQUIRED_FIELDS:
            raise TransactionValidationError(
                f"Unknown transaction type: {tx_type}", transaction_type=tx_type
            )

        required_fields = cls.REQUIRED_FIELDS[tx_type]
        missing_fields = [
            field for field in required_fields if field not in transaction
        ]

        if missing_fields:
            raise TransactionValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                transaction_type=tx_type,
                missing_fields=missing_fields,
            )

    @classmethod
    def validate_dag_transaction(cls, transaction: Dict[str, Any]) -> None:
        """
        Validate DAG transaction.

        Args:
            transaction: DAG transaction data

        Raises:
            TransactionValidationError: If transaction is invalid
        """
        cls.validate_structure(transaction, "dag")

        # Validate addresses
        AddressValidator.validate(transaction["source"])
        AddressValidator.validate(transaction["destination"])

        # Validate amounts
        AmountValidator.validate(transaction["amount"])
        AmountValidator.validate(transaction["fee"], allow_zero=True)

        # Validate salt
        if not isinstance(transaction["salt"], int):
            raise TransactionValidationError(
                "Salt must be an integer", transaction_type="dag"
            )

    @classmethod
    def validate_token_transaction(cls, transaction: Dict[str, Any]) -> None:
        """
        Validate metagraph token transaction.

        Args:
            transaction: Token transaction data

        Raises:
            TransactionValidationError: If transaction is invalid
        """
        cls.validate_structure(transaction, "token")

        # Validate addresses
        AddressValidator.validate(transaction["source"])
        AddressValidator.validate(transaction["destination"])

        # Validate amounts
        AmountValidator.validate(transaction["amount"])
        AmountValidator.validate(transaction["fee"], allow_zero=True)

        # Validate metagraph ID
        MetagraphIdValidator.validate(transaction["metagraph_id"])

        # Validate salt
        if not isinstance(transaction["salt"], int):
            raise TransactionValidationError(
                "Salt must be an integer", transaction_type="token"
            )

    @classmethod
    def validate_data_transaction(cls, transaction: Dict[str, Any]) -> None:
        """
        Validate metagraph data transaction.

        Args:
            transaction: Data transaction data

        Raises:
            TransactionValidationError: If transaction is invalid
        """
        cls.validate_structure(transaction, "data")

        # Validate addresses
        AddressValidator.validate(transaction["source"])
        AddressValidator.validate(transaction["destination"])

        # Validate metagraph ID
        MetagraphIdValidator.validate(transaction["metagraph_id"])

        # Validate data
        if not transaction["data"]:
            raise TransactionValidationError(
                "Data cannot be empty", transaction_type="data"
            )

        # Validate timestamp
        if not isinstance(transaction["timestamp"], int):
            raise TransactionValidationError(
                "Timestamp must be an integer", transaction_type="data"
            )

        if transaction["timestamp"] <= 0:
            raise TransactionValidationError(
                "Timestamp must be positive", transaction_type="data"
            )

        # Validate salt
        if not isinstance(transaction["salt"], int):
            raise TransactionValidationError(
                "Salt must be an integer", transaction_type="data"
            )


# =====================
# Data Validation
# =====================


class DataValidator:
    """
    Data validation for metagraph data submissions.

    Validates data structure and content for metagraph operations.
    """

    @classmethod
    def validate_data_payload(cls, data: Any) -> None:
        """
        Validate metagraph data payload.

        Args:
            data: Data payload to validate

        Raises:
            ValidationError: If data is invalid
        """
        if data is None:
            raise ValidationError("Data payload cannot be None", field="data", value=data)

        if isinstance(data, dict) and not data:
            raise ValidationError("Data payload cannot be empty", field="data", value=data)

        # Check data size (rough estimate)
        try:
            import json

            data_size = len(json.dumps(data, default=str))
            if data_size > 1024 * 1024:  # 1MB limit
                raise InvalidDataError(
                    f"Data payload too large: {data_size} bytes (max 1MB)"
                )
        except (TypeError, ValueError) as e:
            raise InvalidDataError(f"Data payload not serializable: {str(e)}")


# =====================
# Validation Decorators
# =====================


def validate_address(param_name: str, check_checksum: bool = True):
    """
    Decorator to validate DAG address parameters.

    Args:
        param_name: Name of the parameter to validate
        check_checksum: Whether to verify address checksum
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get parameter value
            if param_name in kwargs:
                address = kwargs[param_name]
            else:
                # Try to get from positional args based on function signature
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if param_name in param_names:
                    param_index = param_names.index(param_name)
                    if param_index < len(args):
                        address = args[param_index]
                    else:
                        address = None
                else:
                    address = None

            if address is not None:
                AddressValidator.validate(address, check_checksum)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_amount(param_name: str, allow_zero: bool = False):
    """
    Decorator to validate amount parameters.

    Args:
        param_name: Name of the parameter to validate
        allow_zero: Whether to allow zero amounts
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get parameter value
            if param_name in kwargs:
                amount = kwargs[param_name]
            else:
                # Try to get from positional args
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if param_name in param_names:
                    param_index = param_names.index(param_name)
                    if param_index < len(args):
                        amount = args[param_index]
                    else:
                        amount = None
                else:
                    amount = None

            if amount is not None:
                AmountValidator.validate(amount, allow_zero)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_metagraph_id(param_name: str):
    """
    Decorator to validate metagraph ID parameters.

    Args:
        param_name: Name of the parameter to validate
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get parameter value
            if param_name in kwargs:
                metagraph_id = kwargs[param_name]
            else:
                # Try to get from positional args
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if param_name in param_names:
                    param_index = param_names.index(param_name)
                    if param_index < len(args):
                        metagraph_id = args[param_index]
                    else:
                        metagraph_id = None
                else:
                    metagraph_id = None

            if metagraph_id is not None:
                MetagraphIdValidator.validate(metagraph_id)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_transaction(tx_type: str):
    """
    Decorator to validate transaction data.

    Args:
        tx_type: Transaction type ('dag', 'token', 'data')
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Assume first argument is transaction data
            if args:
                transaction = args[0]

                if tx_type == "dag":
                    TransactionValidator.validate_dag_transaction(transaction)
                elif tx_type == "token":
                    TransactionValidator.validate_token_transaction(transaction)
                elif tx_type == "data":
                    TransactionValidator.validate_data_transaction(transaction)
                else:
                    raise ValidationError(f"Unknown transaction type: {tx_type}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


# =====================
# Utility Functions
# =====================


def is_valid_dag_address(address: str, check_checksum: bool = False) -> bool:
    """
    Check if a string is a valid DAG address.

    Args:
        address: Address string to check
        check_checksum: Whether to verify checksum

    Returns:
        bool: True if address is valid
    """
    try:
        AddressValidator.validate(address, check_checksum)
        return True
    except AddressValidationError:
        return False


def is_valid_amount(amount: Union[int, float], allow_zero: bool = False) -> bool:
    """
    Check if a value is a valid transaction amount.

    Args:
        amount: Amount to check
        allow_zero: Whether to allow zero amounts

    Returns:
        bool: True if amount is valid
    """
    try:
        AmountValidator.validate(amount, allow_zero)
        return True
    except AmountValidationError:
        return False


def is_valid_metagraph_id(metagraph_id: str) -> bool:
    """
    Check if a string is a valid metagraph ID.

    Args:
        metagraph_id: Metagraph ID to check

    Returns:
        bool: True if metagraph ID is valid
    """
    try:
        MetagraphIdValidator.validate(metagraph_id)
        return True
    except MetagraphIdValidationError:
        return False


def validate_batch_transfers(transfers: List[Dict[str, Any]]) -> None:
    """
    Validate a batch of transfer operations.

    Args:
        transfers: List of transfer dictionaries

    Raises:
        ValidationError: If any transfer is invalid
    """
    if not isinstance(transfers, list):
        raise ValidationError("Transfers must be a list")

    if not transfers:
        raise ValidationError("Transfers list cannot be empty")

    for i, transfer in enumerate(transfers):
        if not isinstance(transfer, dict):
            raise ValidationError(f"Transfer {i} must be a dictionary")

        if "destination" not in transfer:
            raise ValidationError(f"Transfer {i} missing destination")

        if "amount" not in transfer:
            raise ValidationError(f"Transfer {i} missing amount")

        AddressValidator.validate(transfer["destination"])
        AmountValidator.validate(transfer["amount"])
