from enum import Enum

class CheckTableSteps(Enum):
    ASK_TYPE = "ask_table_type"
    FETCH = "fetch"

class CountTableSteps(Enum):
    ASK_TYPE = "ask_table_type"
    COUNT = "count"

class CreateTableSteps(Enum):
    ASK_TYPE = "ask_table_type"
    ASK_TABLE_NAME = "ask_table_name"
    ASK_COLUMNS = "ask_columns"
    USER_CONFIRMATION = "user_confirmation"
    CREATE_TABLE = "create_table"

class DeleteTableSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    DELETE_TABLE_CONFIRMATION = "delete_table_confirmation"
    DELETE_TABLE = "delete_table"

class AddRecordSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    VALIDATE_RECORD = "validate_record"
    USER_CONFIRMATION = "user_confirmation"
    ADD_RECORD = "add_record"

class DeleteRecordSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    GET_COLUMN_NAMES = "get_column_names"
    GET_RECORD = "get_record"
    USER_CONFIRMATION = "user_confirmation"
    DELETE_RECORD = "delete_record"

class RetrieveRecordSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    GET_COLUMN_NAMES = "get_column_names"
    GET_RECORD = "get_record"

class FilterRecordSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    GET_COLUMN_NAMES = "get_column_names"
    ASK_FILTERS = "ask_filters"
    EXECUTE_FILTER = "execute_filter"