from __future__ import annotations

from typing import Any

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

SHEET_HEADERS: dict[str, list[str]] = {
    "Recipe_Master": [
        "Recipe_ID",
        "Recipe_Name",
        "Brew_Method",
        "Ownership",
        "Purpose",
        "Source",
        "Version",
        "Status",
        "Created_Date",
        "Last_Update",
        "Favorite",
        "Tags",
    ],
    "Brew_Log": [
        "Log_ID",
        "Date",
        "Recipe_ID",
        "Bean_Name",
        "Roast_Profile",
        "Dose_g",
        "Water_g",
        "Ratio",
        "Grind_Setting",
        "Water_Temp_C",
        "Brew_Time",
        "Result_Score",
        "Aroma",
        "Sweetness",
        "Acidity",
        "Body",
        "Clarity",
        "Balance",
        "Aftertaste",
        "Overall_Notes",
    ],
    "Knowledge_Notes": [
        "Knowledge_ID",
        "Recipe_ID",
        "Deddy_Notes",
        "AI_Insight",
        "Next_Adjustment",
        "Lessons_Learned",
        "Important_Warning",
        "Updated_Date",
    ],
    "Legacy_Purpose": [
        "Legacy_ID",
        "Recipe_ID",
        "Personal_Favorite",
        "Family_Favorite",
        "Commercial_Favorite",
        "Experimental",
        "Reference_Only",
        "Personal_Notes",
        "Family_Notes",
        "Commercial_Notes",
    ],
    "Settings": [
        "Category",
        "Value",
    ],
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
        raise RuntimeError("Streamlit Secret [gcp_service_account] belum tersedia.")

    if "google_sheets" not in st.secrets:
        raise RuntimeError("Streamlit Secret [google_sheets] belum tersedia.")

    google_sheets = st.secrets["google_sheets"]
    if "brewthings_spreadsheet_id" not in google_sheets:
        raise RuntimeError(
            "Secret google_sheets.brewthings_spreadsheet_id belum tersedia."
        )

    service_account_info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )
    client = gspread.authorize(credentials)

    spreadsheet_id = google_sheets["brewthings_spreadsheet_id"]
    return client.open_by_key(spreadsheet_id)


@st.cache_resource(show_spinner=False)
def _get_worksheet(sheet_name: str):
    spreadsheet = _get_spreadsheet()

    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        headers = SHEET_HEADERS[sheet_name]
        return spreadsheet.add_worksheet(
            title=sheet_name,
            rows=1000,
            cols=max(len(headers), 10),
        )


def ensure_database_structure() -> None:
    """Check all required worksheets and make sure their headers exist."""
    for sheet_name, expected_headers in SHEET_HEADERS.items():
        worksheet = _get_worksheet(sheet_name)
        current_headers = worksheet.row_values(1)

        if not current_headers:
            worksheet.update("A1", [expected_headers])
            continue

        missing_headers = [
            header for header in expected_headers if header not in current_headers
        ]
        if missing_headers:
            worksheet.update(
                "A1",
                [current_headers + missing_headers],
            )


def get_database_status() -> pd.DataFrame:
    """Return connection and row-count status for every Brew Things worksheet."""
    rows: list[dict[str, Any]] = []

    for sheet_name, expected_headers in SHEET_HEADERS.items():
        worksheet = _get_worksheet(sheet_name)
        current_headers = worksheet.row_values(1)
        all_values = worksheet.get_all_values()

        missing_headers = [
            header for header in expected_headers if header not in current_headers
        ]
        data_rows = max(len(all_values) - 1, 0)

        rows.append(
            {
                "Worksheet": sheet_name,
                "Status": "Ready" if not missing_headers else "Header incomplete",
                "Data Rows": data_rows,
                "Columns": len(current_headers),
                "Missing Headers": ", ".join(missing_headers),
            }
        )

    return pd.DataFrame(rows)


def read_sheet(sheet_name: str) -> pd.DataFrame:
    """Read one Brew Things worksheet as a DataFrame."""
    if sheet_name not in SHEET_HEADERS:
        raise ValueError(f"Worksheet tidak dikenal: {sheet_name}")

    worksheet = _get_worksheet(sheet_name)
    records = worksheet.get_all_records(default_blank="")

    if not records:
        return pd.DataFrame(columns=SHEET_HEADERS[sheet_name])

    df = pd.DataFrame(records)

    for column in SHEET_HEADERS[sheet_name]:
        if column not in df.columns:
            df[column] = ""

    return df[SHEET_HEADERS[sheet_name]]


def get_settings(category: str) -> list[str]:
    """Return dropdown values from the Settings worksheet."""
    df = read_sheet("Settings")
    if df.empty:
        return []

    category_mask = (
        df["Category"].astype(str).str.strip().str.casefold()
        == category.strip().casefold()
    )
    values = (
        df.loc[category_mask, "Value"]
        .astype(str)
        .str.strip()
    )
    return [value for value in values.tolist() if value]


def clear_connection_cache() -> None:
    """Useful after changing Streamlit Secrets or Google Sheet sharing."""
    _get_worksheet.clear()
    _get_spreadsheet.clear()
