"""
Database Manager for Ontology MCP

Handles PostgreSQL connections and operations for ontology management.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from src.logging import logger
from src.config import DB_HOST, DB_PORT, DB_NAME, DB_SCHEMA, DB_USER, DB_PASSWORD


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.connection_params = {
            'host': DB_HOST,
            'port': DB_PORT,
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD
        }
        logger.info(f"DatabaseManager initialized for {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            conn.set_session(autocommit=False)
            # Set schema
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {DB_SCHEMA}, public")
            logger.debug("Database connection established")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed")
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                return cur.rowcount
    
    def execute_insert(self, query: str, params: tuple = None):
        """Execute an insert and return the inserted row"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchone()


# Singleton instance
db_manager = DatabaseManager()
