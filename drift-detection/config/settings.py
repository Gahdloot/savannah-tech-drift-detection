import os

TENANT_ID = os.getenv("TENANT_ID", "your-tenant-id")
CLIENT_ID = os.getenv("CLIENT_ID", "your-client-id")
CLIENT_SECRET = os.getenv("CLIENT")

GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]
API_BASE_URL = "https://graph.microsoft.com/v1.0/"
SNAPSHOT_DIR = "snapshots/"
