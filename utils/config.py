class Configuration:
    DB_CONFIG = {
        "host": "localhost",
        "port": 5432,
        "dbname": "kushaldevgun",      # or hrdata_clean DB if separate
        "user": "kushaldevgun",        # your username
        "password": "1234",   # put real password
    }

class ToolPrompts:
    # Tool descriptions for LLM Router Tools
    # check_db_public_tables = "Check and list all the public tables(if any) in the connected Postgres database and format them in a numbered / ordered list."
    # check_db_temporary_tables = "Check and list all the temporary tables(if any) in the connected Postgres database and format them in a numbered / ordered list."
    check_db_connection = "Check Postgres connection and run a test query"
    # count_public_tables = "Count the number of public tables in the connected Postgres database"
    # count_temporary_tables = "Count the number of temporary tables in the connected Postgres database"
    #create_new_table = "Do not use this tool directly. Call in the process of Orchestration. Create a new table in the connected Postgres database based on user specifications."

    # Tool descriptions for Orchestration Tools (Human-in-the-loop)
    check_tables = "Orchestrate the process of checking table in the database based on user input. The Steps involved will be: ask_table_type -> fetch"
    create_table = "Orchestrate the process of creating a new table in the database based on user input. The Steps involved will be: ask_table_type -> ask_table_name -> ask_columns -> user_confirmation -> create_table"
    delete_table = "Orchestrate the process of deleting a table. The steps involved will be: ask_table_name -> delete_table_confirmation -> delete_table"
    add_record_to_table = "Orchestrate the process of adding a new record to a specified table in the database based on user input. The Steps involved will be: ask_table_name -> validate_record -> user_confirmation -> add_record"
    delete_record_from_table = "Orchestrate the process of deleting a record from a specified table in the database based on user input. The Steps involved are: ask_table_name -> get_column_names -> get_record -> user_confirmation -> delete_record"