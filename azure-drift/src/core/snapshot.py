"""Snapshot management module for Azure resource configuration snapshots."""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SnapshotManager:
    """Manages Azure resource configuration snapshots."""

    def __init__(self, data_dir: str):
        """Initialize the snapshot manager.
        
        Args:
            data_dir: Base directory for storing snapshots
        """
        self.data_dir = data_dir
        self.snapshots_dir = os.path.join(data_dir, "snapshots")
        os.makedirs(self.snapshots_dir, exist_ok=True)

    def save_snapshot(self, snapshot_data: Dict[str, Any]) -> str:
        """Save a configuration snapshot to disk.
        
        Args:
            snapshot_data: The snapshot data to save
            
        Returns:
            str: The ID of the saved snapshot
        """
        snapshot_id = str(uuid.uuid4())
        snapshot_data["id"] = snapshot_id
        snapshot_data["timestamp"] = datetime.utcnow().isoformat()
        
        file_path = os.path.join(self.snapshots_dir, f"{snapshot_id}.json")
        with open(file_path, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.info(f"Saved snapshot {snapshot_id}")
        return snapshot_id

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Load a snapshot from disk.
        
        Args:
            snapshot_id: The ID of the snapshot to load
            
        Returns:
            Optional[Dict[str, Any]]: The loaded snapshot data or None if not found
        """
        file_path = os.path.join(self.snapshots_dir, f"{snapshot_id}.json")
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Snapshot {snapshot_id} not found")
            return None

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot.
        
        Returns:
            Optional[Dict[str, Any]]: The latest snapshot data or None if no snapshots exist
        """
        try:
            snapshots = [f for f in os.listdir(self.snapshots_dir) if f.endswith('.json')]
            if not snapshots:
                return None
            
            # Sort by timestamp in filename
            latest_file = max(snapshots, key=lambda x: os.path.getctime(os.path.join(self.snapshots_dir, x)))
            return self.load_snapshot(latest_file.replace('.json', ''))
        except Exception as e:
            logger.error(f"Error getting latest snapshot: {e}")
            return None

    def list_snapshots(self, limit: int = 10) -> list[Dict[str, Any]]:
        """List recent snapshots.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            list[Dict[str, Any]]: List of snapshot metadata
        """
        try:
            snapshots = []
            for filename in os.listdir(self.snapshots_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.snapshots_dir, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    snapshots.append({
                        "id": data["id"],
                        "timestamp": data["timestamp"],
                        "resource_count": sum(len(resources) for resources in data["resources"].values())
                    })
            
            # Sort by timestamp descending
            snapshots.sort(key=lambda x: x["timestamp"], reverse=True)
            return snapshots[:limit]
        except Exception as e:
            logger.error(f"Error listing snapshots: {e}")
            return []

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot.
        
        Args:
            snapshot_id: The ID of the snapshot to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            file_path = os.path.join(self.snapshots_dir, f"{snapshot_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted snapshot {snapshot_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting snapshot {snapshot_id}: {e}")
            return False

    def cleanup_old_snapshots(self, days: int = 30) -> int:
        """Remove snapshots older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            int: Number of snapshots deleted
        """
        try:
            count = 0
            cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            
            for filename in os.listdir(self.snapshots_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.snapshots_dir, filename)
                if os.path.getctime(file_path) < cutoff:
                    os.remove(file_path)
                    count += 1
            
            logger.info(f"Cleaned up {count} old snapshots")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up old snapshots: {e}")
            return 0 