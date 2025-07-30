"""
Response models for the Salesforce Data Cloud Middleware API.

This module defines Pydantic models for validating and documenting
API response payloads.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    """Enumeration of response status values."""
    
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class ErrorCode(str, Enum):
    """Enumeration of error codes."""
    
    AUTHENTICATION_FAILED = "authentication_failed"
    INVALID_QUERY = "invalid_query"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_NOT_FOUND = "data_not_found"
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    QUERY_TIMEOUT = "query_timeout"


class RecordMetadata(BaseModel):
    """
    Metadata for a data record.
    
    This model contains metadata information about a single record
    returned from Salesforce Data Cloud.
    """
    
    record_id: str = Field(
        ...,
        description="Unique identifier for the record."
    )
    
    object_type: str = Field(
        ...,
        description="The Salesforce object type of the record."
    )
    
    created_date: Optional[datetime] = Field(
        None,
        description="When the record was created."
    )
    
    last_modified_date: Optional[datetime] = Field(
        None,
        description="When the record was last modified."
    )
    
    record_type: Optional[str] = Field(
        None,
        description="The record type of the record."
    )
    
    owner_id: Optional[str] = Field(
        None,
        description="The owner of the record."
    )


class QueryResult(BaseModel):
    """
    Result of a single query execution.
    
    This model represents the result of executing a query against
    Salesforce Data Cloud.
    """
    
    query: str = Field(
        ...,
        description="The original query that was executed."
    )
    
    query_type: str = Field(
        ...,
        description="The type of query that was executed."
    )
    
    records: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="The records returned by the query."
    )
    
    total_size: int = Field(
        default=0,
        description="Total number of records returned."
    )
    
    done: bool = Field(
        default=True,
        description="Whether all records have been returned."
    )
    
    next_records_url: Optional[str] = Field(
        None,
        description="URL for the next page of records (if pagination is used)."
    )
    
    metadata: Optional[RecordMetadata] = Field(
        None,
        description="Metadata about the query result."
    )
    
    execution_time_ms: Optional[float] = Field(
        None,
        description="Time taken to execute the query in milliseconds."
    )


class ErrorDetail(BaseModel):
    """
    Detailed error information.
    
    This model provides detailed information about errors that occur
    during API operations.
    """
    
    code: ErrorCode = Field(
        ...,
        description="The error code."
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message."
    )
    
    details: Optional[str] = Field(
        None,
        description="Additional error details."
    )
    
    field: Optional[str] = Field(
        None,
        description="The field that caused the error (if applicable)."
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred."
    )


class QueryResponse(BaseModel):
    """
    Response model for query operations.
    
    This model represents the response to a query request, including
    the results and any metadata.
    """
    
    status: ResponseStatus = Field(
        ...,
        description="The status of the response."
    )
    
    data: Optional[QueryResult] = Field(
        None,
        description="The query result data."
    )
    
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error information if the request failed."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated."
    )
    
    processing_time_ms: Optional[float] = Field(
        None,
        description="Total processing time in milliseconds."
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "query": "SELECT Id, FirstName__c, LastName__c FROM UnifiedIndividual__dlm WHERE Email__c = 'user@example.com'",
                    "query_type": "soql",
                    "records": [
                        {
                            "Id": "001xx000003DIloAAG",
                            "FirstName__c": "John",
                            "LastName__c": "Doe"
                        }
                    ],
                    "total_size": 1,
                    "done": True,
                    "execution_time_ms": 150.5
                },
                "correlation_id": "req-12345",
                "timestamp": "2024-01-15T10:30:00Z",
                "processing_time_ms": 200.0
            }
        }


class UserProfileResponse(BaseModel):
    """
    Response model for user profile queries.
    
    This model represents the response to a user profile query,
    including enriched user data.
    """
    
    status: ResponseStatus = Field(
        ...,
        description="The status of the response."
    )
    
    user_profile: Optional[Dict[str, Any]] = Field(
        None,
        description="The user profile data."
    )
    
    related_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Related data (cases, opportunities, etc.)."
    )
    
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error information if the request failed."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated."
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "user_profile": {
                    "Id": "001xx000003DIloAAG",
                    "FirstName__c": "John",
                    "LastName__c": "Doe",
                    "Email__c": "john.doe@example.com",
                    "Phone__c": "+1-555-0123",
                    "Company__c": "Acme Corp"
                },
                "related_data": {
                    "cases": [
                        {
                            "CaseNumber": "CASE-001",
                            "Subject": "Technical Support",
                            "Status": "Open"
                        }
                    ],
                    "opportunities": [
                        {
                            "Name": "Enterprise License",
                            "Amount": 50000,
                            "StageName": "Proposal"
                        }
                    ]
                }
            }
        }


class CaseResponse(BaseModel):
    """
    Response model for case queries.
    
    This model represents the response to a case query,
    including case details and related information.
    """
    
    status: ResponseStatus = Field(
        ...,
        description="The status of the response."
    )
    
    cases: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="The cases returned by the query."
    )
    
    total_count: int = Field(
        default=0,
        description="Total number of cases found."
    )
    
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error information if the request failed."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated."
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "cases": [
                    {
                        "CaseNumber": "CASE-001",
                        "Subject": "Technical Support Request",
                        "Status": "Open",
                        "Priority": "High",
                        "CreatedDate": "2024-01-15T10:30:00Z",
                        "Description": "User experiencing login issues"
                    }
                ],
                "total_count": 1
            }
        }


class LoyaltyResponse(BaseModel):
    """
    Response model for loyalty program queries.
    
    This model represents the response to a loyalty program query,
    including loyalty status and transaction history.
    """
    
    status: ResponseStatus = Field(
        ...,
        description="The status of the response."
    )
    
    loyalty_info: Optional[Dict[str, Any]] = Field(
        None,
        description="The loyalty program information."
    )
    
    transaction_history: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Transaction history (if requested)."
    )
    
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error information if the request failed."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated."
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "loyalty_info": {
                    "Tier__c": "Gold",
                    "PointsBalance__c": 2500,
                    "MemberSince__c": "2020-01-15",
                    "NextTierThreshold__c": 5000
                },
                "transaction_history": [
                    {
                        "TransactionDate": "2024-01-15",
                        "PointsEarned": 100,
                        "TransactionType": "Purchase"
                    }
                ]
            }
        }


class BatchQueryResponse(BaseModel):
    """
    Response model for batch query operations.
    
    This model represents the response to a batch query request,
    including results for multiple queries.
    """
    
    status: ResponseStatus = Field(
        ...,
        description="The status of the response."
    )
    
    results: List[QueryResponse] = Field(
        default_factory=list,
        description="Results for each query in the batch."
    )
    
    total_queries: int = Field(
        default=0,
        description="Total number of queries in the batch."
    )
    
    successful_queries: int = Field(
        default=0,
        description="Number of queries that executed successfully."
    )
    
    failed_queries: int = Field(
        default=0,
        description="Number of queries that failed."
    )
    
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error information if the entire batch failed."
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for request tracking."
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the response was generated."
    )
    
    processing_time_ms: Optional[float] = Field(
        None,
        description="Total processing time in milliseconds."
    )


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoints.
    
    This model represents the response to a health check request,
    including system status and token information.
    """
    
    status: str = Field(
        ...,
        description="The health status of the system."
    )
    
    version: str = Field(
        ...,
        description="The version of the middleware."
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the health check was performed."
    )
    
    uptime_seconds: Optional[float] = Field(
        None,
        description="System uptime in seconds."
    )
    
    token_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Token information (if requested)."
    )
    
    system_info: Optional[Dict[str, Any]] = Field(
        None,
        description="System information (if requested)."
    )
    
    dependencies: Optional[Dict[str, str]] = Field(
        None,
        description="Status of system dependencies."
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "uptime_seconds": 3600.0,
                "token_info": {
                    "platform_token": {
                        "has_token": True,
                        "expires_in": 7200
                    },
                    "data_cloud_token": {
                        "has_token": True,
                        "expires_in": 3600
                    }
                },
                "dependencies": {
                    "salesforce_api": "healthy",
                    "data_cloud_api": "healthy"
                }
            }
        } 