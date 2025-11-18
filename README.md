# Kivor Ontology MCP Server

FastMCP server for dynamic ontology management with LLM-based ticket classification.

## Overview

This MCP server replaces static project-level ontology selection with dynamic ticket-level classification using OpenAI LLMs. It provides comprehensive tools for storing, retrieving, validating, and assigning ontologies to tickets.

## Features

- **Dynamic Ontology Selection**: LLM-based classification for intelligent ticket-to-ontology matching
- **Version Management**: Support for multiple ontology versions
- **Assignment History**: Complete audit trail of ontology assignments
- **Manual Overrides**: Ability to override LLM selections with reasoning
- **GraphRAG-SDK Validation**: Built-in ontology structure validation
- **RESTful API**: FastMCP HTTP interface for easy integration

## Architecture

```
kivor-ontology-mcp/
├── ontology_mcp.py           # Main FastMCP server
├── src/
│   ├── agents/
│   │   └── ontology_agent.py # All 10 tool implementations
│   ├── config/               # Configuration management
│   ├── logging/              # Centralized logging
│   └── utility/
│       ├── db_manager.py     # PostgreSQL connection
│       └── llm_classifier.py # LLM-based classification
├── migrations/               # Database schema migrations
├── logs/                     # Application logs
└── docker-compose.yml        # Container orchestration
```

## Tools Provided

### P0 Tools (Essential)

1. **store_ontology** - Upload and store new ontologies
2. **retrieve_ontology_by_id** - Get ontology by ID
3. **select_ontology_for_ticket** ⭐ - LLM-based ticket classification (PRIMARY TOOL)
4. **list_ontologies** - List with filtering and pagination
5. **validate_ontology** - Validate GraphRAG-SDK compatibility

### P1 Tools (Important)

6. **retrieve_ontology_by_name** - Get by name (latest or specific version)
7. **update_ontology** - Update existing ontologies
8. **delete_ontology** - Soft delete (preserves history)
9. **override_ticket_ontology** - Manual assignment override
10. **get_ticket_ontology_history** - View assignment history

## Database Schema

### ontology_store
Stores all ontology definitions with metadata:
- `ontology_id` (PK)
- `name`, `version` (unique together)
- `ontology_json` (JSONB)
- `category`, `description`, `tags`
- `priority` (1-100 for selection preference)
- `is_active`, `deleted_at` (soft delete)

### ticket_ontology_assignments
Records all ticket-to-ontology assignments:
- `assignment_id` (PK)
- `ticket_id`, `ontology_id` (FK)
- `match_confidence`, `match_method`
- `llm_reasoning`, `llm_category`, `llm_keywords_found`
- `is_override`, `override_reason`, `override_by`
- Complete ticket context for audit

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- OpenAI API key
- Docker (optional)

### Local Setup

1. **Clone and navigate**:
   ```bash
   cd kivor-ontology-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run database migrations**:
   ```bash
   psql -h 74.225.248.241 -p 5433 -U your_user -d kivorticketing -f migrations/001_create_ontology_store.sql
   psql -h 74.225.248.241 -p 5433 -U your_user -d kivorticketing -f migrations/002_create_ticket_assignments.sql
   psql -h 74.225.248.241 -p 5433 -U your_user -d kivorticketing -f migrations/003_create_functions.sql
   ```

5. **Start server**:
   ```bash
   python ontology_mcp.py
   ```

Server runs on `http://localhost:8102`

### Docker Setup

1. **Build and run**:
   ```bash
   docker-compose up -d
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f ontology-mcp
   ```

3. **Stop server**:
   ```bash
   docker-compose down
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | 74.225.248.241 |
| `DB_PORT` | PostgreSQL port | 5433 |
| `DB_NAME` | Database name | kivorticketing |
| `DB_SCHEMA` | Schema name | kivorticketing |
| `DB_USER` | Database user | (required) |
| `DB_PASSWORD` | Database password | (required) |
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `OPENAI_MODEL` | LLM model | gpt-4o-mini |
| `MCP_HOST` | Server host | 0.0.0.0 |
| `MCP_PORT` | Server port | 8102 |

## Usage Examples

### Example 1: Store an Ontology

```json
POST /tools/store_ontology
{
  "name": "infrastructure_ontology",
  "ontology_json": {
    "entities": [
      {"name": "Server", "type": "Infrastructure"},
      {"name": "Network", "type": "Infrastructure"}
    ],
    "relationships": [
      {"source": "Server", "target": "Network", "type": "CONNECTS_TO"}
    ]
  },
  "category": "infrastructure",
  "description": "Ontology for infrastructure tickets",
  "tags": ["infrastructure", "server", "network"],
  "priority": 80,
  "version": "1.0.0"
}
```

### Example 2: Select Ontology for Ticket (LLM-based)

```json
POST /tools/select_ontology_for_ticket
{
  "ticket_id": "TKT-ABC123",
  "ticket_title": "Server connectivity issue in production",
  "ticket_description": "Production server unable to connect to database. Network tests show intermittent packet loss.",
  "project_id": 42
}
```

Response:
```json
{
  "success": true,
  "assignment_id": 123,
  "selected_ontology": {
    "ontology_id": 5,
    "name": "infrastructure_ontology",
    "version": "1.0.0",
    "category": "infrastructure"
  },
  "classification": {
    "confidence": 0.92,
    "reasoning": "Ticket involves infrastructure components (server, network, connectivity) requiring infrastructure ontology",
    "category": "infrastructure",
    "keywords_found": ["server", "network", "connectivity", "production"],
    "processing_time_ms": 1234
  }
}
```

### Example 3: List Ontologies

```json
POST /tools/list_ontologies
{
  "category": "infrastructure",
  "is_active": true,
  "limit": 10
}
```

### Example 4: Manual Override

```json
POST /tools/override_ticket_ontology
{
  "ticket_id": "TKT-ABC123",
  "ontology_id": 7,
  "override_reason": "Ticket requires specialized database ontology",
  "override_by": "admin_user"
}
```

## Integration with Existing System

### Planner Agent Integration

Replace static ontology selection in Planner Agent:

```python
# OLD CODE (project_description_detector.py)
ontology = get_ontology_by_project_description(project_description)

# NEW CODE (using Ontology MCP)
response = await call_mcp_tool(
    "select_ontology_for_ticket",
    {
        "ticket_id": ticket_id,
        "ticket_title": ticket_title,
        "ticket_description": ticket_description,
        "project_id": project_id
    }
)
ontology_id = response["selected_ontology"]["ontology_id"]
```

### Where to Update

1. **KivorPlannerAgent**: Update `generate_workflow_plan()` to call `select_ontology_for_ticket`
2. **Processor**: Pass ticket details to Planner (already does this)
3. **Agent Registry**: Register ontology-mcp server
4. **Remove**: `project_description_detector.py` logic (keep file for backward compatibility)

## Monitoring

### Logs

- **Location**: `logs/ontology_mcp.log`
- **Format**: Timestamped with function and line number
- **Rotation**: 10MB per file, 5 backups

### Metrics to Monitor

- LLM classification confidence scores
- Processing time per classification
- Override rate (manual vs LLM)
- Most frequently selected ontologies

## Troubleshooting

### Common Issues

1. **"No active ontologies available"**
   - Solution: Store at least one ontology with `is_active=true`

2. **"LLM returned invalid JSON"**
   - Solution: Check OpenAI API key and model availability
   - Verify `OPENAI_MODEL` supports JSON response format

3. **Database connection errors**
   - Solution: Verify `DB_*` environment variables
   - Check PostgreSQL accessibility from container/host

4. **Port 8102 already in use**
   - Solution: Change `MCP_PORT` in `.env` and `docker-compose.yml`

## Development

### Running Tests

```bash
# Unit tests (TODO)
pytest tests/

# Manual testing
python -m src.utility.llm_classifier  # Test LLM classifier
python -m src.utility.db_manager      # Test DB connection
```

### Adding New Tools

1. Implement function in `src/agents/ontology_agent.py`
2. Register tool in `ontology_mcp.py` with `@mcp.tool` decorator
3. Add documentation to this README

## Migration from Old System

### Phase 1: Parallel Run (Recommended)
1. Deploy ontology-mcp server
2. Migrate existing ontologies using `store_ontology` tool
3. Update Planner to call both old and new systems
4. Log differences for validation

### Phase 2: Cutover
1. Remove `project_description_detector.py` logic
2. Update all references to use `select_ontology_for_ticket`
3. Monitor classification quality

### Phase 3: Cleanup
1. Archive old ontology storage files
2. Remove unused code
3. Update documentation

## API Reference

Full API documentation available at: `http://localhost:8102/docs` (when server is running)

## Support

For issues or questions:
- Check logs: `logs/ontology_mcp.log`
- Review migrations: `migrations/*.sql`
- Contact: Kivor Platform Team

## License

Proprietary - Kivor AI Platform
