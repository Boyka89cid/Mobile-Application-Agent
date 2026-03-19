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
    ASK_PRIMARY_KEY = "ask_primary_key"
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

class UpdateRecordSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    GET_COLUMN_NAMES = "get_column_names"
    ASK_RECORD_IDENTIFIER = "ask_record_identifier"
    ASK_UPDATED_VALUES = "ask_updated_values"
    USER_CONFIRMATION = "user_confirmation"
    UPDATE_RECORD = "update_record"

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

class PatternMatchRecordSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    GET_COLUMN_NAMES = "get_column_names"
    ASK_PATTERN = "ask_pattern"
    EXECUTE_PATTERN_MATCH = "execute_pattern_match"

class SetPrimaryKeySteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    ASK_PRIMARY_KEY_COLUMN = "ask_primary_key_column"
    SET_PRIMARY_KEY = "set_primary_key"

class SetForeignKeySteps(Enum):
    ASK_SOURCE_TABLE = "ask_source_table"
    ASK_SOURCE_COLUMN = "ask_source_column"
    ASK_TARGET_TABLE = "ask_target_table"
    ASK_TARGET_COLUMN = "ask_target_column"
    SET_FOREIGN_KEY = "set_foreign_key"

class GenerateSchemaGraphSteps(Enum):
    FETCH_TABLES = "fetch_tables"
    FETCH_FOREIGN_KEYS = "fetch_foreign_keys"
    BUILD_GRAPH = "build_graph"