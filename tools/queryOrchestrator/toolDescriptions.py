class ToolPrompts:
    # Tool descriptions for LLM Router Tools
    check_db_connection = "Check Postgres connection and run a test query"


    RULES = '''
    - You can skip a single or multiple steps if you already have the required information. For example, if you already have the table_type, you can skip the ask_table_type step. However, you cannot skip a step or steps if the required information is missing.
    - Respond ONLY with a tool call.
    - Do NOT include any natural-language explanation before the tool call.
    - After the tool returns, you may present exactly the tool's message verbatim.
    - If you see multiple select options in any step of workflow, use your ask_user_input_v0 widget to ask user to select one of the options. For example, if you have 3 table types to select from, use ask_user_input_v0 with those 3 options as input.
    - If their are more than 3 options are available in the human-in-the-loop process, select any 3 options to present to the user in ask_user_input_v0 widget. After user selects one of the 3 options, present the next 3 options and so on until all options are presented. You can use the same ask_user_input_v0 widget to present all options in this way.
    - Do NOT call the final tool unless you have all the required information and user_confirmation=true.
    '''
    # Tool descriptions for Orchestration Tools (Human-in-the-loop)
    create_table_workflow = f'''
    WORKFLOW: create_table (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_type, ask_table_name, ask_columns, user_confirmation, create_table]
    - table_type: string
    - table_name: string
    - columns: list of {{ name: string, type: string }} | null
    - user_confirmation: bool | null
    {RULES}
    1) ask user for table_type (public/temporary) if not provided.
    2) ask user for table_name if not provided.
    3) ask user for columns list if not provided. Also, provide some suggestions for column names and types based on common patterns.
    4) ask for yes/no. Set user_confirmation accordingly.
    5) call create_table ONLY if table_type, table_name, columns are non-null AND user_confirmation=true.
    If any required field is missing, move back to the appropriate ask_* step.
    '''
    create_table = f"Orchestrate the process of creating a new table in the database based on user input.\n {create_table_workflow}"

    delete_table_workflow = f'''
    WORKFLOW: delete_table (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_name, user_confirmation, delete_table]
    - table_name: string
    - user_confirmation: bool | null
    {RULES}
    1) ask user for table_name if not provided.
    2) ask for yes/no. Set user_confirmation accordingly.
    3) call delete_table ONLY if table_name is non-null AND user_confirmation=true.
    If any required field is missing, move back to the appropriate ask_* step.
    '''
    delete_table = f"Orchestrate the process of deleting a table in the database based on user input.\n {delete_table_workflow}"

    check_tables_workflow = f'''
    WORKFLOW: check_tables (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_type, fetch]
    - table_type: string
    {RULES}
    1) ask user for table_type (public/temporary) if not provided.
    2) call fetch after getting the table_type.
    '''
    check_tables = f"Orchestrate the process of checking table in the database based on user input.\n {check_tables_workflow}"
    
    count_tables_workflow = f'''
    WORKFLOW: count_tables (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_type, count]
    - table_type: string
    {RULES}
    1) ask user for table_type (public, temporary or all) if not provided.
    2) call count after getting the table_type.
    '''
    count_tables = f"Orchestrate the process of counting tables in the database based on user input.\n {count_tables_workflow}"

    add_record_to_table_workflow = f'''
    WORKFLOW: add_record_to_table (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_name, validate_record, user_confirmation, add_record]
    - table_name: string
    - record: dict | null
    - user_confirmation: bool | null
    {RULES}
    1) ask user for table_name if not provided.
    2) validate the record by checking if the keys in the record match the column names of the table. If not valid, go back to ask_table_name step.
    3) ask for yes/no. Set user_confirmation accordingly.
    4) call add_record ONLY if table_name, record are non-null AND user_confirmation=true.
    If any required field is missing, move back to the appropriate ask_* step.
    '''
    add_record_to_table = f"Orchestrate the process of adding a new record to a specified table in the database based on user input.\n {add_record_to_table_workflow}"

    delete_record_from_table_workflow = f'''
    WORKFLOW: delete_record_from_table (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_name, get_column_names, get_record, user_confirmation, delete_record]
    - table_name: string 
    - columns: list[string] | null
    - column_name: string
    - column_value: string | null
    - user_confirmation: bool | null
    {RULES}
    1) ask user for table_name if not provided (column names for the given table_name will be fetched).
    2) ask user to select the column name and provide its corresponding value to identify the record(s) to be deleted. Store the selected column name and value in column_name and column_value respectively.
    3) fetch the record(s) based on the provided column_name and column_value and ask for yes/no. Set user_confirmation accordingly. If no record is found, go back to step 2. If multiple records are found, ask user to provide the record_id of the record to be deleted and store it in record_id.
    4) call delete_record ONLY if table_name, column_name, column_value are non-null AND user_confirmation=true. If record_id is available, use it to delete the specific record. Otherwise, delete all records matching the column_name and column_value.
    If any required field is missing, move back to the appropriate ask_* step.
    '''
    delete_record_from_table = f"Orchestrate the process of deleting a record from a specified table in the database based on user input. \n {delete_record_from_table_workflow}"

    retrieve_record_from_table_workflow = f'''
    WORKFLOW: retrieve_record_from_table (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_name, get_column_names, get_record]
    - table_name: string
    - columns: list[string] | null
    - column_name: string | null
    - column_value: string | null
    {RULES}
    1) ask user for table_name if not provided (column names for the given table_name will be fetched and store it in columns).
    2) ask user to select the column name and provide its corresponding value to identify the record(s) to be retrieved. Store the selected column name and value in column_name and column_value respectively.
    3) fetch the record(s) based on the provided column_name and column_value and return the record(s). If no record is found, go back to step 2. If multiple records are found, return all the records matching the column_name and column_value.
    If any required field is missing, move back to the appropriate ask_* step.
    '''
    retrieve_record_from_table = f"Orchestrate the process of retrieving a record from a specified table in the database based on user input. \n {retrieve_record_from_table_workflow}"

    filter_records_workflow = f'''
    WORKFLOW: filter_records (state machine)
    State fields:
    - session_id: string (required)
    - table_name: string
    - filters: dict | null (e.g., {{"department": "Sales"}})
    {RULES}
    1) Ask for table_name if not provided.
    2) Fetch column names and ask user for specific filters (column/value pairs).
    3) Execute the filter and return matching records.
    '''
    filter_records = f"Filter and retrieve multiple records from a table based on specific conditions.\n {filter_records_workflow}"

    pattern_match_records_workflow = f'''
    WORKFLOW: pattern_match_records (state machine)
    State fields:
    - session_id: string (required)
    - table_name: string
    - column_name: string
    - pattern: string
    {RULES}
    1) Ask for table_name if not provided.
    2) Fetch column names and ask user to select a column for pattern matching.
    3) Ask user for the pattern to match (e.g., "name starts with 'A'").
    4) Execute the pattern match and return matching records.
    '''
    pattern_match_records = f"Match a pattern in a specific column and retrieve matching records from a table based on user input.\n {pattern_match_records_workflow}" 