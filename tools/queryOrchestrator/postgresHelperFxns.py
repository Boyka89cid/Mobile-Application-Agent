from typing import List, Dict, Any, Optional
from psycopg2 import sql
import logging, networkx as nx, matplotlib.pyplot as plt
from adapters.postgresAdapter import PostgresAdapter

class PostgresHelperFxns:

    def __init__(self, adapter: PostgresAdapter):
        self.adapter = adapter

    def check_db_tables(self, _type: str) -> str:
        try:
            if _type == 'public':
                query = sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
                results = self.adapter.execute_query(query)
                table_names = [row['table_name'] for row in results]
                return f"Public tables in the database: {table_names}"
            elif _type == 'temporary':
                query = sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';")
                results = self.adapter.execute_query(query)
                table_names = [row['table_name'] for row in results]
                return f"Temporary tables in the database: {table_names}"
            elif _type == 'all':
                query_public = sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
                results_public = self.adapter.execute_query(query_public)
                query_temporary = sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';")
                results_temporary = self.adapter.execute_query(query_temporary)
                public_tables = [row['table_name'] for row in results_public]
                temporary_tables = [row['table_name'] for row in results_temporary]
                return f"Public tables: {public_tables}, Temporary tables: {temporary_tables}"
        except Exception as e:
            #logging.exception("Failed to fetch table names")
            return f"Error fetching table names: {e}"
        
    def count_db_tables(self, _type: str) -> str:
        try:
            if _type == 'public':
                query = sql.SQL("SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';")
                results = self.adapter.execute_query(query)
                return f"Number of public tables: {results[0]['table_count']}"
            elif _type == 'temporary':
                query = sql.SQL("SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';")
                results = self.adapter.execute_query(query)
                return f"Number of temporary tables: {results[0]['table_count']}"
            elif _type == 'all':
                query_public = sql.SQL("SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';")
                results_public = self.adapter.execute_query(query_public)
                query_temporary = sql.SQL("SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';")
                results_temporary = self.adapter.execute_query(query_temporary)
                return f"Public tables count: {results_public[0]['table_count']}, Temporary tables count: {results_temporary[0]['table_count']}"
        except Exception as e:
            #logging.exception("Failed to count tables")
            return f"Error counting tables: {e}"

    def create_new_table(self, table_type: str, table_name: str, columns: list, primary_key_column: Optional[str] = None) -> str:
        try:
        # Expect columns like: [{"name": "id", "type": "INTEGER"}, ...]
            columns_def = ", ".join(
                f"{col['name']} {col['type']}"
                for col in columns
            )
            columns_def = columns_def.rstrip(", ")

            if table_type.lower() == 'public':
               query = sql.SQL("""
                    CREATE TABLE {table_name} ({columns_def}
                    {primary_key_clause});
                """).format(
                    table_name=sql.Identifier(table_name),
                    columns_def=sql.SQL(columns_def),
                    primary_key_clause=sql.SQL(f", PRIMARY KEY ({primary_key_column})") if primary_key_column else sql.SQL("")
                )
            elif table_type.lower() == 'temporary':
                query = sql.SQL("""
                    CREATE TEMPORARY TABLE {table_name} ({columns_def})
                    {primary_key_clause};
                """).format(
                    table_name=sql.Identifier(table_name),
                    columns_def=sql.SQL(columns_def),
                    primary_key_clause=sql.SQL(f", PRIMARY KEY ({primary_key_column})") if primary_key_column else sql.SQL("")
                )
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

    def contains_duplicates(self, table_name: str, column_name: str) -> bool:
        try:
            query = sql.SQL("""
                            SELECT {col}, COUNT(*)
                            FROM {table}
                            GROUP BY {col}
                            HAVING COUNT(*) > 1;
                            """).format(
                                col=sql.Identifier(column_name),
                                table=sql.Identifier(table_name)
                                )
            results = self.adapter.execute_query(query)
            return len(results) > 0
        except Exception as e:
            logging.exception("Failed to check for duplicates")
            return False

    def set_primary_key(self, table_name: str, column_name: str):
        try:
            if self.contains_duplicates(table_name, column_name):
                return f"Cannot set primary key on column '{column_name}' in table '{table_name}' because it contains duplicate values.", False
            else:
                query = sql.SQL("""
                                ALTER TABLE {table}
                                ADD PRIMARY KEY ({col});
                                """).format(
                                    table=sql.Identifier(table_name),
                                    col=sql.Identifier(column_name)
                                    )
                self.adapter.execute_query(query)
            return f"Primary key set on column '{column_name}' in table '{table_name}'.", True
        except Exception as e:
            logging.exception("Failed to set primary key")
            return f"Error setting primary key on table {table_name}: {e}", False
        
    def set_foreign_key(self, source_table: str, source_column: str, target_table: str, target_column: str):

        constraint_name = f"fk_{source_table}_{source_column}"

        try:
            query = sql.SQL(f"""
            ALTER TABLE {source_table}
            ADD CONSTRAINT {constraint_name}
            FOREIGN KEY ({source_column})
            REFERENCES {target_table}({target_column});
            """).format(
                source_table=sql.Identifier(source_table),
                constraint_name=sql.Identifier(constraint_name),
                source_column=sql.Identifier(source_column),
                target_table=sql.Identifier(target_table),
                target_column=sql.Identifier(target_column)
            )

            self.adapter.execute_query(query)

            return "Foreign key created successfully", True

        except Exception as e:
            return str(e), False

    def delete_table_by_name(self, table_name: str):
        try:
            query = sql.SQL("DROP TABLE IF EXISTS {table};").format(
                table=sql.Identifier(table_name)
            )
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

    def get_column_names(self, table_name: str) -> List[str]:
        try:
            query = sql.SQL('''
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = {table};'''
                            ).format(table=sql.Identifier(table_name))
            results = self.adapter.execute_query(query)
            return [row['column_name'] for row in results]
        except Exception as e:
            logging.exception("Failed to get column names")
            return []

    def check_if_primary_or_unique(self, table_name: str, column_name: str) -> bool:
        try:
            query = """
            SELECT 1
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
            AND tc.table_name = %s
            AND kcu.column_name = %s
            AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
            LIMIT 1;
            """

            results = self.adapter.execute_query(query, (table_name, column_name))
            return len(results) > 0

        except Exception as e:
            logging.exception("Failed to check if column is primary key or unique")
            return False
        
    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        try:
            query = """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            AND column_name = %s
            LIMIT 1;
            """

            results = self.adapter.execute_query(query, (table_name, column_name))
            return len(results) > 0

        except Exception as e:
            logging.exception("Failed to check if column exists")
            return False

    def get_column_type(self, table_name: str, column_name: str) -> str | None:
        try:
            query = """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            AND column_name = %s
            LIMIT 1;
            """

            results = self.adapter.execute_query(query, (table_name, column_name))

            if not results:
                return None

            return results[0]["data_type"]

        except Exception as e:
            logging.exception("Failed to get column type")
            return None

    def add_record(self, table_name: str, record: Dict[str, Any]) -> str:
        try:
            columns = ', '.join(record.keys())
            values_placeholders = ', '.join(['%s'] * len(record))
            values = tuple(record.values())
            query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values_placeholders});").format(
                table=sql.Identifier(table_name),
                columns=sql.SQL(columns),
                values_placeholders=sql.SQL(values_placeholders)
            )
            #query = f"INSERT INTO {table_name} ({columns}) VALUES ({values_placeholders});"
            try:
                self.adapter.execute_query(query, values)
            except Exception as e:
                logging.exception("Failed to add record")
                return f"Error adding record to table {table_name}: {e}", False
            return f"Record added successfully to table {table_name}.", True
        except Exception as e:
            logging.exception("Failed to add record")
            return f"Error adding record to table {table_name}: {e}" , False
    
    def update_record(self, table_name: str, identifier_column: str, identifier_value: Any, updated_values: Dict[str, Any]) -> str:
        try:
            set_clause = ', '.join([f"{col} = %s" for col in updated_values.keys()])
            values = tuple(updated_values.values()) + (identifier_value,)
            query = sql.SQL("UPDATE {table} SET {set_clause} WHERE {id_col} = %s;").format(
                table=sql.Identifier(table_name),
                set_clause=sql.SQL(set_clause),
                id_col=sql.Identifier(identifier_column)
            )
            try:
                self.adapter.execute_query(query, values)
            except Exception as e:
                logging.exception("Failed to update record")
                return f"Error updating record in table {table_name}: {e}", False
            return f"Record updated successfully in table {table_name}.", True
        except Exception as e:
            logging.exception("Failed to update record")
            return f"Error updating record in table {table_name}: {e}", False

    def get_column_names(self, table_name: str) -> List[str]:
        try:
            query = sql.SQL("SELECT column_name FROM information_schema.columns WHERE table_name = %s;")
            results = self.adapter.execute_query(query, (table_name,))
            return [row['column_name'] for row in results]
        except Exception as e:
            logging.exception("Failed to get column names")
            return []

    def check_table_exists(self, table_name: str) -> bool:
        try:
            query = sql.SQL("SELECT to_regclass(%s);")
            results = self.adapter.execute_query(query, (table_name,))
            return results[0]['to_regclass'] is not None
        except Exception as e:
            logging.exception("Failed to check table existence")
            return False

    def check_table_example(self, table_name: str) -> List[Dict[str, Any]]:
        try:
            query = sql.SQL("SELECT * FROM {table} LIMIT 1;").format(table=sql.Identifier(table_name))
            results = self.adapter.execute_query(query)
            return results
        except Exception as e:
            logging.exception("Failed to fetch table examples")
            return []
        
    def check_table_example_by_column(self, table_name: str, column_name: str) -> List[Dict[str, Any]]:
        try:
            query = sql.SQL("SELECT {column} FROM {table} LIMIT 5;").format(
                column=sql.Identifier(column_name),
                table=sql.Identifier(table_name)
            )
            results = self.adapter.execute_query(query)
            return results
        except Exception as e:
            logging.exception("Failed to fetch table examples by column")
            return []
    
    def fetch_column_data(self, table_name: str, column_name: str) -> List[Dict[str, Any]]:
        try:
            query = sql.SQL('SELECT {column}, COUNT(*) AS count FROM {table} GROUP BY {column};').format(
                table=sql.Identifier(table_name),
                column=sql.Identifier(column_name)
            )
            results = self.adapter.execute_query(query)
            return results
        except Exception as e:
            logging.exception("Failed to fetch column data")
            return []

    def find_record_by_column(self, table_name: str, column_name: str, value: Any) -> Optional[Dict[str, Any]]:
        try:
            query = sql.SQL("""
                SELECT *
                FROM {table}
                WHERE {column} = %s
                LIMIT 1;
            """).format(
                table=sql.Identifier(table_name),
                column=sql.Identifier(column_name)
            )
            results = self.adapter.execute_query(query, (value,))
            if results:
                return results[0]
            else:
                return None
        except Exception as e:
            logging.exception("Failed to find record")
            return None

    def delete_record_by_column(self, table_name: str, column_name: str, value: Any) -> str:
        try:
            query = sql.SQL("""
                DELETE FROM {table}
                WHERE {column} = %s;
            """).format(
                table=sql.Identifier(table_name),
                column=sql.Identifier(column_name)
            )
            try:
                self.adapter.execute_query(query, (value,))
            except Exception as e:
                logging.exception("Failed to delete record")
                return f"Error deleting record from table {table_name}: {e}", False
            return f"Record with {column_name} {value} deleted successfully from table {table_name}.", True
        except Exception as e:
            logging.exception("Failed to delete record")
            return f"Error deleting record from table {table_name}: {e}", False

    def fetch_filtered_records(self, table_name: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            # WHERE "department" = %s AND "salary" > %s
            conditions = []
            values = []
            for col, val in filters.items():
                conditions.append(f'"{col}" = %s')
                values.append(val)
            
            where_clause = " AND ".join(conditions)
            query = sql.SQL("""
                SELECT *
                FROM {table_name}
                WHERE {where_clause};
            """).format(
                table_name=sql.Identifier(table_name),
                where_clause=sql.SQL(where_clause)
            )
            
            results = self.adapter.execute_query(query, tuple(values))
            return results
        except Exception as e:
            logging.exception("Failed to fetch filtered records")
            return []

    def find_columns_with_unique_values(self, table_name: str) -> List[str]:
        try:
            # Step 1: get all column names
            column_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """
            columns = self.adapter.execute_query(column_query, (table_name,))

            unique_columns = []

            # Step 2: check each column separately
            for row in columns:
                column_name = row["column_name"]

                query = sql.SQL("""
                    SELECT 
                        COUNT(*) AS total_rows,
                        COUNT(DISTINCT {col}) AS distinct_rows,
                        COUNT({col}) AS non_null_rows
                    FROM {table};
                """).format(
                    col=sql.Identifier(column_name),
                    table=sql.Identifier(table_name)
                )

                result = self.adapter.execute_query(query)
                if not result:
                    continue

                total_rows = result[0]["total_rows"]
                distinct_rows = result[0]["distinct_rows"]
                non_null_rows = result[0]["non_null_rows"]

                # Option A: uniqueness ignoring NULLs
                if distinct_rows == non_null_rows:
                    unique_columns.append(column_name)

                # Option B: strict uniqueness including NULL logic
                # if distinct_rows == total_rows:
                #     unique_columns.append(column_name)

            return unique_columns

        except Exception:
            logging.exception("Failed to find columns with unique values")
            return []

    def match_pattern_in_column(self, table_name: str, column_name: str, pattern: str) -> List[Dict[str, Any]]:
        try:
            query = sql.SQL("""
                SELECT *
                FROM {table_name}
                WHERE {column_name} LIKE %s;
            """).format(
                table_name=sql.Identifier(table_name),
                column_name=sql.Identifier(column_name)
            )
            results = self.adapter.execute_query(query, (pattern,))
            return results
        except Exception as e:
            logging.exception("Failed to match pattern in column")
            return []
        
    def get_all_foreign_keys(self) -> list[dict]:
        try:
            query = """
            SELECT
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name;
            """

            results = self.adapter.execute_query(query)
            return results

        except Exception as e:
            logging.exception("Failed to fetch foreign keys")
            return []
    
    def build_networkx_schema_graph(self) -> nx.DiGraph:
        try:
            tables = self.list_all_tables()
            foreign_keys = self.get_all_foreign_keys()

            G = nx.DiGraph()

            # Add all tables as nodes
            for table in tables:
                G.add_node(table)

            # Add FK relationships as directed edges
            for fk in foreign_keys:
                source_table = fk["source_table"]
                source_column = fk["source_column"]
                target_table = fk["target_table"]
                target_column = fk["target_column"]

                G.add_edge(
                    source_table,
                    target_table,
                    source_column=source_column,
                    target_column=target_column,
                    label=f"{source_column} → {target_column}"
                )

            return G

        except Exception as e:
            logging.exception("Failed to build NetworkX schema graph")
            return nx.DiGraph()
        
    def draw_schema_graph(self, output_path: str) -> tuple[str, bool]:
        try:
            G = self.build_networkx_schema_graph()

            if len(G.nodes) == 0:
                return "No schema graph data available to draw.", False

            plt.figure(figsize=(8, 5))
            pos = {}

            # Nodes that have at least one edge
            connected_nodes = [n for n in G.nodes if G.degree(n) > 0]
            isolated_nodes = [n for n in G.nodes if G.degree(n) == 0]

            # Layout for connected component(s)
            if connected_nodes:
                connected_subgraph = G.subgraph(connected_nodes)
                connected_pos = nx.spring_layout(connected_subgraph, seed=42, k=0.8, iterations=100)

                # Keep connected nodes near center
                for node, (x, y) in connected_pos.items():
                    pos[node] = (x * 1.2, y * 1.2)

            # Place isolated nodes in a horizontal row at the bottom
            if isolated_nodes:
                start_x, gap, y = -0.8, 0.8, -1.2
                for i, node in enumerate(isolated_nodes):
                    pos[node] = (start_x + i * gap, y)

            nx.draw(
                G,
                pos,
                with_labels=True,
                node_size=2500,
                font_size=9,
                arrows=True
            )

            edge_labels = {
                (u, v): data.get("label", "")
                for u, v, data in G.edges(data=True)
            }

            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)

            plt.title("Database Schema Graph")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(output_path, format="png", bbox_inches="tight")
            plt.close()

            return output_path, True

        except Exception as e:
            logging.exception("Failed to draw schema graph")
            return str(e), False
            
    