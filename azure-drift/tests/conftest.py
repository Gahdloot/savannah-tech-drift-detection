import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import os
import json

@pytest.fixture
def mock_azure_credentials():
    """Mock Azure credentials for testing."""
    return {
        "subscription_id": "test-subscription-id",
        "tenant_id": "test-tenant-id",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret"
    }

@pytest.fixture
def mock_resource_group():
    """Mock Azure resource group for testing."""
    return {
        "name": "test-rg",
        "location": "eastus",
        "tags": {"environment": "test"}
    }

@pytest.fixture
def mock_snapshot_data():
    """Mock snapshot data for testing."""
    return {
        "id": "test-snapshot-id",
        "timestamp": datetime.utcnow().isoformat(),
        "resources": {
            "virtualMachines": [
                {
                    "id": "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
                    "name": "test-vm",
                    "properties": {
                        "hardwareProfile": {"vmSize": "Standard_DS1_v2"},
                        "storageProfile": {
                            "osDisk": {
                                "createOption": "FromImage",
                                "managedDisk": {"storageAccountType": "Premium_LRS"}
                            }
                        }
                    }
                }
            ]
        }
    }

@pytest.fixture
def mock_drift_report():
    """Mock drift report for testing."""
    return {
        "id": "test-drift-id",
        "timestamp": datetime.utcnow().isoformat(),
        "snapshot_id": "test-snapshot-id",
        "drifts": [
            {
                "resource_id": "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
                "resource_type": "virtualMachines",
                "changes": [
                    {
                        "property": "hardwareProfile.vmSize",
                        "old_value": "Standard_DS1_v2",
                        "new_value": "Standard_DS2_v2"
                    }
                ]
            }
        ]
    }

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock

@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary test data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    snapshots_dir = data_dir / "snapshots"
    snapshots_dir.mkdir()
    drift_dir = data_dir / "drift"
    drift_dir.mkdir()
    return data_dir

@pytest.fixture
def mock_azure_client():
    """Mock Azure client for testing."""
    mock = MagicMock()
    
    # Mock resource group operations
    mock.resource_groups.get.return_value = MagicMock(
        name="test-rg",
        location="eastus",
        tags={"environment": "test"}
    )
    
    # Mock compute operations
    mock.compute.virtual_machines.get.return_value = MagicMock(
        id="/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
        name="test-vm",
        properties=MagicMock(
            hardware_profile=MagicMock(vm_size="Standard_DS1_v2"),
            storage_profile=MagicMock(
                os_disk=MagicMock(
                    create_option="FromImage",
                    managed_disk=MagicMock(storage_account_type="Premium_LRS")
                )
            )
        )
    )
    
    return mock

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    mock = MagicMock()
    mock.info = MagicMock()
    mock.error = MagicMock()
    mock.warning = MagicMock()
    mock.debug = MagicMock()
    return mock 