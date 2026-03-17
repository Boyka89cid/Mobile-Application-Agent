import inspect, logging, base64
import mimetypes
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional, Union
from utils.config import Configuration
from tools.queryOrchestrator.toolDescriptions import ToolPrompts
from adapters.postgresAdapter import PostgresAdapter
from tools.queryOrchestrator.postgresHelperFxns import PostgresHelperFxns
from mcp.types import TextContent, ImageContent
from tools.queryOrchestrator.sessionDataClasses import (
    SessionStateForGenerateSchemaGraph,
    SessionStateForPatternMatchRecord,
    SessionStateForTableCheck,
    SessionStateForTableCount,
    SessionStateForCreateTable,
    SessionStateForDeleteTable,
    SessionStateForAddRecord,
    SessionStateForDeleteRecord,
    SessionStateForUpdateRecord,
    SessionStateForRetrieveRecord,
    SessionStateForFilterRecord,
    SessionStateSettingPrimaryKey,
    SessionStateForSettingForeignKey
)
from tools.queryOrchestrator.sessionSteps import (
    CheckTableSteps,
    CountTableSteps,
    GenerateSchemaGraphSteps,
    SetForeignKeySteps,
    CreateTableSteps,
    DeleteTableSteps,
    AddRecordSteps,
    DeleteRecordSteps,
    PatternMatchRecordSteps,
    RetrieveRecordSteps,
    FilterRecordSteps,
    SetPrimaryKeySteps,
    UpdateRecordSteps
)

TABLECHECKSESSIONS: Dict[str, SessionStateForTableCheck] = {}
TABLECOUNTSESSIONS: Dict[str, SessionStateForTableCount] = {}
CREATETABLESESSIONS: Dict[str, SessionStateForCreateTable] = {}
DELETETABLESESSIONS: Dict[str, SessionStateForDeleteTable] = {}
ADDRECORDSESSIONS: Dict[str, SessionStateForAddRecord] = {}
UPDATERECORDSESSIONS: Dict[str, SessionStateForUpdateRecord] = {}
DELETERECORDSESSIONS: Dict[str, SessionStateForDeleteRecord] = {}
RETRIEVERECORDSESSIONS: Dict[str, SessionStateForRetrieveRecord] = {}
FILTERRECORDSESSIONS: Dict[str, SessionStateForFilterRecord] = {}
PATTERNMATCHRECORDSESSIONS: Dict[str, SessionStateForPatternMatchRecord] = {}
SETTINGPRIMARYKEYSESSIONS: Dict[str, SessionStateSettingPrimaryKey] = {}
SETFOREIGNKEYSESSIONS: Dict[str, SessionStateForSettingForeignKey] = {}
GENERATESCHEMAGRAPHSESSIONS : Dict[str, SessionStateForGenerateSchemaGraph] = {}

def register_orchestration_tools(mcp: FastMCP):
    orchestration_tools = OrchestrationTools(mcp=mcp, adapter=PostgresAdapter(config=Configuration.DB_CONFIG))
    available_tools = [name for name, func in inspect.getmembers(OrchestrationTools, predicate=inspect.isfunction) if not name.startswith('_')]
    for tool_name in available_tools:
        logging.info(f"Registering orchestration tool: {tool_name}")
        mcp.add_tool(
            getattr(orchestration_tools, tool_name),
            name=tool_name,
            description= getattr(ToolPrompts, tool_name, "No description available.")
        )

class OrchestrationTools:

    def __init__(self, mcp: FastMCP, adapter: PostgresAdapter):
        self.mcp = mcp
        self.adapter = adapter

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
            has_primary_key = s.primary_key_column
            has_confirmation = s.user_confirmation
            
            if not has_table_type:
                return CreateTableSteps.ASK_TYPE.value
            if has_table_type and not has_table_name:
                return CreateTableSteps.ASK_TABLE_NAME.value
            if has_table_type and has_table_name and not has_columns:
                return CreateTableSteps.ASK_COLUMNS.value
            if has_table_type and has_table_name and has_columns and has_primary_key is None:
                return CreateTableSteps.ASK_PRIMARY_KEY.value
            if has_table_type and has_table_name and has_columns and has_primary_key is not None and has_confirmation is None:
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
        if session_state.primary_key is not None:
            session.primary_key = session_state.primary_key
        if session_state.primary_key_column is not None:
            session.primary_key_column = session_state.primary_key_column
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
        elif session.step == CreateTableSteps.ASK_PRIMARY_KEY.value:
            return {
                "status": "ask_primary_key",
                "message": f"Do you want to set a primary key for the table? If yes, which column would you like to set as the primary key?"
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
                    columns=session.columns,
                    primary_key_column=session.primary_key_column if session.primary_key else None
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
    
    # Finite State Machine for Retrieve Record Orchestration
    def retrieve_record_from_table(self, session_state: SessionStateForRetrieveRecord) -> Dict[str, Any]:
        def decide_step(s: SessionStateForRetrieveRecord) -> str:
            has_table = bool(s.table_name.strip()) 
            has_columns = bool(s.columns)  # True if list is non-empty; False for None or []

            if not has_table:
                return RetrieveRecordSteps.ASK_TABLE_NAME.value
            if has_table and not has_columns:
                return RetrieveRecordSteps.GET_COLUMN_NAMES.value
            if has_table and has_columns:
                return RetrieveRecordSteps.GET_RECORD.value

        session = RETRIEVERECORDSESSIONS.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            session.table_name = session_state.table_name
        if session_state.columns is not None:
            session.columns = session_state.columns
        if session_state.column_name is not None:
            session.column_name = session_state.column_name
        if session_state.column_value is not None:
            session.column_value = session_state.column_value
        
        session.step = decide_step(session)
        if session.step == RetrieveRecordSteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "Please provide the name of the table you want to retrieve a record from."
            }
        elif session.step == RetrieveRecordSteps.GET_COLUMN_NAMES.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.table_name):
                session.step = RetrieveRecordSteps.ASK_TABLE_NAME.value
                return {
                    "status": "table_error",
                    "message": f"Table {session.table_name} does not exist. Please provide a valid table name."
                }
            else:
                columns_names = PostgresHelperFxns(self.adapter).get_column_names(session.table_name)
            columns_names_str = ', '.join(columns_names)
            session.columns = columns_names
            example_values = PostgresHelperFxns(self.adapter).check_table_example(session.table_name)
            message = f"The table {session.table_name} has the following columns: {columns_names_str} with example values as {example_values}. Please select the column and the record to be retrieved."
            return {
                "status": "get_record",
                "message": message
            }
        elif session.step == RetrieveRecordSteps.GET_RECORD.value:
            tbl, col, val = session.table_name, session.column_name, session.column_value
            record = PostgresHelperFxns(self.adapter).find_record_by_column(tbl, col, val)
            if not record:
                session.column_name = ''  # Reset column name to ask again
                session.column_value = None  # Reset column value to ask again
                session.columns = None  # Reset columns
                return {
                    "status": "record_not_found",
                    "message": f"No record found in table {tbl} with column '{col}' having value '{val}'. Please try again."
                }
            else:
                RETRIEVERECORDSESSIONS.pop(session.session_id, None)  # Clean up session
                return {
                    "status": "record_retrieved",
                    "message": f"I found a record {record} from table {tbl}."
                }

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
                    if session.table_name.lower() == "hrdataset":
                        return {"status": "error", "message": "Deletion of the primary 'hrdataset' table is prohibited."}
                    
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
            user_confirmation = s.user_confirmation

            if not has_table and not has_record:
                return AddRecordSteps.ASK_TABLE_NAME.value
            elif has_table and not has_record:
                return AddRecordSteps.VALIDATE_RECORD.value
            elif has_table and has_record and user_confirmation is None:
                return AddRecordSteps.USER_CONFIRMATION.value
            elif has_table and has_record and user_confirmation is not None:
                return AddRecordSteps.ADD_RECORD.value
            else:                
                return AddRecordSteps.ADD_RECORD.value  # Default to adding record if all info is present
       
        # Set default returns key if session exists else create new session
        sessions = ADDRECORDSESSIONS.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            sessions.table_name = session_state.table_name
        if session_state.record is not None:
            sessions.record = session_state.record
        if session_state.user_confirmation is not None:
            sessions.user_confirmation = session_state.user_confirmation
        
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
                "message": f"Are you sure to add the following record to table {sessions.table_name}: {sessions.record}. with {sessions}"
            }
        elif sessions.step == AddRecordSteps.ADD_RECORD.value:
            if sessions.user_confirmation is False:
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
    
    # Finite State Machine for Update Record Orchestration
    def update_record_in_table(self, session_state: SessionStateForUpdateRecord) -> Dict[str, Any]:

        def decide_step(s: SessionStateForUpdateRecord) -> str:
            has_table = bool(s.table_name.strip())
            has_columns = bool(s.columns)  # True if list is non-empty; False for None or []
            has_record_identifier = bool(s.column_name.strip()) and s.column_value is not None
            has_updated_values = bool(s.updated_values)  # True if dict is non-empty; False for None or {}
            user_confirmation = s.user_confirmation

            if not has_table:
                return UpdateRecordSteps.ASK_TABLE_NAME.value
            elif has_table and not has_columns:
                return UpdateRecordSteps.GET_COLUMN_NAMES.value
            elif has_table and has_columns and not has_record_identifier:
                return UpdateRecordSteps.ASK_RECORD_IDENTIFIER.value
            elif has_table and has_columns and has_record_identifier and not has_updated_values:
                return UpdateRecordSteps.ASK_UPDATED_VALUES.value
            elif has_table and has_columns and has_record_identifier and has_updated_values and user_confirmation is None:
                return UpdateRecordSteps.USER_CONFIRMATION.value
            elif has_table and has_columns and has_record_identifier and has_updated_values and user_confirmation is not None:
                return UpdateRecordSteps.UPDATE_RECORD.value
            else:
                return UpdateRecordSteps.UPDATE_RECORD.value  # Default to updating record if all info is present

        # Set default returns key if session exists else create new session
        sessions = UPDATERECORDSESSIONS.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            sessions.table_name = session_state.table_name
        if session_state.columns is not None:
            sessions.columns = session_state.columns
        if session_state.column_name is not None:
            sessions.column_name = session_state.column_name
        if session_state.column_value is not None:
            sessions.column_value = session_state.column_value
        if session_state.updated_values is not None:
            sessions.updated_values = session_state.updated_values
        if session_state.user_confirmation is not None:
            sessions.user_confirmation = session_state.user_confirmation
        
        sessions.step = decide_step(sessions)

        if sessions.step == UpdateRecordSteps.ASK_TABLE_NAME.value:
            public_tables = PostgresHelperFxns(self.adapter).check_db_tables('public')
            temporary_tables = PostgresHelperFxns(self.adapter).check_db_tables('temporary')
            tables = f"Public tables: {public_tables}. Temporary tables: {temporary_tables}"
            return {
                "status": "ask_table_name",
                "message": f"Please provide the name of the table you want to update a record in. {tables}"
            }
        elif sessions.step == UpdateRecordSteps.GET_COLUMN_NAMES.value:
            if sessions.table_name not in PostgresHelperFxns(self.adapter).list_all_tables():
                sessions.step = UpdateRecordSteps.ASK_TABLE_NAME.value
                return {
                    "status": "error",
                    "message": f"Table '{sessions.table_name}' does not exist. Please provide a valid table name."
                }
            columns_names = PostgresHelperFxns(self.adapter).get_column_names(sessions.table_name)
            columns_names_str = ', '.join(columns_names)
            sessions.columns = columns_names
            message = f"The table {sessions.table_name} has the following columns: {columns_names_str}. Please provide the column and value to identify the record to be updated."
            return {
                "status": f"ask_record_identifier",
                "message": message
            }
        elif sessions.step == UpdateRecordSteps.ASK_RECORD_IDENTIFIER.value:
            example_records_in_column = PostgresHelperFxns(self.adapter).check_table_example_by_column(sessions.table_name, sessions.column_name)
            message = f"To identify the record to be updated, please provide the column name and its corresponding value. Here are some example records for reference: {example_records_in_column}"
            return {
                "status": "ask_record_identifier",
                "message": message
            }
        elif sessions.step == UpdateRecordSteps.ASK_UPDATED_VALUES.value:
            return {
                "status": "ask_updated_values",
                "message": f"Please provide the updated values for the record with column names and their corresponding new values."
            }
        elif sessions.step == UpdateRecordSteps.USER_CONFIRMATION.value:
            return {
                "status": "record_summary",
                "message": f"Are you sure to update the record in table {sessions.table_name} where {sessions.column_name} = {sessions.column_value} with the following updated values: {sessions.updated_values}?"
            }
        elif sessions.step == UpdateRecordSteps.UPDATE_RECORD.value:
            if sessions.user_confirmation is False:
                return {
                    "status": "cancelled",
                    "message": "Record update cancelled by the user."
                }
            else:
                result, success = PostgresHelperFxns(self.adapter).update_record(
                    table_name=sessions.table_name,
                    identifier_column=sessions.column_name,
                    identifier_value=sessions.column_value,
                    updated_values=sessions.updated_values
                )
                if success:
                    UPDATERECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
                    return {
                        "status": "record_updated",
                        "message": result
                    }
                else:
                    sessions.step = UpdateRecordSteps.ASK_RECORD_IDENTIFIER.value
                    return {
                        "status": "error, call the tool again with correct details",
                        "message": result
                    }
        else:
            UPDATERECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
            return {
                "status": f"completed",
                "message": "Update record process completed."
            }

    # Finite State Machine for Delete Record Orchestration
    def delete_record_from_table(self, session_state: SessionStateForDeleteRecord) -> Dict[str, Any]:
        
        def decide_step(s: SessionStateForDeleteRecord) -> str:
            has_table = bool(s.table_name.strip())
            has_column_name = bool(s.column_name.strip())
            has_column_value = s.column_value is not None
            has_confirmation = s.user_confirmation
            if not has_table:
                return DeleteRecordSteps.ASK_TABLE_NAME.value
            if has_table and not (has_column_name and has_column_value):
                return DeleteRecordSteps.GET_COLUMN_NAMES.value
            if has_table and has_column_name and has_column_value and has_confirmation is None:
                return DeleteRecordSteps.GET_RECORD.value
            if has_table and has_column_name and has_column_value and has_confirmation is not None:
                return DeleteRecordSteps.DELETE_RECORD.value
        

        sessions = DELETERECORDSESSIONS.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            sessions.table_name = session_state.table_name
        if session_state.columns is not None:
            sessions.columns = session_state.columns
        if session_state.column_name is not None:
            sessions.column_name = session_state.column_name
        if session_state.column_value is not None:
            sessions.column_value = session_state.column_value
        if session_state.user_confirmation is not None:
            sessions.user_confirmation = session_state.user_confirmation
        
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
                #sessions.record_id = record
                return {
                    "status": "record_summary",
                    "message": f"I found a record {record} from table {sessions.table_name}. Are you sure you want to delete this record?"
                }
        elif sessions.step == DeleteRecordSteps.DELETE_RECORD.value:
            if sessions.user_confirmation is False:
                DELETERECORDSESSIONS.pop(sessions.session_id, None)  # Clean up session
                return {
                    "status": "cancelled",
                    "message": "Record deletion cancelled by the user."
                }
            else:
                result, success = PostgresHelperFxns(self.adapter).delete_record_by_column(
                    table_name=sessions.table_name,
                    column_name=sessions.column_name,
                    value=sessions.column_value
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
    
    # Finite State Machine for Filter Record Orchestration
    def filter_records(self, session_state: SessionStateForFilterRecord) -> Dict[str, Any]:
        def decide_step(s: SessionStateForFilterRecord) -> str:
            if not bool(s.table_name.strip()):
                return FilterRecordSteps.ASK_TABLE_NAME.value
            if not s.columns:
                return FilterRecordSteps.GET_COLUMN_NAMES.value
            return FilterRecordSteps.ASK_FILTERS.value

        session = FILTERRECORDSESSIONS.setdefault(session_state.session_id, session_state)
        
        # Update session with any new incoming data
        if session_state.table_name: session.table_name = session_state.table_name
        if session_state.filters: session.filters.update(session_state.filters)

        session.step = decide_step(session)

        if session.step == FilterRecordSteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "Which table would you like to filter records from?"
            }

        elif session.step == FilterRecordSteps.GET_COLUMN_NAMES.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.table_name):
                session.table_name = '' # Reset
                return {"status": "error", "message": f"Table '{session_state.table_name}' not found."}
            
            session.columns = PostgresHelperFxns(self.adapter).get_column_names(session.table_name)
            return {
                "status": "ask_filters",
                "message": f"Table '{session.table_name}' has columns: {', '.join(session.columns)}. Which column(s) and value(s) would you like to filter by? (Provide as a dictionary)"
            }

        elif session.step == FilterRecordSteps.ASK_FILTERS.value:
            results = PostgresHelperFxns(self.adapter).fetch_filtered_records(session.table_name, session.filters)
            FILTERRECORDSESSIONS.pop(session.session_id, None) # Clean up
            
            if not results:
                return {"status": "no_results", "message": "No records matched your filters."}
            
            return {
                "status": "success",
                "message": f"Found {len(results)} matching records.",
                "data": results[:5] # Return a snippet for the LLM
            }

    # Finite State Machine for Pattern Match Record Orchestration
    def pattern_match_records(self, session_state: SessionStateForPatternMatchRecord) -> Dict[str, Any]:    

        def decide_step(s: SessionStateForPatternMatchRecord) -> str:
            if not bool(s.table_name.strip()):
                return PatternMatchRecordSteps.ASK_TABLE_NAME.value
            if not s.columns or s.column_name not in s.columns:
                return PatternMatchRecordSteps.GET_COLUMN_NAMES.value
            if not bool(s.column_name.strip()):
                return PatternMatchRecordSteps.ASK_PATTERN.value
            return PatternMatchRecordSteps.EXECUTE_PATTERN_MATCH.value

        session = PATTERNMATCHRECORDSESSIONS.setdefault(session_state.session_id, session_state)
        
        # Update session with any new incoming data
        if session_state.table_name:
            session.table_name = session_state.table_name
            if session.columns is None:  # Only fetch columns if we don't already have them
                session.columns = PostgresHelperFxns(self.adapter).get_column_names(session.table_name)
        if session_state.column_name: session.column_name = session_state.column_name
        if session_state.pattern: session.pattern = session_state.pattern

        session.step = decide_step(session)

        if session.step == PatternMatchRecordSteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "Which table would you like to perform pattern match on?"
            }

        elif session.step == PatternMatchRecordSteps.GET_COLUMN_NAMES.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.table_name):
                session.table_name = '' # Reset
                return {"status": "error", "message": f"Table '{session_state.table_name}' not found."}
            
            return {
                "status": "ask_column_for_pattern",
                "message": f"Table '{session.table_name}' has columns: {', '.join(session.columns)}. Which column would you like to apply the pattern match on?"
            }
        
        elif session.step == PatternMatchRecordSteps.ASK_PATTERN.value:
            return {
                "status": "ask_pattern",
                "message": f"What pattern would you like to match in column '{session.column_name}'? (Use SQL LIKE syntax, e.g. '%pattern%')"
            }
        
        elif session.step == PatternMatchRecordSteps.EXECUTE_PATTERN_MATCH.value:
            results: List[Any] = PostgresHelperFxns(self.adapter).match_pattern_in_column(
                table_name=session.table_name,
                column_name=session.column_name,
                pattern=session.pattern
            )
            PATTERNMATCHRECORDSESSIONS.pop(session.session_id, None) # Clean up
            
            if not results:
                return {"status": "no_results", "message": "No records matched your pattern."}
            
            return {
                "status": "success",
                "message": f"Found {len(results)} matching records.",
                "data": results[:5], # Return a snippet for the LLM
                "count": len(results) # Return total count of matched records
            }
    
    # Finite State Machine for Setting Primary Key Orchestration
    def set_primary_key(self, session_state: SessionStateSettingPrimaryKey) -> Dict[str, Any]:
        def decide_step(s: SessionStateSettingPrimaryKey) -> str:
            if not bool(s.table_name.strip()):
                return SetPrimaryKeySteps.ASK_TABLE_NAME.value
            if not s.columns or s.primary_key_column not in s.columns:
                return SetPrimaryKeySteps.GET_COLUMN_NAMES.value
            if not bool(s.primary_key_column.strip()):
                return SetPrimaryKeySteps.ASK_PRIMARY_KEY_COLUMN.value
            return SetPrimaryKeySteps.SET_PRIMARY_KEY.value

        session = SETTINGPRIMARYKEYSESSIONS.setdefault(session_state.session_id, session_state)
        
        # Update session with any new incoming data
        if session_state.table_name: session.table_name = session_state.table_name
        if session_state.primary_key_column: session.primary_key_column = session_state.primary_key_column
        if session_state.columns is not None: session.columns = session_state.columns

        session.step = decide_step(session)

        if session.step == SetPrimaryKeySteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "For which table would you like to set a primary key?"
            }

        elif session.step == SetPrimaryKeySteps.GET_COLUMN_NAMES.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.table_name):
                session.table_name = '' # Reset
                return {"status": "error", "message": f"Table '{session_state.table_name}' not found."}
            
            _columns = PostgresHelperFxns(self.adapter).find_columns_with_unique_values(session.table_name)
            session.columns = _columns
            return {
                "status": "ask_primary_key",
                "message": f"Table '{session.table_name}' has columns with unique values: {_columns}. Which column would you like to set as the primary key?"
            }
        
        elif session.step == SetPrimaryKeySteps.ASK_PRIMARY_KEY_COLUMN.value:
            return {
                "status": "ask_primary_key",
                "message": f"Which column would you like to set as the primary key for table '{session.table_name}'?"
            }
        
        elif session.step == SetPrimaryKeySteps.SET_PRIMARY_KEY.value:
            result, success = PostgresHelperFxns(self.adapter).set_primary_key(
                table_name=session.table_name,
                primary_key_column=session.primary_key_column
            )
            if not success:
                session.primary_key_column = ''  # Reset primary key column to ask again
                return {
                    "status": "error",
                    "message": result
                }
            SETTINGPRIMARYKEYSESSIONS.pop(session.session_id, None) # Clean up
            return {
                "status": "success",
                "message": f"Primary key '{session.primary_key_column}' set for table '{session.table_name}'."
            }
    
    # Finite State Machine for Setting Foreign Key Orchestration
    def set_foreign_key(self, session_state: SessionStateForSettingForeignKey) -> Dict[str, Any]:
        def decide_step(s: SessionStateForSettingForeignKey) -> str:
            if not bool(s.source_table.strip()):
                return SetForeignKeySteps.ASK_SOURCE_TABLE.value
            if not bool(s.source_column.strip()):
                return SetForeignKeySteps.ASK_SOURCE_COLUMN.value
            if not bool(s.target_table.strip()):
                return SetForeignKeySteps.ASK_TARGET_TABLE.value
            if not bool(s.target_column.strip()):
                return SetForeignKeySteps.ASK_TARGET_COLUMN.value
            return SetForeignKeySteps.SET_FOREIGN_KEY.value

        session = SETFOREIGNKEYSESSIONS.setdefault(session_state.session_id, session_state)

        # Update session with new incoming values
        if session_state.source_table:
            session.source_table = session_state.source_table
        if session_state.source_column:
            session.source_column = session_state.source_column
        if session_state.target_table:
            session.target_table = session_state.target_table
        if session_state.target_column:
            session.target_column = session_state.target_column

        session.step = decide_step(session)

        if session.step == SetForeignKeySteps.ASK_SOURCE_TABLE.value:
            return {
                "status": "ask_source_table",
                "message": "From which table should the foreign key originate?"
            }

        elif session.step == SetForeignKeySteps.ASK_SOURCE_COLUMN.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.source_table):
                session.source_table = ''
                return {
                    "status": "error",
                    "message": f"Table '{session.source_table}' does not exist."
                }

            columns = PostgresHelperFxns(self.adapter).get_column_names(session.source_table)

            return {
                "status": "ask_source_column",
                "message": f"Table '{session.source_table}' has columns: {', '.join(columns)}. Which column should be the foreign key?"
            }

        elif session.step == SetForeignKeySteps.ASK_TARGET_TABLE.value:
            tables = PostgresHelperFxns(self.adapter).list_all_tables()
            available_tables = [t for t in tables if t != session.source_table]  # Exclude source table to prevent self-referencing FKs
            return {
                "status": "ask_target_table",
                "message": f"Which table should '{session.source_table}.{session.source_column}' reference? Available tables: {available_tables}"
            }

        elif session.step == SetForeignKeySteps.ASK_TARGET_COLUMN.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.target_table):
                session.target_table = ''
                return {
                    "status": "error",
                    "message": f"Table '{session.target_table}' does not exist."
                }

            columns = PostgresHelperFxns(self.adapter).get_column_names(session.target_table)
            return {
                "status": "ask_target_column",
                "message": f"Table '{session.target_table}' has columns: {', '.join(columns)}. Which column should be referenced?"
            }

        elif session.step == SetForeignKeySteps.SET_FOREIGN_KEY.value:
            helper = PostgresHelperFxns(self.adapter)

            # Validate columns
            if not helper.check_column_exists(session.source_table, session.source_column):
                return {
                    "status": "error",
                    "message": f"Column '{session.source_column}' does not exist in table '{session.source_table}'."
                }

            if not helper.check_column_exists(session.target_table, session.target_column):
                return {
                    "status": "error",
                    "message": f"Column '{session.target_column}' does not exist in table '{session.target_table}'."
                }

            # Check referenced column is PK or UNIQUE
            if not helper.check_if_primary_or_unique(session.target_table, session.target_column):
                return {
                    "status": "error",
                    "message": f"Column '{session.target_column}' must be PRIMARY KEY or UNIQUE to reference."
                }

            # Check datatype compatibility
            source_type = helper.get_column_type(session.source_table, session.source_column)
            target_type = helper.get_column_type(session.target_table, session.target_column)

            if source_type != target_type:
                return {
                    "status": "error",
                    "message": f"Datatype mismatch: {source_type} vs {target_type}"
                }

            # Finally create FK
            result, success = helper.set_foreign_key(
                source_table=session.source_table,
                source_column=session.source_column,
                target_table=session.target_table,
                target_column=session.target_column
            )

            if not success:
                session.target_column = ''
                return {
                    "status": "error",
                    "message": result
                }

            SETFOREIGNKEYSESSIONS.pop(session.session_id, None)

            return {
                "status": "success",
                "message": f"Foreign key created: '{session.source_table}.{session.source_column}' → '{session.target_table}.{session.target_column}'."
            }

    # Finite State Machine for Generate Schema Graph Orchestration
    def generate_schema_graph(self, session_state: SessionStateForGenerateSchemaGraph) -> Dict[str, Any] | List[Union[TextContent, ImageContent]]:  

        def decide_step(s: SessionStateForGenerateSchemaGraph) -> str:
            if s.graph_data is None:
                return GenerateSchemaGraphSteps.FETCH_TABLES.value
            if "tables" not in s.graph_data:
                return GenerateSchemaGraphSteps.FETCH_TABLES.value
            if "foreign_keys" not in s.graph_data:
                return GenerateSchemaGraphSteps.FETCH_FOREIGN_KEYS.value
            return GenerateSchemaGraphSteps.BUILD_GRAPH.value

        session = GENERATESCHEMAGRAPHSESSIONS.setdefault(session_state.session_id, session_state)
        helper = PostgresHelperFxns(self.adapter)
        session.step = decide_step(session)

        if session.step == GenerateSchemaGraphSteps.FETCH_TABLES.value:
            tables = helper.list_all_tables()
            if not tables:
                GENERATESCHEMAGRAPHSESSIONS.pop(session.session_id, None)
                return {
                    "status": "error",
                    "message": "No tables found in the public schema."
                }

            if session.graph_data is None:
                session.graph_data = {}
            session.graph_data["tables"] = tables
            return {
                "status": "fetching_foreign_keys",
                "message": f"Found {len(tables)} tables. Fetching foreign key relationships..."
            }

        elif session.step == GenerateSchemaGraphSteps.FETCH_FOREIGN_KEYS.value:
            foreign_keys = helper.get_all_foreign_keys()
            if session.graph_data is None:
                session.graph_data = {}
            session.graph_data["foreign_keys"] = foreign_keys
            return {
                "status": "building_graph",
                "message": f"Found {len(foreign_keys)} foreign key relationships. Building schema graph..."
            }


        elif session.step == GenerateSchemaGraphSteps.BUILD_GRAPH.value:
            helper = PostgresHelperFxns(self.adapter)

            tables = session.graph_data.get("tables", [])
            foreign_keys = session.graph_data.get("foreign_keys", [])
            graph = {table: {"outgoing": [], "incoming": []} for table in tables}

            for fk in foreign_keys:
                source_table = fk["source_table"]
                source_column = fk["source_column"]
                target_table = fk["target_table"]
                target_column = fk["target_column"]

                if source_table not in graph:
                    graph[source_table] = {"outgoing": [], "incoming": []}

                if target_table not in graph:
                    graph[target_table] = {"outgoing": [], "incoming": []}

                graph[source_table]["outgoing"].append({
                    "source_column": source_column,
                    "target_table": target_table,
                    "target_column": target_column
                })

                graph[target_table]["incoming"].append({
                    "source_table": source_table,
                    "source_column": source_column,
                    "target_column": target_column
                })

            session.graph_data["graph"] = graph
            path = f"/Users/kushaldevgun/Downloads/images/schema_graph.png"
            image_path, success = helper.draw_schema_graph(path)

            if not success:
                GENERATESCHEMAGRAPHSESSIONS.pop(session.session_id, None)
                return {
                    "status": "error",
                    "message": image_path
                }
            with open(image_path, "rb") as f:
                png_bytes = f.read()
                b64 = base64.b64encode(png_bytes).decode("utf-8")
                mime, _ = mimetypes.guess_type(image_path)

            relationships = [
                f"{fk['source_table']}.{fk['source_column']} -> {fk['target_table']}.{fk['target_column']}"
                for fk in foreign_keys
            ]

            summary_text = (
                f"Schema graph generated successfully.\n"
                f"Tables found: {len(tables)}\n"
                f"Foreign key relationships found: {len(foreign_keys)}\n\n"
                f"Relationships:\n" + "\n".join(relationships)
            )

            GENERATESCHEMAGRAPHSESSIONS.pop(session.session_id, None)

            return [
                TextContent(
                    type="text",
                    text=summary_text
                ),
                ImageContent(
                    type="image",
                    mimeType=mime,
                    data=b64
                    )
            ]