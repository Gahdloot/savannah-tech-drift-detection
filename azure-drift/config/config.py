import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DRIFT_DIR = DATA_DIR / "drift"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
SNAPSHOTS_DIR.mkdir(exist_ok=True)
DRIFT_DIR.mkdir(exist_ok=True)

# Azure configuration
AZURE_CONFIG = {
    "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
    "tenant_id": os.getenv("AZURE_TENANT_ID"),
    "client_id": os.getenv("AZURE_CLIENT_ID"),
    "client_secret": os.getenv("AZURE_CLIENT_SECRET"),
    "resource_group": os.getenv("AZURE_RESOURCE_GROUP")
}

# API configuration
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "8000")),
    "debug": os.getenv("API_DEBUG", "False").lower() == "true",
    "reload": os.getenv("API_RELOAD", "False").lower() == "true"
}

# Drift detection configuration
DRIFT_CONFIG = {
    "collection_interval": int(os.getenv("DRIFT_COLLECTION_INTERVAL", "1800")),  # 30 minutes
    "retention_days": int(os.getenv("DRIFT_RETENTION_DAYS", "30")),
    "max_snapshots": int(os.getenv("DRIFT_MAX_SNAPSHOTS", "1000")),
    "max_drift_reports": int(os.getenv("DRIFT_MAX_REPORTS", "1000"))
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(DATA_DIR / "drift_detection.log")
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}

# Security configuration
SECURITY_CONFIG = {
    "allowed_origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
    "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
    "allowed_headers": ["*"],
    "max_requests_per_minute": int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
}

def get_config() -> Dict[str, Any]:
    """Get the complete configuration."""
    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "snapshots_dir": str(SNAPSHOTS_DIR),
        "drift_dir": str(DRIFT_DIR),
        "azure": AZURE_CONFIG,
        "api": API_CONFIG,
        "drift": DRIFT_CONFIG,
        "logging": LOGGING_CONFIG,
        "security": SECURITY_CONFIG
    } 