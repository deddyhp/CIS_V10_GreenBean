
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

# ==========================================
# CREATE CIS DATABASE
# ==========================================

def create_database(db_path="greenbean.db"):

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

if species == "Arabica":
    prefix = "AR"
elif species == "Robusta":
    prefix = "RB"
elif species == "Liberica":
    prefix = "LB"
elif species == "Excelsa":
    prefix = "EX"
else:
    prefix = "OT"

cursor.execute(
    "SELECT COUNT(*) FROM greenbean WHERE species=?",
    (species,)
)

count = cursor.fetchone()[0] + 1

bean_id = f"{prefix}-{count:04d}"
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS greenbean (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        bean_id TEXT,

        bean_name TEXT,

        species TEXT,

        origin TEXT,

        region TEXT,

        supplier TEXT,

        process TEXT,

        variety TEXT,

        density REAL,

        moisture REAL,

        stock REAL,

        location TEXT,

        notes TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()

    conn.close()

def add_greenbean(
    bean_name,
    species,
    origin,
    region,
    supplier,
    process,
    variety,
    density,
    moisture,
    stock,
    location,
    notes
):

    conn = sqlite3.connect("greenbean.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO greenbean (
            bean_id,
            bean_name,
            origin,
            region,
            supplier,
            process,
            variety,
            density,
            moisture,
            stock,
            location,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bean_name,
        origin,
        region,
        supplier,
        process,
        variety,
        density,
        moisture,
        stock,
        location,
        notes
    ))

    conn.commit()
    conn.close()
