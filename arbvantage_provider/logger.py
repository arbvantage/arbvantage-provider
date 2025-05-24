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

# Import standard logging module for log management.
import logging
# Import json for structured log formatting.
import json
# Import time for performance measurement.
import time
# Import os for process information in logs.
import os
# Import typing for type hints and flexibility.
from typing import Dict, Any, Optional, Union
# Import datetime for timestamps in logs.
from datetime import datetime
# Import wraps for decorator implementation.
from functools import wraps
# Import ProviderResponse for structured response logging.
from arbvantage_provider.schemas import ProviderResponse

class ProviderLogger:
    """
    Universal logger for Arbvantage providers.
    
    This logger provides structured logging, performance metrics, error tracking,
    and supports both console and file output. It is designed to be used across all
    providers for consistent and informative logging.
    
    Why is this important?
    -----------------------------------
    Logging is essential for debugging, monitoring, and maintaining production systems.
    Structured logs make it easier to search and analyze logs in log management systems.
    Including context and metrics helps with root cause analysis and performance optimization.
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
        # Store the logger name for context.
        self.name = name
        # Create the logger instance.
        self.logger = logging.getLogger(name)
        # Set the logging level.
        self.logger.setLevel(level)
        
        # Use a default log format if none is provided.
        if not log_format:
            log_format = (
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(message)s - %(context)s'
            )
        
        # Create a formatter for log messages.
        formatter = logging.Formatter(log_format)
        
        # Add a console handler for output to stdout.
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Add a file handler with rotation if a log file is specified.
        if log_file:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Initialize metrics for error, warning, and request tracking.
        self.metrics = {
            "error_count": 0,
            "warning_count": 0,
            "total_requests": 0,
            "processing_times": []
        }
    
    def _format_context(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format context dictionary for logging.
        
        This method serializes the context dictionary to a JSON string, so it can be included
        in log messages. This makes logs more machine-readable and easier to parse.
        
        Args:
            context: Context dictionary to format
        
        Returns:
            Formatted context string (JSON)
        """
        if not context:
            return "{}"
        return json.dumps(context)
    
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """
        Get context from kwargs and add default fields.
        
        This method adds useful metadata (timestamp, process id) to the context for every log.
        This helps correlate logs across distributed systems and processes.
        
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
        
        Use this for general informational messages about application state or progress.
        
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
        
        Use this for detailed debugging information that is useful during development.
        
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
        
        Use this for situations that are not errors but may require attention.
        
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
        
        Use this for errors that do not stop the application but should be investigated.
        
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
        
        Use this for logging exceptions (with stack trace) when an error occurs.
        
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
        
        Use this for very serious errors that may require immediate attention.
        
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
        
        Use this for tracking custom metrics (e.g., API latency, queue size).
        
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
        
        Use this to measure how long operations take and track performance over time.
        
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
        
        Returns a dictionary of all tracked metrics (error count, warning count, timings, etc.).
        This is useful for monitoring and alerting.
        
        Returns:
            Dict[str, Any]: Current metrics
        """
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """
        Reset all tracked metrics to their initial state.
        
        Use this to clear metrics between test runs or after handling incidents.
        """
        self.metrics = {
            "error_count": 0,
            "warning_count": 0,
            "total_requests": 0,
            "processing_times": []
        }
    
    def log_request(self, action: str, **kwargs) -> None:
        """
        Log the start of an action or request.
        
        This is useful for tracing the flow of requests through the system.
        
        Args:
            action: Name of the action being executed
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
        Log the completion of an action or request.
        
        This is useful for tracking the outcome of requests and correlating with log_request.
        
        Args:
            action: Name of the action
            status: Result status (success, error, etc.)
            **kwargs: Additional context
        """
        context = self._get_context(action=action, status=status, **kwargs)
        self.logger.info(
            f"Response: {action} - {status}",
            extra={"context": self._format_context(context)}
        )
    
    def _handle_response(self, response: ProviderResponse) -> Dict[str, Any]:
        """
        Convert a ProviderResponse to a dictionary for logging or output.
        
        Args:
            response (ProviderResponse): The response object to convert
        
        Returns:
            Dict[str, Any]: The response as a dictionary
        """
        return response.model_dump()

    def performance_monitor(self, operation: str):
        """
        Decorator for measuring and logging the performance of a function.
        
        Use this to automatically log how long a function takes to execute.
        
        Args:
            operation: Name of the operation being measured
        
        Returns:
            Callable: Decorator that wraps the function
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
                    return self._handle_response(ProviderResponse(
                        status="error",
                        message=f"Error in {operation}",
                        data={"error": str(e)}
                    ))
            return wrapper
        return decorator 