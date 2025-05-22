# Azure Drift Detection Service Development Guide

## Development Environment Setup

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Azure CLI
- Git
- MongoDB 4.4 or higher
- Redis 6.0 or higher

### Local Development Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd azure-drift
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration

# Azure credentials
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"

# MongoDB configuration
export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DB_NAME="azure_drift"

# Redis configuration
export REDIS_URL="redis://localhost:6379/0"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_drift_detector.py

# Run with coverage
pytest --cov=src tests/
```

### Running Background Tasks

1. Start Redis server:

```bash
# Ubuntu/Debian
sudo service redis-server start

# macOS
brew services start redis

# Windows
# Redis runs as a service
```

2. Start Celery worker:

```bash
celery -A src.core.tasks worker --loglevel=info
```

3. Start Celery beat (scheduler):

```bash
celery -A src.core.tasks beat --loglevel=info
```

### Background Task Configuration

The system uses Celery for background task processing with the following tasks:

1. **Configuration Collection** (`collect_azure_configuration`):

   - Runs every 3 hours
   - Collects current Azure resource configurations
   - Saves snapshots to MongoDB

2. **Drift Detection** (`detect_drift`):
   - Runs every 3 hours
   - Analyzes configuration changes
   - Generates drift reports

To modify task schedules, edit the `celery_app.conf.beat_schedule` in `src/core/tasks.py`:

```python
celery_app.conf.beat_schedule = {
    'collect-azure-configuration': {
        'task': 'src.core.tasks.collect_azure_configuration',
        'schedule': timedelta(hours=3),  # Change interval here
        'args': (),
    },
    'detect-drift': {
        'task': 'src.core.tasks.detect_drift',
        'schedule': timedelta(hours=3),  # Change interval here
        'args': (),
    },
}
```

### Monitoring Background Tasks

1. **Celery Flower** (Web-based monitoring):

```bash
pip install flower
celery -A src.core.tasks flower
```

Access at: http://localhost:5555

2. **Task Results**:

```python
from src.core.tasks import collect_azure_configuration, detect_drift

# Get task result
result = collect_azure_configuration.delay()
task_result = result.get()  # Wait for result
```

3. **Logging**:

```python
import logging

logger = logging.getLogger('celery.task')
logger.info('Task started')
```

## Project Structure

```
azure-drift/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes/
│   ├── core/
│   │   ├── __init__.py
│   │   └── drift_detector.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_drift_detector.py
├── config/
│   └── config.py
├── data/
│   ├── snapshots/
│   └── drift/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── requirements-dev.txt
```

## Development Workflow

### 1. Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions and classes
- Keep functions small and focused

### 2. Testing

- Write unit tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for test setup
- Mock external dependencies

### 3. Git Workflow

1. Create a feature branch:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:

```bash
git add .
git commit -m "feat: your feature description"
```

3. Push and create a pull request:

```bash
git push origin feature/your-feature-name
```

### 4. Code Review Process

1. Self-review your changes
2. Run tests and linting
3. Create pull request
4. Address review comments
5. Merge after approval

## Adding New Features

### 1. API Endpoints

1. Create new route in `src/api/routes/`
2. Add request/response models
3. Implement business logic
4. Add tests
5. Update API documentation

### 2. Drift Detection

1. Add new resource type in `src/core/drift_detector.py`
2. Implement collection method
3. Add comparison logic
4. Update tests
5. Update documentation

## Debugging

### Local Debugging

1. Run service locally:

```bash
python -m src.api.main
```

2. Use debugger:

```python
import pdb; pdb.set_trace()
```

### Docker Debugging

1. Build and run with debug:

```bash
docker-compose up --build
```

2. View logs:

```bash
docker-compose logs -f azure-drift
```

## Performance Optimization

### 1. Caching

- Use Redis for caching
- Implement cache invalidation
- Monitor cache hit rates

### 2. Async Operations

- Use async/await for I/O operations
- Implement background tasks
- Handle timeouts properly

### 3. Resource Management

- Monitor memory usage
- Implement connection pooling
- Clean up resources properly

## Security Best Practices

### 1. Authentication

- Use Azure AD authentication
- Implement token validation
- Handle token refresh

### 2. Authorization

- Implement RBAC
- Validate permissions
- Log access attempts

### 3. Data Protection

- Encrypt sensitive data
- Use secure communication
- Implement audit logging

## Monitoring and Logging

### 1. Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Your log message")
```

### 2. Metrics

- Track API performance
- Monitor resource usage
- Set up alerts

## Deployment

### 1. Docker Build

```bash
docker build -t azure-drift .
```

### 2. Docker Compose

```bash
docker-compose up -d
```

### 3. Kubernetes

- Create deployment manifests
- Set up service accounts
- Configure ingress

## Troubleshooting

### Common Issues

1. Authentication failures

   - Check Azure credentials
   - Verify token endpoint
   - Check permissions

2. Performance issues

   - Monitor resource usage
   - Check cache configuration
   - Review async operations

3. API errors
   - Check request format
   - Verify authentication
   - Review error logs

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Create pull request

## Resources

- [Azure SDK Documentation](https://docs.microsoft.com/en-us/python/api/overview/azure/?view=azure-python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Best Practices](https://docs.python-guide.org/)

## MongoDB Setup

1. Install MongoDB:

```bash
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS
brew install mongodb-community

# Windows
# Download and install from MongoDB website
```

2. Start MongoDB service:

```bash
# Ubuntu/Debian
sudo service mongodb start

# macOS
brew services start mongodb-community

# Windows
# MongoDB runs as a service
```

3. Create database and collections:

```javascript
use azure_drift

// Create collections
db.createCollection("snapshots")
db.createCollection("drift_reports")

// Create indexes
db.snapshots.createIndex({ "timestamp": -1 })
db.snapshots.createIndex({ "_id": 1 })

db.drift_reports.createIndex({ "timestamp": -1 })
db.drift_reports.createIndex({ "snapshot_id": 1 })
```

## MongoDB Operations

1. **Snapshot Management**:

```python
# Save snapshot
snapshot_id = await snapshot_manager.save_snapshot(snapshot_data)

# Load snapshot
snapshot = await snapshot_manager.load_snapshot(snapshot_id)

# Get latest snapshot
latest = await snapshot_manager.get_latest_snapshot()
```

2. **Drift Report Management**:

```python
# Save report
report_id = await drift_report_manager.save_report(report_data)

# Load report
report = await drift_report_manager.load_report(report_id)

# Get latest report
latest = await drift_report_manager.get_latest_report()
```

## API Development

1. Start development server:

```bash
uvicorn src.api.main:app --reload
```

2. Access API documentation:

```
http://localhost:8000/docs
```

## Best Practices

### MongoDB Usage

1. **Connection Management**:

   - Use connection pooling
   - Handle connection errors
   - Close connections properly

2. **Query Optimization**:

   - Use appropriate indexes
   - Limit result sets
   - Use projection for large documents

3. **Data Management**:
   - Implement data cleanup
   - Monitor collection sizes
   - Regular backup strategy

### Code Style

1. Follow PEP 8 guidelines
2. Use type hints
3. Write docstrings
4. Use async/await properly

### Error Handling

1. Use proper exception handling
2. Log errors appropriately
3. Implement retry mechanisms
4. Handle MongoDB-specific errors

## Deployment

### Production Setup

1. Configure MongoDB:

   - Enable authentication
   - Set up replication
   - Configure backup

2. Environment Variables:

   - Use secure connection strings
   - Set appropriate timeouts
   - Configure logging

3. Monitoring:
   - Set up MongoDB monitoring
   - Configure alerts
   - Track performance metrics

### Scaling

1. MongoDB:

   - Use replica sets
   - Implement sharding
   - Monitor performance

2. Application:
   - Use connection pooling
   - Implement caching
   - Handle concurrent requests

## Troubleshooting

### Common Issues

1. **Connection Issues**:

   - Check MongoDB service
   - Verify connection string
   - Check network connectivity

2. **Performance Issues**:

   - Check indexes
   - Monitor query performance
   - Review connection settings

3. **Data Issues**:
   - Verify data integrity
   - Check backup status
   - Monitor disk space

### Debugging

1. Enable debug logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

2. Use MongoDB shell:

```bash
mongosh
```

3. Check MongoDB logs:

```bash
tail -f /var/log/mongodb/mongodb.log
```
