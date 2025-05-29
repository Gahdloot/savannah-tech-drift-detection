"""MongoDB configuration and connection management."""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Manages MongoDB connection and operations."""

    def __init__(self, connection_string: str, database_name: str = "azure_drift"):
        """Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            # Verify connection
            await self.db.command('ping')
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def get_collection(self, collection_name: str):
        """Get a collection from the database.
        
        Args:
            collection_name: Name of the collection to get
            
        Returns:
            Collection: MongoDB collection
        """
        if self.db is None:
            raise RuntimeError("Database connection not established")
        return self.db[collection_name] 