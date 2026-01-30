"""
SQLite database manager for customer accounts, policies, and claims.
Provides connection management and query execution methods.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from config.settings import settings


class SQLiteManager:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the SQLite manager.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to settings.db_path
        """
        self.db_path = db_path or settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize the database with schema if it doesn't exist."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        with self.get_connection() as conn:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        fetch_one: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters for parameterized queries
            fetch_one: If True, return only the first result
            
        Returns:
            List of dictionaries representing rows, or single dict if fetch_one=True
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_write(
        self, 
        query: str, 
        params: Optional[tuple] = None
    ) -> int:
        """
        Execute a write operation (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query string
            params: Query parameters for parameterized queries
            
        Returns:
            Last row ID for INSERT operations, or number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    
    def execute_many(
        self, 
        query: str, 
        params_list: List[tuple]
    ) -> int:
        """
        Execute a query with multiple parameter sets (bulk insert/update).
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
    
    # Customer operations
    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email address."""
        query = "SELECT * FROM customers WHERE email = ?"
        return self.execute_query(query, (email,), fetch_one=True)
    
    def get_customer_by_account_number(self, account_number: str) -> Optional[Dict[str, Any]]:
        """Get customer by account number."""
        query = "SELECT * FROM customers WHERE account_number = ?"
        return self.execute_query(query, (account_number,), fetch_one=True)
    
    def get_customer_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Get customers by name (partial match)."""
        query = "SELECT * FROM customers WHERE name LIKE ?"
        return self.execute_query(query, (f"%{name}%",))
    
    # Policy operations
    def get_policies_by_customer_id(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get all policies for a customer."""
        query = """
            SELECT p.*, c.name as customer_name, c.email as customer_email
            FROM policies p
            JOIN customers c ON p.customer_id = c.id
            WHERE p.customer_id = ?
        """
        return self.execute_query(query, (customer_id,))
    
    def get_policy_by_number(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """Get policy by policy number."""
        query = """
            SELECT p.*, c.name as customer_name, c.email as customer_email
            FROM policies p
            JOIN customers c ON p.customer_id = c.id
            WHERE p.policy_number = ?
        """
        return self.execute_query(query, (policy_number,), fetch_one=True)
    
    def get_active_policies(self) -> List[Dict[str, Any]]:
        """Get all active policies."""
        query = """
            SELECT p.*, c.name as customer_name, c.email as customer_email
            FROM policies p
            JOIN customers c ON p.customer_id = c.id
            WHERE p.status = 'active'
        """
        return self.execute_query(query)
    
    # Claim operations
    def get_claims_by_policy_id(self, policy_id: int) -> List[Dict[str, Any]]:
        """Get all claims for a policy."""
        query = """
            SELECT cl.*, p.policy_number, p.type as policy_type
            FROM claims cl
            JOIN policies p ON cl.policy_id = p.id
            WHERE cl.policy_id = ?
        """
        return self.execute_query(query, (policy_id,))
    
    def get_claim_by_number(self, claim_number: str) -> Optional[Dict[str, Any]]:
        """Get claim by claim number."""
        query = """
            SELECT cl.*, p.policy_number, p.type as policy_type, c.name as customer_name
            FROM claims cl
            JOIN policies p ON cl.policy_id = p.id
            JOIN customers c ON p.customer_id = c.id
            WHERE cl.claim_number = ?
        """
        return self.execute_query(query, (claim_number,), fetch_one=True)
    
    def get_pending_claims(self) -> List[Dict[str, Any]]:
        """Get all pending claims."""
        query = """
            SELECT cl.*, p.policy_number, p.type as policy_type, c.name as customer_name
            FROM claims cl
            JOIN policies p ON cl.policy_id = p.id
            JOIN customers c ON p.customer_id = c.id
            WHERE cl.status = 'pending'
        """
        return self.execute_query(query)


# Global database manager instance
db_manager = SQLiteManager()
