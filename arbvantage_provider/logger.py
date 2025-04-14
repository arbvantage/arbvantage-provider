"""
Universal logger implementation for Arbvantage Provider Framework.

This module provides a comprehensive logging solution that can be used across all providers.
It includes features like:
- Structured logging
- Log levels
- Context management
- Performance metrics
- Error tracking
- Custom formatters
"""

import logging
import json
import time
import os
from typing import Dict, Any, Optional, Union
from datetime import datetime
from functools import wraps
from arbvantage_provider.schemas import ProviderResponse
class ProviderLogger:
    """
    Universal logger for Arbvantage providers.
    
    This logger provides:
    - Structured logging with context
    - Performance metrics tracking
    - Error tracking and reporting
    - Custom log levels
    - Log rotation
    - Multiple output handlers
    """
    
    def __init__(
        self,
        name: str,
        level: Union[int, str] = logging.INFO,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Initialize the logger with configuration.
        
        Args:
            name: Logger name (usually provider name)
            level: Logging level (default: INFO)
            log_file: Path to log file (optional)
            log_format: Custom log format (optional)
            max_file_size: Maximum log file size in bytes
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Default format if not provided
        if not log_format:
            log_format = (
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(message)s - %(context)s'
            )
            
        formatter = logging.Formatter(log_format)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if log_file is provided
        if log_file:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
        # Initialize metrics
        self.metrics = {
            "error_count": 0,
            "warning_count": 0,
            "total_requests": 0,
            "processing_times": []
        }
        
    def _format_context(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format context dictionary for logging.
        
        Args:
            context: Context dictionary to format
            
        Returns:
            Formatted context string
        """
        if not context:
            return "{}"
        return json.dumps(context)
        
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """
        Get context from kwargs and add default fields.
        
        Args:
            **kwargs: Context fields
            
        Returns:
            Context dictionary
        """
        context = kwargs.copy()
        context.update({
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid()
        })
        return context
        
    def info(self, message: str, **kwargs) -> None:
        """
        Log info message with context.
        
        Args:
            message: Log message
            **kwargs: Context fields
        """
        context = self._get_context(**kwargs)
        self.logger.info(
            message,
            extra={"context": self._format_context(context)}
        )
        
    def debug(self, message: str, **kwargs) -> None:
        """
        Log debug message with context.
        
        Args:
            message: Log message
            **kwargs: Context fields
        """
        context = self._get_context(**kwargs)
        self.logger.debug(
            message,
            extra={"context": self._format_context(context)}
        )
        
    def warning(self, message: str, **kwargs) -> None:
        """
        Log warning message with context.
        
        Args:
            message: Log message
            **kwargs: Context fields
        """
        context = self._get_context(**kwargs)
        self.metrics["warning_count"] += 1
        self.logger.warning(
            message,
            extra={"context": self._format_context(context)}
        )
        
    def error(self, message: str, **kwargs) -> None:
        """
        Log error message with context.
        
        Args:
            message: Log message
            **kwargs: Context fields
        """
        context = self._get_context(**kwargs)
        self.metrics["error_count"] += 1
        self.logger.error(
            message,
            extra={"context": self._format_context(context)}
        )
        
    def exception(self, message: str, **kwargs) -> None:
        """
        Log exception with context and stack trace.
        
        Args:
            message: Log message
            **kwargs: Context fields
        """
        context = self._get_context(**kwargs)
        self.metrics["error_count"] += 1
        self.logger.exception(
            message,
            extra={"context": self._format_context(context)}
        )
        
    def critical(self, message: str, **kwargs) -> None:
        """
        Log critical message with context.
        
        Args:
            message: Log message
            **kwargs: Context fields
        """
        context = self._get_context(**kwargs)
        self.metrics["error_count"] += 1
        self.logger.critical(
            message,
            extra={"context": self._format_context(context)}
        )
        
    def log_metric(self, name: str, value: float, **kwargs) -> None:
        """
        Log a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            **kwargs: Additional context
        """
        context = self._get_context(metric_name=name, metric_value=value, **kwargs)
        self.logger.info(
            f"Metric: {name} = {value}",
            extra={"context": self._format_context(context)}
        )
        
    def log_performance(self, operation: str, start_time: float, **kwargs) -> None:
        """
        Log performance metrics for an operation.
        
        Args:
            operation: Operation name
            start_time: Operation start time
            **kwargs: Additional context
        """
        duration = time.time() - start_time
        self.metrics["processing_times"].append(duration)
        context = self._get_context(
            operation=operation,
            duration=duration,
            **kwargs
        )
        self.logger.info(
            f"Performance: {operation} took {duration:.2f}s",
            extra={"context": self._format_context(context)}
        )
        
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.
        
        Returns:
            Dictionary with current metrics
        """
        return self.metrics.copy()
        
    def reset_metrics(self) -> None:
        """
        Reset all metrics to zero.
        """
        self.metrics = {
            "error_count": 0,
            "warning_count": 0,
            "total_requests": 0,
            "processing_times": []
        }
        
    def log_request(self, action: str, **kwargs) -> None:
        """
        Log a request with context.
        
        Args:
            action: Action name
            **kwargs: Additional context
        """
        self.metrics["total_requests"] += 1
        context = self._get_context(action=action, **kwargs)
        self.logger.info(
            f"Request: {action}",
            extra={"context": self._format_context(context)}
        )
        
    def log_response(self, action: str, status: str, **kwargs) -> None:
        """
        Log a response with context.
        
        Args:
            action: Action name
            status: Response status
            **kwargs: Additional context
        """
        context = self._get_context(action=action, status=status, **kwargs)
        self.logger.info(
            f"Response: {action} - {status}",
            extra={"context": self._format_context(context)}
        )
        
    def performance_monitor(self, operation: str):
        """
        Decorator for monitoring function performance.
        
        Args:
            operation: Operation name
            
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.log_performance(operation, start_time)
                    return result
                except Exception as e:
                    self.log_performance(operation, start_time)
                    return ProviderResponse(
                        status="error",
                        message=f"Error in {operation}",
                        data={"error": str(e)}
                    ).model_dump()
            return wrapper
        return decorator 