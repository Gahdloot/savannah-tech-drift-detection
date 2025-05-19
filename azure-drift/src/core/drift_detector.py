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

logger = logging.getLogger(__name__)

class DriftDetector:
    """Main class for detecting configuration drift in Azure resources."""

    def __init__(self, subscription_id: str, resource_group: str,
                 tenant_id: Optional[str] = None, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None, data_dir: str = "data"):
        """Initialize the drift detector.
        
        Args:
            subscription_id: Azure subscription ID
            resource_group: Azure resource group name
            tenant_id: Azure tenant ID (optional)
            client_id: Azure client ID (optional)
            client_secret: Azure client secret (optional)
            data_dir: Directory for storing snapshots and reports
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
        self.snapshot_manager = SnapshotManager(data_dir)
        self.drift_report_manager = DriftReportManager(data_dir)
        self.drift_analyzer = DriftAnalyzer()
        self.resource_group = resource_group

    def collect_configuration(self) -> Dict[str, Any]:
        """Collect current configuration of Azure resources.
        
        Returns:
            Dict[str, Any]: Configuration snapshot
        """
        try:
            # Collect all resource configurations
            resources = self.resource_collector.collect_all_resources()
            
            # Create snapshot
            snapshot = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "subscription_id": self.azure_client.subscription_id,
                "resource_group": self.resource_group,
                "resources": resources
            }
            
            # Save snapshot
            self.snapshot_manager.save_snapshot(snapshot)
            
            return snapshot
        except Exception as e:
            logger.error(f"Error collecting configuration: {e}")
            raise

    def detect_drift(self) -> Dict[str, Any]:
        """Detect drift between current and previous configurations.
        
        Returns:
            Dict[str, Any]: Drift detection report
        """
        try:
            # Get current configuration
            current_snapshot = self.collect_configuration()
            
            # Get previous snapshot
            previous_snapshot = self.snapshot_manager.get_latest_snapshot()
            if not previous_snapshot:
                return {
                    "has_drift": False,
                    "message": "No previous snapshot available for comparison"
                }
            
            # Analyze drift
            drift_report = self.drift_analyzer.analyze_snapshot_drift(
                current_snapshot,
                previous_snapshot
            )
            
            # Save drift report
            if drift_report.get("has_drift"):
                self.drift_report_manager.save_report(drift_report)
            
            return drift_report
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            raise

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the latest configuration snapshot.
        
        Returns:
            Optional[Dict[str, Any]]: Latest snapshot or None if not found
        """
        return self.snapshot_manager.get_latest_snapshot()

    def get_latest_drift_report(self) -> Optional[Dict[str, Any]]:
        """Get the latest drift detection report.
        
        Returns:
            Optional[Dict[str, Any]]: Latest drift report or None if not found
        """
        return self.drift_report_manager.get_latest_report()

    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old snapshots and drift reports.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Dict[str, int]: Number of files deleted by type
        """
        try:
            snapshots_deleted = self.snapshot_manager.cleanup_old_snapshots(days)
            reports_deleted = self.drift_report_manager.cleanup_old_reports(days)
            
            return {
                "snapshots_deleted": snapshots_deleted,
                "reports_deleted": reports_deleted
            }
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise

    def get_drift_summary(self) -> Dict[str, Any]:
        """Get a summary of the latest drift detection.
        
        Returns:
            Dict[str, Any]: Drift summary
        """
        try:
            latest_report = self.get_latest_drift_report()
            if not latest_report:
                return {
                    "has_drift": False,
                    "message": "No drift reports available"
                }
            
            return self.drift_analyzer.get_drift_summary(latest_report)
        except Exception as e:
            logger.error(f"Error getting drift summary: {e}")
            raise

    def close(self):
        """Clean up resources."""
        try:
            self.azure_client.close()
        except Exception as e:
            logger.error(f"Error closing Azure client: {e}") 