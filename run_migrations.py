#!/usr/bin/env python3
"""
Database Migration Runner

Runs all SQL migrations in order.
Usage: python run_migrations.py
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'kivorticketing')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'kivorticketing')

MIGRATIONS_DIR = 'migrations'


def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def run_migration(conn, migration_file):
    """Run a single migration file"""
    print(f"\n{'='*60}")
    print(f"Running migration: {migration_file}")
    print('='*60)
    
    with open(os.path.join(MIGRATIONS_DIR, migration_file), 'r') as f:
        sql = f.read()
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"✓ Migration {migration_file} completed successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration {migration_file} failed: {str(e)}")
        return False


def main():
    """Run all migrations"""
    print("\n" + "="*60)
    print("Kivor Ontology MCP - Database Migration Runner")
    print("="*60)
    print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Schema: {DB_SCHEMA}")
    print("="*60)
    
    if not DB_USER or not DB_PASSWORD:
        print("\n✗ ERROR: DB_USER and DB_PASSWORD must be set in .env file")
        sys.exit(1)
    
    # Get migration files
    migration_files = sorted([
        f for f in os.listdir(MIGRATIONS_DIR)
        if f.endswith('.sql')
    ])
    
    if not migration_files:
        print("\n✗ No migration files found in migrations/ directory")
        sys.exit(1)
    
    print(f"\nFound {len(migration_files)} migration(s):")
    for mf in migration_files:
        print(f"  - {mf}")
    
    print("\nConnecting to database...")
    
    try:
        conn = get_connection()
        print("✓ Connected successfully")
        
        success_count = 0
        for migration_file in migration_files:
            if run_migration(conn, migration_file):
                success_count += 1
            else:
                print("\n✗ Migration failed. Stopping execution.")
                break
        
        conn.close()
        
        print("\n" + "="*60)
        print(f"Migration Summary: {success_count}/{len(migration_files)} completed")
        print("="*60)
        
        if success_count == len(migration_files):
            print("\n✓ All migrations completed successfully!")
            sys.exit(0)
        else:
            print("\n✗ Some migrations failed. Please check errors above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Database connection error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
