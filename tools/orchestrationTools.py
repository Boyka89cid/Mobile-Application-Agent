import inspect, logging
from dataclasses import dataclass, field
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from utils.config import ToolPrompts, Configuration
from adapters.postgresAdapter import PostgresAdapter
from tools.llmRouterTools import CheckingToolsLLMAsRouter

@dataclass
class SessionStateForTableCheck:
    session_id: str
    step: str = 'Start'
    table_type: str = ''

@dataclass
class SessionStateForCreateTable:
    session_id: str
    step: str = 'Start'
    table_type: str = ''
    table_name: str = ''
    user_confirmation: bool = False  # User confirmation input
    columns: List[Dict[str, str]] = None  # List of dicts with column name and type

@dataclass
class SessionStateForDeleteTable:
    session_id: str
    step: str = 'Start '
    table_name: str = ''
    user_confirmation: bool = False  # User confirmation input

@dataclass
class SessionStateForAddRecord:
    session_id: str
    step: str = 'Start'
    table_name: str = ''
    validated: bool = False
    record: Dict[str, Any] = field(default_factory=dict)  # Record to be added

@dataclass
class SessionStateForDeleteRecord:
    session_id: str
    step: str = 'Start'
    table_name: str = ''
    columns : List[str] = field(default_factory=list)  # List of column names in the table
    column_name: str = ''  # Column name to identify the record
    column_value: Any = None  # Value of the column to identify the record
    record_id: Any = None  # ID of the record to be deleted

TABLECHECKSESSIONS: Dict[str, SessionStateForTableCheck] = {}
CREATETABLESESSIONS: Dict[str, SessionStateForCreateTable] = {}
DELETETABLESESSIONS: Dict[str, SessionStateForDeleteTable] = {}
ADDRECORDSESSIONS: Dict[str, SessionStateForAddRecord] = {}
DELETERECORDSESSIONS: Dict[str, SessionStateForDeleteRecord] = {}

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

    # Finite State Machine for Check Table Types Orchestration
    def check_table_types(self, session_state: SessionStateForTableCheck) -> Dict[str, Any]:

        # On first call, create a new session if it doesn't exist, session_id would be passed from the LLM
        session = TABLECHECKSESSIONS.setdefault(session_state.session_id, session_state)

        if session.step == 'Start':
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
    
    # Finite State Machine for Create Table Orchestration
    def create_table(self, session_state: SessionStateForCreateTable) -> Dict[str, Any]:
        
        def decide_step(s: SessionStateForCreateTable) -> str:
            has_table_type = bool(s.table_type.strip())
            has_table_name = bool(s.table_name.strip())
            has_columns = bool(s.columns)  # True if list is non-empty; False for None or []
            has_confirmation = s.user_confirmation
            if not has_table_type:
                return "Start" # Start from beginning
            if has_table_type and not has_table_name:
                return "ASK_Table_Type"
            if has_table_type and has_table_name and not has_columns:
                return "ASK_Table_Name"
            if has_table_type and has_table_name and has_columns and not has_confirmation:
                return "ASK_Columns"
            return "Creating_Table..." if has_confirmation else "ASK_Columns"
            

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

        if session_state.table_type is not None:
            session.table_type = session_state.table_type
        if session_state.table_name is not None:
            session.table_name = session_state.table_name
        if session_state.columns is not None:
            session.columns = session_state.columns
        if session_state.user_confirmation is not None:
            session.user_confirmation = session_state.user_confirmation
        
        session.step = decide_step(session)

        if session.step == 'Start':
            session.step = 'ASK_Table_Type'
            return {
                "status": f"ask_table_type",
                "message": "Do you want to create a public table or a temporary table?"
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
            session.user_confirmation = session_state.user_confirmation
            result, success = create_new_table(
                table_type=session.table_type,
                table_name=session.table_name,
                columns=session.columns
            )
            if success:
                session.step = 'Completed'
                CREATETABLESESSIONS.pop(session.session_id, None)  # Clean up session
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
            CREATETABLESESSIONS.pop(session.session_id, None)  # Clean up session
            return {
                "status": "completed",
                "message": "Table creation process completed."
            }
    
       # Finite State Machine for Add Record Orchestration
    
    # Finite State Machine for Delete Table Orchestration
    def delete_table(self, session_state: SessionStateForDeleteTable) -> Dict[str, Any]:

        def decide_step(s: SessionStateForDeleteTable) -> str:
            has_table = bool(s.table_name.strip())
            has_confirmation = s.user_confirmation

            if not has_table:
                return "Start" # Start from beginning
            if has_table and not has_confirmation:
                return "ASK_Table_Name"
            else:
                return "DELETE_Table_confirmation"
            

        session = DELETETABLESESSIONS.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            session.table_name = session_state.table_name
        if session_state.user_confirmation is not None:
            session.user_confirmation = session_state.user_confirmation

        session.step = decide_step(session)
        # Asking table name
        if session.step == 'Start':
            session.step = 'ASK_Table_Name'
            return {
                "status": "ask_table_name",
                "message": "Which table would you like to delete? Please provide the exact name."
            }

        # Asking for confirmation
        elif session.step == 'ASK_Table_Name':
            session.table_name = session_state.table_name
            session.step = 'DELETE_Table_confirmation'
            return {
                "status": "DELETE_Table_confirmation",
                "message": f"Are you absolutely sure you want to delete the table '{session.table_name}'? This action cannot be undone. Please respond with 'YES' to proceed."
            }

        # Excecute the deletion of the table
        elif session.step == 'DELETE_Table_confirmation':
            if session_state.user_confirmation:
                try:
                    # Protection against deleting the main dataset
                    if session.table_name.lower() == "hrdataset_clean":
                        return {"status": "error", "message": "Deletion of the primary 'hrdataset_clean' table is prohibited."}
                    
                    query = f"DROP TABLE IF EXISTS {session.table_name};"
                    PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query)
                    session.step = 'Completed'
                    DELETETABLESESSIONS.pop(session.session_id, None)  # Clean up session
                    return {
                        "status": "success",
                        "message": f"Table '{session.table_name}' has been successfully deleted."
                    }
                except Exception as e:
                    return {"status": "error", "message": f"Failed to delete table: {str(e)}"}
            else:
                session.step = 'Start' # Reset session
                DELETETABLESESSIONS.pop(session.session_id, None)  # Clean up session
                return {
                    "status": "cancelled",
                    "message": "Deletion cancelled. The table was not removed."
                }
        
        return {"status": "completed", "message": "Process finished."}
    
    # Finite State Machine for Add Record Orchestration
    def add_record_to_table(self, session_state: SessionStateForAddRecord) -> Dict[str, Any]:

        def decide_step(s: SessionStateForAddRecord) -> str:
            has_table = bool(s.table_name.strip())
            has_record = bool(s.record)  # True if dict is non-empty; False for None or {}
            validated = bool(getattr(s, "validated", False))

            if not has_table and not has_record:
                return "Start" # Start from beginning
            if has_table and not has_record:
                return "ASK_Table_Name"
            # if not has_table and has_record:
            #     return "ASK_Table_Name"
            # has_table and has_record
            return "Add_Record" if validated else "Validate_Record"

        def get_column_names(table_name: str) -> List[str]:
            try:
                query = f"SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
                results = PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query, (table_name,))
                return [row['column_name'] for row in results]
            except Exception as e:
                logging.exception("Failed to get column names")
                return []

        def add_record(table_name: str, record: Dict[str, Any]) -> str:
            try:
                columns = ', '.join(record.keys())
                values_placeholders = ', '.join(['%s'] * len(record))
                values = tuple(record.values())
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({values_placeholders});"
                try:
                    PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query, values)
                except Exception as e:
                    logging.exception("Failed to add record")
                    return f"Error adding record to table {table_name}: {e}", False
                return f"Record added successfully to table {table_name}.", True
            except Exception as e:
                logging.exception("Failed to add record")
                return f"Error adding record to table {table_name}: {e}" , False
        
        # Set default returns key if session exists else create new session
        sessions = ADDRECORDSESSIONS.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            sessions.table_name = session_state.table_name
        if session_state.record is not None:
            sessions.record = session_state.record
        if session_state.validated is not None:
            sessions.validated = session_state.validated
        if session_state.record is not None:
            sessions.record = session_state.record
        
        # Check if table_name is already set, if yes, skip to next step
        sessions.step = decide_step(sessions)
    
        #logging.info(sessions.step)
        if sessions.step == 'Start':
            sessions.step = 'ASK_Table_Name'
            tables = CheckingToolsLLMAsRouter().check_db_public_tables()
            return {
                "status": "ask_table_name",
                "message": f"Please provide the name of the table you want to add a record to. {tables}"
            }
        elif sessions.step == 'ASK_Table_Name':
            sessions.table_name = session_state.table_name
            columns_names = get_column_names(sessions.table_name)
            columns_names_str = ', '.join(columns_names)
            message = f"The table {sessions.table_name} has the following columns: {columns_names_str}. Please provide the record to be added as a dictionary."
            sessions.step = 'Validate_Record'
            return {
                "status": f"ask_record",
                "message": message
            }
        elif sessions.step == 'Validate_Record':
            sessions.record = session_state.record
            # Here you would normally validate the record against the table schema
            sessions.validated = True
            sessions.step = 'Add_Record'
            return {
                "status": "record_summary",
                "message": f"Are you sure to add the following record to table {sessions.table_name}: {sessions.record}."
            }
        
        elif sessions.step == 'Add_Record':
            result, success = add_record(
                table_name=sessions.table_name,
                record = sessions.record
            )
            if success:
                sessions.step = 'Completed'
                ADDRECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
                return {
                    "status": "record_added",
                    "message": result
                }
            else:
                sessions.step = 'Add_Record'
                return {
                    "status": "error, call the tool again with correct details",
                    "message": result
                }
        else:
            ADDRECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
            return {
                'session': sessions,
                "status": f"completed", #{sessions.step}
                "message": "Add record process completed."
            }
    
    # Finite State Machine for Delete Record Orchestration
    def delete_record_from_table(self, session_state: SessionStateForDeleteRecord) -> Dict[str, Any]:
        
        def decide_step(s: SessionStateForDeleteRecord) -> str:
            has_table = bool(s.table_name.strip())
            has_column_name = bool(s.column_name.strip())
            has_column_value = s.column_value is not None
            has_record_id = s.record_id is not None

            if not has_table:
                return "Start" # Start from beginning
            if has_table and not (has_column_name and has_column_value):
                return "ASK_Table_Name"
            if has_table and has_column_name and has_column_value and not has_record_id:
                return "Ask_Record_Column_Name_and_Value"
            return "Delete_Record" if has_record_id else "Ask_Record_Column_Name_and_Value"
        

        def get_column_names(table_name: str) -> List[str]:
            try:
                query = f"SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
                results = PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query, (table_name,))
                return [row['column_name'] for row in results]
            except Exception as e:
                logging.exception("Failed to get column names")
                return []

        def check_table_exists(table_name: str) -> bool:
            try:
                query = f"SELECT to_regclass('{table_name}');"
                results = PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query)
                return results[0]['to_regclass'] is not None
            except Exception as e:
                logging.exception("Failed to check table existence")
                return False

        def find_record_by_column(table_name: str, column_name: str, value: Any) -> Optional[Dict[str, Any]]:
            try:
                query = f"SELECT * FROM {table_name} WHERE {column_name} = %s;"
                results = PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query, (value,))
                if results:
                    return results[0]
                else:
                    return None
            except Exception as e:
                logging.exception("Failed to find record")
                return None

        def delete_record_by_id(table_name: str, record_id: Any) -> str:
            try:
                query = f"DELETE FROM {table_name} WHERE id = %s;"
                try:
                    PostgresAdapter(config=Configuration.DB_CONFIG).execute_query(query, (record_id,))
                except Exception as e:
                    logging.exception("Failed to delete record")
                    return f"Error deleting record from table {table_name}: {e}", False
                return f"Record with ID {record_id} deleted successfully from table {table_name}.", True
            except Exception as e:
                logging.exception("Failed to delete record")
                return f"Error deleting record from table {table_name}: {e}", False

        sessions = DELETERECORDSESSIONS.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            sessions.table_name = session_state.table_name
        if session_state.columns is not None:
            sessions.columns = session_state.columns
        if session_state.column_name is not None:
            sessions.column_name = session_state.column_name
        if session_state.column_value is not None:
            sessions.column_value = session_state.column_value
        if session_state.record_id is not None:
            sessions.record_id = session_state.record_id
        
        sessions.step = decide_step(sessions)
        # Check if table_name is already set, if yes, skip to next step
        #sessions.step = 'ASK_Table_Name' if len(sessions.table_name) == 0 else sessions.step

        logging.info(f"session.step: {sessions.step}")
        if sessions.step == 'Start':
            sessions.step = 'ASK_Table_Name'
            return {
                "status": "ask_table_name",
                "message": "Please provide the name of the table you want to delete a record from."
            }
        elif sessions.step == 'ASK_Table_Name':
            sessions.table_name = session_state.table_name
            if not check_table_exists(sessions.table_name):
                sessions.step = 'ASK_Table_Name'
                return {
                    "status": "table_error",
                    "message": f"Table {sessions.table_name} does not exist. Please provide a valid table name."
                }
            else:
                columns_names = get_column_names(sessions.table_name)
            sessions.step = 'Ask_Record_Column_Name_and_Value'
            columns_names_str = ', '.join(columns_names)
            sessions.columns = columns_names
            message = f"The table {sessions.table_name} has the following columns: {columns_names_str}. Please select the column name with its corresponding value to identify the record to be deleted."
            return {
                "status": "ask_column_name_and_value",
                "message": message
            }
        elif sessions.step == 'Ask_Record_Column_Name_and_Value':
            sessions.column_name = session_state.column_name
            sessions.column_value = session_state.column_value
            record = find_record_by_column(sessions.table_name, sessions.column_name, sessions.column_value)
            # TODO YET TO HANDLE MULTIPLE RECORDS FOUND CASE
            if not record:
                sessions.step = 'Ask_Record_Column_Name_and_Value'
                return {
                    "status": "record_not_found",
                    "message": f"No record found in table {sessions.table_name} with column '{sessions.column_name}' having value '{sessions.column_value}'. Please try again."
                }
            sessions.record_id = record['id']
            sessions.step = 'Delete_Record'
            return {
                "status": "record_summary",
                "message": f"Delete record with ID {sessions.record_id} from table {sessions.table_name}."
            }
        elif sessions.step == 'Delete_Record':
            result, success = delete_record_by_id(
                table_name=sessions.table_name,
                record_id=sessions.record_id
            )
            if success:
                sessions.step = 'Completed'
                DELETERECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
                return {
                    "status": "record_deleted",
                    "message": result
                }
            else:
                sessions.step = 'Delete_Record'
                return {
                    "status": "error, call the tool again with correct details",
                    "message": result
                }
        else:
            DELETERECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
            return {
                "status": f"completed",
                "message": "Delete record process completed."
            }