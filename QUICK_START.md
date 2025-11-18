# Quick Start Guide - Kivor Ontology MCP

## 🚀 Setup in 5 Minutes

### Step 1: Configure Environment (1 min)

```bash
cd kivor-ontology-mcp
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
OPENAI_API_KEY=sk-your-openai-key
```

### Step 2: Run Database Migrations (1 min)

```bash
python run_migrations.py
```

Expected output:
```
✓ Migration 001_create_ontology_store.sql completed successfully
✓ Migration 002_create_ticket_assignments.sql completed successfully
✓ Migration 003_create_functions.sql completed successfully
✓ All migrations completed successfully!
```

### Step 3: Start Server (1 min)

**Option A: Local**
```bash
pip install -r requirements.txt
python ontology_mcp.py
```

**Option B: Docker**
```bash
docker-compose up -d
```

Server running at: `http://localhost:8102`

### Step 4: Store Your First Ontology (1 min)

```bash
curl -X POST http://localhost:8102/tools/store_ontology \
  -H "Content-Type: application/json" \
  -d '{
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
    "description": "Ontology for infrastructure-related tickets",
    "tags": ["infrastructure", "server", "network"],
    "priority": 80,
    "version": "1.0.0",
    "created_by": "admin"
  }'
```

### Step 5: Test Ticket Classification (1 min)

```bash
curl -X POST http://localhost:8102/tools/select_ontology_for_ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-TEST001",
    "ticket_title": "Production server connectivity issue",
    "ticket_description": "The main application server cannot reach the database server. Network diagnostics show packet loss.",
    "project_id": 1
  }'
```

Expected response:
```json
{
  "success": true,
  "assignment_id": 1,
  "selected_ontology": {
    "ontology_id": 1,
    "name": "infrastructure_ontology",
    "version": "1.0.0",
    "category": "infrastructure"
  },
  "classification": {
    "confidence": 0.95,
    "reasoning": "Ticket involves infrastructure components...",
    "category": "infrastructure",
    "keywords_found": ["server", "network", "connectivity"],
    "processing_time_ms": 1200
  }
}
```

## ✅ Verification Checklist

- [ ] Database migrations completed
- [ ] Server starts without errors
- [ ] At least one ontology stored
- [ ] Test ticket classification succeeds
- [ ] Logs appear in `logs/ontology_mcp.log`

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'fastmcp'"
```bash
pip install -r requirements.txt
```

### "Database connection error"
Check your `.env` file:
- `DB_HOST`, `DB_PORT`, `DB_NAME` correct?
- `DB_USER` has permissions?
- Can you connect with: `psql -h 74.225.248.241 -p 5433 -U your_user -d kivorticketing`

### "No active ontologies available"
Store at least one ontology using Step 4 above.

## 📊 View Logs

```bash
# Local
tail -f logs/ontology_mcp.log

# Docker
docker-compose logs -f ontology-mcp
```

## 🎯 Next Steps

1. **Store production ontologies** - Migrate existing ontologies from files
2. **Integrate with Planner** - Update KivorPlannerAgent to call `select_ontology_for_ticket`
3. **Monitor performance** - Check LLM confidence scores and processing times
4. **Tune priorities** - Adjust ontology priorities based on selection patterns

## 📚 Full Documentation

See [README.md](README.md) for complete API reference and integration guide.

---

**Need Help?** Check logs or contact Kivor Platform Team.
