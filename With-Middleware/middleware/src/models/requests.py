"""
Request models for the Salesforce Data Cloud Middleware API.

This module defines Pydantic models for validating and documenting
API request payloads.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class QueryType(str, Enum):
    """Enumeration of supported query types."""
    
    SOQL = "soql"
    SQL = "sql"
    NATURAL_LANGUAGE = "natural_language"


class DataObjectType(str, Enum):
    """Enumeration of Salesforce Data Cloud object types."""
    
    UNIFIED_INDIVIDUAL = "UnifiedIndividual__dlm"
    CASE = "Case__dlm"
    ACCOUNT = "Account__dlm"
    CONTACT = "Contact__dlm"
    OPPORTUNITY = "Opportunity__dlm"
    LOYALTY_MEMBER = "LoyaltyMember__dmo"
    CUSTOMER_PROFILE = "CustomerProfile__dmo"


class QueryRequest(BaseModel):
    """
    Request model for data queries.
    
    This model validates and documents the structure of query requests
    sent to the middleware API.
    """
    
    query: str = Field(
        ...,
        description="The query to execute. Can be SOQL, SQL, or natural language.",
        min_length=1,
        max_length=10000,
        example="SELECT Id, FirstName__c, LastName__c FROM UnifiedIndividual__dlm WHERE Email__c = 'user@example.com'"
    )
    
    query_type: QueryType = Field(
        default=QueryType.NATURAL_LANGUAGE,
        description="The type of query being executed."
    )
    
    object_type: Optional[DataObjectType] = Field(
        None,
        description="The Salesforce object type to query (optional for natural language queries)."
    )
    
    limit: Optional[int] = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return."
    )
    
    offset: Optional[int] = Field(
        default=0,
        ge=0,
        description="Number of records to skip (for pagination)."
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Whether to include metadata in the response."
    )
    
    enrich_data: bool = Field(
        default=True,
        description="Whether to perform data enrichment on the results."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate that the query is not empty and contains valid characters."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        
        # Check for potentially dangerous SQL injection patterns
        dangerous_patterns = [
            ';', '--', '/*', '*/', 'DROP', 'DELETE', 'UPDATE', 'INSERT',
            'CREATE', 'ALTER', 'EXEC', 'EXECUTE'
        ]
        
        query_upper = v.upper()
        for pattern in dangerous_patterns:
            if pattern in query_upper:
                raise ValueError(f"Query contains potentially dangerous pattern: {pattern}")
        
        return v.strip()
    
    @validator('correlation_id')
    def validate_correlation_id(cls, v):
        """Validate correlation ID format."""
        if v is not None and len(v) > 100:
            raise ValueError("Correlation ID must be 100 characters or less")
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "query": "Show me recent cases for user@example.com",
                "query_type": "natural_language",
                "limit": 10,
                "include_metadata": True,
                "enrich_data": True
            }
        }


class UserProfileRequest(BaseModel):
    """
    Request model for user profile queries.
    
    This model is specifically for querying user profile information
    from Salesforce Data Cloud.
    """
    
    email: str = Field(
        ...,
        description="The email address of the user to query.",
        example="user@example.com"
    )
    
    include_related_data: bool = Field(
        default=True,
        description="Whether to include related data (cases, opportunities, etc.)."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "include_related_data": True
            }
        }


class CaseQueryRequest(BaseModel):
    """
    Request model for case queries.
    
    This model is specifically for querying case information
    from Salesforce Data Cloud.
    """
    
    email: str = Field(
        ...,
        description="The email address to query cases for.",
        example="user@example.com"
    )
    
    status_filter: Optional[str] = Field(
        None,
        description="Filter cases by status (e.g., 'Open', 'Closed')."
    )
    
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of cases to return."
    )
    
    include_case_details: bool = Field(
        default=True,
        description="Whether to include detailed case information."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "status_filter": "Open",
                "limit": 5,
                "include_case_details": True
            }
        }


class LoyaltyQueryRequest(BaseModel):
    """
    Request model for loyalty program queries.
    
    This model is specifically for querying loyalty program information
    from Salesforce Data Cloud.
    """
    
    email: str = Field(
        ...,
        description="The email address to query loyalty information for.",
        example="user@example.com"
    )
    
    include_transaction_history: bool = Field(
        default=False,
        description="Whether to include transaction history."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "include_transaction_history": False
            }
        }


class BatchQueryRequest(BaseModel):
    """
    Request model for batch queries.
    
    This model allows multiple queries to be executed in a single request.
    """
    
    queries: List[QueryRequest] = Field(
        ...,
        description="List of queries to execute.",
        min_items=1,
        max_items=10
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    @validator('queries')
    def validate_queries(cls, v):
        """Validate that queries are not empty and within limits."""
        if not v:
            raise ValueError("At least one query must be provided")
        
        if len(v) > 10:
            raise ValueError("Maximum of 10 queries allowed per batch")
        
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "queries": [
                    {
                        "query": "SELECT Id, FirstName__c FROM UnifiedIndividual__dlm WHERE Email__c = 'user@example.com'",
                        "query_type": "soql"
                    },
                    {
                        "query": "Show me recent cases for user@example.com",
                        "query_type": "natural_language"
                    }
                ]
            }
        }


class HealthCheckRequest(BaseModel):
    """
    Request model for health check endpoints.
    
    This model is used for health check and status endpoints.
    """
    
    include_token_info: bool = Field(
        default=False,
        description="Whether to include token information in the response."
    )
    
    include_system_info: bool = Field(
        default=False,
        description="Whether to include system information in the response."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "include_token_info": True,
                "include_system_info": True
            }
        } 