import psycopg2
from psycopg2.extras import DictCursor
from typing import List, Dict, Any, Optional, Sequence
from logging import log

class PostgresAdapter:

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def _connect(self):
        return psycopg2.connect(
            host=self.config.get('host', 'localhost'),
            port=self.config.get('port', 5432),
            database=self.config['dbname'],
            user=self.config['user'],
            password=self.config['password']
        )

    def execute_query(self, query: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
        conn = self._connect()
        #conn.cursor(cursor_factory=DictCursor).execute(query, params)
        try:
            with conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall() if cur.description else []
                    return [dict(r) for r in rows]
        except Exception as e:
            conn.rollback()
            error_msg = f"Error executing query: {e}"
            log(error_msg)
            raise
        finally:
            conn.close()
