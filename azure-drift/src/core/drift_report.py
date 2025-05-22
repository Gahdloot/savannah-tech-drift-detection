"""Drift report management module for Azure resource configuration drift detection."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from .db.mongodb import MongoDBManager

logger = logging.getLogger(__name__)

class DriftReportManager:
    """Manages drift detection reports."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize the drift report manager.
        
        Args:
            db_manager: MongoDB connection manager
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("drift_reports")

    async def save_report(self, report_data: Dict[str, Any]) -> str:
        """Save a drift report to MongoDB.
        
        Args:
            report_data: The drift report data to save
            
        Returns:
            str: The ID of the saved report
        """
        report_id = str(uuid.uuid4())
        report_data["_id"] = report_id
        report_data["timestamp"] = datetime.utcnow().isoformat()
        
        await self.collection.insert_one(report_data)
        logger.info(f"Saved drift report {report_id}")
        return report_id

    async def load_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Load a drift report from MongoDB.
        
        Args:
            report_id: The ID of the report to load
            
        Returns:
            Optional[Dict[str, Any]]: The loaded report data or None if not found
        """
        try:
            report = await self.collection.find_one({"_id": report_id})
            return report
        except Exception as e:
            logger.warning(f"Error loading drift report {report_id}: {e}")
            return None

    async def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recent drift report.
        
        Returns:
            Optional[Dict[str, Any]]: The latest report data or None if no reports exist
        """
        try:
            report = await self.collection.find_one(
                sort=[("timestamp", -1)]
            )
            return report
        except Exception as e:
            logger.error(f"Error getting latest drift report: {e}")
            return None

    async def list_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent drift reports.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List[Dict[str, Any]]: List of report metadata
        """
        try:
            cursor = self.collection.find(
                {},
                {"_id": 1, "timestamp": 1, "snapshot_id": 1, "drifts": 1}
            ).sort("timestamp", -1).limit(limit)
            
            reports = []
            async for doc in cursor:
                reports.append({
                    "id": doc["_id"],
                    "timestamp": doc["timestamp"],
                    "snapshot_id": doc["snapshot_id"],
                    "drift_count": len(doc["drifts"])
                })
            return reports
        except Exception as e:
            logger.error(f"Error listing drift reports: {e}")
            return []

    async def delete_report(self, report_id: str) -> bool:
        """Delete a drift report.
        
        Args:
            report_id: The ID of the report to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            result = await self.collection.delete_one({"_id": report_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted drift report {report_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting drift report {report_id}: {e}")
            return False

    async def cleanup_old_reports(self, days: int = 30) -> int:
        """Remove reports older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            int: Number of reports deleted
        """
        try:
            cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            result = await self.collection.delete_many({
                "timestamp": {"$lt": datetime.fromtimestamp(cutoff).isoformat()}
            })
            count = result.deleted_count
            logger.info(f"Cleaned up {count} old drift reports")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up old drift reports: {e}")
            return 0

    async def get_drift_summary(self, report_id: str) -> Dict[str, Any]:
        """Get a summary of drift changes from a report.
        
        Args:
            report_id: The ID of the report to summarize
            
        Returns:
            Dict[str, Any]: Summary of drift changes
        """
        report = await self.load_report(report_id)
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