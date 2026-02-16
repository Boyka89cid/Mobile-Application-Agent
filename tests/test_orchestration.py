import pytest
from unittest.mock import MagicMock, call
from tools.queryOrchestrator.orchestrationTools import OrchestrationTools
from tools.queryOrchestrator.sessionDataClasses import SessionStateForTableCheck, SessionStateForTableCount
from tools.queryOrchestrator.postgresHelperFxns import PostgresHelperFxns

@pytest.fixture
def mcp_mock():
    return MagicMock()

@pytest.fixture
def tools(mcp_mock):
    return OrchestrationTools(mcp=mcp_mock)


def test_tablecheck_flow_ask_type_then_set_type(tools):
    s = SessionStateForTableCheck(session_id="s1", step="ASK_TYPE", table_type="")

    # Step 1: ASK_TYPE -> should ask for type
    r1 = tools.check_tables(s)
    assert r1["status"] == "ask_table_type"
    
    # Step 2: simulate user provided type, advance session
    s.table_type = "all"
    s.step = "fetch" 

    r2 = tools.check_tables(s)
    assert r2["status"] in {f"checked_{s.table_type}_tables"}

def test_tablecount_flow_ask_type_then_count(tools):
    s = SessionStateForTableCount(session_id="s2", step="ASK_TYPE", table_type="public")

    # Step 1: simulate user provided type, advance session
    s.table_type = "public"
    s.step = "count" 

    r2 = tools.count_tables(s)
    assert r2["status"] in {f"counted_{s.table_type}_tables"}

@pytest.fixture
def adapter():
    return MagicMock()


@pytest.fixture
def helper(adapter):
    return PostgresHelperFxns(adapter)

@pytest.mark.parametrize(
    "table_type, expected_sql",
    [
        ("public", "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"),
        ("temporary", "SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"),
    ],
)
def test_check_db_tables_queries_right_sql(helper, adapter, table_type, expected_sql):
    adapter.execute_query.return_value = [{"table_name": "t1"}, {"table_name": "t2"}]

    out = helper.check_db_tables(table_type)

    adapter.execute_query.assert_called_once_with(expected_sql)
    assert "Tables in the database:" in out
    assert "t1" in out and "t2" in out


def test_check_db_tables_handles_exception(helper, adapter):
    adapter.execute_query.side_effect = Exception("boom")

    out = helper.check_db_tables("public")

    # Your last definition logs exception + returns a string
    assert out.startswith("Error fetching table names:")


# -------------------------
# count_db_tables
# -------------------------

@pytest.mark.parametrize(
    "table_type, expected_sql, expected_prefix",
    [
        ("public", "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';",
         "Number of public tables:"),
        ("temporary", "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';",
         "Number of temporary tables:"),
    ],
)
def test_count_db_tables_basic(helper, adapter, table_type, expected_sql, expected_prefix):
    adapter.execute_query.return_value = [{"table_count": 7}]

    out = helper.count_db_tables(table_type)

    adapter.execute_query.assert_called_once_with(expected_sql)
    assert out.startswith(expected_prefix)
    assert "7" in out


def test_count_db_tables_all(helper, adapter):
    adapter.execute_query.side_effect = [
        [{"table_count": 3}],   # public
        [{"table_count": 2}],   # temporary
    ]

    out = helper.count_db_tables("all")

    assert adapter.execute_query.call_args_list == [
        call("SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';"),
        call("SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"),
    ]
    assert "Public tables count: 3" in out
    assert "Temporary tables count: 2" in out


def test_count_db_tables_handles_exception(helper, adapter):
    adapter.execute_query.side_effect = Exception("error")

    out = helper.count_db_tables("public")

    assert out.startswith("Error counting tables:")


# -------------------------
# create_new_table
# -------------------------

def test_create_new_table_public_builds_sql_and_executes(helper, adapter):
    adapter.execute_query.return_value = []

    msg, ok = helper.create_new_table(
        table_type="public",
        table_name="employees",
        columns=[{"name": "id", "type": "INTEGER"}, {"name": "name", "type": "TEXT"}],
    )

    adapter.execute_query.assert_called_once_with("CREATE TABLE employees (id INTEGER, name TEXT);")
    assert ok is True
    assert "created successfully" in msg


def test_create_new_table_temporary_builds_sql_and_executes(helper, adapter):
    adapter.execute_query.return_value = []

    msg, ok = helper.create_new_table(
        table_type="temporary",
        table_name="tmp_employees",
        columns=[{"name": "id", "type": "INTEGER"}],
    )

    adapter.execute_query.assert_called_once_with("CREATE TEMPORARY TABLE tmp_employees (id INTEGER);")
    assert ok is True


def test_create_new_table_invalid_type(helper, adapter):
    msg, ok = helper.create_new_table(
        table_type="weird",
        table_name="x",
        columns=[{"name": "id", "type": "INTEGER"}],
    )
    assert ok is False
    assert "Invalid table type" in msg
    adapter.execute_query.assert_not_called()


def test_create_new_table_exec_error(helper, adapter):
    adapter.execute_query.side_effect = Exception("permission denied")

    msg, ok = helper.create_new_table(
        table_type="public",
        table_name="employees",
        columns=[{"name": "id", "type": "INTEGER"}],
    )

    assert ok is False
    assert "Error creating table employees:" in msg


# -------------------------
# list_all_tables (last definition)
# -------------------------

def test_list_all_tables_combines_public_and_temp(helper, adapter):
    adapter.execute_query.side_effect = [
        [{"table_name": "p1"}, {"table_name": "p2"}],
        [{"table_name": "t1"}],
    ]

    out = helper.list_all_tables()

    assert adapter.execute_query.call_args_list == [
        call("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"),
        call("SELECT table_name FROM information_schema.tables WHERE table_type='LOCAL TEMPORARY';"),
    ]
    assert out == ["p1", "p2", "t1"]


def test_list_all_tables_exception_returns_empty(helper, adapter):
    adapter.execute_query.side_effect = Exception("error")

    out = helper.list_all_tables()

    assert out == []


# -------------------------
# delete_table_by_name
# -------------------------

def test_delete_table_by_name_success(helper, adapter):
    adapter.execute_query.return_value = []

    msg, ok = helper.delete_table_by_name("employees")

    adapter.execute_query.assert_called_once_with("DROP TABLE IF EXISTS employees;")
    assert ok is True
    assert "deleted successfully" in msg


def test_delete_table_by_name_error(helper, adapter):
    adapter.execute_query.side_effect = Exception("error")

    msg, ok = helper.delete_table_by_name("employees")

    assert ok is False
    assert msg.startswith("Error deleting table employees:")


# -------------------------
# get_column_names (last definition)
# -------------------------

def test_get_column_names_uses_params(helper, adapter):
    adapter.execute_query.return_value = [{"column_name": "id"}, {"column_name": "name"}]

    cols = helper.get_column_names("employees")

    adapter.execute_query.assert_called_once_with(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s;",
        ("employees",),
    )
    assert cols == ["id", "name"]


def test_get_column_names_exception_returns_empty(helper, adapter):
    adapter.execute_query.side_effect = Exception("error")

    cols = helper.get_column_names("employees")

    assert cols == []


# -------------------------
# add_record
# -------------------------

def test_add_record_builds_insert_sql(helper, adapter):
    adapter.execute_query.return_value = []

    msg, ok = helper.add_record("employees", {"id": 1, "name": "Kushal"})

    adapter.execute_query.assert_called_once()
    called_sql, called_params = adapter.execute_query.call_args.args

    assert called_sql == "INSERT INTO employees (id, name) VALUES (%s, %s);"
    assert called_params == (1, "Kushal")
    assert ok is True
    assert "Record added successfully" in msg


def test_add_record_exec_error(helper, adapter):
    adapter.execute_query.side_effect = Exception("error")

    msg, ok = helper.add_record("employees", {"id": 1})

    assert ok is False
    assert msg.startswith("Error adding record to table employees:")


# -------------------------
# check_table_exists
# -------------------------

def test_check_table_exists_true(helper, adapter):
    adapter.execute_query.return_value = [{"to_regclass": "employees"}]

    ok = helper.check_table_exists("employees")

    adapter.execute_query.assert_called_once_with("SELECT to_regclass('employees');")
    assert ok is True


def test_check_table_exists_false(helper, adapter):
    adapter.execute_query.return_value = [{"to_regclass": None}]

    ok = helper.check_table_exists("employees")

    assert ok is False


def test_check_table_exists_exception_false(helper, adapter):
    adapter.execute_query.side_effect = Exception("error")
    assert helper.check_table_exists("employees") is False


# -------------------------
# check_table_example
# -------------------------

def test_check_table_example_uses_limit(helper, adapter):
    adapter.execute_query.return_value = [{"id": 1}]

    rows = helper.check_table_example("employees")

    adapter.execute_query.assert_called_once_with('SELECT * FROM "employees" LIMIT 1;')
    assert rows == [{"id": 1}]


# -------------------------
# find_record_by_column
# -------------------------

def test_find_record_by_column_found(helper, adapter):
    adapter.execute_query.return_value = [{"id": 1, "name": "Kushal"}]

    row = helper.find_record_by_column("employees", "id", 1)

    adapter.execute_query.assert_called_once_with('SELECT * FROM employees WHERE "id" = %s;', (1,))
    assert row == {"id": 1, "name": "Kushal"}


def test_find_record_by_column_not_found(helper, adapter):
    adapter.execute_query.return_value = []

    row = helper.find_record_by_column("employees", "id", 999)

    assert row is None


# -------------------------
# delete_record_by_column
# -------------------------

def test_delete_record_by_column_success(helper, adapter):
    adapter.execute_query.return_value = []

    msg, ok = helper.delete_record_by_column("employees", "id", 1)

    adapter.execute_query.assert_called_once_with('DELETE FROM employees WHERE "id" = %s;', (1,))
    assert ok is True
    assert "deleted successfully" in msg


def test_delete_record_by_column_exec_error(helper, adapter):
    adapter.execute_query.side_effect = Exception("error")

    msg, ok = helper.delete_record_by_column("employees", "id", 1)

    assert ok is False
    assert msg.startswith("Error deleting record from table employees:")
