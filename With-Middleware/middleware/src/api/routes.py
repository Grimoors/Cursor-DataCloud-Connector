"""
API routes for the Salesforce Data Cloud Middleware.

This module defines all the REST API endpoints for the middleware,
including query execution, user profile retrieval, and health checks.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.auth.oauth import get_salesforce_headers
from src.config.settings import get_settings
from src.models.requests import (
    BatchQueryRequest,
    CaseQueryRequest,
    HealthCheckRequest,
    LoyaltyQueryRequest,
    QueryRequest,
    UserProfileRequest,
)
from src.models.responses import (
    BatchQueryResponse,
    CaseResponse,
    ErrorCode,
    ErrorDetail,
    HealthCheckResponse,
    LoyaltyResponse,
    QueryResponse,
    QueryResult,
    RecordMetadata,
    ResponseStatus,
    UserProfileResponse,
)
from src.services.data_service import DataService
from src.services.query_service import QueryService
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Create API router
api_router = APIRouter()

# Global service instances
_settings = get_settings()
_data_service = DataService()
_query_service = QueryService()


def get_correlation_id(request: Request) -> Optional[str]:
    """
    Extract correlation ID from request headers.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        Optional[str]: The correlation ID if present
    """
    return request.headers.get("X-Correlation-ID")


async def validate_api_key(request: Request) -> bool:
    """
    Validate the API key from the request.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        bool: True if the API key is valid
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if not _settings.enable_api_key_validation:
        return True
    
    api_key = request.headers.get(_settings.api_key_header)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    if api_key not in _settings.allowed_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True


@api_router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    api_key_valid: bool = Depends(validate_api_key),
    correlation_id: Optional[str] = Depends(get_correlation_id)
) -> QueryResponse:
    """
    Execute a query against Salesforce Data Cloud.
    
    This endpoint supports SOQL, SQL, and natural language queries.
    The query is validated, executed, and the results are enriched
    before being returned.
    
    Args:
        request: The query request
        api_key_valid: API key validation result
        correlation_id: Request correlation ID
        
    Returns:
        QueryResponse: The query results
        
    Raises:
        HTTPException: If the query fails or authentication fails
    """
    start_time = time.time()
    
    try:
        logger.info("Executing query",
                   query=request.query,
                   query_type=request.query_type.value,
                   correlation_id=correlation_id)
        
        # Get Salesforce headers
        headers = await get_salesforce_headers(for_data_cloud=True)
        
        # Execute query
        result = await _query_service.execute_query(
            query=request.query,
            query_type=request.query_type.value,
            headers=headers,
            limit=request.limit,
            offset=request.offset,
            enrich_data=request.enrich_data
        )
        
        # Create response
        processing_time = (time.time() - start_time) * 1000
        
        response = QueryResponse(
            status=ResponseStatus.SUCCESS,
            data=QueryResult(
                query=request.query,
                query_type=request.query_type.value,
                records=result.get("records", []),
                total_size=result.get("totalSize", 0),
                done=result.get("done", True),
                next_records_url=result.get("nextRecordsUrl"),
                execution_time_ms=result.get("execution_time_ms"),
                metadata=RecordMetadata(
                    record_id=result.get("metadata", {}).get("record_id", ""),
                    object_type=result.get("metadata", {}).get("object_type", ""),
                    created_date=result.get("metadata", {}).get("created_date"),
                    last_modified_date=result.get("metadata", {}).get("last_modified_date"),
                    record_type=result.get("metadata", {}).get("record_type"),
                    owner_id=result.get("metadata", {}).get("owner_id")
                ) if result.get("metadata") else None
            ),
            correlation_id=correlation_id,
            processing_time_ms=processing_time
        )
        
        logger.info("Query executed successfully",
                   query=request.query,
                   record_count=len(result.get("records", [])),
                   processing_time_ms=processing_time,
                   correlation_id=correlation_id)
        
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        logger.error("Query execution failed",
                    query=request.query,
                    error=str(e),
                    processing_time_ms=processing_time,
                    correlation_id=correlation_id,
                    exc_info=True)
        
        error_detail = ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="Query execution failed",
            details=str(e),
            timestamp=datetime.utcnow()
        )
        
        return QueryResponse(
            status=ResponseStatus.ERROR,
            error=error_detail,
            correlation_id=correlation_id,
            processing_time_ms=processing_time
        )


@api_router.post("/user-profile", response_model=UserProfileResponse)
async def get_user_profile(
    request: UserProfileRequest,
    api_key_valid: bool = Depends(validate_api_key),
    correlation_id: Optional[str] = Depends(get_correlation_id)
) -> UserProfileResponse:
    """
    Get user profile information from Salesforce Data Cloud.
    
    This endpoint retrieves comprehensive user profile information
    including related data like cases and opportunities.
    
    Args:
        request: The user profile request
        api_key_valid: API key validation result
        correlation_id: Request correlation ID
        
    Returns:
        UserProfileResponse: The user profile data
        
    Raises:
        HTTPException: If the request fails or authentication fails
    """
    try:
        logger.info("Getting user profile",
                   email=request.email,
                   correlation_id=correlation_id)
        
        # Get Salesforce headers
        headers = await get_salesforce_headers(for_data_cloud=True)
        
        # Get user profile
        profile_data = await _data_service.get_user_profile(
            email=request.email,
            headers=headers,
            include_related_data=request.include_related_data
        )
        
        response = UserProfileResponse(
            status=ResponseStatus.SUCCESS,
            user_profile=profile_data.get("profile"),
            related_data=profile_data.get("related_data"),
            correlation_id=correlation_id
        )
        
        logger.info("User profile retrieved successfully",
                   email=request.email,
                   correlation_id=correlation_id)
        
        return response
        
    except Exception as e:
        logger.error("Failed to get user profile",
                    email=request.email,
                    error=str(e),
                    correlation_id=correlation_id,
                    exc_info=True)
        
        error_detail = ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to get user profile",
            details=str(e),
            timestamp=datetime.utcnow()
        )
        
        return UserProfileResponse(
            status=ResponseStatus.ERROR,
            error=error_detail,
            correlation_id=correlation_id
        )


@api_router.post("/cases", response_model=CaseResponse)
async def get_user_cases(
    request: CaseQueryRequest,
    api_key_valid: bool = Depends(validate_api_key),
    correlation_id: Optional[str] = Depends(get_correlation_id)
) -> CaseResponse:
    """
    Get cases for a user from Salesforce Data Cloud.
    
    This endpoint retrieves case information for a specific user,
    with optional filtering by status.
    
    Args:
        request: The case query request
        api_key_valid: API key validation result
        correlation_id: Request correlation ID
        
    Returns:
        CaseResponse: The case data
        
    Raises:
        HTTPException: If the request fails or authentication fails
    """
    try:
        logger.info("Getting user cases",
                   email=request.email,
                   status_filter=request.status_filter,
                   limit=request.limit,
                   correlation_id=correlation_id)
        
        # Get Salesforce headers
        headers = await get_salesforce_headers(for_data_cloud=True)
        
        # Get cases
        cases_data = await _data_service.get_user_cases(
            email=request.email,
            headers=headers,
            status_filter=request.status_filter,
            limit=request.limit,
            include_case_details=request.include_case_details
        )
        
        response = CaseResponse(
            status=ResponseStatus.SUCCESS,
            cases=cases_data.get("cases", []),
            total_count=cases_data.get("total_count", 0),
            correlation_id=correlation_id
        )
        
        logger.info("User cases retrieved successfully",
                   email=request.email,
                   case_count=len(cases_data.get("cases", [])),
                   correlation_id=correlation_id)
        
        return response
        
    except Exception as e:
        logger.error("Failed to get user cases",
                    email=request.email,
                    error=str(e),
                    correlation_id=correlation_id,
                    exc_info=True)
        
        error_detail = ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to get user cases",
            details=str(e),
            timestamp=datetime.utcnow()
        )
        
        return CaseResponse(
            status=ResponseStatus.ERROR,
            error=error_detail,
            correlation_id=correlation_id
        )


@api_router.post("/loyalty", response_model=LoyaltyResponse)
async def get_loyalty_info(
    request: LoyaltyQueryRequest,
    api_key_valid: bool = Depends(validate_api_key),
    correlation_id: Optional[str] = Depends(get_correlation_id)
) -> LoyaltyResponse:
    """
    Get loyalty program information for a user.
    
    This endpoint retrieves loyalty program status and optionally
    transaction history for a specific user.
    
    Args:
        request: The loyalty query request
        api_key_valid: API key validation result
        correlation_id: Request correlation ID
        
    Returns:
        LoyaltyResponse: The loyalty program data
        
    Raises:
        HTTPException: If the request fails or authentication fails
    """
    try:
        logger.info("Getting loyalty information",
                   email=request.email,
                   include_transaction_history=request.include_transaction_history,
                   correlation_id=correlation_id)
        
        # Get Salesforce headers
        headers = await get_salesforce_headers(for_data_cloud=True)
        
        # Get loyalty information
        loyalty_data = await _data_service.get_loyalty_info(
            email=request.email,
            headers=headers,
            include_transaction_history=request.include_transaction_history
        )
        
        response = LoyaltyResponse(
            status=ResponseStatus.SUCCESS,
            loyalty_info=loyalty_data.get("loyalty_info"),
            transaction_history=loyalty_data.get("transaction_history"),
            correlation_id=correlation_id
        )
        
        logger.info("Loyalty information retrieved successfully",
                   email=request.email,
                   correlation_id=correlation_id)
        
        return response
        
    except Exception as e:
        logger.error("Failed to get loyalty information",
                    email=request.email,
                    error=str(e),
                    correlation_id=correlation_id,
                    exc_info=True)
        
        error_detail = ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to get loyalty information",
            details=str(e),
            timestamp=datetime.utcnow()
        )
        
        return LoyaltyResponse(
            status=ResponseStatus.ERROR,
            error=error_detail,
            correlation_id=correlation_id
        )


@api_router.post("/batch-query", response_model=BatchQueryResponse)
async def execute_batch_query(
    request: BatchQueryRequest,
    api_key_valid: bool = Depends(validate_api_key),
    correlation_id: Optional[str] = Depends(get_correlation_id)
) -> BatchQueryResponse:
    """
    Execute multiple queries in a single request.
    
    This endpoint allows executing multiple queries in a batch,
    which is useful for retrieving related data efficiently.
    
    Args:
        request: The batch query request
        api_key_valid: API key validation result
        correlation_id: Request correlation ID
        
    Returns:
        BatchQueryResponse: The batch query results
        
    Raises:
        HTTPException: If the batch execution fails or authentication fails
    """
    start_time = time.time()
    
    try:
        logger.info("Executing batch query",
                   query_count=len(request.queries),
                   correlation_id=correlation_id)
        
        # Get Salesforce headers
        headers = await get_salesforce_headers(for_data_cloud=True)
        
        # Execute batch queries
        results = []
        successful_queries = 0
        failed_queries = 0
        
        for query_request in request.queries:
            try:
                result = await _query_service.execute_query(
                    query=query_request.query,
                    query_type=query_request.query_type.value,
                    headers=headers,
                    limit=query_request.limit,
                    offset=query_request.offset,
                    enrich_data=query_request.enrich_data
                )
                
                query_response = QueryResponse(
                    status=ResponseStatus.SUCCESS,
                    data=QueryResult(
                        query=query_request.query,
                        query_type=query_request.query_type.value,
                        records=result.get("records", []),
                        total_size=result.get("totalSize", 0),
                        done=result.get("done", True),
                        next_records_url=result.get("nextRecordsUrl"),
                        execution_time_ms=result.get("execution_time_ms")
                    ),
                    correlation_id=correlation_id
                )
                
                results.append(query_response)
                successful_queries += 1
                
            except Exception as e:
                logger.error("Query in batch failed",
                           query=query_request.query,
                           error=str(e),
                           correlation_id=correlation_id)
                
                error_detail = ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Query execution failed",
                    details=str(e),
                    timestamp=datetime.utcnow()
                )
                
                query_response = QueryResponse(
                    status=ResponseStatus.ERROR,
                    error=error_detail,
                    correlation_id=correlation_id
                )
                
                results.append(query_response)
                failed_queries += 1
        
        processing_time = (time.time() - start_time) * 1000
        
        response = BatchQueryResponse(
            status=ResponseStatus.SUCCESS if failed_queries == 0 else ResponseStatus.PARTIAL,
            results=results,
            total_queries=len(request.queries),
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            correlation_id=correlation_id,
            processing_time_ms=processing_time
        )
        
        logger.info("Batch query executed",
                   total_queries=len(request.queries),
                   successful_queries=successful_queries,
                   failed_queries=failed_queries,
                   processing_time_ms=processing_time,
                   correlation_id=correlation_id)
        
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        
        logger.error("Batch query execution failed",
                    error=str(e),
                    processing_time_ms=processing_time,
                    correlation_id=correlation_id,
                    exc_info=True)
        
        error_detail = ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="Batch query execution failed",
            details=str(e),
            timestamp=datetime.utcnow()
        )
        
        return BatchQueryResponse(
            status=ResponseStatus.ERROR,
            error=error_detail,
            correlation_id=correlation_id,
            processing_time_ms=processing_time
        )


@api_router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    request: HealthCheckRequest = Depends(),
    correlation_id: Optional[str] = Depends(get_correlation_id)
) -> HealthCheckResponse:
    """
    Health check endpoint for monitoring.
    
    This endpoint provides system health information including
    token status and dependency health.
    
    Args:
        request: The health check request
        correlation_id: Request correlation ID
        
    Returns:
        HealthCheckResponse: The health check results
    """
    try:
        logger.info("Health check requested",
                   include_token_info=request.include_token_info,
                   include_system_info=request.include_system_info,
                   correlation_id=correlation_id)
        
        # Get token information if requested
        token_info = None
        if request.include_token_info:
            from src.auth.oauth import get_salesforce_authenticator
            authenticator = get_salesforce_authenticator()
            token_info = authenticator.get_token_info()
        
        # Get system information if requested
        system_info = None
        if request.include_system_info:
            import psutil
            system_info = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        
        # Check dependencies
        dependencies = {
            "salesforce_api": "healthy",
            "data_cloud_api": "healthy"
        }
        
        # Test Salesforce connectivity
        try:
            headers = await get_salesforce_headers(for_data_cloud=True)
            dependencies["salesforce_api"] = "healthy"
        except Exception as e:
            logger.warning("Salesforce API health check failed", error=str(e))
            dependencies["salesforce_api"] = "unhealthy"
        
        response = HealthCheckResponse(
            status="healthy",
            version=_settings.version,
            token_info=token_info,
            system_info=system_info,
            dependencies=dependencies
        )
        
        logger.info("Health check completed successfully",
                   correlation_id=correlation_id)
        
        return response
        
    except Exception as e:
        logger.error("Health check failed",
                    error=str(e),
                    correlation_id=correlation_id,
                    exc_info=True)
        
        return HealthCheckResponse(
            status="unhealthy",
            version=_settings.version
        )


@api_router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get system status information.
    
    This endpoint provides basic system status without authentication
    requirements, useful for load balancers and monitoring systems.
    
    Returns:
        Dict[str, Any]: System status information
    """
    return {
        "status": "operational",
        "version": _settings.version,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": _settings.environment
    } 