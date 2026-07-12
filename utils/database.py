
import sqlite3
import pandas as pd


def connect_database(db_path):
    """
    Connect to SQLite database
    """
    return sqlite3.connect(db_path)


def get_tables(db_path):
    """
    Return all table names
    """
    conn = connect_database(db_path)

    query = """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    """

    tables = pd.read_sql(query, conn)

    conn.close()

    return tables


def read_table(db_path, table_name):
    """
    Read any table into DataFrame
    """
    conn = connect_database(db_path)

    df = pd.read_sql(
        f"SELECT * FROM {table_name}",
        conn
    )

    conn.close()

    return df
