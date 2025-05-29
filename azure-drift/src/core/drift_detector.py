"""Main drift detection module for Azure resources."""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid
from .azure_client import AzureClientManager
from .resource_collector import ResourceCollector
from .snapshot import SnapshotManager
from .drift_report import DriftReportManager
from .drift_analyzer import DriftAnalyzer
from .db.mongodb import MongoDBManager

logger = logging.getLogger(__name__)

class DriftDetector:
    """Main class for detecting configuration drift in Azure resources."""

    def __init__(self, subscription_id: str, resource_group: str,
                 tenant_id: Optional[str] = None, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None, db_manager: Optional[MongoDBManager] = None):
        """Initialize the drift detector.
        
        Args:
            subscription_id: Azure subscription ID
            resource_group: Azure resource group name
            tenant_id: Azure tenant ID (optional)
            client_id: Azure client ID (optional)
            client_secret: Azure client secret (optional)
            db_manager: MongoDB connection manager
        """
        self.azure_client = AzureClientManager(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        self.resource_collector = ResourceCollector(
            subscription_id=subscription_id,
            resource_group=resource_group
        )
        self.snapshot_manager = SnapshotManager(db_manager)
        self.drift_report_manager = DriftReportManager(db_manager)
        self.drift_analyzer = DriftAnalyzer()
        self.resource_group = resource_group

    async def collect_configuration(self) -> Dict[str, Any]:
        """Collect current configuration of Azure resources.
        
        Returns:
            Dict[str, Any]: Configuration snapshot
        """
        try:
            # Collect all resource configurations
            resources = self.resource_collector.collect_resources()
            
            # Create snapshot
            snapshot = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "subscription_id": self.azure_client.subscription_id,
                "resource_group": self.resource_group,
                "resources": resources
            }
            
            return snapshot
        except Exception as e:
            logger.error(f"Error collecting configuration: {e}")
            raise

    async def save_snapshot(self, snapshot_data: Dict[str, Any]) -> str:
        """Save a configuration snapshot.
        
        Args:
            snapshot_data: The snapshot data to save
            
        Returns:
            str: The ID of the saved snapshot
        """
        return await self.snapshot_manager.save_snapshot(snapshot_data)

    async def detect_drift(self, current_config: Dict[str, Any], previous_config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect drift between current and previous configurations.
        
        Args:
            current_config: Current configuration snapshot
            previous_config: Previous configuration snapshot
            
        Returns:
            Dict[str, Any]: Drift detection report
        """
        try:
            # Analyze drift
            drift_report = self.drift_analyzer.analyze_snapshot_drift(
                current_config,
                previous_config
            )
            
            # Save drift report
            if drift_report.get("has_drift"):
                await self.drift_report_manager.save_report(drift_report)
            
            return drift_report
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            raise

    async def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the latest configuration snapshot.
        
        Returns:
            Optional[Dict[str, Any]]: Latest snapshot or None if not found
        """
        return await self.snapshot_manager.get_latest_snapshot()

    async def get_latest_drift_report(self) -> Optional[Dict[str, Any]]:
        """Get the latest drift detection report.
        
        Returns:
            Optional[Dict[str, Any]]: Latest drift report or None if not found
        """
        return await self.drift_report_manager.get_latest_report()

    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old snapshots and drift reports.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Dict[str, int]: Number of files deleted by type
        """
        try:
            snapshots_deleted = await self.snapshot_manager.cleanup_old_snapshots(days)
            reports_deleted = await self.drift_report_manager.cleanup_old_reports(days)
            
            return {
                "snapshots_deleted": snapshots_deleted,
                "reports_deleted": reports_deleted
            }
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise

    async def get_drift_summary(self) -> Dict[str, Any]:
        """Get a summary of the latest drift detection.
        
        Returns:
            Dict[str, Any]: Drift summary
        """
        try:
            latest_report = await self.get_latest_drift_report()
            if not latest_report:
                return {
                    "has_drift": False,
                    "message": "No drift reports available"
                }
            
            return await self.drift_report_manager.get_drift_summary(latest_report["_id"])
        except Exception as e:
            logger.error(f"Error getting drift summary: {e}")
            raise

    async def close(self):
        """Clean up resources."""
        try:
            await self.azure_client.close()
        except Exception as e:
            logger.error(f"Error closing Azure client: {e}") 