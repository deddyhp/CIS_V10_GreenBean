from __future__ import annotations

from datetime import date
import re
from typing import Any

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

SHEET_HEADERS = {
    "Recipe_Master": [
        "Recipe_ID","Recipe_Name","Brew_Method","Ownership","Purpose","Source",
        "Version","Status","Created_Date","Last_Update","Favorite","Tags","Bean_Name","Dose_g","Water_g","Ratio","Grind_Setting","Water_Temp_C","Target_Brew_Time","Brewing_Steps"
    ],
    "Brew_Log": [
        "Log_ID","Date","Recipe_ID","Bean_Name","Roast_Profile","Dose_g",
        "Water_g","Ratio","Grind_Setting","Water_Temp_C","Brew_Time",
        "Result_Score","Aroma","Sweetness","Acidity","Body","Clarity",
        "Balance","Aftertaste","Overall_Notes"
    ],
    "Knowledge_Notes": [
        "Knowledge_ID","Recipe_ID","Deddy_Notes","AI_Insight",
        "Next_Adjustment","Lessons_Learned","Important_Warning","Updated_Date"
    ],
    "Legacy_Purpose": [
        "Legacy_ID","Recipe_ID","Personal_Favorite","Family_Favorite",
        "Commercial_Favorite","Experimental","Reference_Only",
        "Personal_Notes","Family_Notes","Commercial_Notes"
    ],
    "Settings": ["Category","Value"],
}

def _clean(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return value

@st.cache_resource(show_spinner=False)
def _get_spreadsheet():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("Secret [gcp_service_account] belum tersedia.")
    if "google_sheets" not in st.secrets:
        raise RuntimeError("Secret [google_sheets] belum tersedia.")
    gs = st.secrets["google_sheets"]
    if "brewthings_spreadsheet_id" not in gs:
        raise RuntimeError("Secret google_sheets.brewthings_spreadsheet_id belum tersedia.")

    info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client.open_by_key(gs["brewthings_spreadsheet_id"])

@st.cache_resource(show_spinner=False)
def _get_worksheet(sheet_name: str):
    if sheet_name not in SHEET_HEADERS:
        raise ValueError(f"Worksheet tidak dikenal: {sheet_name}")
    spreadsheet = _get_spreadsheet()
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        headers = SHEET_HEADERS[sheet_name]
        ws = spreadsheet.add_worksheet(
            title=sheet_name, rows=1000, cols=max(len(headers), 10)
        )
        ws.update("A1", [headers])
        return ws

def ensure_database_structure() -> None:
    for sheet_name, expected in SHEET_HEADERS.items():
        ws = _get_worksheet(sheet_name)
        current = ws.row_values(1)
        if not current:
            ws.update("A1", [expected])
            continue
        missing = [h for h in expected if h not in current]
        if missing:
            ws.update("A1", [current + missing])

def get_database_status() -> pd.DataFrame:
    rows = []
    for sheet_name, expected in SHEET_HEADERS.items():
        ws = _get_worksheet(sheet_name)
        current = ws.row_values(1)
        values = ws.get_all_values()
        missing = [h for h in expected if h not in current]
        rows.append({
            "Worksheet": sheet_name,
            "Status": "Ready" if not missing else "Header incomplete",
            "Data Rows": max(len(values) - 1, 0),
            "Columns": len(current),
            "Missing Headers": ", ".join(missing),
        })
    return pd.DataFrame(rows)

@st.cache_data(ttl=60, show_spinner=False)
def read_sheet(sheet_name: str) -> pd.DataFrame:
    ws = _get_worksheet(sheet_name)
    records = ws.get_all_records(default_blank="")
    if not records:
        return pd.DataFrame(columns=SHEET_HEADERS[sheet_name])
    df = pd.DataFrame(records)
    for column in SHEET_HEADERS[sheet_name]:
        if column not in df.columns:
            df[column] = ""
    return df[SHEET_HEADERS[sheet_name]].fillna("")

def get_settings(category: str) -> list[str]:
    df = read_sheet("Settings")
    if df.empty:
        return []
    mask = (
        df["Category"].astype(str).str.strip().str.casefold()
        == category.strip().casefold()
    )
    values = df.loc[mask, "Value"].astype(str).str.strip()
    return [v for v in values.tolist() if v]

def _next_id(existing: list[str], prefix: str, digits: int = 4) -> str:
    highest = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
    for value in existing:
        match = pattern.match(str(value).strip())
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}{highest + 1:0{digits}d}"

def generate_recipe_id() -> str:
    recipes = read_sheet("Recipe_Master")
    ids = recipes["Recipe_ID"].astype(str).tolist() if not recipes.empty else []
    return _next_id(ids, "BT", 4)

def add_recipe(
    *, recipe_name: str, brew_method: str, ownership: str,
    purposes: list[str], source: str, version: str, status: str,
    favorite: str, tags: str
) -> str:
    recipe_name = recipe_name.strip()
    if not recipe_name:
        raise ValueError("Recipe Name wajib diisi.")

    recipes = read_sheet("Recipe_Master")
    if not recipes.empty:
        duplicate = (
            recipes["Recipe_Name"].astype(str).str.strip().str.casefold()
            == recipe_name.casefold()
        )
        if duplicate.any():
            raise ValueError("Recipe Name sudah tersedia. Gunakan nama atau versi berbeda.")

    recipe_id = generate_recipe_id()
    today = date.today().isoformat()
    record = {
        "Recipe_ID": recipe_id,
        "Recipe_Name": recipe_name,
        "Brew_Method": brew_method.strip(),
        "Ownership": ownership.strip(),
        "Purpose": "; ".join(purposes),
        "Source": source.strip(),
        "Version": version.strip() or "V1",
        "Status": status.strip(),
        "Created_Date": today,
        "Last_Update": today,
        "Favorite": favorite.strip(),
        "Tags": tags.strip(),
    }

    ws = _get_worksheet("Recipe_Master")
    ws.append_row(
        [_clean(record.get(c, "")) for c in SHEET_HEADERS["Recipe_Master"]],
        value_input_option="USER_ENTERED",
    )
    clear_data_cache()
    return recipe_id


def get_recipe(recipe_id: str):
    recipes = read_sheet("Recipe_Master")
    if recipes.empty:
        return None
    match = recipes.loc[
        recipes["Recipe_ID"].astype(str).str.strip() == recipe_id.strip()
    ]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def update_recipe(recipe_id: str, updates: dict[str, Any]) -> None:
    ws = _get_worksheet("Recipe_Master")
    headers = ws.row_values(1)

    if "Recipe_ID" not in headers:
        raise RuntimeError("Header Recipe_ID tidak ditemukan.")

    id_column = headers.index("Recipe_ID") + 1
    cell = ws.find(recipe_id, in_column=id_column)
    if cell is None:
        raise ValueError(f"Recipe {recipe_id} tidak ditemukan.")

    current_values = ws.row_values(cell.row)
    if len(current_values) < len(headers):
        current_values += [""] * (len(headers) - len(current_values))

    row_map = dict(zip(headers, current_values))
    row_map.update({key: _clean(value) for key, value in updates.items()})
    row_map["Recipe_ID"] = recipe_id
    row_map["Last_Update"] = date.today().isoformat()

    ws.update(
        f"A{cell.row}",
        [[row_map.get(header, "") for header in headers]],
        value_input_option="USER_ENTERED",
    )
    clear_data_cache()


def clear_data_cache() -> None:
    read_sheet.clear()


def clear_connection_cache() -> None:
    clear_data_cache()
    _get_worksheet.clear()
    _get_spreadsheet.clear()
