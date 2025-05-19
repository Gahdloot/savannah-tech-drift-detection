"""Drift detection and analysis module for Azure resource configurations.

This module implements a comprehensive drift detection algorithm that compares Azure resource
configurations across different points in time. The algorithm uses DeepDiff for deep comparison
of nested configurations and provides detailed analysis of changes.

The drift detection process follows these steps:
1. Configuration Collection: Gather current and previous resource configurations
2. Deep Comparison: Use DeepDiff to identify differences in configurations
3. Change Analysis: Categorize and analyze the detected changes
4. Severity Assessment: Evaluate the impact of each change
5. Report Generation: Create detailed drift reports with change summaries

The algorithm handles various types of changes:
- Value modifications: Changes to existing property values
- Resource additions: New resources added to the configuration
- Resource removals: Resources removed from the configuration
- Nested changes: Modifications in nested resource properties
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json
from deepdiff import DeepDiff

logger = logging.getLogger(__name__)

class DriftAnalyzer:
    """Analyzes configuration drift between snapshots.
    
    This class implements the core drift detection algorithm that compares Azure resource
    configurations to identify and analyze changes. It uses DeepDiff for deep comparison
    and provides detailed analysis of configuration changes.
    
    The analyzer maintains a list of ignored paths that are excluded from drift detection,
    such as timestamps and metadata fields that don't represent actual configuration changes.
    """

    def __init__(self):
        """Initialize the drift analyzer.
        
        Sets up the list of paths to ignore during drift detection. These paths typically
        include metadata fields and timestamps that don't represent actual configuration
        changes.
        """
        self.ignored_paths = [
            "root['timestamp']",
            "root['id']",
            "root['metadata']"
        ]

    def detect_drift(self, current_config: Dict[str, Any], previous_config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect drift between current and previous configurations.
        
        This method implements the core drift detection algorithm:
        1. Uses DeepDiff to perform a deep comparison of configurations
        2. Processes the differences to identify specific changes
        3. Categorizes changes into modifications, additions, and removals
        4. Returns a detailed report of all detected changes
        
        The comparison is performed with the following considerations:
        - Order of elements is ignored (ignore_order=True)
        - Certain paths are excluded from comparison (excluded_paths)
        - Detailed change information is captured (verbose_level=2)
        
        Args:
            current_config: Current resource configuration
            previous_config: Previous resource configuration
            
        Returns:
            Dict[str, Any]: Drift detection report containing:
                - has_drift: Boolean indicating if drift was detected
                - changes: List of detected changes, each containing:
                    - property: Path to the changed property
                    - old_value: Previous value
                    - new_value: New value
                    - change_type: Type of change (modified, added, removed)
        """
        try:
            # Compare configurations using DeepDiff
            diff = DeepDiff(
                previous_config,
                current_config,
                ignore_order=True,
                exclude_paths=self.ignored_paths,
                verbose_level=2
            )
            
            if not diff:
                return {
                    "has_drift": False,
                    "changes": []
                }
            
            # Process the differences
            changes = []
            for change_type, changes_dict in diff.items():
                for path, change in changes_dict.items():
                    # Extract property path and values
                    property_path = path.replace("root['", "").replace("']", "")
                    if change_type == "values_changed":
                        old_value = change["old_value"]
                        new_value = change["new_value"]
                        changes.append({
                            "property": property_path,
                            "old_value": old_value,
                            "new_value": new_value,
                            "change_type": "modified"
                        })
                    elif change_type == "dictionary_item_added":
                        changes.append({
                            "property": property_path,
                            "old_value": None,
                            "new_value": change,
                            "change_type": "added"
                        })
                    elif change_type == "dictionary_item_removed":
                        changes.append({
                            "property": property_path,
                            "old_value": change,
                            "new_value": None,
                            "change_type": "removed"
                        })
            
            return {
                "has_drift": True,
                "changes": changes
            }
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return {
                "has_drift": False,
                "error": str(e)
            }

    def analyze_resource_drift(self, resource_id: str, current_config: Dict[str, Any], 
                             previous_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drift for a specific resource.
        
        This method analyzes drift for a single Azure resource by:
        1. Detecting changes in the resource's configuration
        2. Identifying the resource type from its ID
        3. Recording the timestamp of the analysis
        4. Providing detailed information about detected changes
        
        Args:
            resource_id: Azure resource ID
            current_config: Current resource configuration
            previous_config: Previous resource configuration
            
        Returns:
            Dict[str, Any]: Resource drift analysis containing:
                - resource_id: ID of the analyzed resource
                - resource_type: Type of the resource
                - has_drift: Boolean indicating if drift was detected
                - changes: List of detected changes
                - timestamp: Analysis timestamp
        """
        try:
            drift_result = self.detect_drift(current_config, previous_config)
            
            return {
                "resource_id": resource_id,
                "resource_type": resource_id.split('/')[6],
                "has_drift": drift_result["has_drift"],
                "changes": drift_result.get("changes", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing drift for resource {resource_id}: {e}")
            return {
                "resource_id": resource_id,
                "error": str(e)
            }

    def analyze_snapshot_drift(self, current_snapshot: Dict[str, Any], 
                             previous_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drift between snapshots.
        
        This method performs a comprehensive drift analysis between two configuration snapshots:
        1. Analyzes each resource type in the current snapshot
        2. Compares resources with their previous configurations
        3. Identifies new resources that were added
        4. Detects resources that were removed
        5. Generates a complete drift report
        
        The analysis process:
        - Iterates through each resource type in the current snapshot
        - For each resource, finds its corresponding previous configuration
        - Analyzes drift for existing resources
        - Identifies new resources that weren't in the previous snapshot
        - Checks for resources that were removed from the previous snapshot
        
        Args:
            current_snapshot: Current configuration snapshot
            previous_snapshot: Previous configuration snapshot
            
        Returns:
            Dict[str, Any]: Complete drift analysis report containing:
                - id: Unique report ID
                - timestamp: Analysis timestamp
                - snapshot_id: ID of the current snapshot
                - previous_snapshot_id: ID of the previous snapshot
                - has_drift: Boolean indicating if any drift was detected
                - drifts: List of all detected drifts
        """
        try:
            drifts = []
            
            # Analyze each resource type
            for resource_type, resources in current_snapshot["resources"].items():
                previous_resources = previous_snapshot["resources"].get(resource_type, {})
                
                # Analyze each resource
                for resource in resources:
                    resource_id = resource["id"]
                    previous_resource = next(
                        (r for r in previous_resources if r["id"] == resource_id),
                        None
                    )
                    
                    if previous_resource:
                        # Resource exists in both snapshots, check for drift
                        drift = self.analyze_resource_drift(
                            resource_id,
                            resource,
                            previous_resource
                        )
                        if drift["has_drift"]:
                            drifts.append(drift)
                    else:
                        # Resource is new
                        drifts.append({
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "has_drift": True,
                            "changes": [{
                                "property": "resource",
                                "old_value": None,
                                "new_value": resource,
                                "change_type": "added"
                            }],
                            "timestamp": datetime.utcnow().isoformat()
                        })
            
            # Check for removed resources
            for resource_type, resources in previous_snapshot["resources"].items():
                current_resources = current_snapshot["resources"].get(resource_type, {})
                
                for resource in resources:
                    resource_id = resource["id"]
                    if not any(r["id"] == resource_id for r in current_resources):
                        drifts.append({
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "has_drift": True,
                            "changes": [{
                                "property": "resource",
                                "old_value": resource,
                                "new_value": None,
                                "change_type": "removed"
                            }],
                            "timestamp": datetime.utcnow().isoformat()
                        })
            
            return {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "snapshot_id": current_snapshot["id"],
                "previous_snapshot_id": previous_snapshot["id"],
                "has_drift": len(drifts) > 0,
                "drifts": drifts
            }
        except Exception as e:
            logger.error(f"Error analyzing snapshot drift: {e}")
            return {
                "error": str(e)
            }

    def get_drift_summary(self, drift_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of drift changes.
        
        This method creates a comprehensive summary of drift changes by:
        1. Counting total number of drifts
        2. Categorizing drifts by resource type
        3. Categorizing drifts by change type
        4. Assessing severity of each change
        5. Providing statistical information about the drift
        
        The severity assessment is based on predefined criteria:
        - High severity: Security, encryption, authentication, authorization, firewall, network security
        - Medium severity: Size, capacity, performance, scaling, replication
        - Low severity: All other changes
        
        Args:
            drift_report: Complete drift analysis report
            
        Returns:
            Dict[str, Any]: Summary of drift changes containing:
                - total_drifts: Total number of detected drifts
                - resource_types: Count of drifts by resource type
                - change_types: Count of drifts by change type
                - severity: Count of drifts by severity level
        """
        try:
            summary = {
                "total_drifts": len(drift_report["drifts"]),
                "resource_types": {},
                "change_types": {},
                "severity": {
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
            
            for drift in drift_report["drifts"]:
                # Count by resource type
                resource_type = drift["resource_type"]
                summary["resource_types"][resource_type] = summary["resource_types"].get(resource_type, 0) + 1
                
                # Count by change type and assess severity
                for change in drift["changes"]:
                    change_type = change["change_type"]
                    summary["change_types"][change_type] = summary["change_types"].get(change_type, 0) + 1
                    
                    # Assess severity based on change type and property
                    severity = self._assess_change_severity(change)
                    summary["severity"][severity] += 1
            
            return summary
        except Exception as e:
            logger.error(f"Error generating drift summary: {e}")
            return {}

    def _assess_change_severity(self, change: Dict[str, Any]) -> str:
        """Assess the severity of a configuration change.
        
        This method evaluates the severity of a configuration change based on:
        1. The type of property being changed
        2. Predefined severity criteria for different property types
        3. The potential impact of the change
        
        Severity levels are determined by predefined criteria:
        - High severity: Security-related properties (security, encryption, authentication, etc.)
        - Medium severity: Performance and capacity-related properties (size, capacity, performance, etc.)
        - Low severity: All other properties
        
        Args:
            change: Configuration change details
            
        Returns:
            str: Severity level (high, medium, low)
        """
        # Define high-severity properties
        high_severity_props = [
            "security",
            "encryption",
            "authentication",
            "authorization",
            "firewall",
            "network_security"
        ]
        
        # Define medium-severity properties
        medium_severity_props = [
            "size",
            "capacity",
            "performance",
            "scaling",
            "replication"
        ]
        
        property_path = change["property"].lower()
        
        # Check for high-severity properties
        if any(prop in property_path for prop in high_severity_props):
            return "high"
        
        # Check for medium-severity properties
        if any(prop in property_path for prop in medium_severity_props):
            return "medium"
        
        return "low" 