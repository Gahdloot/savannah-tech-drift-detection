"""Configuration management module for Azure drift detection."""

from typing import Dict, Any, Optional
import logging
import json
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration settings for the drift detection service."""

    def __init__(self, config_dir: str = "config"):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "azure": {
                "subscription_id": "",
                "tenant_id": "",
                "client_id": "",
                "client_secret": ""
            },
            "drift_detection": {
                "enabled_resource_types": [
                    "Microsoft.Compute/virtualMachines",
                    "Microsoft.Network/networkInterfaces",
                    "Microsoft.Storage/storageAccounts",
                    "Microsoft.KeyVault/vaults",
                    "Microsoft.Web/sites",
                    "Microsoft.Sql/servers",
                    "Microsoft.CosmosDB/databaseAccounts",
                    "Microsoft.Cache/Redis"
                ],
                "ignored_properties": [
                    "tags",
                    "lastModified",
                    "lastModifiedBy",
                    "lastModifiedByType",
                    "lastModifiedAt"
                ],
                "severity_thresholds": {
                    "high": ["security", "encryption", "authentication"],
                    "medium": ["size", "capacity", "performance"],
                    "low": ["tags", "description", "metadata"]
                }
            },
            "storage": {
                "data_dir": "data",
                "retention_days": 30,
                "max_snapshots": 100,
                "max_reports": 100
            },
            "monitoring": {
                "enabled": True,
                "log_level": "INFO",
                "metrics_enabled": True,
                "alert_threshold": {
                    "high_severity_changes": 5,
                    "medium_severity_changes": 10,
                    "low_severity_changes": 20
                }
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "cors_origins": ["*"],
                "rate_limit": {
                    "requests_per_minute": 60,
                    "burst_size": 10
                }
            }
        }
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default.
        
        Returns:
            Dict[str, Any]: Configuration settings
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with default config to ensure all settings exist
                return self._merge_configs(self.default_config, config)
            else:
                # Create default config file
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self.default_config

    def _merge_configs(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """Merge custom configuration with default settings.
        
        Args:
            default: Default configuration
            custom: Custom configuration
            
        Returns:
            Dict[str, Any]: Merged configuration
        """
        merged = default.copy()
        for key, value in custom.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Dict[str, Any]: Current configuration
        """
        return self.config

    def get_azure_config(self) -> Dict[str, str]:
        """Get Azure configuration settings.
        
        Returns:
            Dict[str, str]: Azure configuration
        """
        return self.config["azure"]

    def get_drift_config(self) -> Dict[str, Any]:
        """Get drift detection configuration.
        
        Returns:
            Dict[str, Any]: Drift detection settings
        """
        return self.config["drift_detection"]

    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration.
        
        Returns:
            Dict[str, Any]: Storage settings
        """
        return self.config["storage"]

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration.
        
        Returns:
            Dict[str, Any]: Monitoring settings
        """
        return self.config["monitoring"]

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration.
        
        Returns:
            Dict[str, Any]: API settings
        """
        return self.config["api"]

    def update_config(self, section: str, settings: Dict[str, Any]) -> None:
        """Update a specific configuration section.
        
        Args:
            section: Configuration section to update
            settings: New settings for the section
        """
        if section not in self.config:
            raise ValueError(f"Invalid configuration section: {section}")
        
        self.config[section].update(settings)
        self.save_config(self.config)

    def validate_config(self) -> bool:
        """Validate the current configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Check required Azure settings
            azure_config = self.get_azure_config()
            if not azure_config["subscription_id"]:
                logger.error("Missing Azure subscription ID")
                return False
            
            # Check drift detection settings
            drift_config = self.get_drift_config()
            if not drift_config["enabled_resource_types"]:
                logger.error("No enabled resource types specified")
                return False
            
            # Check storage settings
            storage_config = self.get_storage_config()
            if storage_config["retention_days"] < 1:
                logger.error("Invalid retention period")
                return False
            
            # Check monitoring settings
            monitoring_config = self.get_monitoring_config()
            if monitoring_config["enabled"] and not monitoring_config["log_level"]:
                logger.error("Missing log level for monitoring")
                return False
            
            # Check API settings
            api_config = self.get_api_config()
            if not isinstance(api_config["port"], int) or api_config["port"] < 1:
                logger.error("Invalid API port")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return False

    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        try:
            # Azure settings
            self.config["azure"]["subscription_id"] = os.getenv("AZURE_SUBSCRIPTION_ID", "")
            self.config["azure"]["tenant_id"] = os.getenv("AZURE_TENANT_ID", "")
            self.config["azure"]["client_id"] = os.getenv("AZURE_CLIENT_ID", "")
            self.config["azure"]["client_secret"] = os.getenv("AZURE_CLIENT_SECRET", "")
            
            # Storage settings
            data_dir = os.getenv("DATA_DIR")
            if data_dir:
                self.config["storage"]["data_dir"] = data_dir
            
            # API settings
            api_port = os.getenv("API_PORT")
            if api_port:
                self.config["api"]["port"] = int(api_port)
            
            # Save updated configuration
            self.save_config(self.config)
        except Exception as e:
            logger.error(f"Error loading configuration from environment: {e}")
            raise 