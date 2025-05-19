"""Monitoring and metrics collection module for Azure drift detection."""

from typing import Dict, Any, Optional, List
import logging
import time
from datetime import datetime
import json
from pathlib import Path
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and manages metrics for drift detection."""

    def __init__(self, metrics_dir: str = "metrics"):
        """Initialize the metrics collector.
        
        Args:
            metrics_dir: Directory for storing metrics
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "metrics.json"
        self.metrics_lock = threading.Lock()
        self.metrics = self._load_metrics()
        self.start_time = time.time()

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file or initialize new metrics.
        
        Returns:
            Dict[str, Any]: Current metrics
        """
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            return self._initialize_metrics()
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            return self._initialize_metrics()

    def _initialize_metrics(self) -> Dict[str, Any]:
        """Initialize new metrics structure.
        
        Returns:
            Dict[str, Any]: Initialized metrics
        """
        return {
            "drift_detection": {
                "total_snapshots": 0,
                "total_drifts": 0,
                "drifts_by_severity": {
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "drifts_by_resource_type": defaultdict(int),
                "last_detection_time": None,
                "average_detection_time": 0
            },
            "resource_collection": {
                "total_resources": 0,
                "resources_by_type": defaultdict(int),
                "collection_errors": 0,
                "last_collection_time": None,
                "average_collection_time": 0
            },
            "api_usage": {
                "total_requests": 0,
                "requests_by_endpoint": defaultdict(int),
                "errors_by_endpoint": defaultdict(int),
                "average_response_time": 0
            },
            "system": {
                "uptime": 0,
                "memory_usage": 0,
                "cpu_usage": 0,
                "disk_usage": 0
            }
        }

    def save_metrics(self) -> None:
        """Save current metrics to file."""
        try:
            with self.metrics_lock:
                with open(self.metrics_file, 'w') as f:
                    json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def record_snapshot(self, resource_count: int, collection_time: float) -> None:
        """Record metrics for a new snapshot.
        
        Args:
            resource_count: Number of resources in snapshot
            collection_time: Time taken to collect snapshot
        """
        with self.metrics_lock:
            self.metrics["drift_detection"]["total_snapshots"] += 1
            self.metrics["resource_collection"]["total_resources"] += resource_count
            self.metrics["resource_collection"]["last_collection_time"] = datetime.utcnow().isoformat()
            
            # Update average collection time
            current_avg = self.metrics["resource_collection"]["average_collection_time"]
            total_snapshots = self.metrics["drift_detection"]["total_snapshots"]
            self.metrics["resource_collection"]["average_collection_time"] = (
                (current_avg * (total_snapshots - 1) + collection_time) / total_snapshots
            )
            
            self.save_metrics()

    def record_drift(self, severity: str, resource_type: str, detection_time: float) -> None:
        """Record metrics for detected drift.
        
        Args:
            severity: Severity of drift (high, medium, low)
            resource_type: Type of resource with drift
            detection_time: Time taken to detect drift
        """
        with self.metrics_lock:
            self.metrics["drift_detection"]["total_drifts"] += 1
            self.metrics["drift_detection"]["drifts_by_severity"][severity] += 1
            self.metrics["drift_detection"]["drifts_by_resource_type"][resource_type] += 1
            self.metrics["drift_detection"]["last_detection_time"] = datetime.utcnow().isoformat()
            
            # Update average detection time
            current_avg = self.metrics["drift_detection"]["average_detection_time"]
            total_drifts = self.metrics["drift_detection"]["total_drifts"]
            self.metrics["drift_detection"]["average_detection_time"] = (
                (current_avg * (total_drifts - 1) + detection_time) / total_drifts
            )
            
            self.save_metrics()

    def record_api_request(self, endpoint: str, response_time: float, error: bool = False) -> None:
        """Record metrics for API request.
        
        Args:
            endpoint: API endpoint
            response_time: Time taken to process request
            error: Whether request resulted in error
        """
        with self.metrics_lock:
            self.metrics["api_usage"]["total_requests"] += 1
            self.metrics["api_usage"]["requests_by_endpoint"][endpoint] += 1
            
            if error:
                self.metrics["api_usage"]["errors_by_endpoint"][endpoint] += 1
            
            # Update average response time
            current_avg = self.metrics["api_usage"]["average_response_time"]
            total_requests = self.metrics["api_usage"]["total_requests"]
            self.metrics["api_usage"]["average_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
            
            self.save_metrics()

    def record_collection_error(self) -> None:
        """Record a resource collection error."""
        with self.metrics_lock:
            self.metrics["resource_collection"]["collection_errors"] += 1
            self.save_metrics()

    def update_system_metrics(self, memory_usage: float, cpu_usage: float, disk_usage: float) -> None:
        """Update system resource usage metrics.
        
        Args:
            memory_usage: Current memory usage percentage
            cpu_usage: Current CPU usage percentage
            disk_usage: Current disk usage percentage
        """
        with self.metrics_lock:
            self.metrics["system"]["uptime"] = time.time() - self.start_time
            self.metrics["system"]["memory_usage"] = memory_usage
            self.metrics["system"]["cpu_usage"] = cpu_usage
            self.metrics["system"]["disk_usage"] = disk_usage
            self.save_metrics()

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Dict[str, Any]: Current metrics
        """
        with self.metrics_lock:
            return self.metrics.copy()

    def get_drift_metrics(self) -> Dict[str, Any]:
        """Get drift detection metrics.
        
        Returns:
            Dict[str, Any]: Drift detection metrics
        """
        with self.metrics_lock:
            return self.metrics["drift_detection"].copy()

    def get_resource_metrics(self) -> Dict[str, Any]:
        """Get resource collection metrics.
        
        Returns:
            Dict[str, Any]: Resource collection metrics
        """
        with self.metrics_lock:
            return self.metrics["resource_collection"].copy()

    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API usage metrics.
        
        Returns:
            Dict[str, Any]: API usage metrics
        """
        with self.metrics_lock:
            return self.metrics["api_usage"].copy()

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics.
        
        Returns:
            Dict[str, Any]: System metrics
        """
        with self.metrics_lock:
            return self.metrics["system"].copy()

    def reset_metrics(self) -> None:
        """Reset all metrics to initial values."""
        with self.metrics_lock:
            self.metrics = self._initialize_metrics()
            self.start_time = time.time()
            self.save_metrics()


class AlertManager:
    """Manages alerts based on metrics and thresholds."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the alert manager.
        
        Args:
            config: Alert configuration
        """
        self.config = config
        self.alerts: List[Dict[str, Any]] = []
        self.alert_lock = threading.Lock()

    def check_drift_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for drift-related alerts.
        
        Args:
            metrics: Current drift metrics
            
        Returns:
            List[Dict[str, Any]]: List of triggered alerts
        """
        alerts = []
        thresholds = self.config["alert_threshold"]
        
        # Check high severity changes
        if metrics["drifts_by_severity"]["high"] >= thresholds["high_severity_changes"]:
            alerts.append({
                "type": "high_severity_drift",
                "message": f"High severity drift threshold exceeded: {metrics['drifts_by_severity']['high']} changes",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high"
            })
        
        # Check medium severity changes
        if metrics["drifts_by_severity"]["medium"] >= thresholds["medium_severity_changes"]:
            alerts.append({
                "type": "medium_severity_drift",
                "message": f"Medium severity drift threshold exceeded: {metrics['drifts_by_severity']['medium']} changes",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "medium"
            })
        
        # Check low severity changes
        if metrics["drifts_by_severity"]["low"] >= thresholds["low_severity_changes"]:
            alerts.append({
                "type": "low_severity_drift",
                "message": f"Low severity drift threshold exceeded: {metrics['drifts_by_severity']['low']} changes",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "low"
            })
        
        with self.alert_lock:
            self.alerts.extend(alerts)
        
        return alerts

    def check_system_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for system-related alerts.
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List[Dict[str, Any]]: List of triggered alerts
        """
        alerts = []
        
        # Check memory usage
        if metrics["memory_usage"] > 90:
            alerts.append({
                "type": "high_memory_usage",
                "message": f"High memory usage: {metrics['memory_usage']}%",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high"
            })
        
        # Check CPU usage
        if metrics["cpu_usage"] > 90:
            alerts.append({
                "type": "high_cpu_usage",
                "message": f"High CPU usage: {metrics['cpu_usage']}%",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high"
            })
        
        # Check disk usage
        if metrics["disk_usage"] > 90:
            alerts.append({
                "type": "high_disk_usage",
                "message": f"High disk usage: {metrics['disk_usage']}%",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "high"
            })
        
        with self.alert_lock:
            self.alerts.extend(alerts)
        
        return alerts

    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get current alerts, optionally filtered by severity.
        
        Args:
            severity: Alert severity to filter by
            
        Returns:
            List[Dict[str, Any]]: List of alerts
        """
        with self.alert_lock:
            if severity:
                return [alert for alert in self.alerts if alert["severity"] == severity]
            return self.alerts.copy()

    def clear_alerts(self, severity: Optional[str] = None) -> None:
        """Clear alerts, optionally filtered by severity.
        
        Args:
            severity: Alert severity to clear
        """
        with self.alert_lock:
            if severity:
                self.alerts = [alert for alert in self.alerts if alert["severity"] != severity]
            else:
                self.alerts.clear() 