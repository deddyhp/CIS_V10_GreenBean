from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

MODULE_VERSION = "10.19"
WORKSHEET_NAME = "roasting_plans"
HEADERS = [
    "plan_id", "plan_name", "bean", "purpose", "goal", "status",
    "batch_size_g", "density", "moisture", "plan_json", "rating",
    "usage_count", "last_used_at", "result_notes", "cupping_notes",
    "created_at", "updated_at", "source",
]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def _now() -> str:
    return datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")


@st.cache_resource(show_spinner=False)
def _worksheet():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("Streamlit Secret [gcp_service_account] belum tersedia.")
    if "google_sheets" not in st.secrets:
        raise RuntimeError("Streamlit Secret [google_sheets] belum tersedia.")

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(st.secrets["google_sheets"]["spreadsheet_id"])
    try:
        ws = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=len(HEADERS))
    return ws


def create_database() -> None:
    ws = _worksheet()
    if ws.col_count < len(HEADERS):
        ws.resize(rows=max(ws.row_count, 1000), cols=len(HEADERS))
    first = ws.row_values(1)
    if not first:
        ws.update("A1", [HEADERS])
    elif first != HEADERS:
        missing = [h for h in HEADERS if h not in first]
        if missing:
            ws.update("A1", [first + missing])


def _records() -> pd.DataFrame:
    create_database()
    records = _worksheet().get_all_records(default_blank="")
    if not records:
        return pd.DataFrame(columns=HEADERS)
    df = pd.DataFrame(records)
    for col in HEADERS:
        if col not in df.columns:
            df[col] = ""
    for col in ["batch_size_g", "density", "moisture", "rating", "usage_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df[HEADERS]


def get_all_plans() -> pd.DataFrame:
    df = _records()
    if df.empty:
        return df
    return df.sort_values(["updated_at", "plan_id"], ascending=[False, False], kind="stable").reset_index(drop=True)


def get_plan(plan_id: str) -> dict[str, Any] | None:
    df = _records()
    match = df[df["plan_id"].astype(str) == str(plan_id)]
    if match.empty:
        return None
    row = match.iloc[0].to_dict()
    try:
        row["plan_data"] = json.loads(row.get("plan_json") or "{}")
    except json.JSONDecodeError:
        row["plan_data"] = {}
    return row


def _generate_id() -> str:
    prefix = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("RP-%Y%m%d")
    df = _records()
    if df.empty:
        return f"{prefix}-001"
    same = df[df["plan_id"].astype(str).str.startswith(prefix)]
    if same.empty:
        return f"{prefix}-001"
    nums = pd.to_numeric(same["plan_id"].astype(str).str.extract(r"(\d+)$", expand=False), errors="coerce").dropna()
    return f"{prefix}-{int(nums.max()) + 1:03d}"


def _find_row(plan_id: str) -> int | None:
    values = _worksheet().col_values(1)
    for idx, value in enumerate(values[1:], start=2):
        if value == plan_id:
            return idx
    return None


def save_plan(metadata: dict[str, Any], plan_data: dict[str, Any], plan_id: str | None = None) -> str:
    ws = _worksheet()
    now = _now()
    existing: dict[str, Any] = {}

    if plan_id:
        existing = get_plan(plan_id) or {}
        if not existing:
            raise ValueError(f"Plan {plan_id} tidak ditemukan.")
        created_at = existing.get("created_at") or now
        rating = float(existing.get("rating") or 0)
        usage_count = int(existing.get("usage_count") or 0)
        last_used_at = existing.get("last_used_at") or ""
        result_notes = existing.get("result_notes") or ""
        cupping_notes = existing.get("cupping_notes") or ""
        source = metadata.get("source") or existing.get("source") or "Manual Plan"
    else:
        plan_id = _generate_id()
        created_at, rating, usage_count = now, 0, 0
        last_used_at = result_notes = cupping_notes = ""
        source = metadata.get("source") or "Manual Plan"

    row = [
        plan_id,
        metadata.get("plan_name", ""), metadata.get("bean", ""),
        metadata.get("purpose", ""), metadata.get("goal", ""),
        metadata.get("status", "Draft"), float(metadata.get("batch_size_g") or 0),
        float(metadata.get("density") or 0), float(metadata.get("moisture") or 0),
        json.dumps(plan_data, ensure_ascii=False), rating, usage_count,
        last_used_at, result_notes, cupping_notes, created_at, now, source,
    ]
    row_num = _find_row(plan_id)
    if row_num is not None:
        ws.update(f"A{row_num}:R{row_num}", [row], value_input_option="USER_ENTERED")
    else:
        ws.append_row(row, value_input_option="USER_ENTERED")
    return plan_id


def duplicate_plan(source_plan_id: str, new_name: str) -> str:
    source = get_plan(source_plan_id)
    if not source:
        raise ValueError("Source plan tidak ditemukan.")
    metadata = {
        "plan_name": new_name,
        "bean": source.get("bean", ""), "purpose": source.get("purpose", ""),
        "goal": source.get("goal", ""), "status": "Draft",
        "batch_size_g": source.get("batch_size_g", 0),
        "density": source.get("density", 0), "moisture": source.get("moisture", 0),
        "source": source.get("source", "Manual Plan"),
    }
    return save_plan(metadata, source.get("plan_data", {}))


def save_evaluation(plan_id: str, rating: float, result_notes: str, cupping_notes: str, mark_used: bool) -> None:
    ws = _worksheet()
    row_num = _find_row(plan_id)
    plan = get_plan(plan_id)
    if row_num is None or not plan:
        raise ValueError("Plan tidak ditemukan.")
    usage = int(plan.get("usage_count") or 0) + (1 if mark_used else 0)
    last_used = _now() if mark_used else (plan.get("last_used_at") or "")
    ws.update(
        f"K{row_num}:Q{row_num}",
        [[float(rating), usage, last_used, result_notes, cupping_notes, plan.get("created_at", ""), _now()]],
        value_input_option="USER_ENTERED",
    )


def delete_plan(plan_id: str) -> None:
    row_num = _find_row(plan_id)
    if row_num is None:
        raise ValueError("Plan tidak ditemukan.")
    _worksheet().delete_rows(row_num)
