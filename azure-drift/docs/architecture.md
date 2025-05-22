# Azure Drift Detection Architecture

## Overview

The Azure Drift Detection system is designed to monitor and detect configuration changes in Azure resources. The system uses a modular architecture with the following key components:

## Core Components

### 1. Drift Detector

- Main component responsible for detecting configuration changes
- Manages the drift detection workflow
- Coordinates between different components

### 2. Resource Collector

- Collects current state of Azure resources
- Supports multiple resource types
- Handles Azure API interactions

### 3. Snapshot Management

- Stores configuration snapshots in MongoDB
- Manages snapshot lifecycle
- Provides historical data access

### 4. Drift Analysis

- Analyzes configuration changes
- Generates drift reports
- Identifies drift patterns

## Data Storage

### MongoDB Integration

The system uses MongoDB for storing snapshots and drift reports:

#### Collections

1. **Snapshots Collection**

   - Stores configuration snapshots
   - Indexed by timestamp and ID
   - Contains resource configurations

2. **Drift Reports Collection**
   - Stores drift detection results
   - Indexed by timestamp and snapshot ID
   - Contains drift analysis data

#### Data Models

1. **Snapshot Document**

```json
{
  "_id": "uuid",
  "timestamp": "ISO-8601 timestamp",
  "subscription_id": "Azure subscription ID",
  "resource_group": "Resource group name",
  "resources": {
    "resource_type": {
      "resource_id": {
        "properties": {}
      }
    }
  }
}
```

2. **Drift Report Document**

```json
{
  "_id": "uuid",
  "timestamp": "ISO-8601 timestamp",
  "snapshot_id": "Reference to snapshot",
  "has_drift": true,
  "drifts": [
    {
      "resource_type": "string",
      "resource_id": "string",
      "changes": [
        {
          "property": "string",
          "old_value": "any",
          "new_value": "any"
        }
      ]
    }
  ]
}
```

## API Layer

### FastAPI Application

- RESTful API endpoints
- Async request handling
- Background task processing

### Endpoints

- `/initialize`: Initialize drift detector
- `/collect`: Collect current configuration
- `/latest-snapshot`: Get latest snapshot
- `/latest-drift`: Get latest drift report
- `/health`: Health check endpoint

## Background Tasks

### Task Types

1. **Configuration Collection**

   - Regular resource state collection
   - Background snapshot creation

2. **Drift Detection**

   - Asynchronous drift analysis
   - Report generation

3. **Maintenance Tasks**
   - Data cleanup
   - Index maintenance

## Security

### Authentication

- Azure AD integration
- Service principal authentication
- API key management

### Authorization

- Role-based access control
- Resource-level permissions
- API endpoint protection

## Monitoring

### Metrics

- Drift detection metrics
- Performance metrics
- Resource usage metrics

### Logging

- Structured logging
- Error tracking
- Audit logging

## Deployment

### Requirements

- Python 3.8+
- MongoDB 4.4+
- Azure subscription
- Required environment variables:
  ```
  MONGODB_URL=mongodb://localhost:27017
  MONGODB_DB_NAME=azure_drift
  ```

### Configuration

- Environment-based configuration
- MongoDB connection settings
- Azure credentials
