"""
Model Context Protocol (MCP) server for Salesforce Data Cloud integration.

This module implements an MCP server that provides tools for interacting
with Salesforce Data Cloud, enabling AI agents to query customer data
through natural language interfaces.
"""

import asyncio
from typing import Any, Dict, List, Optional

import mcp
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from src.auth.oauth import get_salesforce_headers
from src.config.settings import get_settings
from src.services.data_service import DataService
from src.utils.logging import get_logger

logger = get_logger(__name__)


def create_mcp_server() -> Server:
    """
    Create and configure the MCP server.
    
    Returns:
        Server: Configured MCP server instance
    """
    settings = get_settings()
    data_service = DataService()
    
    # Create server
    server = Server("salesforce-data-tools")
    
    @server.list_tools()
    async def handle_list_tools() -> List[mcp.Tool]:
        """List available tools."""
        return [
            mcp.Tool(
                name="get_user_profile",
                description="Fetches the unified profile and key attributes of a customer from Salesforce Data Cloud given their email address.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The customer's email address."
                        }
                    },
                    "required": ["email"]
                }
            ),
            mcp.Tool(
                name="get_recent_cases",
                description="Retrieves the 5 most recent support cases for a customer, identified by their email. Includes case number, subject, and status.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The customer's email address."
                        }
                    },
                    "required": ["email"]
                }
            ),
            mcp.Tool(
                name="get_loyalty_status",
                description="Gets the current loyalty program tier and points balance for a customer from Salesforce Data Cloud.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The customer's email address."
                        }
                    },
                    "required": ["email"]
                }
            ),
            mcp.Tool(
                name="get_customer_summary",
                description="Provides a comprehensive summary of a customer including profile, recent cases, and loyalty status.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The customer's email address."
                        }
                    },
                    "required": ["email"]
                }
            ),
            mcp.Tool(
                name="search_customers",
                description="Searches for customers by name or email pattern in Salesforce Data Cloud.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "The search term (name or email pattern)."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return.",
                            "default": 10
                        }
                    },
                    "required": ["search_term"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[mcp.TextContent]:
        """Handle tool calls."""
        try:
            logger.info("MCP tool called", tool_name=name, arguments=arguments)
            
            if name == "get_user_profile":
                result = await _get_user_profile_tool(arguments, data_service)
            elif name == "get_recent_cases":
                result = await _get_recent_cases_tool(arguments, data_service)
            elif name == "get_loyalty_status":
                result = await _get_loyalty_status_tool(arguments, data_service)
            elif name == "get_customer_summary":
                result = await _get_customer_summary_tool(arguments, data_service)
            elif name == "search_customers":
                result = await _search_customers_tool(arguments, data_service)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            logger.info("MCP tool completed successfully", tool_name=name)
            return [mcp.TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error("MCP tool failed",
                        tool_name=name,
                        error=str(e),
                        exc_info=True)
            error_message = f"Tool '{name}' failed: {str(e)}"
            return [mcp.TextContent(type="text", text=error_message)]
    
    return server


async def _get_user_profile_tool(
    arguments: Dict[str, Any],
    data_service: DataService
) -> str:
    """
    Tool implementation for getting user profile.
    
    Args:
        arguments: Tool arguments
        data_service: Data service instance
        
    Returns:
        str: Formatted user profile information
    """
    email = arguments["email"]
    
    # Get Salesforce headers
    headers = await get_salesforce_headers(for_data_cloud=True)
    
    # Get user profile
    profile_data = await data_service.get_user_profile(
        email=email,
        headers=headers,
        include_related_data=True
    )
    
    profile = profile_data.get("profile")
    if not profile:
        return f"No profile found for email: {email}"
    
    # Format the response
    result = f"**Customer Profile for {email}**\n\n"
    result += f"**Name:** {profile.get('FirstName__c', '')} {profile.get('LastName__c', '')}\n"
    result += f"**Email:** {profile.get('Email__c', '')}\n"
    result += f"**Phone:** {profile.get('Phone__c', 'N/A')}\n"
    result += f"**Company:** {profile.get('Company__c', 'N/A')}\n"
    result += f"**Title:** {profile.get('Title__c', 'N/A')}\n"
    result += f"**Member Since:** {profile.get('CreatedDate', 'N/A')}\n"
    
    # Add related data if available
    related_data = profile_data.get("related_data")
    if related_data:
        cases = related_data.get("cases", [])
        opportunities = related_data.get("opportunities", [])
        
        if cases:
            result += f"\n**Recent Cases ({len(cases)}):**\n"
            for case in cases:
                result += f"- {case.get('CaseNumber', 'N/A')}: {case.get('Subject', 'N/A')} ({case.get('Status', 'N/A')})\n"
        
        if opportunities:
            result += f"\n**Recent Opportunities ({len(opportunities)}):**\n"
            for opp in opportunities:
                result += f"- {opp.get('Name', 'N/A')}: ${opp.get('Amount', 0):,.2f} ({opp.get('StageName', 'N/A')})\n"
    
    return result


async def _get_recent_cases_tool(
    arguments: Dict[str, Any],
    data_service: DataService
) -> str:
    """
    Tool implementation for getting recent cases.
    
    Args:
        arguments: Tool arguments
        data_service: Data service instance
        
    Returns:
        str: Formatted case information
    """
    email = arguments["email"]
    
    # Get Salesforce headers
    headers = await get_salesforce_headers(for_data_cloud=True)
    
    # Get user cases
    cases_data = await data_service.get_user_cases(
        email=email,
        headers=headers,
        limit=5,
        include_case_details=True
    )
    
    cases = cases_data.get("cases", [])
    if not cases:
        return f"No cases found for email: {email}"
    
    # Format the response
    result = f"**Recent Cases for {email}**\n\n"
    
    for case in cases:
        result += f"**Case {case.get('CaseNumber', 'N/A')}**\n"
        result += f"- Subject: {case.get('Subject', 'N/A')}\n"
        result += f"- Status: {case.get('Status', 'N/A')}\n"
        result += f"- Priority: {case.get('Priority', 'N/A')}\n"
        result += f"- Created: {case.get('CreatedDate', 'N/A')}\n"
        
        if case.get('DaysOpen'):
            result += f"- Days Open: {case['DaysOpen']}\n"
        
        if case.get('Description'):
            result += f"- Description: {case['Description'][:100]}...\n"
        
        result += "\n"
    
    return result


async def _get_loyalty_status_tool(
    arguments: Dict[str, Any],
    data_service: DataService
) -> str:
    """
    Tool implementation for getting loyalty status.
    
    Args:
        arguments: Tool arguments
        data_service: Data service instance
        
    Returns:
        str: Formatted loyalty information
    """
    email = arguments["email"]
    
    # Get Salesforce headers
    headers = await get_salesforce_headers(for_data_cloud=True)
    
    # Get loyalty information
    loyalty_data = await data_service.get_loyalty_info(
        email=email,
        headers=headers,
        include_transaction_history=False
    )
    
    loyalty_info = loyalty_data.get("loyalty_info")
    if not loyalty_info:
        return f"No loyalty information found for email: {email}"
    
    # Format the response
    result = f"**Loyalty Status for {email}**\n\n"
    result += f"**Tier:** {loyalty_info.get('Tier__c', 'N/A')}\n"
    result += f"**Points Balance:** {loyalty_info.get('PointsBalance__c', 0):,}\n"
    result += f"**Member Since:** {loyalty_info.get('MemberSince__c', 'N/A')}\n"
    
    next_threshold = loyalty_info.get('NextTierThreshold__c')
    if next_threshold:
        current_points = loyalty_info.get('PointsBalance__c', 0)
        points_needed = next_threshold - current_points
        if points_needed > 0:
            result += f"**Points to Next Tier:** {points_needed:,}\n"
    
    last_transaction = loyalty_info.get('LastTransactionDate__c')
    if last_transaction:
        result += f"**Last Transaction:** {last_transaction}\n"
    
    return result


async def _get_customer_summary_tool(
    arguments: Dict[str, Any],
    data_service: DataService
) -> str:
    """
    Tool implementation for getting comprehensive customer summary.
    
    Args:
        arguments: Tool arguments
        data_service: Data service instance
        
    Returns:
        str: Formatted customer summary
    """
    email = arguments["email"]
    
    # Get Salesforce headers
    headers = await get_salesforce_headers(for_data_cloud=True)
    
    # Get all customer data concurrently
    tasks = [
        data_service.get_user_profile(email, headers, include_related_data=True),
        data_service.get_user_cases(email, headers, limit=3, include_case_details=True),
        data_service.get_loyalty_info(email, headers, include_transaction_history=False)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    profile_data = results[0] if not isinstance(results[0], Exception) else {"profile": None, "related_data": None}
    cases_data = results[1] if not isinstance(results[1], Exception) else {"cases": [], "total_count": 0}
    loyalty_data = results[2] if not isinstance(results[2], Exception) else {"loyalty_info": None}
    
    # Format the comprehensive response
    result = f"**Customer Summary for {email}**\n\n"
    
    # Profile section
    profile = profile_data.get("profile")
    if profile:
        result += "**📋 Profile Information**\n"
        result += f"Name: {profile.get('FirstName__c', '')} {profile.get('LastName__c', '')}\n"
        result += f"Email: {profile.get('Email__c', '')}\n"
        result += f"Phone: {profile.get('Phone__c', 'N/A')}\n"
        result += f"Company: {profile.get('Company__c', 'N/A')}\n"
        result += f"Title: {profile.get('Title__c', 'N/A')}\n"
        result += f"Member Since: {profile.get('CreatedDate', 'N/A')}\n\n"
    else:
        result += "**📋 Profile Information**\nNo profile found\n\n"
    
    # Cases section
    cases = cases_data.get("cases", [])
    result += f"**🎫 Recent Cases ({len(cases)})**\n"
    if cases:
        for case in cases:
            result += f"- {case.get('CaseNumber', 'N/A')}: {case.get('Subject', 'N/A')} ({case.get('Status', 'N/A')})\n"
    else:
        result += "No recent cases\n"
    result += "\n"
    
    # Loyalty section
    loyalty_info = loyalty_data.get("loyalty_info")
    result += "**🏆 Loyalty Status**\n"
    if loyalty_info:
        result += f"Tier: {loyalty_info.get('Tier__c', 'N/A')}\n"
        result += f"Points Balance: {loyalty_info.get('PointsBalance__c', 0):,}\n"
        result += f"Member Since: {loyalty_info.get('MemberSince__c', 'N/A')}\n"
    else:
        result += "No loyalty information available\n"
    
    return result


async def _search_customers_tool(
    arguments: Dict[str, Any],
    data_service: DataService
) -> str:
    """
    Tool implementation for searching customers.
    
    Args:
        arguments: Tool arguments
        data_service: Data service instance
        
    Returns:
        str: Formatted search results
    """
    search_term = arguments["search_term"]
    limit = arguments.get("limit", 10)
    
    # Get Salesforce headers
    headers = await get_salesforce_headers(for_data_cloud=True)
    
    # Build search query
    search_query = f"""
        SELECT Id, FirstName__c, LastName__c, Email__c, Company__c
        FROM UnifiedIndividual__dlm 
        WHERE FirstName__c LIKE '%{search_term}%' 
           OR LastName__c LIKE '%{search_term}%' 
           OR Email__c LIKE '%{search_term}%'
        ORDER BY LastName__c, FirstName__c
        LIMIT {limit}
    """
    
    try:
        # Execute search query
        search_results = await data_service._execute_soql_query(search_query, headers)
        customers = search_results.get("records", [])
        
        if not customers:
            return f"No customers found matching '{search_term}'"
        
        # Format the response
        result = f"**Customer Search Results for '{search_term}'**\n\n"
        
        for customer in customers:
            result += f"**{customer.get('FirstName__c', '')} {customer.get('LastName__c', '')}**\n"
            result += f"Email: {customer.get('Email__c', 'N/A')}\n"
            result += f"Company: {customer.get('Company__c', 'N/A')}\n\n"
        
        result += f"Found {len(customers)} customer(s)"
        
        return result
        
    except Exception as e:
        logger.error("Customer search failed",
                    search_term=search_term,
                    error=str(e))
        return f"Search failed: {str(e)}"


def run_mcp_server():
    """Run the MCP server using stdio transport."""
    server = create_mcp_server()
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="salesforce-data-tools",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )
    
    asyncio.run(main())


if __name__ == "__main__":
    run_mcp_server() 