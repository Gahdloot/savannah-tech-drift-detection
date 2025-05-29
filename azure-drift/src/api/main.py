from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from datetime import datetime
import asyncio
import logging
from pathlib import Path
import json
import os

from ..core.drift_detector import DriftDetector
from ..core.db.mongodb import MongoDBManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "azure_drift")

# Initialize MongoDB connection
db_manager = MongoDBManager(MONGODB_URL, DB_NAME)

app = FastAPI(
    title="Azure Drift Detection API",
    description="API for detecting configuration drift in Azure resources",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class DriftDetectionRequest(BaseModel):
    subscription_id: str
    resource_group: str
    collect_now: bool = False

class DriftReport(BaseModel):
    timestamp: str
    changes: Dict[str, Any]

# Global drift detector instance
drift_detector: Optional[DriftDetector] = None

@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB connection on startup."""
    await db_manager.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown."""
    await db_manager.close()

async def get_drift_detector() -> DriftDetector:
    """Dependency to get or create drift detector instance."""
    global drift_detector
    if drift_detector is None:
        raise HTTPException(status_code=400, detail="Drift detector not initialized")
    return drift_detector

@app.post("/initialize")
async def initialize_drift_detector(request: DriftDetectionRequest):
    """Initialize the drift detector with subscription and resource group."""
    global drift_detector
    try:
        drift_detector = DriftDetector(
            request.subscription_id,
            request.resource_group,
            db_manager=db_manager
        )
        return {"message": "Drift detector initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing drift detector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collect")
async def collect_configuration(
    background_tasks: BackgroundTasks,
    detector: DriftDetector = Depends(get_drift_detector)
):
    """Collect current configuration and save as snapshot."""
    try:
        config = await detector.collect_configuration()
        snapshot_id = await detector.save_snapshot(config)
        
        # Compare with previous snapshot in background
        background_tasks.add_task(compare_with_previous, detector, config)
        
        return {
            "message": "Configuration collected successfully",
            "snapshot_id": snapshot_id
        }
    except Exception as e:
        logger.error(f"Error collecting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def compare_with_previous(detector: DriftDetector, current_config: Dict[str, Any]):
    """Compare current configuration with previous snapshot."""
    try:
        previous_config = await detector.get_latest_snapshot()
        if previous_config:
            drift = await detector.detect_drift(current_config, previous_config)
            logger.info("Drift detection completed")
    except Exception as e:
        logger.error(f"Error comparing configurations: {str(e)}")

@app.get("/latest-snapshot")
async def get_latest_snapshot(
    detector: DriftDetector = Depends(get_drift_detector)
):
    """Get the most recent configuration snapshot."""
    try:
        snapshot = await detector.get_latest_snapshot()
        if not snapshot:
            raise HTTPException(status_code=404, detail="No snapshots found")
        return snapshot
    except Exception as e:
        logger.error(f"Error getting latest snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-drift")
async def get_latest_drift(
    detector: DriftDetector = Depends(get_drift_detector)
):
    """Get the most recent drift report."""
    try:
        drift_report = await detector.get_latest_drift_report()
        if not drift_report:
            raise HTTPException(status_code=404, detail="No drift reports found")
        return drift_report
    except Exception as e:
        logger.error(f"Error getting latest drift report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/drift/check")
async def check_drift(
    background_tasks: BackgroundTasks,
    detector: DriftDetector = Depends(get_drift_detector)
):
    """Trigger a manual drift check."""
    try:
        config = await detector.collect_configuration()
        snapshot_id = await detector.save_snapshot(config)
        
        # Compare with previous snapshot in background
        background_tasks.add_task(compare_with_previous, detector, config)
        
        return {
            "message": "Drift check triggered successfully",
            "snapshot_id": snapshot_id
        }
    except Exception as e:
        logger.error(f"Error triggering drift check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 