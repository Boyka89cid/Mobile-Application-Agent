class Configuration:
    DB_CONFIG = {
        "host": "localhost",
        "port": 5432,
        "dbname": "luisdhernandez",      # or hrdata_clean DB if separate
        "user": "luisdhernandez",        # your username
        "password": "1234",   # put real password
    }

class ToolPrompts:
    # Tool descriptions for LLM Router Tools
    check_db_public_tables = "Check and list all the public tables(if any) in the connected Postgres database and format them in a numbered / ordered list."
    check_db_temporary_tables = "Check and list all the temporary tables(if any) in the connected Postgres database and format them in a numbered / ordered list."
    check_db_connection = "Check Postgres connection and run a test query"
    count_public_tables = "Count the number of public tables in the connected Postgres database"
    count_temporary_tables = "Count the number of temporary tables in the connected Postgres database"
    #create_new_table = "Do not use this tool directly. Call in the process of Orchestration. Create a new table in the connected Postgres database based on user specifications."

    # Tool descriptions for Employee Database Management
    get_employee_details = ("Retrieve employee details. IMPORTANT: If the user recently created a custom table or is working with a specific table, you MUST pass "
        "that table name to the 'table_name' argument.")
    search_employees = ("Search for employees with a given query and limit. IMPORTANT: If the user recently created a custom table or is working with a specific table, you MUST pass "
        "that table name to the 'table_name' argument.")
    create_employee = ("Create a new employee, validate fields, and preview. IMPORTANT: If the user recently created a custom table or is working with a specific table, you MUST pass "
        "that table name to the 'table_name' argument.")
    delete_employee = ("Delete employees by name. Supports targeting specific tables and handles duplicates safely. IMPORTANT: If the user recently created a custom table or is working with a specific table, you MUST pass "
        "that table name to the 'table_name' argument.")

    # Tool descriptions for Orchestration Tools (Human-in-the-loop)
    check_table_types = "Orchestrate the process of checking table types in the database based on user input."
    create_table = "Orchestrate the process of creating a new table in the database based on user input."