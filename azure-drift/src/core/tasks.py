from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Celery
celery_app = Celery(
    'azure_drift',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'collect-azure-configuration': {
        'task': 'src.core.tasks.collect_azure_configuration',
        'schedule': timedelta(hours=3),  # Run every 3 hours
        'args': (),
    },
    'detect-drift': {
        'task': 'src.core.tasks.detect_drift',
        'schedule': timedelta(hours=3),  # Run every 3 hours
        'args': (),
    },
}

@celery_app.task(name='src.core.tasks.collect_azure_configuration')
def collect_azure_configuration():
    """
    Task to collect Azure resource configurations.
    This task runs every 3 hours to collect the current state of Azure resources.
    """
    from .drift_detector import DriftDetector
    from .snapshot import SnapshotManager
    
    try:
        # Initialize components
        drift_detector = DriftDetector()
        snapshot_manager = SnapshotManager()
        
        # Collect current configuration
        current_config = drift_detector.collect_current_configuration()
        
        # Save snapshot
        snapshot_id = snapshot_manager.save_snapshot(current_config)
        
        return {
            'status': 'success',
            'snapshot_id': snapshot_id,
            'timestamp': current_config.get('timestamp')
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

@celery_app.task(name='src.core.tasks.detect_drift')
def detect_drift():
    """
    Task to detect configuration drift.
    This task runs every 3 hours to detect any changes in Azure resource configurations.
    """
    from .drift_detector import DriftDetector
    from .snapshot import SnapshotManager
    from .drift_report import DriftReportManager
    
    try:
        # Initialize components
        drift_detector = DriftDetector()
        snapshot_manager = SnapshotManager()
        drift_report_manager = DriftReportManager()
        
        # Get latest snapshot
        latest_snapshot = snapshot_manager.get_latest_snapshot()
        
        if not latest_snapshot:
            return {
                'status': 'error',
                'error': 'No snapshots available for drift detection'
            }
        
        # Detect drift
        drift_result = drift_detector.detect_drift(latest_snapshot)
        
        # Save drift report
        report_id = drift_report_manager.save_report(drift_result)
        
        return {
            'status': 'success',
            'report_id': report_id,
            'has_drift': drift_result.get('has_drift', False),
            'timestamp': drift_result.get('timestamp')
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        } 