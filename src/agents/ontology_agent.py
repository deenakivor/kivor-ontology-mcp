"""
Ontology Agent

Provides all ontology management operations:
- P0 Tools: store, retrieve_by_id, select_for_ticket, list, validate
- P1 Tools: retrieve_by_name, update, delete, override, get_history
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.logging import logger
from src.utility.db_manager import db_manager
from src.utility.llm_classifier import llm_classifier


async def store_ontology(
    name: str,
    ontology_json: Dict[str, Any],
    category: str = "general",
    description: str = "",
    tags: List[str] = None,
    priority: int = 50,
    version: str = "1.0.0",
    created_by: str = "system"
) -> Dict[str, Any]:
    """
    Store a new ontology in the database.
    
    Args:
        name: Unique name for the ontology
        ontology_json: The ontology JSON structure
        category: Category (e.g., 'infrastructure', 'application')
        description: Human-readable description
        tags: List of tags for searching
        priority: Priority for selection (higher = preferred)
        version: Version string (semver format)
        created_by: Username who created this
    
    Returns:
        Dict with ontology_id and status
    """
    try:
        logger.info(f"Storing new ontology: {name} v{version}")
        
        query = """
        INSERT INTO ontology_store 
        (name, version, ontology_json, category, description, tags, priority, created_by, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING ontology_id, name, version, created_at
        """
        
        result = db_manager.execute_insert(
            query,
            (name, version, json.dumps(ontology_json), category, description, tags, priority, created_by)
        )
        
        logger.info(f"Ontology stored successfully with ID: {result['ontology_id']}")
        
        return {
            "success": True,
            "ontology_id": result['ontology_id'],
            "name": result['name'],
            "version": result['version'],
            "created_at": str(result['created_at']),
            "message": f"Ontology '{name}' stored successfully"
        }
        
    except Exception as e:
        logger.error(f"Error storing ontology: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to store ontology: {str(e)}"
        }


async def retrieve_ontology_by_id(ontology_id: int) -> Dict[str, Any]:
    """
    Retrieve an ontology by its ID.
    
    Args:
        ontology_id: The ontology ID
    
    Returns:
        Dict with ontology data
    """
    try:
        logger.info(f"Retrieving ontology by ID: {ontology_id}")
        
        query = """
        SELECT ontology_id, name, version, ontology_json, category, description, 
               tags, priority, is_active, created_by, created_at, updated_at
        FROM ontology_store
        WHERE ontology_id = %s AND deleted_at IS NULL
        """
        
        results = db_manager.execute_query(query, (ontology_id,))
        
        if not results:
            logger.warning(f"Ontology not found: {ontology_id}")
            return {
                "success": False,
                "error": "Ontology not found",
                "message": f"No ontology found with ID {ontology_id}"
            }
        
        ontology = dict(results[0])
        
        # Parse JSON field
        if isinstance(ontology['ontology_json'], str):
            ontology['ontology_json'] = json.loads(ontology['ontology_json'])
        
        logger.info(f"Retrieved ontology: {ontology['name']} v{ontology['version']}")
        
        return {
            "success": True,
            "ontology": ontology,
            "message": "Ontology retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ontology: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve ontology: {str(e)}"
        }


async def select_ontology_for_ticket(
    ticket_id: str,
    ticket_title: str,
    ticket_description: str,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Select the most appropriate ontology for a ticket using LLM classification.
    Records the assignment in ticket_ontology_assignments table.
    
    Args:
        ticket_id: The ticket ID
        ticket_title: Ticket title
        ticket_description: Ticket description
        project_id: Optional project ID
    
    Returns:
        Dict with selected ontology and assignment details
    """
    try:
        logger.info(f"Selecting ontology for ticket: {ticket_id}")
        
        # Get all active ontologies
        query = """
        SELECT ontology_id, name, version, category, description, tags, priority
        FROM ontology_store
        WHERE is_active = true AND deleted_at IS NULL
        ORDER BY priority DESC
        """
        
        ontologies = db_manager.execute_query(query)
        
        if not ontologies:
            logger.warning("No active ontologies found")
            return {
                "success": False,
                "error": "No active ontologies available",
                "message": "No ontologies available for selection"
            }
        
        # Convert to list of dicts
        ontology_list = [dict(row) for row in ontologies]
        
        logger.info(f"Found {len(ontology_list)} active ontologies for classification")
        
        # Use LLM to select ontology
        llm_result = llm_classifier.select_ontology(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            available_ontologies=ontology_list
        )
        
        selected_ontology_id = llm_result['ontology_id']
        
        # Record assignment
        insert_query = """
        INSERT INTO ticket_ontology_assignments
        (ticket_id, ontology_id, project_id, match_confidence, match_method, 
         llm_reasoning, llm_category, llm_keywords_found, llm_model, processing_time_ms,
         ticket_title, ticket_description, assigned_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING assignment_id, assigned_at
        """
        
        assignment = db_manager.execute_insert(
            insert_query,
            (
                ticket_id,
                selected_ontology_id,
                project_id,
                llm_result['confidence'],
                'llm_classification',
                llm_result['reasoning'],
                llm_result['category'],
                llm_result.get('keywords_found', []),
                llm_result['llm_model'],
                llm_result['processing_time_ms'],
                ticket_title,
                ticket_description
            )
        )
        
        # Get selected ontology details
        selected_ontology = next(
            (ont for ont in ontology_list if ont['ontology_id'] == selected_ontology_id),
            None
        )
        
        logger.info(f"Ontology selected and assigned: {selected_ontology['name']} (ID: {selected_ontology_id})")
        
        return {
            "success": True,
            "assignment_id": assignment['assignment_id'],
            "ticket_id": ticket_id,
            "selected_ontology": {
                "ontology_id": selected_ontology_id,
                "name": selected_ontology['name'],
                "version": selected_ontology['version'],
                "category": selected_ontology['category']
            },
            "classification": {
                "confidence": llm_result['confidence'],
                "reasoning": llm_result['reasoning'],
                "category": llm_result['category'],
                "keywords_found": llm_result.get('keywords_found', []),
                "processing_time_ms": llm_result['processing_time_ms']
            },
            "assigned_at": str(assignment['assigned_at']),
            "message": f"Ontology '{selected_ontology['name']}' selected with {llm_result['confidence']:.2f} confidence"
        }
        
    except Exception as e:
        logger.error(f"Error selecting ontology for ticket: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to select ontology: {str(e)}"
        }


async def list_ontologies(
    category: Optional[str] = None,
    is_active: bool = True,
    include_deleted: bool = False,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List ontologies with optional filtering.
    
    Args:
        category: Filter by category
        is_active: Filter by active status
        include_deleted: Include soft-deleted ontologies
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        Dict with list of ontologies
    """
    try:
        logger.info(f"Listing ontologies (category={category}, is_active={is_active})")
        
        conditions = []
        params = []
        
        if not include_deleted:
            conditions.append("deleted_at IS NULL")
        
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)
        
        if category:
            conditions.append("category = %s")
            params.append(category)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
        SELECT ontology_id, name, version, category, description, tags, 
               priority, is_active, created_by, created_at, updated_at
        FROM ontology_store
        WHERE {where_clause}
        ORDER BY priority DESC, created_at DESC
        LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        
        results = db_manager.execute_query(query, tuple(params))
        
        ontologies = [dict(row) for row in results]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM ontology_store WHERE {where_clause}"
        count_result = db_manager.execute_query(count_query, tuple(params[:-2]))  # Exclude limit/offset
        total_count = count_result[0]['total']
        
        logger.info(f"Found {len(ontologies)} ontologies (total: {total_count})")
        
        return {
            "success": True,
            "ontologies": ontologies,
            "count": len(ontologies),
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "message": f"Retrieved {len(ontologies)} ontologies"
        }
        
    except Exception as e:
        logger.error(f"Error listing ontologies: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to list ontologies: {str(e)}"
        }


async def validate_ontology(ontology_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate ontology JSON structure for GraphRAG-SDK compatibility.
    
    Args:
        ontology_json: The ontology JSON to validate
    
    Returns:
        Dict with validation results
    """
    try:
        logger.info("Validating ontology structure")
        
        validation_result = llm_classifier.validate_ontology_structure(ontology_json)
        
        logger.info(f"Validation complete: is_valid={validation_result['is_valid']}, "
                   f"errors={len(validation_result['errors'])}, "
                   f"warnings={len(validation_result['warnings'])}")
        
        return {
            "success": True,
            "validation": validation_result,
            "message": "Validation completed" if validation_result['is_valid'] 
                      else f"Validation failed with {len(validation_result['errors'])} errors"
        }
        
    except Exception as e:
        logger.error(f"Error validating ontology: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Validation failed: {str(e)}"
        }


# P1 Tools

async def retrieve_ontology_by_name(
    name: str,
    version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve an ontology by name (optionally specific version, else latest).
    
    Args:
        name: Ontology name
        version: Specific version (if None, returns latest)
    
    Returns:
        Dict with ontology data
    """
    try:
        logger.info(f"Retrieving ontology by name: {name} (version={version or 'latest'})")
        
        if version:
            query = """
            SELECT ontology_id, name, version, ontology_json, category, description, 
                   tags, priority, is_active, created_by, created_at, updated_at
            FROM ontology_store
            WHERE name = %s AND version = %s AND deleted_at IS NULL
            """
            params = (name, version)
        else:
            query = """
            SELECT ontology_id, name, version, ontology_json, category, description, 
                   tags, priority, is_active, created_by, created_at, updated_at
            FROM ontology_store
            WHERE name = %s AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """
            params = (name,)
        
        results = db_manager.execute_query(query, params)
        
        if not results:
            logger.warning(f"Ontology not found: {name} (version={version})")
            return {
                "success": False,
                "error": "Ontology not found",
                "message": f"No ontology found with name '{name}'"
            }
        
        ontology = dict(results[0])
        
        # Parse JSON field
        if isinstance(ontology['ontology_json'], str):
            ontology['ontology_json'] = json.loads(ontology['ontology_json'])
        
        logger.info(f"Retrieved ontology: {ontology['name']} v{ontology['version']}")
        
        return {
            "success": True,
            "ontology": ontology,
            "message": "Ontology retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ontology by name: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve ontology: {str(e)}"
        }


async def update_ontology(
    ontology_id: int,
    ontology_json: Optional[Dict[str, Any]] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    priority: Optional[int] = None,
    is_active: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update an existing ontology (partial update supported).
    
    Args:
        ontology_id: The ontology ID to update
        ontology_json: New ontology JSON (if provided)
        category: New category (if provided)
        description: New description (if provided)
        tags: New tags (if provided)
        priority: New priority (if provided)
        is_active: New active status (if provided)
    
    Returns:
        Dict with updated ontology
    """
    try:
        logger.info(f"Updating ontology ID: {ontology_id}")
        
        # Build dynamic UPDATE query
        update_fields = []
        params = []
        
        if ontology_json is not None:
            update_fields.append("ontology_json = %s")
            params.append(json.dumps(ontology_json))
        
        if category is not None:
            update_fields.append("category = %s")
            params.append(category)
        
        if description is not None:
            update_fields.append("description = %s")
            params.append(description)
        
        if tags is not None:
            update_fields.append("tags = %s")
            params.append(tags)
        
        if priority is not None:
            update_fields.append("priority = %s")
            params.append(priority)
        
        if is_active is not None:
            update_fields.append("is_active = %s")
            params.append(is_active)
        
        if not update_fields:
            return {
                "success": False,
                "error": "No fields to update",
                "message": "No update parameters provided"
            }
        
        update_fields.append("updated_at = NOW()")
        params.append(ontology_id)
        
        query = f"""
        UPDATE ontology_store
        SET {', '.join(update_fields)}
        WHERE ontology_id = %s AND deleted_at IS NULL
        RETURNING ontology_id, name, version, updated_at
        """
        
        result = db_manager.execute_insert(query, tuple(params))
        
        if not result:
            return {
                "success": False,
                "error": "Ontology not found",
                "message": f"No ontology found with ID {ontology_id}"
            }
        
        logger.info(f"Ontology updated: {result['name']} v{result['version']}")
        
        return {
            "success": True,
            "ontology_id": result['ontology_id'],
            "name": result['name'],
            "version": result['version'],
            "updated_at": str(result['updated_at']),
            "message": f"Ontology updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating ontology: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to update ontology: {str(e)}"
        }


async def delete_ontology(ontology_id: int) -> Dict[str, Any]:
    """
    Soft delete an ontology (sets deleted_at timestamp).
    
    Args:
        ontology_id: The ontology ID to delete
    
    Returns:
        Dict with deletion status
    """
    try:
        logger.info(f"Deleting ontology ID: {ontology_id}")
        
        query = """
        UPDATE ontology_store
        SET deleted_at = NOW(), is_active = false
        WHERE ontology_id = %s AND deleted_at IS NULL
        RETURNING ontology_id, name, version, deleted_at
        """
        
        result = db_manager.execute_insert(query, (ontology_id,))
        
        if not result:
            return {
                "success": False,
                "error": "Ontology not found or already deleted",
                "message": f"No active ontology found with ID {ontology_id}"
            }
        
        logger.info(f"Ontology deleted: {result['name']} v{result['version']}")
        
        return {
            "success": True,
            "ontology_id": result['ontology_id'],
            "name": result['name'],
            "version": result['version'],
            "deleted_at": str(result['deleted_at']),
            "message": f"Ontology '{result['name']}' deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting ontology: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to delete ontology: {str(e)}"
        }


async def override_ticket_ontology(
    ticket_id: str,
    ontology_id: int,
    override_reason: str,
    override_by: str,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Manually override the ontology assignment for a ticket.
    
    Args:
        ticket_id: The ticket ID
        ontology_id: The ontology ID to assign
        override_reason: Reason for manual override
        override_by: Username performing the override
        project_id: Optional project ID
    
    Returns:
        Dict with assignment details
    """
    try:
        logger.info(f"Overriding ontology for ticket {ticket_id} to ontology {ontology_id}")
        
        # Verify ontology exists
        check_query = "SELECT name, version FROM ontology_store WHERE ontology_id = %s AND deleted_at IS NULL"
        ontology = db_manager.execute_query(check_query, (ontology_id,))
        
        if not ontology:
            return {
                "success": False,
                "error": "Ontology not found",
                "message": f"No ontology found with ID {ontology_id}"
            }
        
        ontology_info = dict(ontology[0])
        
        # Insert override assignment
        insert_query = """
        INSERT INTO ticket_ontology_assignments
        (ticket_id, ontology_id, project_id, match_method, is_override, 
         override_reason, override_by, assigned_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING assignment_id, assigned_at
        """
        
        result = db_manager.execute_insert(
            insert_query,
            (ticket_id, ontology_id, project_id, 'manual_override', True, override_reason, override_by)
        )
        
        logger.info(f"Override recorded: assignment_id={result['assignment_id']}")
        
        return {
            "success": True,
            "assignment_id": result['assignment_id'],
            "ticket_id": ticket_id,
            "ontology": {
                "ontology_id": ontology_id,
                "name": ontology_info['name'],
                "version": ontology_info['version']
            },
            "override_reason": override_reason,
            "override_by": override_by,
            "assigned_at": str(result['assigned_at']),
            "message": f"Ontology manually assigned to ticket {ticket_id}"
        }
        
    except Exception as e:
        logger.error(f"Error overriding ticket ontology: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to override ontology: {str(e)}"
        }


async def get_ticket_ontology_history(
    ticket_id: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get the assignment history for a ticket.
    
    Args:
        ticket_id: The ticket ID
        limit: Maximum number of assignments to return
    
    Returns:
        Dict with assignment history
    """
    try:
        logger.info(f"Retrieving ontology history for ticket: {ticket_id}")
        
        query = """
        SELECT 
            toa.assignment_id,
            toa.ticket_id,
            toa.ontology_id,
            os.name as ontology_name,
            os.version as ontology_version,
            os.category,
            toa.match_confidence,
            toa.match_method,
            toa.llm_reasoning,
            toa.llm_category,
            toa.is_override,
            toa.override_reason,
            toa.override_by,
            toa.assigned_at
        FROM ticket_ontology_assignments toa
        LEFT JOIN ontology_store os ON toa.ontology_id = os.ontology_id
        WHERE toa.ticket_id = %s
        ORDER BY toa.assigned_at DESC
        LIMIT %s
        """
        
        results = db_manager.execute_query(query, (ticket_id, limit))
        
        assignments = [dict(row) for row in results]
        
        logger.info(f"Found {len(assignments)} assignments for ticket {ticket_id}")
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "assignments": assignments,
            "count": len(assignments),
            "message": f"Retrieved {len(assignments)} assignment(s) for ticket {ticket_id}"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ticket ontology history: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve history: {str(e)}"
        }


async def list_available_ontology_names(
    is_active: bool = True
) -> Dict[str, Any]:
    """
    Get a simple list of ontology names for dropdown/selection UI.
    Returns only the name strings, optimized for SharePoint integration.
    
    Args:
        is_active: Filter by active status (default: True)
    
    Returns:
        Dict with list of ontology name strings
    """
    try:
        logger.info(f"Retrieving available ontology names (is_active={is_active})")
        
        query = """
        SELECT DISTINCT name
        FROM ontology_store
        WHERE deleted_at IS NULL AND is_active = %s
        ORDER BY name ASC
        """
        
        results = db_manager.execute_query(query, (is_active,))
        
        # Extract just the names as a simple list of strings
        ontology_names = [row['name'] for row in results]
        
        logger.info(f"Found {len(ontology_names)} available ontology names: {ontology_names}")
        
        return {
            "success": True,
            "ontology_names": ontology_names,
            "count": len(ontology_names),
            "message": f"Retrieved {len(ontology_names)} ontology name(s)"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ontology names: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "ontology_names": [],
            "message": f"Failed to retrieve ontology names: {str(e)}"
        }
