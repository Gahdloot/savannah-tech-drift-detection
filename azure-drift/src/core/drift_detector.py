from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import logging
from pathlib import Path
import asyncio
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.security import SecurityCenter
from azure.mgmt.authorization import AuthorizationManagementClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DriftDetector:
    def __init__(self, subscription_id: str, resource_group: str):
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.credential = DefaultAzureCredential()
        self.resource_client = ResourceManagementClient(self.credential, subscription_id)
        self.monitor_client = MonitorManagementClient(self.credential, subscription_id)
        self.security_client = SecurityCenter(self.credential, subscription_id)
        self.auth_client = AuthorizationManagementClient(self.credential, subscription_id)
        
        # Initialize storage paths
        self.base_path = Path("data")
        self.snapshots_path = self.base_path / "snapshots"
        self.drift_path = self.base_path / "drift"
        self._setup_storage()

    def _setup_storage(self):
        """Create necessary directories for storing snapshots and drift data."""
        self.snapshots_path.mkdir(parents=True, exist_ok=True)
        self.drift_path.mkdir(parents=True, exist_ok=True)

    async def collect_configuration(self) -> Dict[str, Any]:
        """Collect current configuration from Azure resources."""
        try:
            config = {
                "timestamp": datetime.utcnow().isoformat(),
                "subscription_id": self.subscription_id,
                "resource_group": self.resource_group,
                "resources": await self._collect_resources(),
                "security_settings": await self._collect_security_settings(),
                "rbac_assignments": await self._collect_rbac_assignments(),
                "monitoring_settings": await self._collect_monitoring_settings()
            }
            return config
        except Exception as e:
            logger.error(f"Error collecting configuration: {str(e)}")
            raise

    async def _collect_resources(self) -> List[Dict[str, Any]]:
        """Collect all resources in the resource group."""
        resources = []
        try:
            for resource in self.resource_client.resources.list_by_resource_group(self.resource_group):
                resource_dict = {
                    "id": resource.id,
                    "name": resource.name,
                    "type": resource.type,
                    "location": resource.location,
                    "tags": resource.tags,
                    "properties": resource.properties
                }
                resources.append(resource_dict)
        except Exception as e:
            logger.error(f"Error collecting resources: {str(e)}")
        return resources

    async def _collect_security_settings(self) -> Dict[str, Any]:
        """Collect security-related settings and configurations."""
        security_settings = {}
        try:
            # Collect security center policies
            policies = self.security_client.policies.list()
            security_settings["policies"] = [policy.as_dict() for policy in policies]

            # Collect security assessments
            assessments = self.security_client.assessments.list()
            security_settings["assessments"] = [assessment.as_dict() for assessment in assessments]
        except Exception as e:
            logger.error(f"Error collecting security settings: {str(e)}")
        return security_settings

    async def _collect_rbac_assignments(self) -> List[Dict[str, Any]]:
        """Collect RBAC role assignments."""
        assignments = []
        try:
            for assignment in self.auth_client.role_assignments.list():
                assignment_dict = {
                    "id": assignment.id,
                    "name": assignment.name,
                    "type": assignment.type,
                    "principal_id": assignment.principal_id,
                    "role_definition_id": assignment.role_definition_id,
                    "scope": assignment.scope
                }
                assignments.append(assignment_dict)
        except Exception as e:
            logger.error(f"Error collecting RBAC assignments: {str(e)}")
        return assignments

    async def _collect_monitoring_settings(self) -> Dict[str, Any]:
        """Collect monitoring and logging settings."""
        monitoring_settings = {}
        try:
            # Collect diagnostic settings
            diagnostic_settings = self.monitor_client.diagnostic_settings.list(
                resource_uri=f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}"
            )
            monitoring_settings["diagnostic_settings"] = [setting.as_dict() for setting in diagnostic_settings]

            # Collect alert rules
            alert_rules = self.monitor_client.alert_rules.list_by_resource_group(self.resource_group)
            monitoring_settings["alert_rules"] = [rule.as_dict() for rule in alert_rules]
        except Exception as e:
            logger.error(f"Error collecting monitoring settings: {str(e)}")
        return monitoring_settings

    def save_snapshot(self, config: Dict[str, Any]) -> str:
        """Save the current configuration as a snapshot."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.json"
        filepath = self.snapshots_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        return filename

    def detect_drift(self, current_config: Dict[str, Any], previous_config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect configuration drift between two snapshots."""
        drift = {
            "timestamp": datetime.utcnow().isoformat(),
            "changes": {
                "resources": self._compare_resources(
                    current_config.get("resources", []),
                    previous_config.get("resources", [])
                ),
                "security_settings": self._compare_security_settings(
                    current_config.get("security_settings", {}),
                    previous_config.get("security_settings", {})
                ),
                "rbac_assignments": self._compare_rbac_assignments(
                    current_config.get("rbac_assignments", []),
                    previous_config.get("rbac_assignments", [])
                ),
                "monitoring_settings": self._compare_monitoring_settings(
                    current_config.get("monitoring_settings", {}),
                    previous_config.get("monitoring_settings", {})
                )
            }
        }
        
        # Save drift report
        self._save_drift_report(drift)
        return drift

    def _compare_resources(self, current: List[Dict], previous: List[Dict]) -> Dict[str, Any]:
        """Compare resource configurations."""
        changes = {
            "added": [],
            "removed": [],
            "modified": []
        }
        
        current_dict = {r["id"]: r for r in current}
        previous_dict = {r["id"]: r for r in previous}
        
        # Find added and modified resources
        for resource_id, resource in current_dict.items():
            if resource_id not in previous_dict:
                changes["added"].append(resource)
            elif resource != previous_dict[resource_id]:
                changes["modified"].append({
                    "id": resource_id,
                    "previous": previous_dict[resource_id],
                    "current": resource
                })
        
        # Find removed resources
        for resource_id, resource in previous_dict.items():
            if resource_id not in current_dict:
                changes["removed"].append(resource)
        
        return changes

    def _compare_security_settings(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        """Compare security settings."""
        changes = {
            "policies": self._compare_dicts(current.get("policies", {}), previous.get("policies", {})),
            "assessments": self._compare_dicts(current.get("assessments", {}), previous.get("assessments", {}))
        }
        return changes

    def _compare_rbac_assignments(self, current: List[Dict], previous: List[Dict]) -> Dict[str, Any]:
        """Compare RBAC assignments."""
        changes = {
            "added": [],
            "removed": [],
            "modified": []
        }
        
        current_dict = {a["id"]: a for a in current}
        previous_dict = {a["id"]: a for a in previous}
        
        # Find added and modified assignments
        for assignment_id, assignment in current_dict.items():
            if assignment_id not in previous_dict:
                changes["added"].append(assignment)
            elif assignment != previous_dict[assignment_id]:
                changes["modified"].append({
                    "id": assignment_id,
                    "previous": previous_dict[assignment_id],
                    "current": assignment
                })
        
        # Find removed assignments
        for assignment_id, assignment in previous_dict.items():
            if assignment_id not in current_dict:
                changes["removed"].append(assignment)
        
        return changes

    def _compare_monitoring_settings(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        """Compare monitoring settings."""
        changes = {
            "diagnostic_settings": self._compare_dicts(
                current.get("diagnostic_settings", {}),
                previous.get("diagnostic_settings", {})
            ),
            "alert_rules": self._compare_dicts(
                current.get("alert_rules", {}),
                previous.get("alert_rules", {})
            )
        }
        return changes

    def _compare_dicts(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        """Compare two dictionaries and return changes."""
        changes = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # Find added and modified items
        for key, value in current.items():
            if key not in previous:
                changes["added"][key] = value
            elif value != previous[key]:
                changes["modified"][key] = {
                    "previous": previous[key],
                    "current": value
                }
        
        # Find removed items
        for key, value in previous.items():
            if key not in current:
                changes["removed"][key] = value
        
        return changes

    def _save_drift_report(self, drift: Dict[str, Any]) -> None:
        """Save the drift report to a file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"drift_report_{timestamp}.json"
        filepath = self.drift_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(drift, f, indent=2)
        
        logger.info(f"Drift report saved to {filepath}")

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent configuration snapshot."""
        try:
            snapshots = list(self.snapshots_path.glob("snapshot_*.json"))
            if not snapshots:
                return None
            
            latest_snapshot = max(snapshots, key=lambda x: x.stat().st_mtime)
            with open(latest_snapshot, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting latest snapshot: {str(e)}")
            return None

    def get_latest_drift_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recent drift report."""
        try:
            drift_reports = list(self.drift_path.glob("drift_report_*.json"))
            if not drift_reports:
                return None
            
            latest_report = max(drift_reports, key=lambda x: x.stat().st_mtime)
            with open(latest_report, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting latest drift report: {str(e)}")
            return None 