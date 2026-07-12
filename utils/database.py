import sqlite3
import pandas as pd

DB_NAME = "greenbean_v104.db"

def connect_database():
    return sqlite3.connect(DB_NAME)

def create_database():
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS greenbean(
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

def generate_bean_id(species):
    prefix = {
        "Arabica":"AR",
        "Robusta":"RB",
        "Liberica":"LB",
        "Excelsa":"EX",
        "Other":"OT"
    }.get(species,"OT")

    conn = connect_database()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM greenbean WHERE species=?", (species,))
    num = cur.fetchone()[0] + 1
    conn.close()
    return f"{prefix}{num:04d}"

def add_greenbean(bean_name,species,origin,region,supplier,process,variety,density,moisture,stock,location,notes):
    conn = connect_database()
    cur = conn.cursor()
    bean_id = generate_bean_id(species)
    cur.execute("""
    INSERT INTO greenbean(
    bean_id,bean_name,species,origin,region,supplier,process,variety,density,moisture,stock,location,notes)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        bean_id,bean_name,species,origin,region,supplier,process,variety,density,moisture,stock,location,notes
    ))
    conn.commit()
    conn.close()

def get_all_greenbean():
    conn = connect_database()
    df = pd.read_sql("SELECT * FROM greenbean ORDER BY bean_name", conn)
    conn.close()
    return df

def search_greenbean(keyword):
    conn = connect_database()
    df = pd.read_sql("""
    SELECT * FROM greenbean
    WHERE bean_name LIKE ?
       OR species LIKE ?
       OR origin LIKE ?
       OR process LIKE ?
    ORDER BY bean_name
    """, conn,
    params=(f"%{keyword}%",f"%{keyword}%",f"%{keyword}%",f"%{keyword}%"))
    conn.close()
    return df
