"""Error handling module for Azure drift detection."""

from typing import Dict, Any, Optional, Type
import logging
import traceback
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class DriftDetectionError(Exception):
    """Base exception for drift detection errors."""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.error_code = error_code
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)

class AzureConnectionError(DriftDetectionError):
    """Exception for Azure connection errors."""
    def __init__(self, message: str):
        super().__init__(message, "AZURE_CONNECTION_ERROR")

class ResourceCollectionError(DriftDetectionError):
    """Exception for resource collection errors."""
    def __init__(self, message: str, resource_type: Optional[str] = None):
        self.resource_type = resource_type
        super().__init__(message, "RESOURCE_COLLECTION_ERROR")

class DriftAnalysisError(DriftDetectionError):
    """Exception for drift analysis errors."""
    def __init__(self, message: str):
        super().__init__(message, "DRIFT_ANALYSIS_ERROR")

class ConfigurationError(DriftDetectionError):
    """Exception for configuration errors."""
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")

class StorageError(DriftDetectionError):
    """Exception for storage errors."""
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")

class RateLimitError(DriftDetectionError):
    """Exception for rate limiting errors."""
    def __init__(self, message: str):
        super().__init__(message, "RATE_LIMIT_ERROR")

class AuthenticationError(DriftDetectionError):
    """Exception for authentication errors."""
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR")

class AuthorizationError(DriftDetectionError):
    """Exception for authorization errors."""
    def __init__(self, message: str):
        super().__init__(message, "AUTHORIZATION_ERROR")


class ErrorHandler:
    """Handles and logs errors in the drift detection service."""

    def __init__(self, error_log_dir: str = "logs/errors"):
        """Initialize the error handler.
        
        Args:
            error_log_dir: Directory for error logs
        """
        self.error_log_dir = Path(error_log_dir)
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        self.error_log_file = self.error_log_dir / "error_log.json"
        self.error_counts: Dict[str, int] = {}
        self._load_error_counts()

    def _load_error_counts(self) -> None:
        """Load error counts from file."""
        try:
            if self.error_log_file.exists():
                with open(self.error_log_file, 'r') as f:
                    self.error_counts = json.load(f)
        except Exception as e:
            logger.error(f"Error loading error counts: {e}")
            self.error_counts = {}

    def _save_error_counts(self) -> None:
        """Save error counts to file."""
        try:
            with open(self.error_log_file, 'w') as f:
                json.dump(self.error_counts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving error counts: {e}")

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle and log an error.
        
        Args:
            error: Exception to handle
            context: Additional context information
            
        Returns:
            Dict[str, Any]: Error details
        """
        error_details = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
            "traceback": traceback.format_exc()
        }

        if isinstance(error, DriftDetectionError):
            error_details["error_code"] = error.error_code
            if hasattr(error, "resource_type"):
                error_details["resource_type"] = error.resource_type

        if context:
            error_details["context"] = context

        # Update error counts
        error_type = error_details["error_type"]
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self._save_error_counts()

        # Log error
        logger.error(
            f"Error: {error_details['error_type']} - {error_details['message']}",
            extra={"error_details": error_details}
        )

        return error_details

    def get_error_counts(self) -> Dict[str, int]:
        """Get current error counts.
        
        Returns:
            Dict[str, int]: Error counts by type
        """
        return self.error_counts.copy()

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error statistics.
        
        Returns:
            Dict[str, Any]: Error statistics
        """
        total_errors = sum(self.error_counts.values())
        return {
            "total_errors": total_errors,
            "error_counts": self.error_counts,
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }

    def clear_error_counts(self) -> None:
        """Clear all error counts."""
        self.error_counts.clear()
        self._save_error_counts()


class ErrorMiddleware:
    """Middleware for handling errors in API requests."""

    def __init__(self, error_handler: ErrorHandler):
        """Initialize the error middleware.
        
        Args:
            error_handler: Error handler instance
        """
        self.error_handler = error_handler

    def handle_request_error(self, error: Exception, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error in API request.
        
        Args:
            error: Exception to handle
            request_info: Request information
            
        Returns:
            Dict[str, Any]: Error response
        """
        error_details = self.error_handler.handle_error(error, request_info)
        
        if isinstance(error, RateLimitError):
            status_code = 429
        elif isinstance(error, AuthenticationError):
            status_code = 401
        elif isinstance(error, AuthorizationError):
            status_code = 403
        elif isinstance(error, ConfigurationError):
            status_code = 500
        else:
            status_code = 500

        return {
            "status_code": status_code,
            "error": {
                "code": error_details.get("error_code", "INTERNAL_ERROR"),
                "message": error_details["message"],
                "type": error_details["error_type"]
            }
        }


def handle_exceptions(func):
    """Decorator for handling exceptions in functions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DriftDetectionError as e:
            logger.error(f"Drift detection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise DriftDetectionError(str(e))
    return wrapper 