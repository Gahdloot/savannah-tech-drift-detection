"""Drift report management module for Azure resource configuration drift detection."""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class DriftReportManager:
    """Manages drift detection reports."""

    def __init__(self, data_dir: str):
        """Initialize the drift report manager.
        
        Args:
            data_dir: Base directory for storing drift reports
        """
        self.data_dir = data_dir
        self.drift_dir = os.path.join(data_dir, "drift")
        os.makedirs(self.drift_dir, exist_ok=True)

    def save_report(self, report_data: Dict[str, Any]) -> str:
        """Save a drift report to disk.
        
        Args:
            report_data: The drift report data to save
            
        Returns:
            str: The ID of the saved report
        """
        report_id = str(uuid.uuid4())
        report_data["id"] = report_id
        report_data["timestamp"] = datetime.utcnow().isoformat()
        
        file_path = os.path.join(self.drift_dir, f"{report_id}.json")
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Saved drift report {report_id}")
        return report_id

    def load_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Load a drift report from disk.
        
        Args:
            report_id: The ID of the report to load
            
        Returns:
            Optional[Dict[str, Any]]: The loaded report data or None if not found
        """
        file_path = os.path.join(self.drift_dir, f"{report_id}.json")
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Drift report {report_id} not found")
            return None

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recent drift report.
        
        Returns:
            Optional[Dict[str, Any]]: The latest report data or None if no reports exist
        """
        try:
            reports = [f for f in os.listdir(self.drift_dir) if f.endswith('.json')]
            if not reports:
                return None
            
            # Sort by timestamp in filename
            latest_file = max(reports, key=lambda x: os.path.getctime(os.path.join(self.drift_dir, x)))
            return self.load_report(latest_file.replace('.json', ''))
        except Exception as e:
            logger.error(f"Error getting latest drift report: {e}")
            return None

    def list_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent drift reports.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List[Dict[str, Any]]: List of report metadata
        """
        try:
            reports = []
            for filename in os.listdir(self.drift_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.drift_dir, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    reports.append({
                        "id": data["id"],
                        "timestamp": data["timestamp"],
                        "snapshot_id": data["snapshot_id"],
                        "drift_count": len(data["drifts"])
                    })
            
            # Sort by timestamp descending
            reports.sort(key=lambda x: x["timestamp"], reverse=True)
            return reports[:limit]
        except Exception as e:
            logger.error(f"Error listing drift reports: {e}")
            return []

    def delete_report(self, report_id: str) -> bool:
        """Delete a drift report.
        
        Args:
            report_id: The ID of the report to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            file_path = os.path.join(self.drift_dir, f"{report_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted drift report {report_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting drift report {report_id}: {e}")
            return False

    def cleanup_old_reports(self, days: int = 30) -> int:
        """Remove reports older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            int: Number of reports deleted
        """
        try:
            count = 0
            cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            
            for filename in os.listdir(self.drift_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.drift_dir, filename)
                if os.path.getctime(file_path) < cutoff:
                    os.remove(file_path)
                    count += 1
            
            logger.info(f"Cleaned up {count} old drift reports")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up old drift reports: {e}")
            return 0

    def get_drift_summary(self, report_id: str) -> Dict[str, Any]:
        """Get a summary of drift changes from a report.
        
        Args:
            report_id: The ID of the report to summarize
            
        Returns:
            Dict[str, Any]: Summary of drift changes
        """
        report = self.load_report(report_id)
        if not report:
            return {}
        
        summary = {
            "total_drifts": len(report["drifts"]),
            "resource_types": {},
            "change_types": {}
        }
        
        for drift in report["drifts"]:
            # Count by resource type
            resource_type = drift["resource_type"]
            summary["resource_types"][resource_type] = summary["resource_types"].get(resource_type, 0) + 1
            
            # Count by change type
            for change in drift["changes"]:
                change_type = change["property"].split('.')[-1]
                summary["change_types"][change_type] = summary["change_types"].get(change_type, 0) + 1
        
        return summary 