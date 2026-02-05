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


def validate_table(db: Connection, table_name: str,
                   fields: str | list[str] = None,
                   ignore_fields: str | list[str] = None):
    """
    Validate that a table exists in the database and optionally that it
    contains the specified fields.
    """
    if not check_table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist in "
                         "the database.")

    if fields:
        if isinstance(fields, str):
            fields = (fields,)

        if isinstance(ignore_fields, str):
            ignore_fields = (ignore_fields,)

        valid_fields = get_table_fields(db, table_name)
        check_fields = ([f for f in fields if f not in ignore_fields]
                        if ignore_fields else fields)
        if not all(f in valid_fields for f in check_fields):
            raise ValueError("One or more fields do not exist in "
                             f"table '{table_name}'.")
        return ', '.join(fields)
    return '*'


@log_func_call
def execute_select(db: Connection, table_name: str,
                   fields: str | list[str] = None, conditions: str = None,
                   expansions: tuple[str] = ()):
    """
    Execute select for specified fields from a table in the database.
    """
    field_list = validate_table(db, table_name, fields)
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
