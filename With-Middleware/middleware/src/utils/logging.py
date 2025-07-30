"""
Logging configuration for the Salesforce Data Cloud Middleware.

This module sets up structured logging with correlation IDs,
proper formatting, and integration with FastAPI.
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    enable_console: bool = True,
    enable_file: bool = False,
    log_file_path: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: The log format (json, text)
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging
        log_file_path: Path to the log file (if file logging is enabled)
    """
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        handlers=[]
    )
    
    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        logging.getLogger().addHandler(console_handler)
    
    # Add file handler
    if enable_file and log_file_path:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logging.getLogger().addHandler(file_handler)
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON formatter for structured logging
    if log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: The logger name (usually __name__)
        
    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


def add_correlation_id(correlation_id: str) -> None:
    """
    Add correlation ID to the current logging context.
    
    Args:
        correlation_id: The correlation ID to add
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def log_request(
    logger: structlog.BoundLogger,
    method: str,
    url: str,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log an incoming HTTP request.
    
    Args:
        logger: The logger instance
        method: HTTP method
        url: Request URL
        client_ip: Client IP address
        user_agent: User agent string
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "http_request",
        "method": method,
        "url": url,
    }
    
    if client_ip:
        log_data["client_ip"] = client_ip
    if user_agent:
        log_data["user_agent"] = user_agent
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    logger.info(**log_data)


def log_response(
    logger: structlog.BoundLogger,
    method: str,
    url: str,
    status_code: int,
    response_time: float,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log an HTTP response.
    
    Args:
        logger: The logger instance
        method: HTTP method
        url: Request URL
        status_code: HTTP status code
        response_time: Response time in seconds
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "http_response",
        "method": method,
        "url": url,
        "status_code": status_code,
        "response_time": response_time,
    }
    
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    logger.info(**log_data)


def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log an error with structured context.
    
    Args:
        logger: The logger instance
        error: The exception that occurred
        context: Additional context information
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        log_data.update(context)
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    logger.error(**log_data, exc_info=True)


def log_salesforce_request(
    logger: structlog.BoundLogger,
    operation: str,
    object_type: str,
    query: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log a Salesforce API request.
    
    Args:
        logger: The logger instance
        operation: The operation being performed
        object_type: The Salesforce object type
        query: The SOQL/SQL query (if applicable)
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "salesforce_request",
        "operation": operation,
        "object_type": object_type,
    }
    
    if query:
        log_data["query"] = query
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    logger.info(**log_data)


def log_salesforce_response(
    logger: structlog.BoundLogger,
    operation: str,
    object_type: str,
    record_count: int,
    response_time: float,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log a Salesforce API response.
    
    Args:
        logger: The logger instance
        operation: The operation that was performed
        object_type: The Salesforce object type
        record_count: Number of records returned
        response_time: Response time in seconds
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "salesforce_response",
        "operation": operation,
        "object_type": object_type,
        "record_count": record_count,
        "response_time": response_time,
    }
    
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    logger.info(**log_data)


def log_cache_hit(
    logger: structlog.BoundLogger,
    cache_key: str,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log a cache hit.
    
    Args:
        logger: The logger instance
        cache_key: The cache key that was hit
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "cache_hit",
        "cache_key": cache_key,
    }
    
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    logger.debug(**log_data)


def log_cache_miss(
    logger: structlog.BoundLogger,
    cache_key: str,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log a cache miss.
    
    Args:
        logger: The logger instance
        cache_key: The cache key that was missed
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "cache_miss",
        "cache_key": cache_key,
    }
    
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    logger.debug(**log_data)


def log_rate_limit(
    logger: structlog.BoundLogger,
    client_ip: str,
    limit_exceeded: bool,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Log rate limiting events.
    
    Args:
        logger: The logger instance
        client_ip: The client IP address
        limit_exceeded: Whether the rate limit was exceeded
        correlation_id: Request correlation ID
    """
    log_data = {
        "event": "rate_limit",
        "client_ip": client_ip,
        "limit_exceeded": limit_exceeded,
    }
    
    if correlation_id:
        log_data["correlation_id"] = correlation_id
    
    if limit_exceeded:
        logger.warning(**log_data)
    else:
        logger.debug(**log_data) 