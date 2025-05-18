# Azure Drift Detection Service API Documentation

## Overview

The Azure Drift Detection Service provides a RESTful API for managing and monitoring configuration drift in Azure resources. This document details the available endpoints, request/response formats, and authentication requirements.

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints require authentication using Azure AD tokens. Include the token in the Authorization header:

```
Authorization: Bearer <token>
```

## API Endpoints

### Health Check

```http
GET /health
```

Checks the health status of the service.

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2024-03-21T10:00:00Z"
}
```

### Initialize Drift Detector

```http
POST /initialize
```

Initializes the drift detector with subscription and resource group information.

#### Request Body

```json
{
  "subscription_id": "string",
  "resource_group": "string"
}
```

#### Response

```json
{
  "message": "Drift detector initialized successfully",
  "subscription_id": "string",
  "resource_group": "string"
}
```

### Collect Configuration

```http
POST /collect
```

Collects current configuration from Azure resources and saves it as a snapshot.

#### Response

```json
{
  "message": "Configuration collection started",
  "snapshot_id": "string",
  "timestamp": "2024-03-21T10:00:00Z"
}
```

### Get Latest Snapshot

```http
GET /latest-snapshot
```

Retrieves the most recent configuration snapshot.

#### Response

```json
{
  "snapshot_id": "string",
  "timestamp": "2024-03-21T10:00:00Z",
  "configuration": {
    "resources": {},
    "security_settings": {},
    "rbac_assignments": {},
    "monitoring_settings": {}
  }
}
```

### Get Latest Drift Report

```http
GET /latest-drift
```

Retrieves the most recent drift detection report.

#### Response

```json
{
  "report_id": "string",
  "timestamp": "2024-03-21T10:00:00Z",
  "changes": {
    "resources": [],
    "security_settings": [],
    "rbac_assignments": [],
    "monitoring_settings": []
  },
  "summary": {
    "total_changes": 0,
    "severity": "low|medium|high"
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid request parameters",
  "details": {}
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}
```

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- 60 requests per minute per client
- 1000 requests per hour per client

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1616323200
```

## Data Models

### Configuration Snapshot

```json
{
  "snapshot_id": "string",
  "timestamp": "string",
  "configuration": {
    "resources": {
      "virtual_machines": [],
      "storage_accounts": [],
      "networks": []
    },
    "security_settings": {
      "firewall_rules": [],
      "security_groups": []
    },
    "rbac_assignments": {
      "role_assignments": [],
      "permissions": []
    },
    "monitoring_settings": {
      "alerts": [],
      "metrics": []
    }
  }
}
```

### Drift Report

```json
{
  "report_id": "string",
  "timestamp": "string",
  "changes": {
    "resources": [
      {
        "resource_id": "string",
        "change_type": "added|modified|deleted",
        "details": {}
      }
    ],
    "security_settings": [],
    "rbac_assignments": [],
    "monitoring_settings": []
  },
  "summary": {
    "total_changes": 0,
    "severity": "low|medium|high",
    "categories": {
      "security": 0,
      "configuration": 0,
      "access": 0
    }
  }
}
```

## Best Practices

1. Always handle rate limiting in your client applications
2. Implement proper error handling
3. Cache responses when appropriate
4. Use appropriate authentication mechanisms
5. Monitor API usage and performance
