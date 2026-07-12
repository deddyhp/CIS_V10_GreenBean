import sqlite3
import pandas as pd


# ==========================================
# DATABASE CONNECTION
# ==========================================

def connect_database(db_path="greenbean.db"):
    return sqlite3.connect(db_path)


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database(db_path="greenbean.db"):

    conn = connect_database(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS greenbean (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        bean_id TEXT UNIQUE,

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


# ==========================================
# GENERATE BEAN ID
# ==========================================

def generate_bean_id(species):

    conn = connect_database()
    cursor = conn.cursor()

    prefix = "AR" if species == "Arabica" else "RB"

    cursor.execute(
        "SELECT COUNT(*) FROM greenbean WHERE species=?",
        (species,)
    )

    total = cursor.fetchone()[0] + 1

    conn.close()

    return f"{prefix}{total:04d}"


# ==========================================
# ADD GREEN BEAN
# ==========================================

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

    conn = connect_database()
    cursor = conn.cursor()

    bean_id = generate_bean_id(species)

    cursor.execute("""
    INSERT INTO greenbean (

        bean_id,
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

    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        bean_id,
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

    ))

    conn.commit()
    conn.close()


# ==========================================
# READ DATABASE
# ==========================================

def get_all_greenbean():

    conn = connect_database()

    df = pd.read_sql(
        "SELECT * FROM greenbean ORDER BY bean_name",
        conn
    )

    conn.close()

    return df


# ==========================================
# SEARCH
# ==========================================

def search_greenbean(keyword):

    conn = connect_database()

    query = """
    SELECT *
    FROM greenbean
    WHERE
        bean_name LIKE ?
        OR origin LIKE ?
        OR species LIKE ?
        OR process LIKE ?
    ORDER BY bean_name
    """

    df = pd.read_sql(
        query,
        conn,
        params=(
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%"
        )
    )

    conn.close()

    return df
