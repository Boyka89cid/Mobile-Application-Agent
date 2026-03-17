from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from tools.queryOrchestrator.sessionSteps import (
    CheckTableSteps,
    CountTableSteps,
    CreateTableSteps,
    DeleteTableSteps,
    AddRecordSteps,
    UpdateRecordSteps,
    DeleteRecordSteps,
    GenerateSchemaGraphSteps,
    PatternMatchRecordSteps,
    RetrieveRecordSteps,
    FilterRecordSteps,
    SetForeignKeySteps,
    SetPrimaryKeySteps
)

@dataclass
class SessionStateForTableCheck:
    session_id: str
    step: str = CheckTableSteps.ASK_TYPE.value
    table_type: str = ''

@dataclass
class SessionStateForTableCount:
    session_id: str
    step: str = CountTableSteps.ASK_TYPE.value
    table_type: str = ''

@dataclass
class SessionStateForCreateTable:
    session_id: str
    step: str = CreateTableSteps.ASK_TYPE.value
    table_type: str = ''
    table_name: str = ''
    primary_key: bool | None = None
    primary_key_column: str = ''  # Column name to set as primary key
    user_confirmation: bool | None = None  # User confirmation input
    columns: List[Dict[str, str]] | None = None  # List of dicts with column name and type

@dataclass
class SessionStateForDeleteTable:
    session_id: str
    step: str = DeleteTableSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    user_confirmation: bool | None = None  # User confirmation input

@dataclass
class SessionStateForAddRecord:
    session_id: str
    step: str = AddRecordSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    user_confirmation: bool | None = None
    record: Dict[str, Any] | None = None  # Record to be added

@dataclass
class SessionStateForUpdateRecord:
    session_id: str
    step: str = UpdateRecordSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    columns : List[str] | None = None  # List of column names in the table
    column_name: str = ''  # Column name to identify the record
    column_value: Any  | None = None  # Value of the column to identify the record
    updated_values: Dict[str, Any] | None = None  # Dictionary of columns and their new values
    user_confirmation: bool | None = None  # User confirmation input

@dataclass
class SessionStateForDeleteRecord:
    session_id: str
    step: str = DeleteRecordSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    columns : List[str] | None = None  # List of column names in the table
    column_name: str = ''  # Column name to identify the record
    column_value: Any  | None = None  # Value of the column to identify the record
    user_confirmation: bool | None = None  # User confirmation input
    #record_id: Any | None = None  # ID of the record to be deleted

@dataclass
class SessionStateForRetrieveRecord:
    session_id: str
    step: str = RetrieveRecordSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    columns : List[str] | None = None  # List of column names in the table
    column_name: str = ''  # Column name to identify the record
    column_value: Any  | None = None  # Value of the column to identify the record

@dataclass
class SessionStateForFilterRecord:
    session_id: str
    step: str = FilterRecordSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    columns: List[str] | None = None
    filters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SessionStateForPatternMatchRecord:
    session_id: str
    step: str = PatternMatchRecordSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    columns: List[str] | None = None
    column_name: str = ''  # Column name to apply the pattern match
    pattern: str = ''  # Pattern to match in the specified column

@dataclass
class SessionStateSettingPrimaryKey:
    session_id: str
    step: str = SetPrimaryKeySteps.ASK_TABLE_NAME.value
    table_name: str = ''
    columns: List[str] | None = None
    primary_key_column: str = ''  # Column name to set as primary key

@dataclass
class SessionStateForSettingForeignKey:
    session_id: str
    step: str = SetForeignKeySteps.ASK_SOURCE_TABLE.value

    source_table: str = ''
    source_column: str = ''

    target_table: str = ''
    target_column: str = ''

    source_columns: List[str] | None = None
    target_columns: List[str] | None = None

@dataclass
class SessionStateForGenerateSchemaGraph:
    session_id: str
    step: str = GenerateSchemaGraphSteps.FETCH_TABLES.value
    graph_data: dict[str, Any] | None = None