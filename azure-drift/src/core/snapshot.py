"""Snapshot management module for Azure resource configuration snapshots."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from .db.mongodb import MongoDBManager

logger = logging.getLogger(__name__)

class SnapshotManager:
    """Manages Azure resource configuration snapshots."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize the snapshot manager.
        
        Args:
            db_manager: MongoDB connection manager
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("snapshots")

    async def save_snapshot(self, snapshot_data: Dict[str, Any]) -> str:
        """Save a configuration snapshot to MongoDB.
        
        Args:
            snapshot_data: The snapshot data to save
            
        Returns:
            str: The ID of the saved snapshot
        """
        snapshot_id = str(uuid.uuid4())
        snapshot_data["_id"] = snapshot_id
        snapshot_data["timestamp"] = datetime.utcnow().isoformat()
        
        await self.collection.insert_one(snapshot_data)
        logger.info(f"Saved snapshot {snapshot_id}")
        return snapshot_id

    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Load a snapshot from MongoDB.
        
        Args:
            snapshot_id: The ID of the snapshot to load
            
        Returns:
            Optional[Dict[str, Any]]: The loaded snapshot data or None if not found
        """
        try:
            snapshot = await self.collection.find_one({"_id": snapshot_id})
            return snapshot
        except Exception as e:
            logger.warning(f"Error loading snapshot {snapshot_id}: {e}")
            return None

    async def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot.
        
        Returns:
            Optional[Dict[str, Any]]: The latest snapshot data or None if no snapshots exist
        """
        try:
            snapshot = await self.collection.find_one(
                sort=[("timestamp", -1)]
            )
            return snapshot
        except Exception as e:
            logger.error(f"Error getting latest snapshot: {e}")
            return None

    async def list_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent snapshots.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List[Dict[str, Any]]: List of snapshot metadata
        """
        try:
            cursor = self.collection.find(
                {},
                {"_id": 1, "timestamp": 1, "resources": 1}
            ).sort("timestamp", -1).limit(limit)
            
            snapshots = []
            async for doc in cursor:
                snapshots.append({
                    "id": doc["_id"],
                    "timestamp": doc["timestamp"],
                    "resource_count": sum(len(resources) for resources in doc["resources"].values())
                })
            return snapshots
        except Exception as e:
            logger.error(f"Error listing snapshots: {e}")
            return []

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot.
        
        Args:
            snapshot_id: The ID of the snapshot to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            result = await self.collection.delete_one({"_id": snapshot_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted snapshot {snapshot_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting snapshot {snapshot_id}: {e}")
            return False

    async def cleanup_old_snapshots(self, days: int = 30) -> int:
        """Remove snapshots older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            int: Number of snapshots deleted
        """
        try:
            cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            result = await self.collection.delete_many({
                "timestamp": {"$lt": datetime.fromtimestamp(cutoff).isoformat()}
            })
            count = result.deleted_count
            logger.info(f"Cleaned up {count} old snapshots")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up old snapshots: {e}")
            return 0 