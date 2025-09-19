from datetime import datetime
from sqlite3 import Connection
from contextlib import contextmanager


from ..logging import log_func_call

GET_TABLES_QUERY = "select name from sqlite_master where type='table'"


@log_func_call
def get_tables(db: Connection):
    """
    Get all table names in the database.
    """
    return tuple(row[0] for row in db.execute(GET_TABLES_QUERY).fetchall())


@log_func_call
def check_table_exists(db: Connection, table_name: str):
    """
    Check if a table exists in the database.
    """
    return table_name in get_tables(db)


@log_func_call
def get_table_fields(db: Connection, table_name: str):
    """
    Get all fields from the specified table of the database.
    """
    if not check_table_exists(db, table_name):
        return False

    query = f"pragma table_info({table_name!r})"
    return tuple(row[1] for row in db.execute(query).fetchall())


@log_func_call
def execute_select(db: Connection, table_name: str,
                   fields: str | list[str] = None, conditions: str = None,
                   expansions: tuple[str] = ()):
    """
    Execute select for specified fields from a table in the database.
    """
    if not check_table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist in "
                         "the database.")

    if fields:
        if isinstance(fields, str):
            fields = (fields,)

        valid_fields = get_table_fields(db, table_name)
        if not all(f in valid_fields for f in fields):
            raise ValueError("One or more fields do not exist in "
                             f"table '{table_name}'.")
        field_list = ', '.join(fields)
    else:
        field_list = '*'

    query = (f"select {field_list} from {table_name!r} "
             f"{' ' + conditions if conditions else ''}")
    # log_debug(f"Executing query: {query} with expansions: {expansions}")

    return db.execute(query, expansions)


@log_func_call
def sql_timestamp_to_datetime(ts: str):
    return datetime.fromisoformat(ts.replace('Z', '+00:00')) if ts else None


@contextmanager
@log_func_call
def sqlite_context(cxn: Connection):
    try:
        yield cxn
    except Exception:
        raise
    else:
        cxn.commit()
    finally:
        cxn.close()
