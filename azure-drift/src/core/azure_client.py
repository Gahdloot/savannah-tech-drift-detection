"""Azure client management and authentication module."""

from typing import Dict, Any, Optional
import logging
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.redis import RedisManagementClient

logger = logging.getLogger(__name__)

class AzureClientManager:
    """Manages Azure client connections and authentication."""

    def __init__(self, subscription_id: str, tenant_id: str = None, client_id: str = None, client_secret: str = None):
        """Initialize the Azure client manager.
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID (optional)
            client_id: Azure client ID (optional)
            client_secret: Azure client secret (optional)
        """
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.credential = self._get_credential(tenant_id, client_id, client_secret)
        self.clients: Dict[str, Any] = {}

    def _get_credential(self, tenant_id: Optional[str], client_id: Optional[str],
                       client_secret: Optional[str]) -> Any:
        """Get Azure credentials based on provided parameters.
        
        Args:
            tenant_id: Azure tenant ID
            client_id: Azure client ID
            client_secret: Azure client secret
            
        Returns:
            Any: Azure credential object
        """
        try:
            if all([tenant_id, client_id, client_secret]):
                return ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret
                )
            return DefaultAzureCredential()
        except Exception as e:
            logger.error(f"Error getting Azure credentials: {e}")
            raise

    def get_client(self, client_type: str) -> Any:
        """Get or create an Azure management client.
        
        Args:
            client_type: Type of Azure client to get
            
        Returns:
            Any: Azure management client
        """
        if client_type in self.clients:
            return self.clients[client_type]

        try:
            client = self._create_client(client_type)
            self.clients[client_type] = client
            return client
        except Exception as e:
            logger.error(f"Error creating Azure client {client_type}: {e}")
            raise

    def _create_client(self, client_type: str) -> Any:
        """Create a new Azure management client.
        
        Args:
            client_type: Type of Azure client to create
            
        Returns:
            Any: Azure management client
        """
        client_map = {
            "compute": ComputeManagementClient,
            "network": NetworkManagementClient,
            "storage": StorageManagementClient,
            "resource": ResourceManagementClient,
            "monitor": MonitorManagementClient,
            "keyvault": KeyVaultManagementClient,
            "sql": SqlManagementClient,
            "web": WebSiteManagementClient,
            "cosmosdb": CosmosDBManagementClient,
            "redis": RedisManagementClient
        }

        if client_type not in client_map:
            raise ValueError(f"Unsupported client type: {client_type}")

        return client_map[client_type](
            credential=self.credential,
            subscription_id=self.subscription_id
        )

    def get_resource_client(self) -> ResourceManagementClient:
        """Get the Azure Resource Management client.
        
        Returns:
            ResourceManagementClient: Azure Resource Management client
        """
        return self.get_client("resource")

    def get_compute_client(self) -> ComputeManagementClient:
        """Get the Azure Compute Management client.
        
        Returns:
            ComputeManagementClient: Azure Compute Management client
        """
        return self.get_client("compute")

    def get_network_client(self) -> NetworkManagementClient:
        """Get the Azure Network Management client.
        
        Returns:
            NetworkManagementClient: Azure Network Management client
        """
        return self.get_client("network")

    def get_storage_client(self) -> StorageManagementClient:
        """Get the Azure Storage Management client.
        
        Returns:
            StorageManagementClient: Azure Storage Management client
        """
        return self.get_client("storage")

    def get_monitor_client(self) -> MonitorManagementClient:
        """Get the Azure Monitor Management client.
        
        Returns:
            MonitorManagementClient: Azure Monitor Management client
        """
        return self.get_client("monitor")

    def get_keyvault_client(self) -> KeyVaultManagementClient:
        """Get the Azure Key Vault Management client.
        
        Returns:
            KeyVaultManagementClient: Azure Key Vault Management client
        """
        return self.get_client("keyvault")

    def get_sql_client(self) -> SqlManagementClient:
        """Get the Azure SQL Management client.
        
        Returns:
            SqlManagementClient: Azure SQL Management client
        """
        return self.get_client("sql")

    def get_web_client(self) -> WebSiteManagementClient:
        """Get the Azure Web Management client.
        
        Returns:
            WebSiteManagementClient: Azure Web Management client
        """
        return self.get_client("web")

    def get_cosmosdb_client(self) -> CosmosDBManagementClient:
        """Get the Azure Cosmos DB Management client.
        
        Returns:
            CosmosDBManagementClient: Azure Cosmos DB Management client
        """
        return self.get_client("cosmosdb")

    def get_redis_client(self) -> RedisManagementClient:
        """Get the Azure Redis Management client.
        
        Returns:
            RedisManagementClient: Azure Redis Management client
        """
        return self.get_client("redis")

    def close(self):
        """Close all Azure client connections."""
        for client in self.clients.values():
            try:
                client.close()
            except Exception as e:
                logger.error(f"Error closing Azure client: {e}")
        self.clients.clear() 