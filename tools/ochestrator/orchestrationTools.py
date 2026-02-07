import inspect, logging
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from utils.config import ToolPrompts, Configuration
from adapters.postgresAdapter import PostgresAdapter
from tools.ochestrator.postgresHelperFxns import PostgresHelperFxns
from tools.llmRouterTools import CheckingToolsLLMAsRouter
from tools.ochestrator.sessionDataClasses import (
    SessionStateForTableCheck,
    SessionStateForTableCount,
    SessionStateForCreateTable,
    SessionStateForDeleteTable,
    SessionStateForAddRecord,
    SessionStateForDeleteRecord
)
from tools.ochestrator.sessionSteps import (
    CheckTableSteps,
    CountTableSteps,
    CreateTableSteps,
    DeleteTableSteps,
    AddRecordSteps,
    DeleteRecordSteps
)

TABLECHECKSESSIONS: Dict[str, SessionStateForTableCheck] = {}
TABLECOUNTSESSIONS: Dict[str, SessionStateForTableCount] = {}
CREATETABLESESSIONS: Dict[str, SessionStateForCreateTable] = {}
DELETETABLESESSIONS: Dict[str, SessionStateForDeleteTable] = {}
ADDRECORDSESSIONS: Dict[str, SessionStateForAddRecord] = {}
DELETERECORDSESSIONS: Dict[str, SessionStateForDeleteRecord] = {}

def register_orchestration_tools(mcp: FastMCP):
    orchestration_tools = OrchestrationTools(mcp=mcp)
    available_tools = [name for name, func in inspect.getmembers(OrchestrationTools, predicate=inspect.isfunction) if not name.startswith('_')]
    for tool_name in available_tools:
        logging.info(f"Registering orchestration tool: {tool_name}")
        mcp.add_tool(
            getattr(orchestration_tools, tool_name),
            name=tool_name,
            description= getattr(ToolPrompts, tool_name, "No description available.")
        )

class OrchestrationTools:

    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.adapter = PostgresAdapter(config=Configuration.DB_CONFIG)

    # Finite State Machine for Check Table Types Orchestration
    def check_tables(self, session_state: SessionStateForTableCheck) -> Dict[str, Any]:

        def decide_step(s: SessionStateForTableCheck) -> str:
            has_table_type = bool(s.table_type.strip())
            return CheckTableSteps.ASK_TYPE.value if not has_table_type else CheckTableSteps.FETCH.value
        
        # On first call, create a new session if it doesn't exist, session_id would be passed from the LLM
        session = TABLECHECKSESSIONS.setdefault(session_state.session_id, session_state)

        if session_state.table_type is not None:
            session.table_type = session_state.table_type

        session.step = decide_step(session)
        if session.step == CheckTableSteps.ASK_TYPE.value:
            return {
                "status": "ask_table_type",
                "message": "Do you want to check public tables, temporary tables, or all tables? Please respond with 'public', 'temporary', or 'all'."
            }
        elif session.step == CheckTableSteps.FETCH.value:

            table_type = session.table_type.lower()
            if table_type in ('public', 'temporary', 'all'):
                result = PostgresHelperFxns(self.adapter).check_db_tables(table_type)  # Call the actual tool to check temporary tables
                TABLECHECKSESSIONS.pop(session.session_id, None)  # Clean up session
                return {
                    "status": f"checked_{table_type}_tables",
                    "message": f"{table_type.capitalize()} tables in the database: {result}"
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid table type. Please respond with 'public', 'temporary', or 'all'."
                }
        else:
            TABLECHECKSESSIONS.pop(session.session_id, None)  # Clean up session
            return {
                "status": "completed",
                "message": "Table check process completed."
            }
    
    # Finite State Machine for Count Table Orchestration
    def count_tables(self, session_state: SessionStateForTableCount) -> Dict[str, Any]:
        def decide_step(s: SessionStateForTableCount) -> str:
            has_table_type = bool(s.table_type.strip())
            return CountTableSteps.ASK_TYPE.value if not has_table_type else CountTableSteps.COUNT.value
        
        # On first call, create a new session if it doesn't exist, session_id would be passed from the LLM
        session = TABLECOUNTSESSIONS.setdefault(session_state.session_id, session_state)

        if session_state.table_type is not None:
            session.table_type = session_state.table_type

        session.step = decide_step(session)
        if session.step == CountTableSteps.ASK_TYPE.value:
            return {
                "status": "ask_table_type",
                "message": "Do you want to count public tables, temporary tables, or all tables? Please respond with 'public', 'temporary' or 'all'."
            }
        elif session.step == CountTableSteps.COUNT.value:

            table_type = session.table_type.lower()
            if table_type in ('public', 'temporary', 'all'):
                result = PostgresHelperFxns(self.adapter).count_db_tables(table_type)  # Call the actual tool to count tables
                TABLECOUNTSESSIONS.pop(session.session_id, None)  # Clean up session
                return {
                    "status": f"counted_{table_type}_tables",
                    "message": result
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid table type. Please respond with 'public', 'temporary' or 'all'."
                }
        else:
            TABLECOUNTSESSIONS.pop(session.session_id, None)  # Clean up session
            return {
                "status": "completed",
                "message": "Table count process completed."
            }

    # Finite State Machine for Create Table Orchestration
    def create_table(self, session_state: SessionStateForCreateTable) -> Dict[str, Any]:
        
        def decide_step(s: SessionStateForCreateTable) -> str:
            has_table_type = bool(s.table_type.strip())
            has_table_name = bool(s.table_name.strip())
            has_columns = bool(s.columns)  # True if list is non-empty; False for None or []
            has_confirmation = s.user_confirmation
            if not has_table_type:
                return CheckTableSteps.ASK_TYPE.value
            if has_table_type and not has_table_name:
                return CreateTableSteps.ASK_TABLE_NAME.value
            if has_table_type and has_table_name and not has_columns:
                return CreateTableSteps.ASK_COLUMNS.value
            if has_table_type and has_table_name and has_columns and has_confirmation is None:
                return CreateTableSteps.USER_CONFIRMATION.value
            return CreateTableSteps.CREATE_TABLE.value 
            
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

        if session.step == CreateTableSteps.ASK_TYPE.value:
            return {
                "status": f"ask_table_type",
                "message": "Do you want to create a public table or a temporary table?"
                }
        elif session.step == CreateTableSteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "Please provide the name of the table you want to create."
            }
        elif session.step == CreateTableSteps.ASK_COLUMNS.value:
            return {
                "status": "ask_columns",
                "message": f"Please provide the columns for the table"
            }
        elif session.step == CreateTableSteps.USER_CONFIRMATION.value:
                return {
                    "status": "table_summary",
                    "message": f"Create {session.table_type} table named {session.table_name} with columns {session.columns}."
                }
        elif session.step == CreateTableSteps.CREATE_TABLE.value:
            if not session.user_confirmation:
                return {
                    "status": "cancelled",
                    "message": "Table creation cancelled by the user."
                }
            else:
                result, success = PostgresHelperFxns(self.adapter).create_new_table(
                    table_type=session.table_type,
                    table_name=session.table_name,
                    columns=session.columns
                )
                if success:
                    CREATETABLESESSIONS.pop(session.session_id, None)  # Clean up session
                    return {
                        "status": "table_created",
                        "message": result
                    }
                else:
                    session.columns = None  # Reset columns to ask again
                    session.step = CreateTableSteps.ASK_COLUMNS.value
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
                return DeleteTableSteps.ASK_TABLE_NAME.value # Start from beginning
            if has_table and not has_confirmation:
                return DeleteTableSteps.DELETE_TABLE_CONFIRMATION.value
            else:
                return DeleteTableSteps.DELETE_TABLE.value

        session = DELETETABLESESSIONS.setdefault(session_state.session_id, session_state)
        
        if session_state.table_name is not None:
            session.table_name = session_state.table_name
        if session_state.user_confirmation is not None:
            session.user_confirmation = session_state.user_confirmation

        session.step = decide_step(session)
        
        # Asking table name
        if session.step == DeleteTableSteps.ASK_TABLE_NAME.value:
            tables = PostgresHelperFxns(self.adapter).list_all_tables()
            return {
                "status": "ask_table_name",
                "message": f"Which table would you like to delete? Please provide the exact name. Available tables are: {tables}"
            }
        # Asking for confirmation
        elif session.step == DeleteTableSteps.DELETE_TABLE_CONFIRMATION.value:
            return {
                "status": "delete_table_confirmation",
                "message": f"Are you absolutely sure you want to delete the table '{session.table_name}'? This action cannot be undone. Please respond with 'YES' to proceed."
            }
        # Excecute the deletion of the table
        elif session.step == DeleteTableSteps.DELETE_TABLE.value:
            if session_state.user_confirmation:
                try:
                    # Protection against deleting the main dataset
                    if session.table_name.lower() == "hrdataset_clean":
                        return {"status": "error", "message": "Deletion of the primary 'hrdataset_clean' table is prohibited."}
                    
                    message, success = PostgresHelperFxns(self.adapter).delete_table_by_name(session.table_name)
                    if not success:
                        return {"status": "error", "message": message}
                    else:
                        DELETETABLESESSIONS.pop(session.session_id, None)  # Clean up session
                        return {
                            "status": "success",
                            "message": f"Table '{session.table_name}' has been successfully deleted."
                        }
                except Exception as e:
                    return {"status": "error", "message": f"Failed to delete table: {str(e)}"}
            else:
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
            validated = s.validated

            if not has_table and not has_record:
                return AddRecordSteps.ASK_TABLE_NAME.value
            elif has_table and not has_record:
                return AddRecordSteps.VALIDATE_RECORD.value
            elif has_table and has_record and validated is None:
                return AddRecordSteps.USER_CONFIRMATION.value
            elif has_table and has_record and validated:
                return AddRecordSteps.ADD_RECORD.value
            else:                
                return AddRecordSteps.ADD_RECORD.value  # Default to adding record if all info is present
       
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
        
        sessions.step = decide_step(sessions)

        if sessions.step == AddRecordSteps.ASK_TABLE_NAME.value:
            public_tables = PostgresHelperFxns(self.adapter).check_db_tables('public')
            temporary_tables = PostgresHelperFxns(self.adapter).check_db_tables('temporary')
            tables = f"Public tables: {public_tables}. Temporary tables: {temporary_tables}"
            return {
                "status": "ask_table_name",
                "message": f"Please provide the name of the table you want to add a record to. {tables}"
            }
        elif sessions.step == AddRecordSteps.VALIDATE_RECORD.value:
            if sessions.table_name not in PostgresHelperFxns(self.adapter).list_all_tables():
                sessions.step = AddRecordSteps.ASK_TABLE_NAME.value
                return {
                    "status": "error",
                    "message": f"Table '{sessions.table_name}' does not exist. Please provide a valid table name."
                }
            columns_names = PostgresHelperFxns(self.adapter).get_column_names(sessions.table_name)
            columns_names_str = ', '.join(columns_names)
            message = f"The table {sessions.table_name} has the following columns: {columns_names_str}. Please provide the record to be added as a dictionary."
            return {
                "status": f"ask_record",
                "message": message
            }
        elif sessions.step == AddRecordSteps.USER_CONFIRMATION.value:
            return {
                "status": "record_summary",
                "message": f"Are you sure to add the following record to table {sessions.table_name}: {sessions.record}."
            }
        elif sessions.step == AddRecordSteps.ADD_RECORD.value:
            if sessions.validated is False:
                return {
                    "status": "cancelled",
                    "message": "Record addition cancelled by the user."
                }
            else:
                result, success = PostgresHelperFxns(self.adapter).add_record(
                    table_name=sessions.table_name,
                    record = sessions.record
                )
                if success:
                    ADDRECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
                    return {
                        "status": "record_added",
                        "message": result
                    }
                else:
                    sessions.step = AddRecordSteps.VALIDATE_RECORD.value
                    return {
                        "status": "error, call the tool again with correct details",
                        "message": result
                    }
        else:
            ADDRECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
            return {
                'session': sessions,
                "status": f"completed",
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
                return DeleteRecordSteps.ASK_TABLE_NAME.value
            if has_table and not (has_column_name and has_column_value):
                return DeleteRecordSteps.GET_COLUMN_NAMES.value
            if has_table and has_column_name and has_column_value and not has_record_id:
                return DeleteRecordSteps.GET_RECORD.value
            return DeleteRecordSteps.DELETE_RECORD.value if has_record_id else DeleteRecordSteps.GET_RECORD.value
        

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
        if sessions.step == DeleteRecordSteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "Please provide the name of the table you want to delete a record from."
            }
        elif sessions.step == DeleteRecordSteps.GET_COLUMN_NAMES.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(sessions.table_name):
                sessions.step = DeleteRecordSteps.ASK_TABLE_NAME.value
                return {
                    "status": "table_error",
                    "message": f"Table {sessions.table_name} does not exist. Please provide a valid table name."
                }
            else:
                columns_names = PostgresHelperFxns(self.adapter).get_column_names(sessions.table_name)
            columns_names_str = ', '.join(columns_names)
            sessions.columns = columns_names
            message = f"The table {sessions.table_name} has the following columns: {columns_names_str}. Please select the column name with its corresponding value to identify the record to be deleted."
            return {
                "status": "get_record",
                "message": message
            }
        elif sessions.step == DeleteRecordSteps.GET_RECORD.value:
            record = PostgresHelperFxns(self.adapter).find_record_by_column(sessions.table_name, sessions.column_name, sessions.column_value)
            # TODO YET TO HANDLE MULTIPLE RECORDS FOUND CASE
            if not record:
                sessions.column_name = None  # Reset column name to ask again
                sessions.column_value = None  # Reset column value to ask again
                return {
                    "status": "record_not_found",
                    "message": f"No record found in table {sessions.table_name} with column '{sessions.column_name}' having value '{sessions.column_value}'. Please try again."
                }
            else:
                sessions.record_id = record
                return {
                    "status": "record_summary",
                    "message": f"Delete record with ID {sessions.record_id} from table {sessions.table_name}."
                }
        elif sessions.step == DeleteRecordSteps.DELETE_RECORD.value:
            if sessions.user_confirmation is False:
                DELETERECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
                return {
                    "status": "cancelled",
                    "message": "Record deletion cancelled by the user."
                }
            else:
                result, success = PostgresHelperFxns(self.adapter).delete_record_by_id(
                    table_name=sessions.table_name,
                    record_id=sessions.record_id
                )
                if success:
                    DELETERECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
                    return {
                        "status": "record_deleted",
                        "message": result
                    }
                else:
                    sessions.column_name = None  # Reset column name to ask again
                    sessions.column_value = None  # Reset column value to ask again
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