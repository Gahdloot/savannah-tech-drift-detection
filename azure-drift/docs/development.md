# Azure Drift Detection Service Development Guide

## Development Environment Setup

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Azure CLI
- Git

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
