from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
import zipfile
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PAGE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "artisan_raw"
DB_PATH = DATA_DIR / "coffee_intelligence.db"
RAW_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ParsedRoast:
    raw: dict[str, Any]
    file_name: str
    checksum: str
    source_path: str
    summary: dict[str, Any]
    curves: pd.DataFrame
    events: pd.DataFrame


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con
