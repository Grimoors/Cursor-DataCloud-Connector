# API Reference

This document provides comprehensive documentation for the Salesforce Data Cloud Middleware API endpoints, including request/response formats, authentication, and error handling.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication using an API key passed in the `X-API-Key` header.

```http
X-API-Key: your_secure_api_key_here
```

## Common Headers

```http
Content-Type: application/json
Accept: application/json
X-Correlation-ID: req-12345-abc123def
```

## Response Format

All API responses follow a consistent format:

```json
{
  "status": "success|error|partial",
  "data": { ... },
  "error": {
    "code": "error_code",
    "message": "Human readable error message",
    "details": "Additional error details"
  },
  "correlation_id": "req-12345-abc123def",
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time_ms": 150.5
}
```

## Endpoints

### 1. Health Check

**GET** `/health`

Returns the health status of the middleware service.

#### Request

```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime_seconds": 3600.0,
  "token_info": {
    "platform_token": {
      "has_token": true,
      "expires_in": 7200
    },
    "data_cloud_token": {
      "has_token": true,
      "expires_in": 3600
    }
  },
  "dependencies": {
    "salesforce_api": "healthy",
    "data_cloud_api": "healthy"
  }
}
```

### 2. Execute Query

**POST** `/query`

Executes a query against Salesforce Data Cloud.

#### Request

```json
{
  "query": "Show me recent cases for user@example.com",
  "query_type": "natural_language",
  "object_type": "Case__dlm",
  "limit": 100,
  "offset": 0,
  "include_metadata": true,
  "enrich_data": true,
  "correlation_id": "req-12345-abc123def"
}
```

#### Request Parameters

| Parameter          | Type    | Required | Description                                           |
| ------------------ | ------- | -------- | ----------------------------------------------------- |
| `query`            | string  | Yes      | The query to execute (SOQL, SQL, or natural language) |
| `query_type`       | string  | No       | Type of query (`soql`, `sql`, `natural_language`)     |
| `object_type`      | string  | No       | Salesforce object type to query                       |
| `limit`            | integer | No       | Maximum number of records to return (1-1000)          |
| `offset`           | integer | No       | Number of records to skip for pagination              |
| `include_metadata` | boolean | No       | Whether to include metadata in response               |
| `enrich_data`      | boolean | No       | Whether to perform data enrichment                    |
| `correlation_id`   | string  | No       | Request correlation ID for tracking                   |

#### Response

```json
{
  "status": "success",
  "data": {
    "query": "SELECT Id, CaseNumber, Subject, Status FROM Case__dlm WHERE Contact.Email = 'user@example.com' ORDER BY CreatedDate DESC LIMIT 5",
    "query_type": "soql",
    "records": [
      {
        "Id": "500xx000003DIloAAG",
        "CaseNumber": "CASE-001",
        "Subject": "Technical Support Request",
        "Status": "Open",
        "CreatedDate": "2024-01-15T10:30:00Z"
      }
    ],
    "total_size": 1,
    "done": true,
    "next_records_url": null,
    "metadata": {
      "record_id": "500xx000003DIloAAG",
      "object_type": "Case__dlm",
      "created_date": "2024-01-15T10:30:00Z",
      "last_modified_date": "2024-01-15T10:30:00Z",
      "record_type": "Case",
      "owner_id": "005xx000003DIloAAG"
    },
    "execution_time_ms": 150.5
  },
  "correlation_id": "req-12345-abc123def",
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time_ms": 200.0
}
```

### 3. Get User Profile

**POST** `/user-profile`

Retrieves comprehensive user profile information including related data.

#### Request

```json
{
  "email": "user@example.com",
  "include_related_data": true,
  "correlation_id": "req-12345-abc123def"
}
```

#### Request Parameters

| Parameter              | Type    | Required | Description                                            |
| ---------------------- | ------- | -------- | ------------------------------------------------------ |
| `email`                | string  | Yes      | The user's email address                               |
| `include_related_data` | boolean | No       | Whether to include related data (cases, opportunities) |
| `correlation_id`       | string  | No       | Request correlation ID for tracking                    |

#### Response

```json
{
  "status": "success",
  "user_profile": {
    "Id": "001xx000003DIloAAG",
    "FirstName__c": "John",
    "LastName__c": "Doe",
    "Email__c": "john.doe@example.com",
    "Phone__c": "+1-555-0123",
    "Company__c": "Acme Corp",
    "Title__c": "Software Engineer",
    "CreatedDate": "2020-01-15T10:30:00Z",
    "LastModifiedDate": "2024-01-15T10:30:00Z"
  },
  "related_data": {
    "cases": [
      {
        "CaseNumber": "CASE-001",
        "Subject": "Technical Support",
        "Status": "Open",
        "Priority": "High"
      }
    ],
    "opportunities": [
      {
        "Name": "Enterprise License",
        "Amount": 50000,
        "StageName": "Proposal",
        "CloseDate": "2024-03-15"
      }
    ]
  },
  "correlation_id": "req-12345-abc123def",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. Get User Cases

**POST** `/cases`

Retrieves support cases for a specific user.

#### Request

```json
{
  "email": "user@example.com",
  "status_filter": "Open",
  "limit": 5,
  "include_case_details": true,
  "correlation_id": "req-12345-abc123def"
}
```

#### Request Parameters

| Parameter              | Type    | Required | Description                                     |
| ---------------------- | ------- | -------- | ----------------------------------------------- |
| `email`                | string  | Yes      | The user's email address                        |
| `status_filter`        | string  | No       | Filter cases by status (e.g., "Open", "Closed") |
| `limit`                | integer | No       | Maximum number of cases to return (1-50)        |
| `include_case_details` | boolean | No       | Whether to include detailed case information    |
| `correlation_id`       | string  | No       | Request correlation ID for tracking             |

#### Response

```json
{
  "status": "success",
  "cases": [
    {
      "CaseNumber": "CASE-001",
      "Subject": "Technical Support Request",
      "Status": "Open",
      "Priority": "High",
      "CreatedDate": "2024-01-15T10:30:00Z",
      "Description": "User experiencing login issues",
      "DaysOpen": 2,
      "IsHighPriority": true
    }
  ],
  "total_count": 1,
  "correlation_id": "req-12345-abc123def",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 5. Get Loyalty Information

**POST** `/loyalty`

Retrieves loyalty program information for a user.

#### Request

```json
{
  "email": "user@example.com",
  "include_transaction_history": false,
  "correlation_id": "req-12345-abc123def"
}
```

#### Request Parameters

| Parameter                     | Type    | Required | Description                            |
| ----------------------------- | ------- | -------- | -------------------------------------- |
| `email`                       | string  | Yes      | The user's email address               |
| `include_transaction_history` | boolean | No       | Whether to include transaction history |
| `correlation_id`              | string  | No       | Request correlation ID for tracking    |

#### Response

```json
{
  "status": "success",
  "loyalty_info": {
    "Tier__c": "Gold",
    "PointsBalance__c": 2500,
    "MemberSince__c": "2020-01-15",
    "NextTierThreshold__c": 5000,
    "LastTransactionDate__c": "2024-01-15"
  },
  "transaction_history": [
    {
      "TransactionDate": "2024-01-15",
      "PointsEarned": 100,
      "TransactionType": "Purchase",
      "Description": "Online purchase"
    }
  ],
  "correlation_id": "req-12345-abc123def",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 6. Batch Query

**POST** `/batch-query`

Executes multiple queries in a single request.

#### Request

```json
{
  "queries": [
    {
      "query": "SELECT Id, FirstName__c FROM UnifiedIndividual__dlm WHERE Email__c = 'user@example.com'",
      "query_type": "soql"
    },
    {
      "query": "Show me recent cases for user@example.com",
      "query_type": "natural_language"
    }
  ],
  "correlation_id": "req-12345-abc123def"
}
```

#### Request Parameters

| Parameter        | Type   | Required | Description                           |
| ---------------- | ------ | -------- | ------------------------------------- |
| `queries`        | array  | Yes      | Array of query objects (1-10 queries) |
| `correlation_id` | string | No       | Request correlation ID for tracking   |

#### Response

```json
{
  "status": "success",
  "results": [
    {
      "status": "success",
      "data": {
        "query": "SELECT Id, FirstName__c FROM UnifiedIndividual__dlm WHERE Email__c = 'user@example.com'",
        "query_type": "soql",
        "records": [
          {
            "Id": "001xx000003DIloAAG",
            "FirstName__c": "John"
          }
        ],
        "total_size": 1,
        "done": true
      }
    },
    {
      "status": "success",
      "data": {
        "query": "Show me recent cases for user@example.com",
        "query_type": "natural_language",
        "records": [
          {
            "CaseNumber": "CASE-001",
            "Subject": "Technical Support",
            "Status": "Open"
          }
        ],
        "total_size": 1,
        "done": true
      }
    }
  ],
  "total_queries": 2,
  "successful_queries": 2,
  "failed_queries": 0,
  "correlation_id": "req-12345-abc123def",
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time_ms": 500.0
}
```

## Error Codes

The API uses the following error codes:

| Code                    | Description                                         |
| ----------------------- | --------------------------------------------------- |
| `authentication_failed` | Authentication failed (invalid API key, JWT issues) |
| `invalid_query`         | Query syntax or format is invalid                   |
| `rate_limit_exceeded`   | Rate limit exceeded                                 |
| `data_not_found`        | Requested data not found                            |
| `internal_error`        | Internal server error                               |
| `validation_error`      | Request validation failed                           |
| `query_timeout`         | Query execution timed out                           |

## Error Response Example

```json
{
  "status": "error",
  "error": {
    "code": "authentication_failed",
    "message": "Invalid API key provided",
    "details": "The API key 'invalid_key' is not authorized",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "correlation_id": "req-12345-abc123def",
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time_ms": 5.0
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default**: 60 requests per minute per client
- **Headers**: Rate limit information is included in response headers
- **Exceeded**: Returns 429 status code with rate limit details

## Pagination

For endpoints that return multiple records, pagination is supported:

- **Limit**: Maximum number of records per request (default: 100, max: 1000)
- **Offset**: Number of records to skip
- **Next URL**: Some responses include a `next_records_url` for the next page

## Query Types

### SOQL Queries

```json
{
  "query": "SELECT Id, FirstName__c, LastName__c FROM UnifiedIndividual__dlm WHERE Email__c = 'user@example.com'",
  "query_type": "soql"
}
```

### SQL Queries

```json
{
  "query": "SELECT * FROM LoyaltyMember__dmo WHERE Email__c = 'user@example.com'",
  "query_type": "sql"
}
```

### Natural Language Queries

```json
{
  "query": "Show me recent cases for user@example.com",
  "query_type": "natural_language"
}
```

## Data Enrichment

When `enrich_data` is enabled, the API performs additional processing:

- **Computed fields**: Days open, priority flags, etc.
- **Related data**: Merged from multiple queries
- **Formatted output**: Human-readable summaries
- **Metadata**: Additional context and timestamps

## Testing

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Execute query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "query": "Show me user profile for user@example.com",
    "query_type": "natural_language"
  }'
```

### Using Postman

1. **Set base URL**: `http://localhost:8000`
2. **Add headers**:
   - `Content-Type: application/json`
   - `X-API-Key: your_api_key`
3. **Create requests** using the examples above

## SDK Examples

### Python

```python
import requests

base_url = "http://localhost:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your_api_key"
}

# Execute query
response = requests.post(
    f"{base_url}/query",
    headers=headers,
    json={
        "query": "Show me recent cases for user@example.com",
        "query_type": "natural_language"
    }
)

data = response.json()
print(data["data"]["records"])
```

### JavaScript

```javascript
const baseUrl = "http://localhost:8000/api/v1";
const headers = {
  "Content-Type": "application/json",
  "X-API-Key": "your_api_key",
};

// Execute query
const response = await fetch(`${baseUrl}/query`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    query: "Show me recent cases for user@example.com",
    query_type: "natural_language",
  }),
});

const data = await response.json();
console.log(data.data.records);
```

## Monitoring

### Health Checks

Monitor the health endpoint for service status:

```bash
# Check health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

### Metrics

The API provides processing time metrics in responses:

```json
{
  "processing_time_ms": 150.5,
  "data": {
    "execution_time_ms": 100.2
  }
}
```

### Logs

Enable debug logging for detailed request/response information:

```bash
LOG_LEVEL=DEBUG python -m src.main
```

## Security

### API Key Management

- Use strong, unique API keys
- Rotate keys regularly
- Store keys securely
- Never expose keys in client-side code

### Input Validation

All inputs are validated and sanitized:

- SQL injection prevention
- XSS protection
- Rate limiting
- Input length limits

### HTTPS

Use HTTPS in production:

```bash
# Configure SSL certificates
# Update extension configuration
# Use secure WebSocket connections
```
