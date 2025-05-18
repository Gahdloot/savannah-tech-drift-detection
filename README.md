# Azure Drift Detection and Secure Authentication Services

This repository contains two services:

1. Secure Authentication Service
2. Azure Drift Detection Service

## Prerequisites

- Docker
- Docker Compose
- Azure subscription and credentials

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Update the `.env` file with your Azure credentials and configuration:

```ini
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_RESOURCE_GROUP=your_resource_group
AZURE_RESOURCE=your_resource_name
AZURE_TOKEN_ENDPOINT=your_token_endpoint

# Security Configuration
SECRET_KEY=your_secret_key

# Other configurations...
```

## Running the Services

1. Build and start the services:

```bash
docker-compose up -d
```

2. Check service status:

```bash
docker-compose ps
```

3. View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f secure-auth
docker-compose logs -f azure-drift
```

## Service Endpoints

### Secure Authentication Service

- Health Check: http://localhost:5000/health
- Token Request: http://localhost:5000/requesttoken
- Logout: http://localhost:5000/logout

### Azure Drift Detection Service

- Health Check: http://localhost:8000/health
- Initialize: http://localhost:8000/initialize
- Collect Configuration: http://localhost:8000/collect
- Latest Snapshot: http://localhost:8000/latest-snapshot
- Latest Drift: http://localhost:8000/latest-drift

## Stopping the Services

```bash
docker-compose down
```

To remove volumes as well:

```bash
docker-compose down -v
```

## Development

1. Build services without cache:

```bash
docker-compose build --no-cache
```

2. Rebuild and restart a specific service:

```bash
docker-compose up -d --build secure-auth
```

## Data Persistence

The services use Docker volumes for data persistence:

- `secure_auth_data`: Stores authentication data
- `azure_drift_data`: Stores drift detection data
- `redis_data`: Stores session data

## Security Considerations

1. Never commit the `.env` file
2. Use strong secrets and keys
3. Regularly rotate credentials
4. Monitor service logs
5. Keep Docker images updated

## Troubleshooting

1. Check service logs:

```bash
docker-compose logs -f <service-name>
```

2. Check service status:

```bash
docker-compose ps
```

3. Restart services:

```bash
docker-compose restart
```

4. Rebuild services:

```bash
docker-compose up -d --build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
