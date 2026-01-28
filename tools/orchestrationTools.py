import inspect, logging
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from utils.config import ToolPrompts, Configuration
from adapters.postgresAdapter import PostgresAdapter

@dataclass
class SessionStateForTableCheck:
    session_id: str
    step: str = 'None'
    table_type: str = ''

@dataclass
class SessionStateForCreateTable:
    session_id: str
    step: str = 'None'
    table_type: str = ''
    table_name: str = ''
    columns: List[Dict[str, str]] = None  # List of dicts with column name and type

TABLECHECKSESSIONS: Dict[str, SessionStateForTableCheck] = {}
CREATETABLESESSIONS: Dict[str, SessionStateForCreateTable] = {}

def register_orchestration_tools(mcp: FastMCP):
    orchestration_tools = OrchestrationTools()
    available_tools = [name for name, func in inspect.getmembers(OrchestrationTools, predicate=inspect.isfunction) if not name.startswith('_')]
    for tool_name in available_tools:
        logging.info(f"Registering orchestration tool: {tool_name}")
        mcp.add_tool(
            getattr(orchestration_tools, tool_name),
            name=tool_name,
            description= getattr(ToolPrompts, tool_name, "No description available.")
        )

class OrchestrationTools:

    def check_table_types(self, session_state: SessionStateForTableCheck) -> Dict[str, Any]:

        # On first call, create a new session if it doesn't exist, session_id would be passed from the LLM
        session = TABLECHECKSESSIONS.setdefault(session_state.session_id, session_state)

        if session.step == 'None':
            session.step = 'ASK_Table_Type'
            return {
                "status": "ask_table_type",
                "message": "Do you want to check public tables or temporary tables? Please respond with 'public' or 'temporary'."
            }
        elif session.step == 'ASK_Table_Type':
            table_type = session_state.table_type.lower()
            if table_type == 'public':
                #session.step = 'ASK_Table_Type'
                return {
                    "status": "checking_public_tables",
                    "message": "Checking public tables in the database."
                }
            elif table_type == 'temporary':
                #session.step = 'ASK_Table_Type'
                return {
                    "status": "checking_temporary_tables",
                    "message": "Checking temporary tables in the database."
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid table type. Please respond with 'public' or 'temporary'."
                }
        else:
            return {
                "status": "completed",
                "message": "Table check process completed."
            }
    
    def create_table(self, session_state: SessionStateForCreateTable) -> Dict[str, Any]:
        
        def create_new_table(table_type, table_name, columns:list):
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
                    PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query)
                except Exception as e:
                    logging.exception("Failed to create table")
                    return f"Error creating table {table_name}: {e}", False
                return f"{table_type.capitalize()} table {table_name} created successfully with columns {columns_def}.", True
            except Exception as e:
                logging.exception("Failed to create table")
                return f"Error creating table {table_name}: {e}", False
        # On first call, create a new session if it doesn't exist, session_id would be passed from the LLM
        session = CREATETABLESESSIONS.setdefault(session_state.session_id, session_state)

        if session.step == 'None':
            session.step = 'ASK_Table_Type'
            return {
                "status": "ask_table_type",
                "message": "Do you want to create a public table or a temporary table? Please respond with 'public' or 'temporary'."
                }
        elif session.step == 'ASK_Table_Type':
            session.table_type = session_state.table_type
            session.step = 'ASK_Table_Name'
            return {
                "status": "ask_table_name",
                "message": "Please provide the name of the table you want to create."
            }
        elif session.step == 'ASK_Table_Name':
            session.table_name = session_state.table_name
            session.step = 'ASK_Columns'
            return {
                "status": "ask_columns",
                "message": f"Please provide the columns for the table"
            }
        elif session.step == 'ASK_Columns':
            session.columns = session_state.columns
            # Here you would normally create the table using the provided name and columns
            session.step = 'Creating_Table...'
            return {
                "status": "table_summary",
                "message": f"Create {session.table_type} table named {session.table_name} with columns {session.columns}."
            }
        elif session.step == 'Creating_Table...':
            
            result, success = create_new_table(
                table_type=session.table_type,
                table_name=session.table_name,
                columns=session.columns
            )
            if success:
                session.step = 'Completed'
                return {
                    "status": "table_created",
                    "message": result
                }
            else:
                session.step = 'Creating_Table...'
                return {
                    "status": "error, call the tool again with correct details",
                    "message": result
                }
        else:
            return {
                "status": "completed",
                "message": "Table creation process completed."
            }