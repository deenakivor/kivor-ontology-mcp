"""
Interactive Test for Kivor Ontology MCP Tools
Tests all 10 ontology management tools (P0 + P1)
Results are saved to JSON files
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv

load_dotenv()

# MCP SSE server URL
SERVER = "http://localhost:8102/sse"

# Directory for saving test results
RESULTS_DIR = Path("test_results")

# Path to KivorService ontologies
ONTOLOGIES_DIR = Path(__file__).parent.parent / "KivorService" / "ontologies"
RESULTS_DIR.mkdir(exist_ok=True)


def save_result_to_json(result_data: dict, test_name: str) -> str:
    """Save test result to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in test_name)
    safe_name = safe_name[:50].strip().replace(' ', '_')
    
    filename = f"{safe_name}_{timestamp}.json"
    filepath = RESULTS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
    
    return str(filepath)


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"🔧 {title}")
    print("=" * 80)


async def test_store_ontology(session: ClientSession):
    """Test 1: Store a new ontology"""
    print_header("TEST 1: Store Ontology")
    
    # List available ontologies from KivorService FIRST
    print(f"\n📁 Ontologies directory: {ONTOLOGIES_DIR}")
    
    name = None
    category = None
    description = None
    ontology_json = None
    
    if ONTOLOGIES_DIR.exists():
        ontology_files = sorted(ONTOLOGIES_DIR.glob("*.json"))
        if ontology_files:
            print("\n📋 Available ontologies from KivorService:")
            for idx, file in enumerate(ontology_files, 1):
                print(f"  {idx}. {file.name}")
            
            choice = input(f"\nSelect ontology number (1-{len(ontology_files)}, or 0 to skip): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(ontology_files):
                # Load from selected file
                selected_file = ontology_files[int(choice) - 1]
                json_file = str(selected_file)
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        ontology_json = json.load(f)
                    
                    # Auto-populate name from filename
                    name = selected_file.stem.replace("_ontology", "")
                    
                    # Auto-detect category
                    if 'sql' in json_file.lower() or 'database' in json_file.lower():
                        category = "database"
                    elif 'it_support' in json_file.lower() or 'support' in json_file.lower():
                        category = "it_support"
                    else:
                        category = "general"
                    
                    description = f"Ontology loaded from {selected_file.name}"
                    
                    print(f"\n✅ Loaded: {selected_file.name}")
                    print(f"   Name: {name}")
                    print(f"   Category: {category}")
                    
                except Exception as e:
                    print(f"❌ Error loading file: {e}")
                    return None
        else:
            print("⚠️  No ontology files found in KivorService/ontologies/")
    else:
        print(f"⚠️  Directory not found: {ONTOLOGIES_DIR}")
    
    # If no file selected, ask for manual input or sample
    if not ontology_json:
        print("\n📝 Manual input:")
        name = input("Enter ontology name (or press Enter to skip test): ").strip()
        if not name:
            print("❌ Test skipped")
            return None
        
        json_file = input("Enter JSON file path (or press Enter for sample): ").strip()
        
        if json_file:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    ontology_json = json.load(f)
                print(f"✅ Loaded ontology from: {json_file}")
            except Exception as e:
                print(f"❌ Error: {e}")
                return None
        else:
            ontology_json = {
                "entities": [{"name": "Database", "type": "System"}, {"name": "Query", "type": "Action"}],
                "relationships": [{"from": "Query", "to": "Database", "type": "EXECUTES_ON"}]
            }
            print("Using sample ontology")
        
        category = input("Enter category (default: database): ").strip() or "database"
        description = input("Enter description: ").strip() or f"Ontology for {name}"
    
    payload = {
        "name": name,
        "ontology_json": ontology_json,
        "category": category,
        "description": description,
        "tags": [category],
        "priority": 50
    }
    
    print("\n⏳ Storing ontology...")
    try:
        start_time = datetime.now()
        result = await session.call_tool("store_ontology", payload)
        end_time = datetime.now()
        
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "store_ontology",
            "payload": payload,
            "response": content,
            "duration": (end_time - start_time).total_seconds()
        }
        
        json_path = save_result_to_json(test_result, "store_ontology")
        
        if content.get("success"):
            print(f"\n✅ Ontology stored successfully!")
            print(f"   ID: {content.get('ontology_id')}")
            print(f"   Name: {content.get('name')}")
            print(f"   Version: {content.get('version')}")
            print(f"💾 Result saved to: {json_path}")
            return content.get('ontology_id')
        else:
            print(f"❌ Failed: {content.get('message')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def test_list_ontologies(session: ClientSession):
    """Test 2: List all ontologies"""
    print_header("TEST 2: List Ontologies")
    
    category = input("\nFilter by category (or press Enter for all): ").strip() or None
    
    payload = {"is_active": True}
    if category:
        payload["category"] = category
    
    print("\n⏳ Fetching ontologies...")
    try:
        result = await session.call_tool("list_ontologies", payload)
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "list_ontologies",
            "payload": payload,
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "list_ontologies")
        
        ontologies = content.get("ontologies", [])
        print(f"\n✅ Found {len(ontologies)} ontology(ies)")
        
        for onto in ontologies:
            print(f"\n   📦 {onto['name']} (v{onto['version']})")
            print(f"      ID: {onto['ontology_id']}")
            print(f"      Category: {onto['category']}")
            print(f"      Priority: {onto['priority']}")
        
        print(f"\n💾 Result saved to: {json_path}")
        return ontologies
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


async def test_retrieve_by_id(session: ClientSession, ontology_id: int = None):
    """Test 3: Retrieve ontology by ID"""
    print_header("TEST 3: Retrieve Ontology by ID")
    
    if not ontology_id:
        ontology_id = input("\nEnter ontology ID: ").strip()
        if not ontology_id:
            print("❌ Test skipped")
            return
        ontology_id = int(ontology_id)
    
    print(f"\n⏳ Retrieving ontology ID {ontology_id}...")
    try:
        result = await session.call_tool("retrieve_ontology_by_id", {"ontology_id": ontology_id})
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "retrieve_ontology_by_id",
            "payload": {"ontology_id": ontology_id},
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "retrieve_by_id")
        
        if content.get("success"):
            onto = content.get('ontology', {})
            print(f"\n✅ Ontology retrieved!")
            print(f"   Name: {onto.get('name')}")
            print(f"   Version: {onto.get('version')}")
            print(f"   Category: {onto.get('category')}")
            print(f"   Entities: {len(onto.get('ontology_json', {}).get('entities', []))}")
            print(f"   Relationships: {len(onto.get('ontology_json', {}).get('relationships', []))}")
            print(f"\n💾 Result saved to: {json_path}")
        else:
            print(f"❌ Not found: {content.get('message')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_select_ontology_for_ticket(session: ClientSession):
    """Test 4: Select ontology for a ticket (LLM-based) ⭐"""
    print_header("TEST 4: Select Ontology for Ticket ⭐ (LLM-Based)")
    
    print("\nExample tickets:")
    print("  • 'Database query timeout on production server'")
    print("  • 'Network connectivity issue in building A'")
    
    ticket_id = input("\nEnter ticket ID (e.g., TKT-123): ").strip()
    if not ticket_id:
        ticket_id = f"TKT-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Using auto-generated ID: {ticket_id}")
    
    title = input("Enter ticket title: ").strip()
    if not title:
        print("❌ Test skipped")
        return
    
    description = input("Enter ticket description: ").strip() or title
    
    payload = {
        "ticket_id": ticket_id,
        "ticket_title": title,
        "ticket_description": description
    }
    
    print("\n⏳ Classifying ticket with LLM...")
    print("   • Analyzing ticket content")
    print("   • Calling Azure OpenAI GPT-4.1-mini")
    print("   • Matching to best ontology")
    
    try:
        start_time = datetime.now()
        result = await session.call_tool("select_ontology_for_ticket", payload)
        end_time = datetime.now()
        
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "select_ontology_for_ticket",
            "payload": payload,
            "response": content,
            "duration": (end_time - start_time).total_seconds()
        }
        
        json_path = save_result_to_json(test_result, "select_ontology")
        
        if content.get("success"):
            selected = content.get('selected_ontology', {})
            classification = content.get('classification', {})
            
            print(f"\n✅ Ontology selected!")
            print(f"   Selected: {selected.get('name')} (v{selected.get('version')})")
            print(f"   Category: {selected.get('category')}")
            print(f"   Confidence: {classification.get('confidence', 0):.2f}")
            print(f"   Processing Time: {classification.get('processing_time_ms')}ms")
            print(f"\n🤖 LLM Reasoning:")
            print(f"   {classification.get('reasoning', 'N/A')}")
            if classification.get('keywords_found'):
                print(f"\n🏷️  Keywords Found: {', '.join(classification.get('keywords_found', []))}")
            print(f"\n💾 Result saved to: {json_path}")
        else:
            print(f"❌ Failed: {content.get('message')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_validate_ontology(session: ClientSession, ontology_id: int = None):
    """Test 5: Validate ontology structure"""
    print_header("TEST 5: Validate Ontology")
    
    if not ontology_id:
        ontology_id = input("\nEnter ontology ID to validate: ").strip()
        if not ontology_id:
            print("❌ Test skipped")
            return
        ontology_id = int(ontology_id)
    
    print(f"\n⏳ Validating ontology ID {ontology_id}...")
    try:
        result = await session.call_tool("validate_ontology", {"ontology_id": ontology_id})
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "validate_ontology",
            "payload": {"ontology_id": ontology_id},
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "validate_ontology")
        
        if content.get("is_valid"):
            print(f"\n✅ Ontology is valid!")
            print(f"   Format: {content['format']}")
        else:
            print(f"\n❌ Ontology is invalid!")
            for err in content.get('errors', []):
                print(f"   • {err}")
        
        print(f"\n💾 Result saved to: {json_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_retrieve_by_name(session: ClientSession):
    """Test 6: Retrieve ontology by name"""
    print_header("TEST 6: Retrieve Ontology by Name")
    
    name = input("\nEnter ontology name: ").strip()
    if not name:
        print("❌ Test skipped")
        return None
    
    print(f"\n⏳ Retrieving ontology '{name}' (latest version)...")
    try:
        result = await session.call_tool("retrieve_ontology_by_name", {"name": name})
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "retrieve_ontology_by_name",
            "payload": {"name": name},
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "retrieve_by_name")
        
        if content.get("success"):
            onto = content.get('ontology', {})
            print(f"\n✅ Ontology retrieved (latest version)!")
            print(f"   ID: {onto.get('ontology_id')}")
            print(f"   Version: {onto.get('version')}")
            print(f"   Category: {onto.get('category')}")
            print(f"\n💾 Result saved to: {json_path}")
            return onto.get('ontology_id')
        else:
            print(f"❌ Not found: {content.get('message')}")
            return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def test_update_ontology(session: ClientSession, ontology_id: int = None):
    """Test 7: Update ontology"""
    print_header("TEST 7: Update Ontology")
    
    if not ontology_id:
        ontology_id = input("\nEnter ontology ID to update: ").strip()
        if not ontology_id:
            print("❌ Test skipped")
            return
        ontology_id = int(ontology_id)
    
    description = input("New description (or press Enter to skip): ").strip()
    priority_str = input("New priority 1-100 (or press Enter to skip): ").strip()
    
    payload = {"ontology_id": ontology_id}
    if description:
        payload["description"] = description
    if priority_str:
        payload["priority"] = int(priority_str)
    
    if len(payload) == 1:
        print("❌ No updates specified")
        return
    
    print(f"\n⏳ Updating ontology...")
    try:
        result = await session.call_tool("update_ontology", payload)
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "update_ontology",
            "payload": payload,
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "update_ontology")
        
        if content.get("success"):
            print(f"\n✅ Ontology updated!")
            print(f"   {content.get('message')}")
            print(f"\n💾 Result saved to: {json_path}")
        else:
            print(f"❌ Failed: {content.get('message')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_delete_ontology(session: ClientSession, ontology_id: int = None):
    """Test 8: Delete ontology (soft delete)"""
    print_header("TEST 8: Delete Ontology (Soft Delete)")
    
    if not ontology_id:
        ontology_id = input("\nEnter ontology ID to delete: ").strip()
        if not ontology_id:
            print("❌ Test skipped")
            return
        ontology_id = int(ontology_id)
    
    confirm = input(f"\n⚠️  Delete ontology {ontology_id}? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Deletion cancelled")
        return
    
    print(f"\n⏳ Deleting ontology...")
    try:
        result = await session.call_tool("delete_ontology", {"ontology_id": ontology_id})
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "delete_ontology",
            "payload": {"ontology_id": ontology_id},
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "delete_ontology")
        
        if content.get("success"):
            print(f"\n✅ Ontology soft-deleted!")
            print(f"   {content.get('message')}")
            print(f"\n💾 Result saved to: {json_path}")
        else:
            print(f"❌ Failed: {content.get('message')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_override_ticket_ontology(session: ClientSession):
    """Test 9: Override ticket ontology assignment"""
    print_header("TEST 9: Override Ticket Ontology Assignment")
    
    ticket_id = input("\nEnter ticket ID: ").strip()
    if not ticket_id:
        print("❌ Test skipped")
        return
    
    ontology_id = input("Enter ontology ID to assign: ").strip()
    if not ontology_id:
        print("❌ Test skipped")
        return
    
    reason = input("Override reason: ").strip() or "Manual correction"
    override_by = input("Override by (username): ").strip() or "test_user"
    
    payload = {
        "ticket_id": ticket_id,
        "ontology_id": int(ontology_id),
        "override_reason": reason,
        "override_by": override_by
    }
    
    print(f"\n⏳ Overriding ticket ontology...")
    try:
        result = await session.call_tool("override_ticket_ontology", payload)
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "override_ticket_ontology",
            "payload": payload,
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "override_ontology")
        
        if content.get("success"):
            print(f"\n✅ Override successful!")
            print(f"   Assignment ID: {content.get('assignment_id')}")
            print(f"   {content.get('message')}")
            print(f"\n💾 Result saved to: {json_path}")
        else:
            print(f"❌ Failed: {content.get('message')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_get_ticket_history(session: ClientSession):
    """Test 10: Get ticket ontology assignment history"""
    print_header("TEST 10: Get Ticket Ontology History")
    
    ticket_id = input("\nEnter ticket ID: ").strip()
    if not ticket_id:
        print("❌ Test skipped")
        return
    
    print(f"\n⏳ Fetching assignment history...")
    try:
        result = await session.call_tool("get_ticket_ontology_history", {"ticket_id": ticket_id})
        content = json.loads(result.content[0].text)
        
        test_result = {
            "test_name": "get_ticket_ontology_history",
            "payload": {"ticket_id": ticket_id},
            "response": content
        }
        
        json_path = save_result_to_json(test_result, "ticket_history")
        
        assignments = content.get("assignments", [])
        print(f"\n✅ Found {len(assignments)} assignment(s)")
        
        for i, assign in enumerate(assignments, 1):
            print(f"\n   Assignment {i}:")
            print(f"   • Ontology: {assign['ontology_name']} (v{assign['ontology_version']})")
            print(f"   • Method: {assign['match_method']}")
            print(f"   • Confidence: {assign.get('match_confidence', 'N/A')}")
            print(f"   • Assigned: {assign['assigned_at']}")
        
        print(f"\n💾 Result saved to: {json_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Main test flow"""
    print("\n" + "=" * 80)
    print("🚀 Kivor Ontology MCP - Interactive Tool Testing")
    print("=" * 80)
    print("\nThis script tests all 10 ontology management tools:")
    print("\n🔷 P0 Tools:")
    print("   1. store_ontology")
    print("   2. list_ontologies")
    print("   3. retrieve_ontology_by_id")
    print("   4. select_ontology_for_ticket ⭐ (LLM)")
    print("   5. validate_ontology")
    print("\n🔶 P1 Tools:")
    print("   6. retrieve_ontology_by_name")
    print("   7. update_ontology")
    print("   8. delete_ontology")
    print("   9. override_ticket_ontology")
    print("   10. get_ticket_ontology_history")
    print(f"\n💾 Results: {RESULTS_DIR.absolute()}")
    print(f"🌐 Server: {SERVER}")
    
    print("\n" + "=" * 80)
    print("Connecting to MCP Server...")
    print("=" * 80)
    
    try:
        async with sse_client(SERVER) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("✅ Connected to MCP server")
                
                stored_id = None
                
                while True:
                    print("\n" + "=" * 80)
                    print("📋 TEST MENU")
                    print("=" * 80)
                    print("\n1️⃣  Store Ontology")
                    print("2️⃣  List Ontologies")
                    print("3️⃣  Retrieve by ID")
                    print("4️⃣  Select Ontology for Ticket ⭐ (LLM)")
                    print("5️⃣  Validate Ontology")
                    print("6️⃣  Retrieve by Name")
                    print("7️⃣  Update Ontology")
                    print("8️⃣  Delete Ontology")
                    print("9️⃣  Override Ticket Ontology")
                    print("🔟 Get Ticket History")
                    print("0️⃣  Exit")
                    
                    choice = input("\nSelect test (0-10): ").strip()
                    
                    if choice == '1':
                        stored_id = await test_store_ontology(session)
                    elif choice == '2':
                        await test_list_ontologies(session)
                    elif choice == '3':
                        await test_retrieve_by_id(session, stored_id)
                    elif choice == '4':
                        await test_select_ontology_for_ticket(session)
                    elif choice == '5':
                        await test_validate_ontology(session, stored_id)
                    elif choice == '6':
                        stored_id = await test_retrieve_by_name(session)
                    elif choice == '7':
                        await test_update_ontology(session, stored_id)
                    elif choice == '8':
                        await test_delete_ontology(session, stored_id)
                    elif choice == '9':
                        await test_override_ticket_ontology(session)
                    elif choice == '10':
                        await test_get_ticket_history(session)
                    elif choice == '0':
                        print("\n👋 Exiting...")
                        break
                    else:
                        print("❌ Invalid choice")
                    
                    input("\n⏸️  Press Enter to continue...")
                
                print("\n" + "=" * 80)
                print("✅ ALL TESTS COMPLETED")
                print("=" * 80)
                print(f"\n💾 All results saved to: {RESULTS_DIR.absolute()}")
                
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
