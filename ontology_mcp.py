"""
Kivor Ontology MCP Server

FastMCP server for dynamic ontology management with LLM-based ticket classification.
Provides P0 and P1 tools for ontology storage, retrieval, and assignment.
"""

from fastmcp import FastMCP
from pydantic import Field
from typing import Dict, Any, List, Optional

from src.logging import logger
from src.config import MCP_HOST, MCP_PORT
from src.agents.ontology_agent import (
    # P0 Tools
    store_ontology,
    retrieve_ontology_by_id,
    select_ontology_for_ticket,
    list_ontologies,
    validate_ontology,
    # P1 Tools
    retrieve_ontology_by_name,
    update_ontology,
    delete_ontology,
    override_ticket_ontology,
    get_ticket_ontology_history
)

# Initialize FastMCP server
mcp = FastMCP("kivor-ontology-mcp", host=MCP_HOST, port=MCP_PORT)

logger.info(f"Initializing Kivor Ontology MCP Server on {MCP_HOST}:{MCP_PORT}")


# ==================== P0 TOOLS ====================

@mcp.tool(
    name="store_ontology",
    title="Store New Ontology"
)
async def store_ontology_tool(
    name: str = Field(..., description="Unique name for the ontology (e.g., 'infrastructure_ontology')"),
    ontology_json: Dict[str, Any] = Field(..., description="The ontology JSON structure with entities and relationships"),
    category: str = Field(default="general", description="Category: 'infrastructure', 'application', 'database', 'network', etc."),
    description: str = Field(default="", description="Human-readable description of the ontology"),
    tags: List[str] = Field(default=None, description="List of tags for searching (e.g., ['network', 'cisco', 'routing'])"),
    priority: int = Field(default=50, description="Priority for selection (1-100, higher = preferred)"),
    version: str = Field(default="1.0.0", description="Version string in semver format"),
    created_by: str = Field(default="system", description="Username who created this ontology")
) -> dict:
    """Store a new ontology in the database"""
    return await store_ontology(name, ontology_json, category, description, tags, priority, version, created_by)


@mcp.tool(
    name="retrieve_ontology_by_id",
    title="Retrieve Ontology by ID"
)
async def retrieve_ontology_by_id_tool(
    ontology_id: int = Field(..., description="The ontology ID to retrieve")
) -> dict:
    """Retrieve a specific ontology by its ID"""
    return await retrieve_ontology_by_id(ontology_id)


@mcp.tool(
    name="select_ontology_for_ticket",
    title="Select Ontology for Ticket (LLM-based)"
)
async def select_ontology_for_ticket_tool(
    ticket_id: str = Field(..., description="The ticket ID (e.g., 'TKT-ABC123')"),
    ticket_title: str = Field(..., description="The ticket title"),
    ticket_description: str = Field(..., description="The full ticket description"),
    project_id: Optional[int] = Field(default=None, description="Optional project ID for tracking")
) -> dict:
    """
    Select the most appropriate ontology for a ticket using LLM classification.
    This is the primary tool for dynamic ontology assignment.
    """
    return await select_ontology_for_ticket(ticket_id, ticket_title, ticket_description, project_id)


@mcp.tool(
    name="list_ontologies",
    title="List Ontologies"
)
async def list_ontologies_tool(
    category: Optional[str] = Field(default=None, description="Filter by category"),
    is_active: bool = Field(default=True, description="Filter by active status"),
    include_deleted: bool = Field(default=False, description="Include soft-deleted ontologies"),
    limit: int = Field(default=100, description="Maximum number of results (1-500)"),
    offset: int = Field(default=0, description="Pagination offset")
) -> dict:
    """List ontologies with optional filtering and pagination"""
    return await list_ontologies(category, is_active, include_deleted, limit, offset)


@mcp.tool(
    name="validate_ontology",
    title="Validate Ontology Structure"
)
async def validate_ontology_tool(
    ontology_json: Dict[str, Any] = Field(..., description="The ontology JSON to validate for GraphRAG-SDK compatibility")
) -> dict:
    """Validate ontology JSON structure for GraphRAG-SDK compatibility"""
    return await validate_ontology(ontology_json)


# ==================== P1 TOOLS ====================

@mcp.tool(
    name="retrieve_ontology_by_name",
    title="Retrieve Ontology by Name"
)
async def retrieve_ontology_by_name_tool(
    name: str = Field(..., description="The ontology name"),
    version: Optional[str] = Field(default=None, description="Specific version (if None, returns latest)")
) -> dict:
    """Retrieve an ontology by name (optionally specific version, else latest)"""
    return await retrieve_ontology_by_name(name, version)


@mcp.tool(
    name="update_ontology",
    title="Update Ontology"
)
async def update_ontology_tool(
    ontology_id: int = Field(..., description="The ontology ID to update"),
    ontology_json: Optional[Dict[str, Any]] = Field(default=None, description="New ontology JSON (if updating)"),
    category: Optional[str] = Field(default=None, description="New category (if updating)"),
    description: Optional[str] = Field(default=None, description="New description (if updating)"),
    tags: Optional[List[str]] = Field(default=None, description="New tags (if updating)"),
    priority: Optional[int] = Field(default=None, description="New priority (if updating)"),
    is_active: Optional[bool] = Field(default=None, description="New active status (if updating)")
) -> dict:
    """Update an existing ontology (partial update supported)"""
    return await update_ontology(ontology_id, ontology_json, category, description, tags, priority, is_active)


@mcp.tool(
    name="delete_ontology",
    title="Delete Ontology (Soft Delete)"
)
async def delete_ontology_tool(
    ontology_id: int = Field(..., description="The ontology ID to delete")
) -> dict:
    """Soft delete an ontology (sets deleted_at timestamp, keeps history)"""
    return await delete_ontology(ontology_id)


@mcp.tool(
    name="override_ticket_ontology",
    title="Override Ticket Ontology Assignment"
)
async def override_ticket_ontology_tool(
    ticket_id: str = Field(..., description="The ticket ID"),
    ontology_id: int = Field(..., description="The ontology ID to assign"),
    override_reason: str = Field(..., description="Reason for manual override"),
    override_by: str = Field(..., description="Username performing the override"),
    project_id: Optional[int] = Field(default=None, description="Optional project ID")
) -> dict:
    """Manually override the ontology assignment for a ticket"""
    return await override_ticket_ontology(ticket_id, ontology_id, override_reason, override_by, project_id)


@mcp.tool(
    name="get_ticket_ontology_history",
    title="Get Ticket Ontology History"
)
async def get_ticket_ontology_history_tool(
    ticket_id: str = Field(..., description="The ticket ID"),
    limit: int = Field(default=10, description="Maximum number of assignments to return")
) -> dict:
    """Get the complete assignment history for a ticket"""
    return await get_ticket_ontology_history(ticket_id, limit)


# ==================== SERVER STARTUP ====================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Kivor Ontology MCP Server")
    logger.info(f"Host: {MCP_HOST}")
    logger.info(f"Port: {MCP_PORT}")
    logger.info("=" * 60)
    logger.info("Available Tools:")
    logger.info("  P0: store_ontology, retrieve_ontology_by_id, select_ontology_for_ticket, list_ontologies, validate_ontology")
    logger.info("  P1: retrieve_ontology_by_name, update_ontology, delete_ontology, override_ticket_ontology, get_ticket_ontology_history")
    logger.info("=" * 60)
    
    mcp.run(transport="sse")
