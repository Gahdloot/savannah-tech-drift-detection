"""Resource collector module for Azure drift detection."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from tenacity import retry, stop_after_attempt, wait_exponential
from .error_handler import ResourceCollectionError
from .schema_validator import ResourceSchemaValidator

logger = logging.getLogger(__name__)

class ResourceCollector:
    def __init__(self, subscription_id: str, resource_group: str):
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.credentials = DefaultAzureCredential()
        self.schema_validator = ResourceSchemaValidator()
        self.api_versions = self._load_api_versions()
        
    def _load_api_versions(self) -> Dict[str, str]:
        """Load API versions from configuration file.
        
        Returns:
            Dict[str, str]: Mapping of resource types to API versions
        """
        try:
            config_path = Path(__file__).parent / "config" / "api_versions.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            return self._get_default_api_versions()
        except Exception as e:
            logger.warning(f"Error loading API versions: {e}")
            return self._get_default_api_versions()
            
    def _get_default_api_versions(self) -> Dict[str, str]:
        """Get default API versions for resource types.
        
        Returns:
            Dict[str, str]: Default API versions
        """
        return {
            "virtualMachines": "2023-07-01",
            "networkInterfaces": "2023-05-01",
            "storageAccounts": "2023-01-01"
        }
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _safe_resource_collection(self, collection_func, *args, **kwargs) -> Any:
        """Safely collect resources with retry logic.
        
        Args:
            collection_func: Function to call for resource collection
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Collected resources
            
        Raises:
            ResourceCollectionError: If collection fails after retries
        """
        try:
            return collection_func(*args, **kwargs)
        except HttpResponseError as e:
            if e.status_code == 404:
                logger.warning(f"Resource not found: {e}")
                return []
            raise ResourceCollectionError(f"Azure API error: {str(e)}")
        except Exception as e:
            raise ResourceCollectionError(f"Unexpected error: {str(e)}")

    def collect_resources(self) -> Dict[str, Any]:
        """Collect current state of Azure resources.
        
        Returns:
            Dict[str, Any]: Dictionary containing resource configurations grouped by resource type
        """
        resources = {}
        collection_metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "api_versions": self.api_versions,
            "collection_status": {}
        }
        
        try:
            # Initialize Azure clients for different resource types
            compute_client = self._get_compute_client()
            network_client = self._get_network_client()
            storage_client = self._get_storage_client()
            
            # Collect virtual machines
            try:
                vms = self._safe_resource_collection(
                    compute_client.virtual_machines.list,
                    self.resource_group
                )
                resources["virtualMachines"] = [
                    self._extract_vm_properties(vm)
                    for vm in vms
                ]
                collection_metadata["collection_status"]["virtualMachines"] = "success"
            except Exception as e:
                logger.error(f"Error collecting VMs: {e}")
                collection_metadata["collection_status"]["virtualMachines"] = f"error: {str(e)}"
                resources["virtualMachines"] = []
            
            # Collect network interfaces
            try:
                nics = self._safe_resource_collection(
                    network_client.network_interfaces.list,
                    self.resource_group
                )
                resources["networkInterfaces"] = [
                    self._extract_nic_properties(nic)
                    for nic in nics
                ]
                collection_metadata["collection_status"]["networkInterfaces"] = "success"
            except Exception as e:
                logger.error(f"Error collecting NICs: {e}")
                collection_metadata["collection_status"]["networkInterfaces"] = f"error: {str(e)}"
                resources["networkInterfaces"] = []
            
            # Collect storage accounts
            try:
                storage_accounts = self._safe_resource_collection(
                    storage_client.storage_accounts.list_by_resource_group,
                    self.resource_group
                )
                resources["storageAccounts"] = [
                    self._extract_storage_properties(account)
                    for account in storage_accounts
                ]
                collection_metadata["collection_status"]["storageAccounts"] = "success"
            except Exception as e:
                logger.error(f"Error collecting storage accounts: {e}")
                collection_metadata["collection_status"]["storageAccounts"] = f"error: {str(e)}"
                resources["storageAccounts"] = []
            
            # Validate collected resources against schema
            self.schema_validator.validate_resources(resources)
            
            # Add metadata to resources
            resources["_metadata"] = collection_metadata
            
            return resources
            
        except Exception as e:
            logger.error(f"Error collecting resources: {e}")
            raise ResourceCollectionError(f"Failed to collect resources: {str(e)}")
            
    def _extract_vm_properties(self, vm) -> Dict[str, Any]:
        """Extract and validate VM properties.
        
        Args:
            vm: Virtual machine object
            
        Returns:
            Dict[str, Any]: Extracted properties
        """
        try:
            return {
                "id": vm.id,
                "name": vm.name,
                "properties": {
                    "hardwareProfile": vm.hardware_profile.as_dict() if vm.hardware_profile else None,
                    "storageProfile": vm.storage_profile.as_dict() if vm.storage_profile else None,
                    "osProfile": vm.os_profile.as_dict() if vm.os_profile else None,
                    "networkProfile": vm.network_profile.as_dict() if vm.network_profile else None
                }
            }
        except Exception as e:
            logger.warning(f"Error extracting VM properties: {e}")
            return {"id": vm.id, "name": vm.name, "properties": {}}
            
    def _extract_nic_properties(self, nic) -> Dict[str, Any]:
        """Extract and validate NIC properties.
        
        Args:
            nic: Network interface object
            
        Returns:
            Dict[str, Any]: Extracted properties
        """
        try:
            return {
                "id": nic.id,
                "name": nic.name,
                "properties": {
                    "ipConfigurations": [
                        {
                            "name": ip_config.name,
                            "properties": {
                                "privateIPAddress": ip_config.private_ip_address,
                                "publicIPAddress": ip_config.public_ip_address.id if ip_config.public_ip_address else None,
                                "subnet": ip_config.subnet.id if ip_config.subnet else None
                            }
                        }
                        for ip_config in nic.ip_configurations
                    ]
                }
            }
        except Exception as e:
            logger.warning(f"Error extracting NIC properties: {e}")
            return {"id": nic.id, "name": nic.name, "properties": {}}
            
    def _extract_storage_properties(self, account) -> Dict[str, Any]:
        """Extract and validate storage account properties.
        
        Args:
            account: Storage account object
            
        Returns:
            Dict[str, Any]: Extracted properties
        """
        try:
            return {
                "id": account.id,
                "name": account.name,
                "properties": {
                    "accountType": account.sku.name,
                    "kind": account.kind,
                    "accessTier": account.access_tier,
                    "enableHttpsTrafficOnly": account.enable_https_traffic_only
                }
            }
        except Exception as e:
            logger.warning(f"Error extracting storage account properties: {e}")
            return {"id": account.id, "name": account.name, "properties": {}}
            
    def _get_compute_client(self):
        """Get Azure Compute Management client."""
        from azure.mgmt.compute import ComputeManagementClient
        return ComputeManagementClient(
            self.credentials,
            self.subscription_id,
            api_version=self.api_versions["virtualMachines"]
        )
        
    def _get_network_client(self):
        """Get Azure Network Management client."""
        from azure.mgmt.network import NetworkManagementClient
        return NetworkManagementClient(
            self.credentials,
            self.subscription_id,
            api_version=self.api_versions["networkInterfaces"]
        )
        
    def _get_storage_client(self):
        """Get Azure Storage Management client."""
        from azure.mgmt.storage import StorageManagementClient
        return StorageManagementClient(
            self.credentials,
            self.subscription_id,
            api_version=self.api_versions["storageAccounts"]
        ) 