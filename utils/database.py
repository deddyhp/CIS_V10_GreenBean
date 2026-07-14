from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

HEADERS = [
    "bean_id",
    "bean_name",
    "species",
    "origin",
    "region",
    "supplier",
    "process",
    "variety",
    "density",
    "moisture",
    "stock",
    "location",
    "notes",
    "created_at",
    "updated_at",
    "last_stock_before",
    "last_stock_remark",
    "last_stock_updated_at",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def _now_text() -> str:
    return datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")


def _clean(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return value


@st.cache_resource(show_spinner=False)
def _get_worksheet():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("Streamlit Secret [gcp_service_account] belum tersedia.")
    if "google_sheets" not in st.secrets:
        raise RuntimeError("Streamlit Secret [google_sheets] belum tersedia.")

    service_account_info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )
    client = gspread.authorize(credentials)

    spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
    worksheet_name = st.secrets["google_sheets"].get("worksheet_name", "greenbean")

    spreadsheet = client.open_by_key(spreadsheet_id)
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=len(HEADERS),
        )
    return worksheet


def create_database() -> None:
    worksheet = _get_worksheet()
    first_row = worksheet.row_values(1)

    if not first_row:
        worksheet.update("A1", [HEADERS])
        return

    if first_row != HEADERS:
        missing = [header for header in HEADERS if header not in first_row]
        if missing:
            new_headers = first_row + missing
            worksheet.update("A1", [new_headers])


def _records_dataframe() -> pd.DataFrame:
    worksheet = _get_worksheet()
    records = worksheet.get_all_records(default_blank="")

    if not records:
        return pd.DataFrame(columns=HEADERS)

    df = pd.DataFrame(records)
    for column in HEADERS:
        if column not in df.columns:
            df[column] = ""

    for column in ["density", "moisture", "stock", "last_stock_before"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    return df[HEADERS]


def get_all_greenbean() -> pd.DataFrame:
    df = _records_dataframe()
    if df.empty:
        return df
    return df.sort_values(["bean_name", "bean_id"], kind="stable").reset_index(drop=True)


def search_greenbean(keyword: str) -> pd.DataFrame:
    df = _records_dataframe()
    if df.empty:
        return df

    keyword_lower = keyword.strip().lower()
    searchable_columns = [
        "bean_id",
        "bean_name",
        "species",
        "origin",
        "region",
        "supplier",
        "process",
        "variety",
        "location",
        "notes",
    ]

    mask = pd.Series(False, index=df.index)
    for column in searchable_columns:
        mask = mask | df[column].astype(str).str.lower().str.contains(
            keyword_lower,
            regex=False,
            na=False,
        )

    return (
        df.loc[mask]
        .sort_values(["bean_name", "bean_id"], kind="stable")
        .reset_index(drop=True)
    )


def _generate_bean_id(species: str) -> str:
    prefix = {
        "Arabica": "AR",
        "Robusta": "RB",
        "Liberica": "LB",
        "Excelsa": "EX",
        "Other": "OT",
    }.get(species, "OT")

    df = _records_dataframe()
    if df.empty:
        return f"{prefix}0001"

    same_prefix = df["bean_id"].astype(str).str.startswith(prefix, na=False)
    numbers = (
        df.loc[same_prefix, "bean_id"]
        .astype(str)
        .str.extract(r"(\d+)$", expand=False)
    )
    numeric = pd.to_numeric(numbers, errors="coerce").dropna()
    next_number = int(numeric.max()) + 1 if not numeric.empty else 1
    return f"{prefix}{next_number:04d}"


def add_greenbean(
    bean_name: str,
    species: str,
    origin: str,
    region: str,
    supplier: str,
    process: str,
    variety: str,
    density: float,
    moisture: float,
    stock: float,
    location: str,
    notes: str,
) -> str:
    worksheet = _get_worksheet()
    bean_id = _generate_bean_id(species)
    now = _now_text()

    row = [
        bean_id,
        bean_name,
        species,
        origin,
        region,
        supplier,
        process,
        variety,
        float(density),
        float(moisture),
        float(stock),
        location,
        notes,
        now,
        now,
        "",
        "Initial stock",
        now,
    ]
    worksheet.append_row([_clean(value) for value in row], value_input_option="USER_ENTERED")
    return bean_id


def _find_row_number(bean_id: str) -> int | None:
    worksheet = _get_worksheet()
    values = worksheet.col_values(1)
    for index, value in enumerate(values[1:], start=2):
        if value == bean_id:
            return index
    return None


def get_greenbean_by_bean_id(bean_id: str) -> dict[str, Any] | None:
    df = _records_dataframe()
    if df.empty:
        return None

    matched = df[df["bean_id"].astype(str) == str(bean_id)]
    if matched.empty:
        return None
    return matched.iloc[0].to_dict()


def update_greenbean_properties(
    bean_id: str,
    bean_name: str,
    species: str,
    origin: str,
    region: str,
    supplier: str,
    process: str,
    variety: str,
    density: float,
    moisture: float,
    location: str,
    notes: str,
) -> None:
    worksheet = _get_worksheet()
    row_number = _find_row_number(bean_id)
    if row_number is None:
        raise ValueError(f"Bean ID {bean_id} tidak ditemukan.")

    current = get_greenbean_by_bean_id(bean_id)
    if current is None:
        raise ValueError(f"Bean ID {bean_id} tidak ditemukan.")

    values = [
        bean_id,
        bean_name,
        species,
        origin,
        region,
        supplier,
        process,
        variety,
        float(density),
        float(moisture),
        float(current.get("stock", 0) or 0),
        location,
        notes,
        current.get("created_at", "") or _now_text(),
        _now_text(),
        current.get("last_stock_before", ""),
        current.get("last_stock_remark", ""),
        current.get("last_stock_updated_at", ""),
    ]

    worksheet.update(
        f"A{row_number}:R{row_number}",
        [[_clean(value) for value in values]],
        value_input_option="USER_ENTERED",
    )


def update_greenbean_stock(bean_id: str, new_stock: float, remark: str) -> None:
    if new_stock < 0:
        raise ValueError("Stock tidak boleh negatif.")
    if not remark.strip():
        raise ValueError("Remark perubahan stok wajib diisi.")

    worksheet = _get_worksheet()
    row_number = _find_row_number(bean_id)
    if row_number is None:
        raise ValueError(f"Bean ID {bean_id} tidak ditemukan.")

    current = get_greenbean_by_bean_id(bean_id)
    if current is None:
        raise ValueError(f"Bean ID {bean_id} tidak ditemukan.")

    previous_stock = float(current.get("stock", 0) or 0)
    now = _now_text()

    # K=stock, O=updated_at, P=last_stock_before, Q=last_stock_remark, R=last_stock_updated_at
    worksheet.batch_update(
        [
            {"range": f"K{row_number}", "values": [[float(new_stock)]]},
            {"range": f"O{row_number}", "values": [[now]]},
            {"range": f"P{row_number}", "values": [[previous_stock]]},
            {"range": f"Q{row_number}", "values": [[remark.strip()]]},
            {"range": f"R{row_number}", "values": [[now]]},
        ],
        value_input_option="USER_ENTERED",
    )
