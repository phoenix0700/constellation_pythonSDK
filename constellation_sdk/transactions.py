"""
Centralized transaction creation for Constellation Network.

This module provides a unified interface for creating all types of transactions:
- DAG transactions (core network token transfers)
- Metagraph token transactions (custom token transfers)
- Metagraph data transactions (data submissions)

All transactions are validated using the comprehensive validation system
and use structured error handling for better debugging and user experience.
"""

import secrets
import json
import time
from typing import Dict, Any, Union, Optional, List
from .account import Account
from .validation import (
    AddressValidator, AmountValidator, MetagraphIdValidator,
    TransactionValidator, DataValidator, validate_batch_transfers
)
from .exceptions import (
    ValidationError, TransactionValidationError, InvalidDataError
)


class Transactions:
    """
    Centralized transaction creation for all Constellation Network transaction types.
    
    Provides a consistent API for creating DAG and metagraph transactions.
    Account class handles signing, this class handles creation.
    """
    
    @staticmethod
    def create_dag_transfer(
        source: str,
        destination: str,
        amount: Union[int, float],
        fee: Union[int, float] = 0,
        salt: Optional[int] = None,
        parent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a DAG token transfer transaction.
        
        Args:
            source: Source DAG address
            destination: Recipient DAG address
            amount: Amount to transfer (in nanograms: 1 DAG = 100,000,000 nanograms)
            fee: Transaction fee (usually 0 for Constellation)
            salt: Salt for transaction uniqueness (auto-generated if None)
            parent: Parent transaction reference (None for genesis transactions)
            
        Returns:
            Unsigned transaction ready for signing
            
        Raises:
            AddressValidationError: If addresses are invalid
            AmountValidationError: If amounts are invalid
            TransactionValidationError: If transaction structure is invalid
            
        Example:
            >>> account = Account()
            >>> tx = Transactions.create_dag_transfer(
            ...     account.address, "DAG4J6gixVGKYmcZs9Wmkyrv8ERp39vxtjwbjV5Q", 100000000
            ... )
            >>> signed_tx = account.sign_transaction(tx)
        """
        # Validate addresses
        AddressValidator.validate(source)
        AddressValidator.validate(destination)
        
        # Validate amounts
        AmountValidator.validate(amount)
        AmountValidator.validate(fee, allow_zero=True)
        
        # Generate salt if not provided
        if salt is None:
            salt = Transactions._generate_salt()
        
        # Create transaction data
        transaction_data = {
            'source': source,
            'destination': destination,
            'amount': int(amount),
            'fee': int(fee),
            'salt': salt
        }
        
        # Add parent reference if provided
        if parent is not None:
            transaction_data['parent'] = parent
        
        # Validate final transaction structure
        TransactionValidator.validate_dag_transaction(transaction_data)
        
        return transaction_data
    
    @staticmethod
    def create_token_transfer(
        source: str,
        destination: str,
        amount: Union[int, float],
        metagraph_id: str,
        fee: Union[int, float] = 0,
        salt: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a metagraph token transfer transaction.
        
        Args:
            source: Source address sending the tokens
            destination: Recipient address
            amount: Amount to transfer (in token's smallest unit)
            metagraph_id: ID of the metagraph handling this token
            fee: Transaction fee (usually 0)
            salt: Salt for transaction uniqueness (auto-generated if None)
            
        Returns:
            Unsigned transaction ready for signing
            
        Raises:
            AddressValidationError: If addresses are invalid
            AmountValidationError: If amounts are invalid
            MetagraphIdValidationError: If metagraph ID is invalid
            TransactionValidationError: If transaction structure is invalid
            
        Example:
            >>> account = Account()
            >>> tx = Transactions.create_token_transfer(
            ...     account.address, "DAG4J6gixV...", 1000000000, "DAG7Ghth1WhW..."
            ... )
            >>> signed_tx = account.sign_metagraph_transaction(tx)
        """
        # Validate addresses
        AddressValidator.validate(source)
        AddressValidator.validate(destination)
        
        # Validate amounts
        AmountValidator.validate(amount)
        AmountValidator.validate(fee, allow_zero=True)
        
        # Validate metagraph ID
        MetagraphIdValidator.validate(metagraph_id)
        
        # Generate salt if not provided
        if salt is None:
            salt = Transactions._generate_salt()
        
        # Create transaction structure
        transaction_data = {
            'source': source,
            'destination': destination,
            'amount': int(amount),
            'fee': int(fee),
            'salt': salt,
            'metagraph_id': metagraph_id
        }
        
        # Validate final transaction structure
        TransactionValidator.validate_token_transaction(transaction_data)
        
        return transaction_data
    
    @staticmethod
    def create_data_submission(
        source: str,
        data: Dict[str, Any],
        metagraph_id: str,
        destination: Optional[str] = None,
        timestamp: Optional[int] = None,
        salt: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a metagraph data submission transaction.
        
        Args:
            source: Source address submitting the data
            data: Custom data to submit (will be JSON serialized)
            metagraph_id: ID of the metagraph to submit data to
            destination: Destination address (defaults to source for self-submission)
            timestamp: Unix timestamp (current time if None)
            salt: Salt for transaction uniqueness (auto-generated if None)
            
        Returns:
            Unsigned transaction ready for signing
            
        Raises:
            AddressValidationError: If addresses are invalid
            MetagraphIdValidationError: If metagraph ID is invalid
            InvalidDataError: If data is invalid
            TransactionValidationError: If transaction structure is invalid
            
        Example:
            >>> account = Account()
            >>> tx = Transactions.create_data_submission(
            ...     account.address,
            ...     {'sensor': 'temperature', 'value': 25.7},
            ...     "DAG7Ghth1WhW..."
            ... )
            >>> signed_tx = account.sign_metagraph_transaction(tx)
        """
        # Validate addresses
        AddressValidator.validate(source)
        if destination is None:
            destination = source  # Default to self-submission
        else:
            AddressValidator.validate(destination)
        
        # Validate metagraph ID
        MetagraphIdValidator.validate(metagraph_id)
        
        # Validate data payload
        DataValidator.validate_data_payload(data)
        
        # Use current timestamp if not provided
        if timestamp is None:
            timestamp = Transactions._get_timestamp()
        
        # Validate timestamp
        if not isinstance(timestamp, int) or timestamp <= 0:
            raise TransactionValidationError(
                "Timestamp must be a positive integer",
                transaction_type='data'
            )
        
        # Generate salt if not provided
        if salt is None:
            salt = Transactions._generate_salt()
        
        # Create data transaction structure
        transaction_data = {
            'source': source,
            'destination': destination,
            'data': data,
            'metagraph_id': metagraph_id,
            'timestamp': timestamp,
            'salt': salt
        }
        
        # Validate final transaction structure
        TransactionValidator.validate_data_transaction(transaction_data)
        
        return transaction_data
    
    @staticmethod
    def create_batch_transfer(
        sender: Account,
        transfers: list,
        transaction_type: str = 'dag'
    ) -> list:
        """
        Create multiple transactions in batch.
        
        Args:
            sender: Account sending the transactions
            transfers: List of transfer specifications
            transaction_type: 'dag', 'token', or 'data'
            
        Returns:
            List of signed transactions
            
        Example:
            >>> transfers = [
            ...     {'destination': 'DAG123...', 'amount': 1000000},
            ...     {'destination': 'DAG456...', 'amount': 2000000}
            ... ]
            >>> txs = Transactions.create_batch_transfer(account, transfers, 'dag')
        """
        transactions = []
        
        for transfer in transfers:
            try:
                if transaction_type == 'dag':
                    tx_data = Transactions.create_dag_transfer(
                        sender,
                        transfer['destination'],
                        transfer['amount'],
                        transfer.get('fee', 0),
                        transfer.get('parent')
                    )
                    signed_tx = sender.sign_transaction(tx_data)
                    
                elif transaction_type == 'token':
                    signed_tx = Transactions.create_token_transfer(
                        sender,
                        transfer['destination'],
                        transfer['amount'],
                        transfer['metagraph_id'],
                        transfer.get('fee', 0)
                    )
                    
                elif transaction_type == 'data':
                    signed_tx = Transactions.create_data_submission(
                        sender,
                        transfer['data'],
                        transfer['metagraph_id'],
                        transfer.get('timestamp')
                    )
                    
                else:
                    raise TransactionError(f"Unknown transaction type: {transaction_type}")
                
                transactions.append(signed_tx)
                
            except Exception as e:
                # Log error but continue with other transactions
                print(f"Failed to create transaction: {e}")
                transactions.append(None)
        
        return transactions
    
    @staticmethod
    def _generate_salt() -> int:
        """
        Generate a random salt for transaction uniqueness.
        
        Returns:
            Random integer salt
        """
        return secrets.randbits(32)
    
    @staticmethod
    def _get_timestamp() -> int:
        """
        Get current Unix timestamp.
        
        Returns:
            Current timestamp as integer
        """
        return int(time.time())
    
    @staticmethod
    def estimate_transaction_size(transaction_data: Dict[str, Any]) -> int:
        """
        Estimate the size of a transaction in bytes.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            Estimated size in bytes
        """
        # Convert to JSON and estimate size
        json_str = json.dumps(transaction_data, sort_keys=True)
        return len(json_str.encode('utf-8'))
    
    @staticmethod
    def validate_transaction_structure(transaction_data: Dict[str, Any]) -> bool:
        """
        Validate that transaction data has correct structure.
        
        Args:
            transaction_data: Transaction to validate
            
        Returns:
            True if valid, raises TransactionError if invalid
        """
        required_fields = ['source', 'destination', 'amount', 'fee', 'salt']
        
        for field in required_fields:
            if field not in transaction_data:
                raise TransactionError(f"Missing required field: {field}")
        
        # Validate address formats
        if not transaction_data['source'].startswith('DAG'):
            raise TransactionError("Invalid source address")
        
        if not transaction_data['destination'].startswith('DAG'):
            raise TransactionError("Invalid destination address")
        
        # Validate amounts
        if not isinstance(transaction_data['amount'], int) or transaction_data['amount'] <= 0:
            raise TransactionError("Amount must be a positive integer")
        
        if not isinstance(transaction_data['fee'], int) or transaction_data['fee'] < 0:
            raise TransactionError("Fee must be a non-negative integer")
        
        return True


# Convenience functions for backward compatibility
def create_dag_transaction(sender: Account, destination: str, amount: Union[int, float], **kwargs) -> Dict[str, Any]:
    """Convenience function for DAG transaction creation."""
    return Transactions.create_dag_transfer(sender, destination, amount, **kwargs)

def create_metagraph_token_transaction(sender: Account, destination: str, amount: Union[int, float], 
                                     metagraph_id: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for metagraph token transaction creation."""
    return Transactions.create_token_transfer(sender, destination, amount, metagraph_id, **kwargs)

def create_metagraph_data_transaction(sender: Account, data: Dict[str, Any], 
                                    metagraph_id: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for metagraph data transaction creation."""
    return Transactions.create_data_submission(sender, data, metagraph_id, **kwargs) 