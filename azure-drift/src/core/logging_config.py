"""Logging configuration module for Azure drift detection."""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from datetime import datetime

class LogConfig:
    """Configures logging for the drift detection service."""

    def __init__(self, log_dir: str = "logs", config: Optional[Dict[str, Any]] = None):
        """Initialize the logging configuration.
        
        Args:
            log_dir: Directory for log files
            config: Logging configuration (optional)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or self._default_config()
        self._setup_logging()

    def _default_config(self) -> Dict[str, Any]:
        """Get default logging configuration.
        
        Returns:
            Dict[str, Any]: Default logging configuration
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "json": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "standard",
                    "filename": str(self.log_dir / "drift_detection.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                },
                "json_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "json",
                    "filename": str(self.log_dir / "drift_detection.json"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "": {  # Root logger
                    "handlers": ["console", "file", "json_file"],
                    "level": "INFO",
                    "propagate": True
                },
                "azure": {
                    "handlers": ["file", "json_file"],
                    "level": "WARNING",
                    "propagate": False
                },
                "drift_detection": {
                    "handlers": ["console", "file", "json_file"],
                    "level": "DEBUG",
                    "propagate": False
                }
            }
        }

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        try:
            # Configure root logger
            logging.basicConfig(
                level=self.config["loggers"][""]["level"],
                format=self.config["formatters"]["standard"]["format"],
                datefmt=self.config["formatters"]["standard"]["datefmt"]
            )

            # Configure handlers
            for handler_name, handler_config in self.config["handlers"].items():
                handler_class = self._get_handler_class(handler_config["class"])
                handler = handler_class(**self._get_handler_args(handler_config))
                handler.setLevel(handler_config["level"])
                handler.setFormatter(self._get_formatter(handler_config["formatter"]))

            # Configure loggers
            for logger_name, logger_config in self.config["loggers"].items():
                logger = logging.getLogger(logger_name)
                logger.setLevel(logger_config["level"])
                logger.propagate = logger_config.get("propagate", True)

                # Add handlers
                for handler_name in logger_config.get("handlers", []):
                    handler_config = self.config["handlers"][handler_name]
                    handler_class = self._get_handler_class(handler_config["class"])
                    handler = handler_class(**self._get_handler_args(handler_config))
                    handler.setLevel(handler_config["level"])
                    handler.setFormatter(self._get_formatter(handler_config["formatter"]))
                    logger.addHandler(handler)

        except Exception as e:
            print(f"Error setting up logging: {e}", file=sys.stderr)
            raise

    def _get_handler_class(self, class_name: str) -> type:
        """Get handler class from class name.
        
        Args:
            class_name: Handler class name
            
        Returns:
            type: Handler class
        """
        if class_name == "logging.StreamHandler":
            return logging.StreamHandler
        elif class_name == "logging.handlers.RotatingFileHandler":
            return logging.handlers.RotatingFileHandler
        elif class_name == "logging.handlers.TimedRotatingFileHandler":
            return logging.handlers.TimedRotatingFileHandler
        else:
            raise ValueError(f"Unsupported handler class: {class_name}")

    def _get_handler_args(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get handler arguments from config.
        
        Args:
            config: Handler configuration
            
        Returns:
            Dict[str, Any]: Handler arguments
        """
        args = {}
        if "filename" in config:
            args["filename"] = config["filename"]
        if "maxBytes" in config:
            args["maxBytes"] = config["maxBytes"]
        if "backupCount" in config:
            args["backupCount"] = config["backupCount"]
        if "stream" in config:
            args["stream"] = eval(config["stream"])
        return args

    def _get_formatter(self, formatter_name: str) -> logging.Formatter:
        """Get formatter from name.
        
        Args:
            formatter_name: Formatter name
            
        Returns:
            logging.Formatter: Logging formatter
        """
        formatter_config = self.config["formatters"][formatter_name]
        if formatter_name == "json":
            from pythonjsonlogger import jsonlogger
            return jsonlogger.JsonFormatter(formatter_config["format"])
        else:
            return logging.Formatter(
                formatter_config["format"],
                datefmt=formatter_config.get("datefmt")
            )

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name.
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Configured logger
        """
        return logging.getLogger(name)

    def set_level(self, logger_name: str, level: str) -> None:
        """Set logging level for a logger.
        
        Args:
            logger_name: Logger name
            level: Logging level
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    def add_handler(self, logger_name: str, handler: logging.Handler) -> None:
        """Add a handler to a logger.
        
        Args:
            logger_name: Logger name
            handler: Logging handler
        """
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)

    def remove_handler(self, logger_name: str, handler: logging.Handler) -> None:
        """Remove a handler from a logger.
        
        Args:
            logger_name: Logger name
            handler: Logging handler
        """
        logger = logging.getLogger(logger_name)
        logger.removeHandler(handler)

    def rotate_logs(self) -> None:
        """Rotate log files."""
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()

    def cleanup_old_logs(self, days: int = 30) -> None:
        """Clean up old log files.
        
        Args:
            days: Number of days to keep logs
        """
        try:
            current_time = datetime.now()
            for log_file in self.log_dir.glob("*.log*"):
                if (current_time - datetime.fromtimestamp(log_file.stat().st_mtime)).days > days:
                    log_file.unlink()
        except Exception as e:
            print(f"Error cleaning up old logs: {e}", file=sys.stderr) 