"""
Comprehensive logging framework for Constellation SDK.

This module provides structured logging capabilities with configurable levels,
performance tracking, request/response logging, and error handling integration.
Supports both development debugging and production monitoring.
"""

import functools
import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from .exceptions import ConstellationError, format_error_for_logging

# =====================
# Logger Configuration
# =====================


class ConstellationLogger:
    """
    Centralized logger for Constellation SDK operations.

    Provides structured logging with context, performance metrics,
    and integration with error handling system.
    """

    def __init__(self, name: str = "constellation_sdk"):
        self.logger = logging.getLogger(name)
        self.context = threading.local()
        self._configure_default_handler()

    def _configure_default_handler(self):
        """Configure default console handler if none exists."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def set_level(self, level: Union[str, int]):
        """
        Set logging level.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)

    def add_file_handler(self, filepath: str, level: Union[str, int] = logging.INFO):
        """
        Add file handler for persistent logging.

        Args:
            filepath: Path to log file
            level: Logging level for file handler
        """
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(filepath)
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        handler.setLevel(level)

        # Use JSON formatter for file logs
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def set_context(self, **kwargs):
        """
        Set context for current thread.

        Args:
            **kwargs: Context key-value pairs
        """
        if not hasattr(self.context, "data"):
            self.context.data = {}
        self.context.data.update(kwargs)

    def clear_context(self):
        """Clear context for current thread."""
        if hasattr(self.context, "data"):
            self.context.data.clear()

    def _get_context(self) -> Dict[str, Any]:
        """Get current thread context."""
        if hasattr(self.context, "data"):
            return self.context.data.copy()
        return {}

    def _log_structured(self, level: int, message: str, **kwargs):
        """
        Log structured message with context.

        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional structured data
        """
        data = {
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": self._get_context(),
            **kwargs,
        }

        # Log as JSON for structured logging
        self.logger.log(level, json.dumps(data, default=str))

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_structured(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_structured(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_structured(logging.WARNING, message, **kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """
        Log error message with optional exception details.

        Args:
            message: Error message
            error: Exception object
            **kwargs: Additional data
        """
        if error:
            kwargs.update(format_error_for_logging(error))
        self._log_structured(logging.ERROR, message, **kwargs)

    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """
        Log critical message with optional exception details.

        Args:
            message: Critical message
            error: Exception object
            **kwargs: Additional data
        """
        if error:
            kwargs.update(format_error_for_logging(error))
        self._log_structured(logging.CRITICAL, message, **kwargs)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging.
    """

    def format(self, record):
        # Try to parse as JSON first
        try:
            data = json.loads(record.getMessage())
            return json.dumps(data, indent=None, separators=(",", ":"))
        except (json.JSONDecodeError, TypeError):
            # Fall back to standard formatting
            return super().format(record)


# =====================
# Performance Logging
# =====================


class PerformanceTracker:
    """
    Performance tracking and logging for SDK operations.
    """

    def __init__(self, logger: ConstellationLogger):
        self.logger = logger
        self.active_operations = threading.local()

    def start_operation(self, operation_name: str, **metadata):
        """
        Start tracking an operation.

        Args:
            operation_name: Name of the operation
            **metadata: Additional operation metadata
        """
        if not hasattr(self.active_operations, "stack"):
            self.active_operations.stack = []

        operation_data = {
            "name": operation_name,
            "start_time": time.time(),
            "metadata": metadata,
        }

        self.active_operations.stack.append(operation_data)

        self.logger.debug(
            f"Started operation: {operation_name}",
            operation=operation_name,
            operation_type="start",
            **metadata,
        )

    def end_operation(self, operation_name: str, success: bool = True, **results):
        """
        End tracking an operation.

        Args:
            operation_name: Name of the operation
            success: Whether operation succeeded
            **results: Operation results
        """
        if (
            not hasattr(self.active_operations, "stack")
            or not self.active_operations.stack
        ):
            self.logger.warning(f"No active operation to end: {operation_name}")
            return

        operation_data = self.active_operations.stack.pop()

        if operation_data["name"] != operation_name:
            self.logger.warning(
                f"Operation name mismatch: expected {operation_data['name']}, got {operation_name}"
            )

        duration = time.time() - operation_data["start_time"]

        self.logger.info(
            f"Completed operation: {operation_name}",
            operation=operation_name,
            operation_type="end",
            duration_seconds=duration,
            success=success,
            metadata=operation_data["metadata"],
            results=results,
        )

    def track_operation(self, operation_name: str, **metadata):
        """
        Decorator to track operation performance.

        Args:
            operation_name: Name of the operation
            **metadata: Additional metadata
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.start_operation(operation_name, **metadata)
                try:
                    result = func(*args, **kwargs)
                    self.end_operation(
                        operation_name, success=True, result_type=type(result).__name__
                    )
                    return result
                except Exception as e:
                    self.end_operation(operation_name, success=False, error=str(e))
                    raise

            return wrapper

        return decorator


# =====================
# Network Request Logging
# =====================


class NetworkLogger:
    """
    Specialized logger for network requests and responses.
    """

    def __init__(self, logger: ConstellationLogger):
        self.logger = logger

    def log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        data: Optional[Any] = None,
        **kwargs,
    ):
        """
        Log outgoing network request.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            data: Request data
            **kwargs: Additional request metadata
        """
        # Filter sensitive headers
        safe_headers = self._filter_sensitive_headers(headers or {})

        self.logger.debug(
            f"HTTP Request: {method} {url}",
            request_type="outgoing",
            method=method,
            url=url,
            headers=safe_headers,
            has_data=data is not None,
            data_size=len(str(data)) if data else 0,
            **kwargs,
        )

    def log_response(
        self,
        method: str,
        url: str,
        status_code: int,
        response_time: float,
        response_size: Optional[int] = None,
        error: Optional[str] = None,
        **kwargs,
    ):
        """
        Log network response.

        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            response_time: Response time in seconds
            response_size: Response size in bytes
            error: Error message if any
            **kwargs: Additional response metadata
        """
        log_level = logging.ERROR if error or status_code >= 400 else logging.INFO

        message = f"HTTP Response: {method} {url} - {status_code}"
        if error:
            message += f" - {error}"

        self.logger._log_structured(
            log_level,
            message,
            request_type="response",
            method=method,
            url=url,
            status_code=status_code,
            response_time_seconds=response_time,
            response_size_bytes=response_size,
            error=error,
            **kwargs,
        )

    def _filter_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Filter sensitive information from headers.

        Args:
            headers: Request headers

        Returns:
            Filtered headers
        """
        sensitive_headers = {"authorization", "x-api-key", "cookie", "set-cookie"}

        filtered = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                filtered[key] = "[REDACTED]"
            else:
                filtered[key] = value

        return filtered


# =====================
# Transaction Logging
# =====================


class TransactionLogger:
    """
    Specialized logger for transaction operations.
    """

    def __init__(self, logger: ConstellationLogger):
        self.logger = logger

    def log_transaction_creation(
        self,
        tx_type: str,
        source: str,
        destination: str,
        amount: Optional[int] = None,
        **metadata,
    ):
        """
        Log transaction creation.

        Args:
            tx_type: Transaction type (dag, token, data)
            source: Source address
            destination: Destination address
            amount: Transaction amount
            **metadata: Additional transaction metadata
        """
        self.logger.info(
            f"Created {tx_type} transaction",
            transaction_type=tx_type,
            source=source,
            destination=destination,
            amount=amount,
            operation="transaction_creation",
            **metadata,
        )

    def log_transaction_signing(
        self,
        tx_type: str,
        tx_hash: Optional[str] = None,
        signer: Optional[str] = None,
        **metadata,
    ):
        """
        Log transaction signing.

        Args:
            tx_type: Transaction type
            tx_hash: Transaction hash (if available)
            signer: Signer address
            **metadata: Additional metadata
        """
        self.logger.info(
            f"Signed {tx_type} transaction",
            transaction_type=tx_type,
            transaction_hash=tx_hash,
            signer=signer,
            operation="transaction_signing",
            **metadata,
        )

    def log_transaction_submission(
        self, tx_type: str, tx_hash: str, network: str, success: bool, **metadata
    ):
        """
        Log transaction submission.

        Args:
            tx_type: Transaction type
            tx_hash: Transaction hash
            network: Target network
            success: Whether submission succeeded
            **metadata: Additional metadata
        """
        log_level = logging.INFO if success else logging.ERROR

        message = (
            f"{'Submitted' if success else 'Failed to submit'} {tx_type} transaction"
        )

        self.logger._log_structured(
            log_level,
            message,
            transaction_type=tx_type,
            transaction_hash=tx_hash,
            network=network,
            success=success,
            operation="transaction_submission",
            **metadata,
        )


# =====================
# Global Logger Instance
# =====================

# Global logger instance
_global_logger = ConstellationLogger()
_performance_tracker = PerformanceTracker(_global_logger)
_network_logger = NetworkLogger(_global_logger)
_transaction_logger = TransactionLogger(_global_logger)


def get_logger() -> ConstellationLogger:
    """Get the global logger instance."""
    return _global_logger


def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker."""
    return _performance_tracker


def get_network_logger() -> NetworkLogger:
    """Get the global network logger."""
    return _network_logger


def get_transaction_logger() -> TransactionLogger:
    """Get the global transaction logger."""
    return _transaction_logger


def configure_logging(
    level: str = "INFO",
    file_path: Optional[str] = None,
    console: bool = True,
    structured: bool = True,
):
    """
    Configure global logging settings.

    Args:
        level: Logging level
        file_path: Path to log file (optional)
        console: Whether to log to console
        structured: Whether to use structured JSON logging
    """
    logger = get_logger()

    # Clear existing handlers
    logger.logger.handlers.clear()

    # Set level
    logger.set_level(level)

    # Add console handler
    if console:
        handler = logging.StreamHandler()
        formatter = (
            StructuredFormatter()
            if structured
            else logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        handler.setFormatter(formatter)
        logger.logger.addHandler(handler)

    # Add file handler
    if file_path:
        logger.add_file_handler(file_path, level)


# =====================
# Decorators
# =====================


def log_operation(operation_name: str, **metadata):
    """
    Decorator to log operation start/end with performance tracking.

    Args:
        operation_name: Name of the operation
        **metadata: Additional metadata
    """
    return _performance_tracker.track_operation(operation_name, **metadata)


def log_network_call(func: Callable) -> Callable:
    """
    Decorator to log network calls.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        # Try to extract URL from args/kwargs
        url = kwargs.get("url") or (args[0] if args else "unknown")
        method = getattr(func, "__name__", "unknown").upper()

        _network_logger.log_request(method, url, **kwargs)

        try:
            result = func(*args, **kwargs)
            response_time = time.time() - start_time

            # Try to extract status code from result
            status_code = getattr(result, "status_code", 200)

            _network_logger.log_response(method, url, status_code, response_time)

            return result
        except Exception as e:
            response_time = time.time() - start_time

            _network_logger.log_response(method, url, 0, response_time, error=str(e))
            raise

    return wrapper
