"""
Account management for Constellation Network.
Handles key generation, address derivation, and transaction signing.

Note: Transaction creation has been moved to the transactions module.
Use constellation_sdk.Transactions for creating transactions.
"""

import hashlib
import json
import secrets
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization


class ConstellationError(Exception):
    """Base exception for Constellation SDK errors."""
    pass


class Account:
    """
    Constellation Network account for managing keys and signing transactions.
    
    This class handles:
    - Private/public key generation and management
    - DAG address derivation
    - Transaction and message signing
    
    For creating transactions, use the Transactions class:
        >>> from constellation_sdk import Account, Transactions
        >>> account = Account()
        >>> tx_data = Transactions.create_dag_transfer(
        ...     account, "DAG4J6gixV...", 100000000
        ... )
        >>> signed_tx = account.sign_transaction(tx_data)
    
    Example:
        >>> account = Account()
        >>> print(account.address)
        DAG4J6gixVGKYmcZs9Wmkyrv8ERp39vxtjwbjV5Q
        
        >>> # Import existing account
        >>> account = Account("your_private_key_hex")
    """
    
    def __init__(self, private_key_hex: Optional[str] = None):
        """
        Initialize account with optional private key.
        
        Args:
            private_key_hex: Hex string of private key. If None, generates new key.
        """
        if private_key_hex:
            self.private_key = self._load_private_key(private_key_hex)
        else:
            self.private_key = ec.generate_private_key(ec.SECP256K1())
            
        self.public_key = self.private_key.public_key()
        self.address = self._derive_address()
    
    def _load_private_key(self, hex_key: str) -> ec.EllipticCurvePrivateKey:
        """Load private key from hex string."""
        try:
            key_bytes = bytes.fromhex(hex_key)
            return ec.derive_private_key(
                int.from_bytes(key_bytes, 'big'),
                ec.SECP256K1()
            )
        except Exception as e:
            raise ConstellationError(f"Invalid private key: {e}")
    
    def _derive_address(self) -> str:
        """Derive DAG address from public key."""
        public_bytes = self.public_key.public_numbers().x.to_bytes(32, 'big') + \
                      self.public_key.public_numbers().y.to_bytes(32, 'big')
        address_hash = hashlib.sha256(public_bytes).hexdigest()
        return f"DAG{address_hash[:35]}"
    
    @property
    def private_key_hex(self) -> str:
        """Get private key as hex string."""
        private_bytes = self.private_key.private_numbers().private_value.to_bytes(32, 'big')
        return private_bytes.hex()
    
    @property
    def public_key_hex(self) -> str:
        """Get public key as hex string."""
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        return public_bytes.hex()
    
    def sign_message(self, message: str) -> str:
        """
        Sign a message with the account's private key.
        
        Args:
            message: Message to sign
            
        Returns:
            Hex-encoded signature
        """
        message_bytes = message.encode('utf-8')
        signature = self.private_key.sign(message_bytes, ec.ECDSA(hashes.SHA256()))
        return signature.hex()
    
    # Transaction creation logic moved to transactions.py module
    # Use Transactions.create_dag_transfer() or other methods instead
    
    def sign_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a transaction.
        
        Args:
            transaction_data: Transaction to sign
            
        Returns:
            Signed transaction ready for submission
        """
        # Handle genesis transactions (no parent)
        parent = transaction_data.get('parent')
        if parent is None or parent == {}:
            # Genesis transaction - no parent reference
            value = {
                'source': transaction_data['source'],
                'destination': transaction_data['destination'],
                'amount': transaction_data['amount'],
                'fee': transaction_data['fee'],
                'salt': transaction_data['salt']
            }
        else:
            # Regular transaction with parent
            value = {
                'source': transaction_data['source'],
                'destination': transaction_data['destination'],
                'amount': transaction_data['amount'],
                'fee': transaction_data['fee'],
                'parent': parent,
                'salt': transaction_data['salt']
            }
        
        # Create hash of the value for signing
        value_json = json.dumps(value, sort_keys=True, separators=(',', ':'))
        value_bytes = value_json.encode('utf-8')
        
        # Create signature
        signature = self.private_key.sign(value_bytes, ec.ECDSA(hashes.SHA256()))
        signature_hex = signature.hex()
        
        # Create the complete signed transaction
        signed_transaction = {
            'value': value,
            'proofs': [{
                'id': self.public_key_hex,
                'signature': signature_hex
            }]
        }
        
        return signed_transaction 

    def sign_metagraph_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a metagraph-specific transaction.
        
        Args:
            transaction_data: Metagraph transaction to sign
            
        Returns:
            Signed transaction ready for metagraph submission
        """
        # Handle metagraph-specific transaction structure
        if 'data' in transaction_data:
            # Data submission transaction
            value = {
                'source': transaction_data['source'],
                'data': transaction_data['data'],
                'metagraph_id': transaction_data['metagraph_id'],
                'timestamp': transaction_data.get('timestamp', 0),
                'salt': transaction_data.get('salt', secrets.randbits(64))
            }
        else:
            # Token transfer transaction
            value = {
                'source': transaction_data['source'],
                'destination': transaction_data['destination'],
                'amount': transaction_data['amount'],
                'fee': transaction_data.get('fee', 0),
                'metagraph_id': transaction_data['metagraph_id'],
                'salt': transaction_data.get('salt', secrets.randbits(64))
            }
            
            # Add token identifier if specified
            if 'token' in transaction_data:
                value['token'] = transaction_data['token']
            
            # Add parent if specified (for transaction chaining)
            if 'parent' in transaction_data:
                value['parent'] = transaction_data['parent']
        
        # Create hash of the value for signing
        value_json = json.dumps(value, sort_keys=True, separators=(',', ':'))
        value_bytes = value_json.encode('utf-8')
        
        # Create signature
        signature = self.private_key.sign(value_bytes, ec.ECDSA(hashes.SHA256()))
        signature_hex = signature.hex()
        
        # Create the complete signed transaction
        signed_transaction = {
            'value': value,
            'proofs': [{
                'id': self.public_key_hex,
                'signature': signature_hex
            }]
        }
        
        return signed_transaction 