import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json
import os

from src.core.drift_detector import DriftDetector

class TestDriftDetector:
    """Test suite for DriftDetector class."""

    def test_initialization(self, mock_azure_credentials, mock_redis_client, test_data_dir):
        """Test DriftDetector initialization."""
        detector = DriftDetector(
            subscription_id=mock_azure_credentials["subscription_id"],
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        assert detector.subscription_id == mock_azure_credentials["subscription_id"]
        assert detector.resource_group == "test-rg"
        assert detector.redis_client == mock_redis_client
        assert detector.data_dir == str(test_data_dir)

    def test_collect_configuration(self, mock_azure_client, mock_redis_client, test_data_dir):
        """Test configuration collection from Azure resources."""
        detector = DriftDetector(
            subscription_id="test-sub",
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        with patch('azure.mgmt.compute.ComputeManagementClient') as mock_compute:
            mock_compute.return_value = mock_azure_client
            
            snapshot = detector.collect_configuration()
            
            assert snapshot is not None
            assert "id" in snapshot
            assert "timestamp" in snapshot
            assert "resources" in snapshot
            assert "virtualMachines" in snapshot["resources"]

    def test_detect_drift(self, mock_azure_client, mock_redis_client, test_data_dir, mock_snapshot_data):
        """Test drift detection between snapshots."""
        detector = DriftDetector(
            subscription_id="test-sub",
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        # Save a snapshot
        snapshot_path = os.path.join(test_data_dir, "snapshots", "test-snapshot.json")
        with open(snapshot_path, 'w') as f:
            json.dump(mock_snapshot_data, f)
        
        # Modify the VM size in the current state
        mock_azure_client.compute.virtual_machines.get.return_value.properties.hardware_profile.vm_size = "Standard_DS2_v2"
        
        with patch('azure.mgmt.compute.ComputeManagementClient') as mock_compute:
            mock_compute.return_value = mock_azure_client
            
            drift_report = detector.detect_drift()
            
            assert drift_report is not None
            assert "id" in drift_report
            assert "timestamp" in drift_report
            assert "drifts" in drift_report
            assert len(drift_report["drifts"]) > 0
            
            # Verify the drift details
            drift = drift_report["drifts"][0]
            assert drift["resource_type"] == "virtualMachines"
            assert len(drift["changes"]) > 0
            change = drift["changes"][0]
            assert change["property"] == "hardwareProfile.vmSize"
            assert change["old_value"] == "Standard_DS1_v2"
            assert change["new_value"] == "Standard_DS2_v2"

    def test_get_latest_snapshot(self, mock_redis_client, test_data_dir, mock_snapshot_data):
        """Test retrieving the latest snapshot."""
        detector = DriftDetector(
            subscription_id="test-sub",
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        # Save a snapshot
        snapshot_path = os.path.join(test_data_dir, "snapshots", "test-snapshot.json")
        with open(snapshot_path, 'w') as f:
            json.dump(mock_snapshot_data, f)
        
        latest_snapshot = detector.get_latest_snapshot()
        
        assert latest_snapshot is not None
        assert latest_snapshot["id"] == mock_snapshot_data["id"]
        assert latest_snapshot["timestamp"] == mock_snapshot_data["timestamp"]

    def test_get_latest_drift_report(self, mock_redis_client, test_data_dir, mock_drift_report):
        """Test retrieving the latest drift report."""
        detector = DriftDetector(
            subscription_id="test-sub",
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        # Save a drift report
        report_path = os.path.join(test_data_dir, "drift", "test-drift.json")
        with open(report_path, 'w') as f:
            json.dump(mock_drift_report, f)
        
        latest_report = detector.get_latest_drift_report()
        
        assert latest_report is not None
        assert latest_report["id"] == mock_drift_report["id"]
        assert latest_report["timestamp"] == mock_drift_report["timestamp"]

    def test_cleanup_old_data(self, mock_redis_client, test_data_dir):
        """Test cleanup of old snapshots and drift reports."""
        detector = DriftDetector(
            subscription_id="test-sub",
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        # Create old snapshots and reports
        old_date = datetime.utcnow() - timedelta(days=31)
        old_snapshot = {
            "id": "old-snapshot",
            "timestamp": old_date.isoformat(),
            "resources": {}
        }
        
        old_report = {
            "id": "old-report",
            "timestamp": old_date.isoformat(),
            "drifts": []
        }
        
        # Save old files
        with open(os.path.join(test_data_dir, "snapshots", "old-snapshot.json"), 'w') as f:
            json.dump(old_snapshot, f)
        
        with open(os.path.join(test_data_dir, "drift", "old-report.json"), 'w') as f:
            json.dump(old_report, f)
        
        # Run cleanup
        detector.cleanup_old_data()
        
        # Verify old files are removed
        assert not os.path.exists(os.path.join(test_data_dir, "snapshots", "old-snapshot.json"))
        assert not os.path.exists(os.path.join(test_data_dir, "drift", "old-report.json"))

    def test_error_handling(self, mock_azure_client, mock_redis_client, test_data_dir, mock_logger):
        """Test error handling in drift detection."""
        detector = DriftDetector(
            subscription_id="test-sub",
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        # Simulate Azure API error
        mock_azure_client.compute.virtual_machines.get.side_effect = Exception("API Error")
        
        with patch('azure.mgmt.compute.ComputeManagementClient') as mock_compute:
            mock_compute.return_value = mock_azure_client
            
            with pytest.raises(Exception) as exc_info:
                detector.collect_configuration()
            
            assert "API Error" in str(exc_info.value)

    def test_concurrent_operations(self, mock_azure_client, mock_redis_client, test_data_dir):
        """Test concurrent operations handling."""
        detector = DriftDetector(
            subscription_id="test-sub",
            resource_group="test-rg",
            redis_client=mock_redis_client,
            data_dir=str(test_data_dir)
        )
        
        # Simulate concurrent collection
        with patch('azure.mgmt.compute.ComputeManagementClient') as mock_compute:
            mock_compute.return_value = mock_azure_client
            
            # Start multiple collection operations
            snapshot1 = detector.collect_configuration()
            snapshot2 = detector.collect_configuration()
            
            assert snapshot1 is not None
            assert snapshot2 is not None
            assert snapshot1["id"] != snapshot2["id"]  # Should have different IDs 