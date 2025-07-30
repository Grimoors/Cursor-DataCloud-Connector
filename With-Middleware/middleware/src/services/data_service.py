"""
Data service for Salesforce Data Cloud interactions.

This module provides high-level data access methods for interacting
with Salesforce Data Cloud, including user profiles, cases, and
loyalty program information.
"""

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import structlog

from src.auth.oauth import get_salesforce_headers
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataService:
    """
    Service for interacting with Salesforce Data Cloud.
    
    This class provides methods for retrieving and enriching data
    from Salesforce Data Cloud, with proper error handling and
    data transformation.
    """
    
    def __init__(self):
        """Initialize the data service."""
        self.settings = get_settings()
        self.base_url = f"https://{self.settings.data_cloud_dataspace}.api.salesforce.com"
    
    async def get_user_profile(
        self,
        email: str,
        headers: Dict[str, str],
        include_related_data: bool = True
    ) -> Dict[str, Any]:
        """
        Get user profile information from Salesforce Data Cloud.
        
        Args:
            email: The user's email address
            headers: HTTP headers for authentication
            include_related_data: Whether to include related data
            
        Returns:
            Dict[str, Any]: User profile data with optional related data
            
        Raises:
            ValueError: If the request fails
        """
        try:
            logger.info("Getting user profile", email=email)
            
            # Query for user profile
            soql_query = f"""
                SELECT Id, FirstName__c, LastName__c, Email__c, Phone__c, 
                       Company__c, Title__c, CreatedDate, LastModifiedDate
                FROM UnifiedIndividual__dlm 
                WHERE Email__c = '{email}'
                LIMIT 1
            """
            
            profile_data = await self._execute_soql_query(soql_query, headers)
            
            if not profile_data.get("records"):
                logger.warning("User profile not found", email=email)
                return {"profile": None, "related_data": None}
            
            profile = profile_data["records"][0]
            
            # Get related data if requested
            related_data = None
            if include_related_data:
                related_data = await self._get_related_data(email, headers)
            
            result = {
                "profile": profile,
                "related_data": related_data
            }
            
            logger.info("User profile retrieved successfully",
                       email=email,
                       has_related_data=related_data is not None)
            
            return result
            
        except Exception as e:
            logger.error("Failed to get user profile",
                        email=email,
                        error=str(e),
                        exc_info=True)
            raise ValueError(f"Failed to get user profile: {str(e)}")
    
    async def get_user_cases(
        self,
        email: str,
        headers: Dict[str, str],
        status_filter: Optional[str] = None,
        limit: int = 5,
        include_case_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get cases for a user from Salesforce Data Cloud.
        
        Args:
            email: The user's email address
            headers: HTTP headers for authentication
            status_filter: Optional status filter
            limit: Maximum number of cases to return
            include_case_details: Whether to include detailed case information
            
        Returns:
            Dict[str, Any]: Case data with metadata
            
        Raises:
            ValueError: If the request fails
        """
        try:
            logger.info("Getting user cases",
                       email=email,
                       status_filter=status_filter,
                       limit=limit)
            
            # Build SOQL query
            soql_query = f"""
                SELECT Id, CaseNumber, Subject, Status, Priority, 
                       CreatedDate, LastModifiedDate, Description
                FROM Case__dlm 
                WHERE Contact.Email = '{email}'
            """
            
            if status_filter:
                soql_query += f" AND Status = '{status_filter}'"
            
            soql_query += f" ORDER BY CreatedDate DESC LIMIT {limit}"
            
            cases_data = await self._execute_soql_query(soql_query, headers)
            
            cases = cases_data.get("records", [])
            
            # Enrich case data if requested
            if include_case_details:
                cases = await self._enrich_case_data(cases, headers)
            
            result = {
                "cases": cases,
                "total_count": len(cases)
            }
            
            logger.info("User cases retrieved successfully",
                       email=email,
                       case_count=len(cases))
            
            return result
            
        except Exception as e:
            logger.error("Failed to get user cases",
                        email=email,
                        error=str(e),
                        exc_info=True)
            raise ValueError(f"Failed to get user cases: {str(e)}")
    
    async def get_loyalty_info(
        self,
        email: str,
        headers: Dict[str, str],
        include_transaction_history: bool = False
    ) -> Dict[str, Any]:
        """
        Get loyalty program information for a user.
        
        Args:
            email: The user's email address
            headers: HTTP headers for authentication
            include_transaction_history: Whether to include transaction history
            
        Returns:
            Dict[str, Any]: Loyalty program data
            
        Raises:
            ValueError: If the request fails
        """
        try:
            logger.info("Getting loyalty information",
                       email=email,
                       include_transaction_history=include_transaction_history)
            
            # Query for loyalty information
            soql_query = f"""
                SELECT Id, Tier__c, PointsBalance__c, MemberSince__c,
                       NextTierThreshold__c, LastTransactionDate__c
                FROM LoyaltyMember__dmo 
                WHERE Email__c = '{email}'
                LIMIT 1
            """
            
            loyalty_data = await self._execute_soql_query(soql_query, headers)
            
            loyalty_info = loyalty_data.get("records", [{}])[0] if loyalty_data.get("records") else {}
            
            # Get transaction history if requested
            transaction_history = None
            if include_transaction_history and loyalty_info.get("Id"):
                transaction_history = await self._get_transaction_history(
                    loyalty_info["Id"], headers
                )
            
            result = {
                "loyalty_info": loyalty_info,
                "transaction_history": transaction_history
            }
            
            logger.info("Loyalty information retrieved successfully",
                       email=email,
                       has_transaction_history=transaction_history is not None)
            
            return result
            
        except Exception as e:
            logger.error("Failed to get loyalty information",
                        email=email,
                        error=str(e),
                        exc_info=True)
            raise ValueError(f"Failed to get loyalty information: {str(e)}")
    
    async def _execute_soql_query(
        self,
        query: str,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute a SOQL query against Salesforce Data Cloud.
        
        Args:
            query: The SOQL query to execute
            headers: HTTP headers for authentication
            
        Returns:
            Dict[str, Any]: Query results
            
        Raises:
            ValueError: If the query fails
        """
        try:
            url = f"{self.base_url}/services/data/v{self.settings.data_cloud_api_version}/query"
            params = {"q": query}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    logger.error("SOQL query failed",
                               status_code=response.status_code,
                               response_text=response.text,
                               query=query)
                    raise ValueError(f"Query failed: {response.status_code}")
                
                result = response.json()
                
                logger.debug("SOQL query executed successfully",
                           query=query,
                           record_count=len(result.get("records", [])))
                
                return result
                
        except Exception as e:
            logger.error("Failed to execute SOQL query",
                        query=query,
                        error=str(e),
                        exc_info=True)
            raise ValueError(f"Query execution failed: {str(e)}")
    
    async def _get_related_data(
        self,
        email: str,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Get related data for a user (cases, opportunities, etc.).
        
        Args:
            email: The user's email address
            headers: HTTP headers for authentication
            
        Returns:
            Dict[str, Any]: Related data
        """
        try:
            # Get recent cases
            cases_query = f"""
                SELECT CaseNumber, Subject, Status, Priority
                FROM Case__dlm 
                WHERE Contact.Email = '{email}'
                ORDER BY CreatedDate DESC 
                LIMIT 3
            """
            
            # Get recent opportunities
            opportunities_query = f"""
                SELECT Name, Amount, StageName, CloseDate
                FROM Opportunity__dlm 
                WHERE Contact.Email = '{email}'
                ORDER BY CreatedDate DESC 
                LIMIT 3
            """
            
            # Execute queries concurrently
            tasks = [
                self._execute_soql_query(cases_query, headers),
                self._execute_soql_query(opportunities_query, headers)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            cases_result = results[0] if not isinstance(results[0], Exception) else {"records": []}
            opportunities_result = results[1] if not isinstance(results[1], Exception) else {"records": []}
            
            return {
                "cases": cases_result.get("records", []),
                "opportunities": opportunities_result.get("records", [])
            }
            
        except Exception as e:
            logger.warning("Failed to get related data",
                          email=email,
                          error=str(e))
            return {"cases": [], "opportunities": []}
    
    async def _enrich_case_data(
        self,
        cases: List[Dict[str, Any]],
        headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Enrich case data with additional information.
        
        Args:
            cases: List of case records
            headers: HTTP headers for authentication
            
        Returns:
            List[Dict[str, Any]]: Enriched case data
        """
        try:
            enriched_cases = []
            
            for case in cases:
                # Add computed fields
                case["DaysOpen"] = self._calculate_days_open(case.get("CreatedDate"))
                case["IsHighPriority"] = case.get("Priority") in ["High", "Critical"]
                
                enriched_cases.append(case)
            
            return enriched_cases
            
        except Exception as e:
            logger.warning("Failed to enrich case data", error=str(e))
            return cases
    
    async def _get_transaction_history(
        self,
        loyalty_member_id: str,
        headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history for a loyalty member.
        
        Args:
            loyalty_member_id: The loyalty member ID
            headers: HTTP headers for authentication
            
        Returns:
            List[Dict[str, Any]]: Transaction history
        """
        try:
            query = f"""
                SELECT TransactionDate__c, PointsEarned__c, TransactionType__c,
                       Description__c
                FROM LoyaltyTransaction__dmo 
                WHERE LoyaltyMember__c = '{loyalty_member_id}'
                ORDER BY TransactionDate__c DESC 
                LIMIT 10
            """
            
            result = await self._execute_soql_query(query, headers)
            return result.get("records", [])
            
        except Exception as e:
            logger.warning("Failed to get transaction history",
                          loyalty_member_id=loyalty_member_id,
                          error=str(e))
            return []
    
    def _calculate_days_open(self, created_date: Optional[str]) -> Optional[int]:
        """
        Calculate the number of days a case has been open.
        
        Args:
            created_date: The case creation date
            
        Returns:
            Optional[int]: Number of days open
        """
        if not created_date:
            return None
        
        try:
            from datetime import datetime
            created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            now = datetime.now(created.tzinfo)
            return (now - created).days
        except Exception:
            return None 