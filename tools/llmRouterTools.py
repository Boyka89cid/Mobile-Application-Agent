import logging, inspect
from adapters.postgresAdapter import PostgresAdapter
from utils.config import Configuration, ToolPrompts
from mcp.server.fastmcp import FastMCP

def register_tools(mcp: FastMCP): 
    router_tools = CheckingToolsLLMAsRouter()
    
    # Note: Tool name should not start with underscore(_) to be registered
    available_tools = [name for name, func in inspect.getmembers(CheckingToolsLLMAsRouter, predicate=inspect.isfunction) if not name.startswith('_')]
    for tool_name in available_tools:
        logging.info(f"Registering tool: {tool_name}")
        mcp.add_tool(
            getattr(router_tools, tool_name),
            name=tool_name,
            description=getattr(ToolPrompts, tool_name, "No description available."),
            structured_output=True
        )
    

class CheckingToolsLLMAsRouter:

    def __init__(self):
        self.adapter = PostgresAdapter(config=Configuration.DB_CONFIG)
    
    def check_db_public_tables(self) -> str:
        try:
            results = self.adapter.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
            )
            table_names = [row['table_name'] for row in results]
            return f"Tables in the database: {table_names}"
        except Exception as e:
            logging.exception("Failed to fetch table names")
            return f"Error fetching table names: {e}"
    
    def check_db_temporary_tables(self) -> str:
        try:
            results = self.adapter.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
            )
            table_names = [row['table_name'] for row in results]
            return f"Temporary Tables in the database: {table_names}"
        except Exception as e:
            logging.exception("Failed to fetch temporary table names")
            return f"Error fetching temporary table names: {e}"

    def count_public_tables(self) -> int:
        try:
            results = self.adapter.execute_query(
                "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';"
            )
            return results[0]['table_count']
        except Exception as e:
            logging.exception("Failed to count tables")
            return -1
    
    def count_temporary_tables(self) -> int:
        try:
            results = self.adapter.execute_query(
                "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"
            )
            return results[0]['table_count']
        except Exception as e:
            logging.exception("Failed to count temporary tables")
            return -1

    def check_db_connection(self) -> str:
        try:
            results = self.adapter.execute_query("SELECT * FROM hrdataset_clean LIMIT 1;")
            return f"Database connection successful. Query results: {results}"
        except Exception as e:
            logging.exception("Database connection failed")
            return f"Database connection failed: {e}"
