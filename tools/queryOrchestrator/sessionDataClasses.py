from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from tools.queryOrchestrator.sessionSteps import (
    CheckTableSteps,
    CountTableSteps,
    CreateTableSteps,
    DeleteTableSteps,
    AddRecordSteps,
    DeleteRecordSteps,
    PatternMatchRecordSteps,
    RetrieveRecordSteps,
    FilterRecordSteps
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
    validated: bool | None = None
    record: Dict[str, Any] | None = None  # Record to be added

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