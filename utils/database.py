import sqlite3
import pandas as pd

DB_NAME = "greenbean_v104.db"


def connect_database():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


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
        "Arabica": "AR",
        "Robusta": "RB",
        "Liberica": "LB",
        "Excelsa": "EX",
        "Other": "OT"
    }.get(species, "OT")

    conn = connect_database()
    cur = conn.cursor()
    cur.execute(
        "SELECT bean_id FROM greenbean WHERE species=? ORDER BY id DESC LIMIT 1",
        (species,)
    )
    last_row = cur.fetchone()
    conn.close()

    if last_row and last_row["bean_id"]:
        try:
            next_num = int(last_row["bean_id"][-4:]) + 1
        except (TypeError, ValueError):
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"


def add_greenbean(bean_name, species, origin, region, supplier, process,
                  variety, density, moisture, stock, location, notes):
    conn = connect_database()
    try:
        cur = conn.cursor()
        bean_id = generate_bean_id(species)
        cur.execute("""
        INSERT INTO greenbean(
            bean_id, bean_name, species, origin, region, supplier,
            process, variety, density, moisture, stock, location, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bean_id, bean_name, species, origin, region, supplier,
            process, variety, density, moisture, stock, location, notes
        ))
        conn.commit()
        return bean_id
    finally:
        conn.close()


def get_all_greenbean():
    conn = connect_database()
    try:
        return pd.read_sql_query(
            "SELECT * FROM greenbean ORDER BY bean_name, bean_id",
            conn
        )
    finally:
        conn.close()


def search_greenbean(keyword):
    pattern = f"%{keyword}%"
    conn = connect_database()
    try:
        return pd.read_sql_query("""
        SELECT * FROM greenbean
        WHERE bean_id LIKE ?
           OR bean_name LIKE ?
           OR species LIKE ?
           OR origin LIKE ?
           OR region LIKE ?
           OR supplier LIKE ?
           OR process LIKE ?
           OR variety LIKE ?
           OR location LIKE ?
        ORDER BY bean_name, bean_id
        """, conn, params=(pattern,) * 9)
    finally:
        conn.close()


def get_greenbean_by_bean_id(bean_id):
    conn = connect_database()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM greenbean WHERE bean_id=?", (bean_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_greenbean_stock(bean_id, new_stock):
    if new_stock < 0:
        raise ValueError("Stock tidak boleh negatif.")

    conn = connect_database()
    try:
        cur = conn.cursor()
        cur.execute("""
        UPDATE greenbean
        SET stock=?, updated_at=CURRENT_TIMESTAMP
        WHERE bean_id=?
        """, (float(new_stock), bean_id))

        if cur.rowcount == 0:
            raise ValueError(f"Bean ID {bean_id} tidak ditemukan.")

        conn.commit()
    finally:
        conn.close()
