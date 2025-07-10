"""
Custom exception hierarchy for Constellation SDK.

This module provides a comprehensive set of exception classes for handling
various error conditions that can occur during SDK operations.
"""


class ConstellationError(Exception):
    """
    Base exception class for all Constellation SDK errors.
    
    Attributes:
        message (str): Human-readable error message
        error_code (str): Optional error code for programmatic handling
        details (dict): Optional additional error details
    """
    
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self):
        """Convert exception to dictionary representation."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


# =====================
# Validation Errors
# =====================

class ValidationError(ConstellationError):
    """
    Raised when input validation fails.
    
    Used for invalid addresses, amounts, transaction data, etc.
    """
    
    def __init__(self, message, field=None, value=None, expected=None):
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.details.update({
            'field': field,
            'value': value,
            'expected': expected
        })


class AddressValidationError(ValidationError):
    """Raised when DAG address validation fails."""
    
    def __init__(self, address, reason=None):
        message = f"Invalid DAG address: {address}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, field="address", value=address)


class AmountValidationError(ValidationError):
    """Raised when amount validation fails."""
    
    def __init__(self, amount, reason=None):
        message = f"Invalid amount: {amount}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, field="amount", value=amount)


class MetagraphIdValidationError(ValidationError):
    """Raised when metagraph ID validation fails."""
    
    def __init__(self, metagraph_id, reason=None):
        message = f"Invalid metagraph ID: {metagraph_id}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, field="metagraph_id", value=metagraph_id)


class TransactionValidationError(ValidationError):
    """Raised when transaction data validation fails."""
    
    def __init__(self, message, transaction_type=None, missing_fields=None):
        super().__init__(message, error_code="TRANSACTION_VALIDATION_ERROR")
        self.details.update({
            'transaction_type': transaction_type,
            'missing_fields': missing_fields or []
        })


# =====================
# Network Errors
# =====================

class NetworkError(ConstellationError):
    """
    Base class for network-related errors.
    
    Used for HTTP errors, connection issues, timeouts, etc.
    """
    
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message, error_code="NETWORK_ERROR")
        self.status_code = status_code
        self.response_data = response_data
        self.details.update({
            'status_code': status_code,
            'response_data': response_data
        })


class ConnectionError(NetworkError):
    """Raised when network connection fails."""
    
    def __init__(self, message, url=None):
        super().__init__(message, error_code="CONNECTION_ERROR")
        self.url = url
        self.details['url'] = url


class TimeoutError(NetworkError):
    """Raised when network request times out."""
    
    def __init__(self, message, timeout_duration=None):
        super().__init__(message, error_code="TIMEOUT_ERROR")
        self.timeout_duration = timeout_duration
        self.details['timeout_duration'] = timeout_duration


class HTTPError(NetworkError):
    """Raised when HTTP request returns an error status code."""
    
    def __init__(self, message, status_code, url=None, response_data=None):
        super().__init__(message, error_code="HTTP_ERROR")
        self.status_code = status_code
        self.url = url
        self.response_data = response_data
        self.details.update({
            'status_code': status_code,
            'url': url,
            'response_data': response_data
        })


class APIError(NetworkError):
    """Raised when API returns an error response."""
    
    def __init__(self, message, api_error_code=None, api_error_details=None):
        super().__init__(message, error_code="API_ERROR")
        self.api_error_code = api_error_code
        self.api_error_details = api_error_details
        self.details.update({
            'api_error_code': api_error_code,
            'api_error_details': api_error_details
        })


# =====================
# Transaction Errors
# =====================

class TransactionError(ConstellationError):
    """
    Base class for transaction-related errors.
    
    Used for transaction creation, signing, and submission issues.
    """
    
    def __init__(self, message, transaction_hash=None):
        super().__init__(message, error_code="TRANSACTION_ERROR")
        self.transaction_hash = transaction_hash
        self.details['transaction_hash'] = transaction_hash


class TransactionRejectedError(TransactionError):
    """Raised when a transaction is rejected by the network."""
    
    def __init__(self, message, reason=None, transaction_hash=None):
        super().__init__(message, transaction_hash)
        self.error_code = "TRANSACTION_REJECTED"
        self.reason = reason
        self.details['reason'] = reason


class InsufficientBalanceError(TransactionError):
    """Raised when account has insufficient balance for transaction."""
    
    def __init__(self, required_amount, available_balance, address=None):
        message = f"Insufficient balance: required {required_amount}, available {available_balance}"
        super().__init__(message)
        self.error_code = "INSUFFICIENT_BALANCE"
        self.required_amount = required_amount
        self.available_balance = available_balance
        self.address = address
        self.details.update({
            'required_amount': required_amount,
            'available_balance': available_balance,
            'address': address
        })


class SigningError(TransactionError):
    """Raised when transaction signing fails."""
    
    def __init__(self, message, reason=None):
        super().__init__(message)
        self.error_code = "SIGNING_ERROR"
        self.reason = reason
        self.details['reason'] = reason


class InvalidTransactionError(TransactionError):
    """Raised when transaction data is invalid or malformed."""
    
    def __init__(self, message, transaction_data=None, validation_errors=None):
        super().__init__(message)
        self.error_code = "INVALID_TRANSACTION"
        self.transaction_data = transaction_data
        self.validation_errors = validation_errors or []
        self.details.update({
            'transaction_data': transaction_data,
            'validation_errors': validation_errors
        })


# =====================
# Account Errors
# =====================

class AccountError(ConstellationError):
    """
    Base class for account-related errors.
    
    Used for key management, address generation, etc.
    """
    
    def __init__(self, message, address=None):
        super().__init__(message, error_code="ACCOUNT_ERROR")
        self.address = address
        self.details['address'] = address


class InvalidPrivateKeyError(AccountError):
    """Raised when private key is invalid or malformed."""
    
    def __init__(self, message, private_key=None):
        super().__init__(message)
        self.error_code = "INVALID_PRIVATE_KEY"
        self.private_key = private_key
        # Don't store private key in details for security
        self.details['private_key_provided'] = private_key is not None


class KeyGenerationError(AccountError):
    """Raised when key generation fails."""
    
    def __init__(self, message, reason=None):
        super().__init__(message)
        self.error_code = "KEY_GENERATION_ERROR"
        self.reason = reason
        self.details['reason'] = reason


class AddressGenerationError(AccountError):
    """Raised when address generation fails."""
    
    def __init__(self, message, public_key=None):
        super().__init__(message)
        self.error_code = "ADDRESS_GENERATION_ERROR"
        self.public_key = public_key
        self.details['public_key_provided'] = public_key is not None


# =====================
# Metagraph Errors
# =====================

class MetagraphError(ConstellationError):
    """
    Base class for metagraph-related errors.
    
    Used for metagraph discovery, data queries, token operations, etc.
    """
    
    def __init__(self, message, metagraph_id=None):
        super().__init__(message, error_code="METAGRAPH_ERROR")
        self.metagraph_id = metagraph_id
        self.details['metagraph_id'] = metagraph_id


class MetagraphNotFoundError(MetagraphError):
    """Raised when specified metagraph is not found."""
    
    def __init__(self, metagraph_id):
        message = f"Metagraph not found: {metagraph_id}"
        super().__init__(message, metagraph_id)
        self.error_code = "METAGRAPH_NOT_FOUND"


class MetagraphDiscoveryError(MetagraphError):
    """Raised when metagraph discovery fails."""
    
    def __init__(self, message, network=None):
        super().__init__(message)
        self.error_code = "METAGRAPH_DISCOVERY_ERROR"
        self.network = network
        self.details['network'] = network


class InvalidDataError(MetagraphError):
    """Raised when metagraph data is invalid."""
    
    def __init__(self, message, data=None, validation_errors=None):
        super().__init__(message)
        self.error_code = "INVALID_DATA"
        self.data = data
        self.validation_errors = validation_errors or []
        self.details.update({
            'data': data,
            'validation_errors': validation_errors
        })


# =====================
# Configuration Errors
# =====================

class ConfigurationError(ConstellationError):
    """
    Base class for configuration-related errors.
    
    Used for invalid network configurations, missing settings, etc.
    """
    
    def __init__(self, message, config_key=None, config_value=None):
        super().__init__(message, error_code="CONFIGURATION_ERROR")
        self.config_key = config_key
        self.config_value = config_value
        self.details.update({
            'config_key': config_key,
            'config_value': config_value
        })


class InvalidNetworkError(ConfigurationError):
    """Raised when specified network is invalid or unsupported."""
    
    def __init__(self, network_name, supported_networks=None):
        message = f"Invalid network: {network_name}"
        if supported_networks:
            message += f". Supported networks: {', '.join(supported_networks)}"
        super().__init__(message, config_key="network", config_value=network_name)
        self.error_code = "INVALID_NETWORK"
        self.network_name = network_name
        self.supported_networks = supported_networks or []
        self.details['supported_networks'] = self.supported_networks


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""
    
    def __init__(self, config_key, description=None):
        message = f"Missing required configuration: {config_key}"
        if description:
            message += f" ({description})"
        super().__init__(message, config_key=config_key)
        self.error_code = "MISSING_CONFIGURATION"


# =====================
# Utility Functions
# =====================

def wrap_network_error(func):
    """
    Decorator to wrap network-related exceptions with ConstellationError.
    
    Converts standard network exceptions (requests.RequestException, etc.)
    into appropriate ConstellationError subclasses.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    response_data = e.response.json()
                except:
                    response_data = e.response.text
                raise HTTPError(
                    f"HTTP {status_code}: {str(e)}",
                    status_code=status_code,
                    url=e.response.url,
                    response_data=response_data
                )
            else:
                raise ConnectionError(f"Network connection failed: {str(e)}")
        except Exception as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Request timeout: {str(e)}")
            raise ConstellationError(f"Unexpected error: {str(e)}")
    
    return wrapper


def format_error_for_logging(error):
    """
    Format ConstellationError for structured logging.
    
    Args:
        error: ConstellationError instance
        
    Returns:
        dict: Formatted error information for logging
    """
    if isinstance(error, ConstellationError):
        return {
            'error_type': error.__class__.__name__,
            'error_code': error.error_code,
            'message': error.message,
            'details': error.details
        }
    else:
        return {
            'error_type': error.__class__.__name__,
            'message': str(error)
        }


# Import requests for the decorator
try:
    import requests
except ImportError:
    # If requests not available, create a dummy class
    class requests:
        class RequestException(Exception):
            pass 