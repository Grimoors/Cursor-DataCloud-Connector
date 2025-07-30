# Development Guide

This guide is for developers who want to extend, modify, or contribute to the Salesforce Data Cloud MCP Server.

## Project Structure

```
Cursor-DataCloud-Connector/
├── src/
│   └── salesforce_mcp/
│       ├── __init__.py          # Package initialization
│       ├── auth.py              # Authentication module
│       └── server.py            # Main MCP server
├── scripts/
│   ├── setup.sh                 # Automated setup script
│   └── test_connection.py       # Connection test script
├── docs/
│   ├── SETUP_GUIDE.md          # Detailed setup instructions
│   ├── USAGE_EXAMPLES.md       # Usage examples
│   └── DEVELOPMENT.md           # This file
├── .cursor/
│   └── mcp.json                # Cursor MCP configuration
├── pyproject.toml              # Project configuration
├── env.example                 # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # Main documentation
```

## Development Environment Setup

### 1. Install Development Dependencies

```bash
# Install development dependencies
uv add --dev pytest black flake8 mypy

# Install the package in development mode
uv pip install -e .
```

### 2. Configure Pre-commit Hooks

Create a `.pre-commit-config.yaml` file:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203, W503]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### 3. Run Code Quality Checks

```bash
# Format code
black src/ scripts/

# Lint code
flake8 src/ scripts/

# Type checking
mypy src/

# Run tests
pytest tests/
```

## Architecture Overview

### Authentication Flow

The authentication system uses a two-step OAuth 2.0 JWT Bearer Flow:

1. **JWT Creation**: Creates a signed JWT using the private key
2. **Token Exchange**: Exchanges JWT for Salesforce access token
3. **Data Cloud Token**: Exchanges Salesforce token for Data Cloud token
4. **Caching**: Caches tokens with automatic refresh

### MCP Server Structure

The server is built using the `mcp.server.fastmcp` framework:

- **FastMCP**: Main server class that handles tool registration
- **Tool Decorators**: `@mcp.tool()` decorators define available tools
- **Error Handling**: Comprehensive error handling for API failures
- **Logging**: Structured logging for debugging

## Adding New Tools

### 1. Define the Tool Function

Add a new function to `src/salesforce_mcp/server.py`:

```python
@mcp.tool()
def your_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    Description of what this tool does.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2

    Returns:
        Dictionary with 'success' status and 'data' or 'error'
    """
    print(f"Executing tool 'your_new_tool' with params: {param1}, {param2}")

    try:
        # Get valid access token
        access_token, instance_url = sf_auth.get_token()

        # Your tool logic here
        # Make API calls, process data, etc.

        return {
            "success": True,
            "data": result_data
        }

    except Exception as e:
        error_message = f"Tool execution failed: {str(e)}"
        print(f"❌ {error_message}")
        return {
            "success": False,
            "error": error_message
        }
```

### 2. Update Documentation

- Add the tool to the README.md
- Create usage examples in `docs/USAGE_EXAMPLES.md`
- Update any relevant setup instructions

### 3. Add Tests

Create tests in `tests/test_server.py`:

```python
def test_your_new_tool():
    """Test the your_new_tool function."""
    # Mock the authentication
    with patch('salesforce_mcp.server.sf_auth.get_token') as mock_auth:
        mock_auth.return_value = ("fake_token", "https://fake.instance.com")

        # Mock the API response
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"test": "data"}
            mock_post.return_value.raise_for_status.return_value = None

            result = your_new_tool("test_param", 123)

            assert result["success"] is True
            assert "data" in result
```

## Adding CRUD Operations

To add create, update, and delete operations, you'll need to:

### 1. Update OAuth Scopes

Add these scopes to your Connected App:

- `cdp_ingest_api` - For data ingestion
- `cdp_profile_api` - For profile management

### 2. Create CRUD Tools

```python
@mcp.tool()
def create_record(object_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new record in Data Cloud.

    Args:
        object_name: The Data Model Object name
        data: The record data to create

    Returns:
        Dictionary with 'success' status and created record or error
    """
    # Implementation here
    pass

@mcp.tool()
def update_record(object_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing record in Data Cloud.

    Args:
        object_name: The Data Model Object name
        record_id: The ID of the record to update
        data: The updated data

    Returns:
        Dictionary with 'success' status and updated record or error
    """
    # Implementation here
    pass

@mcp.tool()
def delete_record(object_name: str, record_id: str) -> Dict[str, Any]:
    """
    Deletes a record from Data Cloud.

    Args:
        object_name: The Data Model Object name
        record_id: The ID of the record to delete

    Returns:
        Dictionary with 'success' status and result or error
    """
    # Implementation here
    pass
```

### 3. Update System Prompt

The system prompt should include safety instructions for CRUD operations:

```
6. **Safety and Modification:** If the user asks to create, update, or delete data, you must first acknowledge the request. Then, you must explicitly state that this is a modification operation with potential risks and that it cannot be undone. You must wait for the user to provide explicit, affirmative confirmation (e.g., "Yes, proceed," "Confirm," "Do it") before invoking any tool that modifies data.
```

## Error Handling Best Practices

### 1. HTTP Error Handling

```python
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
except requests.exceptions.HTTPError as e:
    error_message = f"HTTP Error {e.response.status_code}: {e.response.text}"
    print(f"❌ {error_message}")
    return {"success": False, "error": error_message}
```

### 2. Authentication Error Handling

```python
try:
    access_token, instance_url = sf_auth.get_token()
except Exception as e:
    error_message = f"Authentication failed: {str(e)}"
    print(f"❌ {error_message}")
    return {"success": False, "error": error_message}
```

### 3. Validation Error Handling

```python
def validate_sql_query(query: str) -> bool:
    """Validate that the SQL query is safe to execute."""
    # Add validation logic here
    # Check for dangerous keywords, injection attempts, etc.
    pass
```

## Testing

### 1. Unit Tests

Create comprehensive unit tests:

```python
# tests/test_auth.py
def test_salesforce_auth_initialization():
    """Test SalesforceAuth initialization."""
    with patch.dict(os.environ, {
        'SF_CLIENT_ID': 'test_client_id',
        'SF_USERNAME': 'test@example.com',
        'SF_PRIVATE_KEY_PATH': 'test.key'
    }):
        auth = SalesforceAuth()
        assert auth.client_id == 'test_client_id'
        assert auth.username == 'test@example.com'

# tests/test_server.py
def test_search_data_cloud_success():
    """Test successful data cloud search."""
    with patch('salesforce_mcp.server.sf_auth.get_token') as mock_auth:
        mock_auth.return_value = ("fake_token", "https://fake.instance.com")

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"records": []}
            mock_post.return_value.raise_for_status.return_value = None

            result = search_data_cloud("SELECT * FROM Contact__dlm LIMIT 1")

            assert result["success"] is True
            assert "data" in result
```

### 2. Integration Tests

Create integration tests that test the full flow:

```python
# tests/test_integration.py
def test_full_authentication_flow():
    """Test the complete authentication flow."""
    # This would require a test Salesforce org
    pass
```

### 3. Mock Testing

Use mocks for external dependencies:

```python
@patch('requests.post')
@patch('salesforce_mcp.auth.SalesforceAuth.get_token')
def test_api_call_with_mocks(mock_auth, mock_post):
    """Test API call with mocked dependencies."""
    mock_auth.return_value = ("fake_token", "https://fake.instance.com")
    mock_post.return_value.json.return_value = {"test": "data"}
    mock_post.return_value.raise_for_status.return_value = None

    # Your test logic here
```

## Performance Optimization

### 1. Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create a session with connection pooling
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

### 2. Caching

Implement caching for frequently accessed data:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def get_cached_metadata(object_name: str) -> Dict[str, Any]:
    """Cache metadata for frequently accessed objects."""
    # Implementation here
    pass
```

### 3. Async Support

For high-performance scenarios, consider async operations:

```python
import asyncio
import aiohttp

async def async_search_data_cloud(query: str) -> Dict[str, Any]:
    """Async version of search_data_cloud."""
    # Implementation here
    pass
```

## Security Considerations

### 1. Input Validation

Always validate user inputs:

```python
import re

def validate_sql_query(query: str) -> bool:
    """Validate SQL query for dangerous patterns."""
    dangerous_patterns = [
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
        r'TRUNCATE',
        r'ALTER\s+TABLE',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False

    return True
```

### 2. Rate Limiting

Implement rate limiting to prevent abuse:

```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        user_requests = self.requests[user_id]

        # Remove old requests
        user_requests[:] = [req_time for req_time in user_requests
                          if now - req_time < self.window_seconds]

        if len(user_requests) >= self.max_requests:
            return False

        user_requests.append(now)
        return True
```

### 3. Logging and Monitoring

Implement comprehensive logging:

```python
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_tool_execution(tool_name: str, params: Dict[str, Any], result: Dict[str, Any]):
    """Log tool execution for monitoring and debugging."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool_name,
        "params": params,
        "success": result.get("success", False),
        "error": result.get("error") if not result.get("success") else None
    }

    logger.info(f"Tool execution: {json.dumps(log_entry)}")
```

## Deployment

### 1. Docker Support

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv pip install .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the server
CMD ["uv", "run", "salesforce-mcp"]
```

### 2. Environment Management

Use environment-specific configurations:

```python
import os

def get_config():
    """Get configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return {
            "log_level": "WARNING",
            "rate_limit": 100,
            "cache_ttl": 3600
        }
    else:
        return {
            "log_level": "DEBUG",
            "rate_limit": 1000,
            "cache_ttl": 300
        }
```

## Contributing

### 1. Code Style

Follow the established code style:

- Use Black for formatting (88 character line length)
- Use type hints for all function parameters and return values
- Add docstrings for all public functions
- Use descriptive variable names

### 2. Commit Messages

Use conventional commit messages:

```
feat: add new CRUD operation tools
fix: resolve authentication token caching issue
docs: update setup guide with new OAuth scopes
test: add comprehensive test coverage for auth module
```

### 3. Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Run all tests and linting
7. Submit a pull request

### 4. Review Checklist

Before submitting a PR, ensure:

- [ ] All tests pass
- [ ] Code is formatted with Black
- [ ] No linting errors
- [ ] Documentation is updated
- [ ] Security considerations are addressed
- [ ] Performance impact is considered

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Salesforce Data Cloud API Guide](https://developer.salesforce.com/docs/data/data-cloud-ref/)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/fastmcp)
