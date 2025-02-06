import sqlite3
from typing import Optional, Tuple, List, Dict, Any

class Database:
    """SQLite database connection manager with query execution capabilities."""
    
    def __init__(self, db_path: str = 'data.db'):
        self.db_path = db_path
        
    def __enter__(self) -> 'Database':
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.conn.close()
        
    def execute(
        self,
        query: str,
        params: Optional[Tuple] = None,
        commit: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query safely with parameters
        
        Args:
            query: SQL query string
            params: Tuple of parameters for query
            commit: Whether to commit transaction (for INSERT/UPDATE/DELETE)
            
        Returns:
            List of result rows as dictionaries
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params or ())
            if commit:
                self.conn.commit()
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Database error: {str(e)}") from e
        finally:
            cursor.close()