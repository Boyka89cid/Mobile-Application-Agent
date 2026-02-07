from typing import List, Dict, Any, Optional
import logging

class PostgresHelperFxns:

    def __init__(self, adapter):
        self.adapter = adapter

    def check_db_tables(self, type) -> str:
        try:
            if type == 'public':
                results = self.adapter.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
                )
                table_names = [row['table_name'] for row in results]
                return f"Public tables in the database: {table_names}"
            elif type == 'temporary':
                results = self.adapter.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
                )
                table_names = [row['table_name'] for row in results]
                return f"Temporary tables in the database: {table_names}"
            elif type == 'all':
                results_public = self.adapter.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
                )
                results_temporary = self.adapter.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
                )
                public_tables = [row['table_name'] for row in results_public]
                temporary_tables = [row['table_name'] for row in results_temporary]
                return f"Public tables: {public_tables}, Temporary tables: {temporary_tables}"
        except Exception as e:
            #logging.exception("Failed to fetch table names")
            return f"Error fetching table names: {e}"
        
    def count_db_tables(self, type) -> str:
        try:
            if type == 'public':
                results = self.adapter.execute_query(
                    "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';"
                )
                return f"Number of public tables: {results[0]['table_count']}"
            elif type == 'temporary':
                results = self.adapter.execute_query(
                    "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
                )
                return f"Number of temporary tables: {results[0]['table_count']}"
            elif type == 'all':
                results_public = self.adapter.execute_query(
                    "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';"
                )
                results_temporary = self.adapter.execute_query(
                    "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
                )
                return f"Public tables count: {results_public[0]['table_count']}, Temporary tables count: {results_temporary[0]['table_count']}"
        except Exception as e:
            #logging.exception("Failed to count tables")
            return f"Error counting tables: {e}"

    def create_new_table(self, table_type, table_name, columns:list):
        try:
            columns_def = ""
            for col in columns:
                for name, dtype in col.items():
                    columns_def += f"{name} {dtype}, "
            columns_def = columns_def.rstrip(", ")

            if table_type.lower() == 'public':
                query = f"CREATE TABLE {table_name} ({columns_def});"
            elif table_type.lower() == 'temporary':
                query = f"CREATE TEMPORARY TABLE {table_name} ({columns_def});"
            else:
                return "Invalid table type. Please specify 'public' or 'temporary'.", False
            try:
                self.adapter.execute_query(query)
            except Exception as e:
                #logging.exception("Failed to create table")
                return f"Error creating table {table_name}: {e}", False
            return f"{table_type.capitalize()} table {table_name} created successfully with columns {columns_def}.", True
        except Exception as e:
            #logging.exception("Failed to create table")
            return f"Error creating table {table_name}: {e}", False

    def list_all_tables(self) -> List[str]:
        try:
            results_public = self.adapter.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
            )
            results_temporary = self.adapter.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
            )
            table_names = [row['table_name'] for row in results_public + results_temporary]
            return table_names
        except Exception as e:
            logging.exception("Failed to fetch table names")
            return []

            
    def delete_table_by_name(self, table_name: str):
        try:
            query = f"DROP TABLE IF EXISTS {table_name};"
            self.adapter.execute_query(query)
            return f"Table '{table_name}' deleted successfully.", True
        except Exception as e:
            logging.exception("Failed to delete table")
            return f"Error deleting table {table_name}: {e}", False

    def list_all_tables(self) -> List[str]:
        try:
            results_public = self.adapter.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
            )
            results_temporary = self.adapter.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
            )
            table_names = [row['table_name'] for row in results_public + results_temporary]
            return table_names
        except Exception as e:
            logging.exception("Failed to fetch table names")
            return []

    def check_db_tables(self, type) -> str:
        try:
            if type == 'public':
                results = self.adapter.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
                )
            elif type == 'temporary':
                results = self.adapter.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
                )
            table_names = [row['table_name'] for row in results]
            return f"Tables in the database: {table_names}"
        except Exception as e:
            logging.exception("Failed to fetch table names")
            return f"Error fetching table names: {e}"

    def get_column_names(self, table_name: str) -> List[str]:
        try:
            query = f"SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
            results = self.adapter.execute_query(query, (table_name,))
            return [row['column_name'] for row in results]
        except Exception as e:
            logging.exception("Failed to get column names")
            return []

    def add_record(self, table_name: str, record: Dict[str, Any]) -> str:
        try:
            columns = ', '.join(record.keys())
            values_placeholders = ', '.join(['%s'] * len(record))
            values = tuple(record.values())
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({values_placeholders});"
            try:
                self.adapter.execute_query(query, values)
            except Exception as e:
                logging.exception("Failed to add record")
                return f"Error adding record to table {table_name}: {e}", False
            return f"Record added successfully to table {table_name}.", True
        except Exception as e:
            logging.exception("Failed to add record")
            return f"Error adding record to table {table_name}: {e}" , False
        
    def get_column_names(self, table_name: str) -> List[str]:
        try:
            query = f"SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
            results = self.adapter.execute_query(query, (table_name,))
            return [row['column_name'] for row in results]
        except Exception as e:
            logging.exception("Failed to get column names")
            return []

    def check_table_exists(self, table_name: str) -> bool:
        try:
            query = f"SELECT to_regclass('{table_name}');"
            results = self.adapter.execute_query(query)
            return results[0]['to_regclass'] is not None
        except Exception as e:
            logging.exception("Failed to check table existence")
            return False

    def find_record_by_column(self, table_name: str, column_name: str, value: Any) -> Optional[Dict[str, Any]]:
        try:
            query = f"SELECT * FROM {table_name} WHERE {column_name} = %s;"
            results = self.adapter.execute_query(query, (value,))
            if results:
                return results[0]
            else:
                return None
        except Exception as e:
            logging.exception("Failed to find record")
            return None

    def delete_record_by_id(self, table_name: str, record_id: Any) -> str:
        try:
            query = f"DELETE FROM {table_name} WHERE id = %s;"
            try:
                self.adapter.execute_query(query, (record_id,))
            except Exception as e:
                logging.exception("Failed to delete record")
                return f"Error deleting record from table {table_name}: {e}", False
            return f"Record with ID {record_id} deleted successfully from table {table_name}.", True
        except Exception as e:
            logging.exception("Failed to delete record")
            return f"Error deleting record from table {table_name}: {e}", False


 