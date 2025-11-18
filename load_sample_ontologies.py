#!/usr/bin/env python3
"""
Load Sample Ontologies

Loads the sample ontologies from sample_ontologies.json into the database.
Usage: python load_sample_ontologies.py
"""

import json
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Import after setting up path
from src.utility.db_manager import db_manager
from src.logging import logger


def load_sample_ontologies():
    """Load sample ontologies from JSON file"""
    print("\n" + "="*60)
    print("Loading Sample Ontologies")
    print("="*60)
    
    # Read sample ontologies
    with open('sample_ontologies.json', 'r') as f:
        ontologies = json.load(f)
    
    print(f"\nFound {len(ontologies)} sample ontologies to load")
    
    success_count = 0
    for key, ont_data in ontologies.items():
        try:
            print(f"\nLoading: {ont_data['name']}")
            
            query = """
            INSERT INTO ontology_store 
            (name, version, ontology_json, category, description, tags, priority, created_by, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (name, version) DO UPDATE 
            SET ontology_json = EXCLUDED.ontology_json,
                category = EXCLUDED.category,
                description = EXCLUDED.description,
                tags = EXCLUDED.tags,
                priority = EXCLUDED.priority,
                updated_at = NOW()
            RETURNING ontology_id, name, version
            """
            
            result = db_manager.execute_insert(
                query,
                (
                    ont_data['name'],
                    ont_data['version'],
                    json.dumps(ont_data['ontology_json']),
                    ont_data['category'],
                    ont_data['description'],
                    ont_data['tags'],
                    ont_data['priority'],
                    'system'
                )
            )
            
            print(f"  ✓ Loaded: {result['name']} v{result['version']} (ID: {result['ontology_id']})")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to load {ont_data['name']}: {str(e)}")
    
    print("\n" + "="*60)
    print(f"Summary: {success_count}/{len(ontologies)} ontologies loaded")
    print("="*60)
    
    if success_count == len(ontologies):
        print("\n✓ All sample ontologies loaded successfully!")
        return True
    else:
        print("\n✗ Some ontologies failed to load. Check errors above.")
        return False


if __name__ == "__main__":
    try:
        success = load_sample_ontologies()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Error loading sample ontologies: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)
