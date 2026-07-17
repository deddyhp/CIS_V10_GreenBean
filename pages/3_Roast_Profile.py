from __future__ import annotations

import ast
import hashlib
import json
import os
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

# CIS execution mode
# - Laptop/local run: Full Mode
# - Streamlit Community Cloud (/mount/src): Fallback Mode
# Override when needed with environment variable:
#   CIS_MODE=full
#   CIS_MODE=fallback
_MODE_OVERRIDE = os.getenv("CIS_MODE", "").strip().lower()
_IS_STREAMLIT_CLOUD = str(PROJECT_ROOT).replace("\\", "/").startswith("/mount/src/")

if _MODE_OVERRIDE == "full":
    FULL_MODE = True
elif _MODE_OVERRIDE == "fallback":
    FULL_MODE = False
else:
    FULL_MODE = not _IS_STREAMLIT_CLOUD

SYSTEM_MODE = "FULL" if FULL_MODE else "FALLBACK"

# Only Full Mode creates and uses the permanent local data directories.
if FULL_MODE:
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


def init_db() -> None:
    with db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS green_beans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bean_name TEXT NOT NULL,
                species TEXT,
                origin TEXT,
                process TEXT,
                supplier TEXT DEFAULT 'Unknown',
                lot TEXT,
                variety TEXT,
                density REAL,
                moisture REAL,
                initial_weight_g REAL,
                current_stock_g REAL,
                purchase_price REAL,
                selling_price REAL,
                status TEXT DEFAULT 'Active',
                UNIQUE(bean_name, process, supplier, lot)
            );

            CREATE TABLE IF NOT EXISTS roast_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roast_id TEXT UNIQUE NOT NULL,
                bean_id INTEGER,
                title TEXT,
                roast_date TEXT,
                roast_time TEXT,
                operator TEXT,
                roaster TEXT,
                artisan_version TEXT,
                roast_purpose TEXT,
                blend_project TEXT,
                profile_version TEXT,
                drum_speed_rpm REAL DEFAULT 90,
                green_weight_g REAL,
                roasted_weight_g REAL,
                weight_loss_pct REAL,
                yield_pct REAL,
                density REAL,
                moisture REAL,
                agtron REAL,
                notes TEXT,
                data_quality TEXT,
                parser_version TEXT DEFAULT '0.4.1',
                created_at TEXT NOT NULL,
                FOREIGN KEY(bean_id) REFERENCES green_beans(id)
            );

            CREATE TABLE IF NOT EXISTS artisan_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roast_session_id INTEGER NOT NULL,
                original_name TEXT,
                source_path TEXT,
                stored_path TEXT,
                checksum_sha256 TEXT UNIQUE,
                raw_json TEXT,
                imported_at TEXT NOT NULL,
                FOREIGN KEY(roast_session_id) REFERENCES roast_sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS roast_curve_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roast_session_id INTEGER NOT NULL,
                time_s REAL,
                bt REAL,
                et REAL,
                ror_bt REAL,
                ror_et REAL,
                FOREIGN KEY(roast_session_id) REFERENCES roast_sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS roast_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roast_session_id INTEGER NOT NULL,
                event_name TEXT,
                bt REAL,
                et REAL,
                time_s REAL,
                gas REAL,
                airflow REAL,
                drum REAL,
                source TEXT,
                FOREIGN KEY(roast_session_id) REFERENCES roast_sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS roast_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roast_session_id INTEGER NOT NULL,
                milestone TEXT,
                time_s REAL,
                bt REAL,
                et REAL,
                FOREIGN KEY(roast_session_id) REFERENCES roast_sessions(id) ON DELETE CASCADE
            );
            """
        )
        # Safe migrations when the user copies the V0.2 data folder into V0.3.
        bean_cols = {r[1] for r in con.execute("PRAGMA table_info(green_beans)")}
        if "species" not in bean_cols:
            con.execute("ALTER TABLE green_beans ADD COLUMN species TEXT")
        file_cols = {r[1] for r in con.execute("PRAGMA table_info(artisan_files)")}
        if "source_path" not in file_cols:
            con.execute("ALTER TABLE artisan_files ADD COLUMN source_path TEXT")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_num(value: Any) -> float | None:
    try:
        if value in (None, "", -1):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_alog(file_name: str, payload: bytes, source_path: str | None = None) -> ParsedRoast:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        text = payload.decode("latin-1")
    try:
        raw = ast.literal_eval(text)
    except Exception as exc:
        raise ValueError(f"File bukan format Artisan .alog yang dapat dibaca: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Isi .alog tidak berupa dictionary Artisan.")

    timex = raw.get("timex") or []
    et = raw.get("temp1") or []
    bt = raw.get("temp2") or []
    if not (timex and bt):
        raise ValueError("Kurva BT/timex tidak ditemukan.")

    charge_idx = (raw.get("timeindex") or [0])[0] or 0
    charge_t = float(timex[charge_idx]) if charge_idx < len(timex) else 0.0
    n = min(len(timex), len(bt), len(et) if et else len(bt))
    rows = []
    for i in range(n):
        if i < charge_idx:
            continue
        rows.append({
            "time_s": round(float(timex[i]) - charge_t, 3),
            "bt": safe_num(bt[i]),
            "et": safe_num(et[i]) if et else None,
        })
    curves = pd.DataFrame(rows)
    if not curves.empty:
        curves["ror_bt"] = curves["bt"].diff() / curves["time_s"].diff() * 60
        curves["ror_et"] = curves["et"].diff() / curves["time_s"].diff() * 60
        curves.replace([float("inf"), float("-inf")], pd.NA, inplace=True)

    computed = raw.get("computed") or {}
    weight = raw.get("weight") or [None, None, "g"]
    green_w = safe_num(computed.get("weightin")) or safe_num(weight[0] if len(weight) > 0 else None)
    roasted_w = safe_num(computed.get("weightout")) or safe_num(weight[1] if len(weight) > 1 else None)
    loss = safe_num(computed.get("weight_loss"))
    if loss is None and green_w and roasted_w:
        loss = (green_w - roasted_w) / green_w * 100
    yield_pct = 100 - loss if loss is not None else None

    summary = {
        "title": raw.get("title") or Path(file_name).stem,
        "roast_date": raw.get("roastisodate") or raw.get("roastdate"),
        "roast_time": raw.get("roasttime"),
        "operator": raw.get("operator"),
        "roaster": raw.get("roastertype") or raw.get("machinesetup"),
        "artisan_version": raw.get("recording_version") or raw.get("version"),
        "drum_speed": safe_num(raw.get("drumspeed")) or 90.0,
        "green_weight_g": green_w,
        "roasted_weight_g": roasted_w,
        "weight_loss_pct": loss,
        "yield_pct": yield_pct,
        "density": safe_num(computed.get("set_density")) or safe_num((raw.get("density") or [None])[0]),
        "moisture": safe_num(computed.get("moisture_greens")) or safe_num(raw.get("moisture_greens")),
        "charge_bt": safe_num(computed.get("CHARGE_BT")),
        "charge_et": safe_num(computed.get("CHARGE_ET")),
        "tp_time": safe_num(computed.get("TP_time")),
        "tp_bt": safe_num(computed.get("TP_BT")),
        "tp_et": safe_num(computed.get("TP_ET")),
        "dry_time": safe_num(computed.get("DRY_time")),
        "dry_bt": safe_num(computed.get("DRY_BT")),
        "dry_et": safe_num(computed.get("DRY_ET")),
        "fc_time": safe_num(computed.get("FCs_time")),
        "fc_bt": safe_num(computed.get("FCs_BT")),
        "fc_et": safe_num(computed.get("FCs_ET")),
        "fce_time": safe_num(computed.get("FCe_time")),
        "fce_bt": safe_num(computed.get("FCe_BT")),
        "fce_et": safe_num(computed.get("FCe_ET")),
        "drop_time": safe_num(computed.get("DROP_time")),
        "drop_bt": safe_num(computed.get("DROP_BT")),
        "drop_et": safe_num(computed.get("DROP_ET")),
        "total_time": safe_num(computed.get("totaltime")),
        "drying_time": safe_num(computed.get("dryphasetime")),
        "maillard_time": safe_num(computed.get("midphasetime")),
        "development_time": safe_num(computed.get("finishphasetime")),
    }
    if summary["total_time"] and summary["development_time"]:
        summary["dtr_pct"] = summary["development_time"] / summary["total_time"] * 100
    else:
        summary["dtr_pct"] = None

    etypes = raw.get("etypes") or ["Air", "Drum", "Damper", "Burner", "--"]
    ev_idx = raw.get("specialevents") or []
    ev_types = raw.get("specialeventstype") or []
    ev_values = raw.get("specialeventsvalue") or []
    event_rows = []
    for idx, typ, val in zip(ev_idx, ev_types, ev_values):
        if idx >= len(timex):
            continue
        name = etypes[typ] if isinstance(typ, int) and 0 <= typ < len(etypes) else f"Type {typ}"
        event_rows.append({
            "event_name": name,
            "time_s": round(float(timex[idx]) - charge_t, 3),
            "bt": safe_num(bt[idx]) if idx < len(bt) else None,
            "et": safe_num(et[idx]) if idx < len(et) else None,
            "gas": float(val) * 10 if name.lower() == "burner" else None,
            "airflow": float(val) * 10 if name.lower() == "air" else None,
            "drum": float(val) * 10 if name.lower() == "drum" else None,
            "source": "Artisan",
        })
    events = pd.DataFrame(event_rows, columns=["event_name", "time_s", "bt", "et", "gas", "airflow", "drum", "source"])

    return ParsedRoast(raw, file_name, sha256_bytes(payload), source_path or file_name, summary, curves, events)



def infer_title_details(title: str, roast_date: str | None) -> dict[str, Any]:
    clean = (title or "Unknown Bean").replace("_", " ").strip()
    low = clean.lower()
    process = "Unknown"
    for key, label in [
        ("semi washed", "Semi Washed"), ("semi-washed", "Semi Washed"),
        ("full washed", "Washed"), ("washed", "Washed"),
        ("natural", "Natural"), (" nat ", "Natural"),
        ("honey", "Honey"), ("wet hulled", "Wet Hulled"),
        ("anaerobic", "Anaerobic"),
    ]:
        if key in f" {low} ":
            process = label
            break
    purpose = "Blend Component" if any(x in low for x in ["forte", "bloom", "heart", "blend"]) else "Experimental"
    if any(x in low for x in ["v60", "filter"]):
        purpose = "Filter"
    elif "espresso" in low:
        purpose = "Espresso"
    elif any(x in low for x in ["tubruk", "toobroek"]):
        purpose = "Tubruk"
    elif "latte" in low:
        purpose = "Latte"
    blend = next((x.title() for x in ["forte", "bloom", "heart"] if x in low), "")
    year = (roast_date or "0000")[:4]
    bean_name = clean.split(" ratio")[0].strip()
    return {
        "bean_name": bean_name,
        "process": process,
        "supplier": "Unknown",
        "lot": f"LEGACY-{year}",
        "purpose": purpose,
        "blend_project": blend,
        "profile_version": clean,
        "drum_speed": 90.0,
        "agtron": None,
        "notes": "",
        "quality": "Usable",
    }


def infer_single_identity(title: str, roast_date: str | None) -> dict[str, Any]:
    """Best-effort defaults for a single .alog upload.

    All fields remain editable. Archive ZIP imports still use folder path as truth.
    Examples:
      Ar Argopuro Taufik-1-26 -> Arabica / Argopuro
      Rob Bengkulu Maxi-1    -> Robusta / Bengkulu
    """
    details = infer_title_details(title, roast_date)
    clean = (title or "Unknown Bean").replace("_", " " ).strip()
    tokens = [t for t in clean.split() if t]
    species = "Unknown"
    origin = "Unknown"
    if tokens:
        first = tokens[0].lower().rstrip('.:-')
        if first in {"ar", "arabica", "arabika"}:
            species = "Arabica"
            if len(tokens) > 1:
                origin = tokens[1].strip("-_.,:;").title()
        elif first in {"rob", "robusta"}:
            species = "Robusta"
            if len(tokens) > 1:
                origin = tokens[1].strip("-_.,:;").title()
    details.update({"species": species, "origin": origin})
    return details


def infer_folder_identity(source_path: str) -> dict[str, str]:
    """Folder path is the primary truth for archive imports.

    Expected examples:
      ARABIKA/BALI/file.alog
      ROBUSTA/TIRTOYUDO/file.alog
    """
    parts = [p.strip() for p in Path(source_path.replace("\\", "/")).parts if p not in ("", "/")]
    # Ignore file name and common wrapper folders before ARABIKA/ROBUSTA.
    folders = parts[:-1] if parts and parts[-1].lower().endswith(".alog") else parts
    species = "Unknown"
    origin = "Unknown"
    confidence = "Low"
    root_index = None
    for i, part in enumerate(folders):
        key = part.upper().strip()
        if key in {"ARABIKA", "ARABICA"}:
            species, root_index = "Arabica", i
            break
        if key == "ROBUSTA":
            species, root_index = "Robusta", i
            break
    if root_index is not None and root_index + 1 < len(folders):
        origin = folders[root_index + 1].strip().title()
        confidence = "High"
    elif root_index is not None:
        confidence = "Medium"
    return {"species": species, "origin": origin, "confidence": confidence}


def collect_bulk_files(alog_uploads, zip_upload) -> list[tuple[str, str, bytes]]:
    files: list[tuple[str, str, bytes]] = []
    if alog_uploads:
        files.extend((f.name, f.name, f.getvalue()) for f in alog_uploads)
    if zip_upload:
        with zipfile.ZipFile(BytesIO(zip_upload.getvalue())) as zf:
            for info in zf.infolist():
                if not info.is_dir() and info.filename.lower().endswith(".alog"):
                    source_path = info.filename.replace("\\", "/")
                    files.append((Path(source_path).name, source_path, zf.read(info)))
    # Deduplicate within the same upload batch by checksum, preserving first folder path.
    seen = set()
    unique = []
    for name, source_path, payload in files:
        h = sha256_bytes(payload)
        if h not in seen:
            seen.add(h)
            unique.append((name, source_path, payload))
    return unique


def render_bulk_import() -> None:
    st.subheader("Archive Bulk Import")
    st.caption("Upload many .alog files or one ZIP. ZIP folder paths are treated as the primary Species/Origin identity. Nothing is saved until you confirm.")
    uploads = st.file_uploader("Select multiple Artisan .alog files", type=["alog"], accept_multiple_files=True, key="bulk_alog")
    zip_upload = st.file_uploader("Or upload one ZIP archive", type=["zip"], key="bulk_zip")
    if not uploads and not zip_upload:
        st.info("Choose multiple .alog files or a ZIP archive.")
        return
    if st.button("Scan archive", type="primary"):
        queue = []
        parsed_map = {}
        for file_name, source_path, payload in collect_bulk_files(uploads, zip_upload):
            try:
                parsed = parse_alog(file_name, payload, source_path)
                dup = existing_checksum(parsed.checksum)
                details = infer_title_details(parsed.summary.get("title") or file_name, parsed.summary.get("roast_date"))
                folder = infer_folder_identity(source_path)
                status = "Duplicate" if dup else "Ready"
                row = {
                    "import": not bool(dup), "status": status, "file_name": file_name, "source_path": source_path,
                    "title": parsed.summary.get("title"), "date": parsed.summary.get("roast_date"),
                    "species": folder["species"], "origin": folder["origin"], "folder_confidence": folder["confidence"],
                    "bean_name": details["bean_name"], "process": details["process"],
                    "supplier": details["supplier"], "lot": details["lot"], "purpose": details["purpose"],
                    "blend_project": details["blend_project"], "profile_version": details["profile_version"],
                    "drum_speed": parsed.summary.get("drum_speed") or 90.0, "quality": details["quality"],
                    "checksum": parsed.checksum, "message": (f"Already {dup[0]}" if dup else "")
                }
                queue.append(row)
                parsed_map[parsed.checksum] = parsed
            except Exception as exc:
                queue.append({"import": False, "status": "Invalid", "file_name": file_name, "source_path": source_path, "title": "", "date": "",
                              "species": "Unknown", "origin": "Unknown", "folder_confidence": "Low",
                              "bean_name": "", "process": "", "supplier": "Unknown", "lot": "",
                              "purpose": "Experimental", "blend_project": "", "profile_version": "", "drum_speed": 90.0,
                              "quality": "Limited", "checksum": "", "message": str(exc)})
        st.session_state["bulk_queue"] = queue
        st.session_state["bulk_parsed"] = parsed_map

    queue = st.session_state.get("bulk_queue")
    if not queue:
        return
    qdf = pd.DataFrame(queue)
    counts = qdf["status"].value_counts().to_dict()
    st.markdown("#### Archive Summary")
    species_summary = qdf[qdf["status"] != "Invalid"].groupby("species").size().reset_index(name="roasts")
    origin_summary = qdf[qdf["status"] != "Invalid"].groupby(["species", "origin"]).size().reset_index(name="roasts").sort_values(["species", "roasts"], ascending=[True, False])
    sx, ox = st.columns([1, 2])
    with sx:
        st.dataframe(species_summary, hide_index=True, width='stretch')
    with ox:
        st.dataframe(origin_summary, hide_index=True, width='stretch', height=220)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Detected", len(qdf))
    c2.metric("Ready", counts.get("Ready", 0))
    c3.metric("Duplicate", counts.get("Duplicate", 0))
    c4.metric("Invalid", counts.get("Invalid", 0))
    st.markdown("#### Review Queue")
    editable_cols = ["import", "status", "source_path", "file_name", "date", "species", "origin", "folder_confidence", "bean_name", "process", "supplier", "lot", "purpose", "blend_project", "profile_version", "drum_speed", "quality", "message", "checksum"]
    edited = st.data_editor(
        qdf[editable_cols], hide_index=True, width='stretch', num_rows="fixed",
        disabled=["status", "source_path", "file_name", "date", "folder_confidence", "message", "checksum"],
        column_config={
            "import": st.column_config.CheckboxColumn("Import"),
            "source_path": st.column_config.TextColumn("Folder path", width="large"),
            "species": st.column_config.SelectboxColumn("Species", options=["Arabica", "Robusta", "Unknown"]),
            "folder_confidence": st.column_config.TextColumn("Folder confidence"),
            "purpose": st.column_config.SelectboxColumn("Purpose", options=["Filter", "Espresso", "Latte", "Tubruk", "Blend Component", "Sample Roast", "Experimental", "Other"]),
            "quality": st.column_config.SelectboxColumn("Quality", options=["Complete", "Usable", "Limited"]),
            "drum_speed": st.column_config.NumberColumn("Drum rpm", min_value=0.0, step=1.0),
            "checksum": None,
        },
        key="bulk_editor"
    )
    selected = edited[(edited["import"] == True) & (edited["status"] == "Ready")]
    st.caption(f"Selected for import: {len(selected)}")
    if st.button("Import selected usable files", type="primary", disabled=selected.empty):
        ok, failed = [], []
        parsed_map = st.session_state.get("bulk_parsed", {})
        for _, row in selected.iterrows():
            try:
                parsed = parsed_map[row["checksum"]]
                roast_id = save_roast(parsed, {
                    "bean_name": str(row["bean_name"]).strip() or "Unknown Bean",
                    "species": str(row["species"]).strip() or "Unknown",
                    "origin": str(row["origin"]).strip(), "process": str(row["process"]).strip(),
                    "supplier": str(row["supplier"]).strip() or "Unknown", "lot": str(row["lot"]).strip(),
                    "purpose": row["purpose"], "blend_project": str(row["blend_project"]).strip(),
                    "profile_version": str(row["profile_version"]).strip(), "drum_speed": float(row["drum_speed"] or 90),
                    "agtron": None, "notes": "Bulk legacy import", "quality": row["quality"]
                }, pd.DataFrame(columns=["bt", "gas", "airflow"]))
                ok.append(roast_id)
            except Exception as exc:
                failed.append(f"{row['file_name']}: {exc}")
        if ok:
            st.success(f"Imported {len(ok)} roast files successfully.")
        if failed:
            st.error("Some files failed:\n" + "\n".join(failed[:10]))
        st.session_state.pop("bulk_queue", None)
        st.session_state.pop("bulk_parsed", None)


def fmt_time(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def make_roast_id(summary: dict[str, Any], con: sqlite3.Connection) -> str:
    date = (summary.get("roast_date") or datetime.now().date().isoformat()).replace("-", "")
    base = f"RST{date}"
    count = con.execute("SELECT COUNT(*) FROM roast_sessions WHERE roast_id LIKE ?", (base + "%",)).fetchone()[0]
    return f"{base}-{count + 1:03d}"


def existing_checksum(checksum: str) -> tuple | None:
    with db() as con:
        return con.execute(
            "SELECT rs.roast_id, rs.title FROM artisan_files af JOIN roast_sessions rs ON rs.id=af.roast_session_id WHERE af.checksum_sha256=?",
            (checksum,),
        ).fetchone()


def ensure_bean(con: sqlite3.Connection, bean_name: str, species: str, origin: str, process: str, supplier: str, lot: str,
                density: float | None, moisture: float | None) -> int:
    existing = con.execute(
        "SELECT id FROM green_beans WHERE bean_name=? AND COALESCE(process,'')=? AND COALESCE(supplier,'')=? AND COALESCE(lot,'')=?",
        (bean_name, process, supplier, lot),
    ).fetchone()
    if existing:
        con.execute(
            "UPDATE green_beans SET species=COALESCE(NULLIF(species,''),?), origin=CASE WHEN origin IS NULL OR origin='' OR origin='Unknown' THEN ? ELSE origin END WHERE id=?",
            (species, origin, int(existing[0])),
        )
        return int(existing[0])
    cur = con.execute(
        "INSERT INTO green_beans(bean_name,species,origin,process,supplier,lot,density,moisture) VALUES(?,?,?,?,?,?,?,?)",
        (bean_name, species, origin, process, supplier or "Unknown", lot, density, moisture),
    )
    return int(cur.lastrowid)


def save_roast(parsed: ParsedRoast, form: dict[str, Any], manual_events: pd.DataFrame) -> str:
    duplicate = existing_checksum(parsed.checksum) if FULL_MODE else None
    if duplicate:
        raise ValueError(f"File sudah pernah diimport sebagai {duplicate[0]} — {duplicate[1]}")
    with db() as con:
        bean_id = ensure_bean(
            con, form["bean_name"], form.get("species", "Unknown"), form["origin"], form["process"], form["supplier"], form["lot"],
            parsed.summary.get("density"), parsed.summary.get("moisture")
        )
        roast_id = make_roast_id(parsed.summary, con)
        cur = con.execute(
            """
            INSERT INTO roast_sessions(
                roast_id,bean_id,title,roast_date,roast_time,operator,roaster,artisan_version,
                roast_purpose,blend_project,profile_version,drum_speed_rpm,green_weight_g,roasted_weight_g,
                weight_loss_pct,yield_pct,density,moisture,agtron,notes,data_quality,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                roast_id, bean_id, parsed.summary.get("title"), parsed.summary.get("roast_date"), parsed.summary.get("roast_time"),
                parsed.summary.get("operator"), parsed.summary.get("roaster"), parsed.summary.get("artisan_version"),
                form["purpose"], form["blend_project"], form["profile_version"], form["drum_speed"],
                parsed.summary.get("green_weight_g"), parsed.summary.get("roasted_weight_g"),
                parsed.summary.get("weight_loss_pct"), parsed.summary.get("yield_pct"), parsed.summary.get("density"),
                parsed.summary.get("moisture"), form["agtron"], form["notes"], form["quality"], datetime.now().isoformat(timespec="seconds")
            ),
        )
        roast_session_id = int(cur.lastrowid)
        stored = RAW_DIR / f"{roast_id}_{Path(parsed.file_name).name}"
        # raw content is reserialized for portability; checksum still represents original uploaded bytes
        stored.write_text(repr(parsed.raw), encoding="utf-8")
        con.execute(
            "INSERT INTO artisan_files(roast_session_id,original_name,source_path,stored_path,checksum_sha256,raw_json,imported_at) VALUES(?,?,?,?,?,?,?)",
            (roast_session_id, parsed.file_name, parsed.source_path, str(stored), parsed.checksum, json.dumps(parsed.raw, default=str), datetime.now().isoformat(timespec="seconds")),
        )
        curve_rows = [
            (roast_session_id, r.time_s, r.bt, r.et, None if pd.isna(r.ror_bt) else r.ror_bt, None if pd.isna(r.ror_et) else r.ror_et)
            for r in parsed.curves.itertuples(index=False)
        ]
        con.executemany(
            "INSERT INTO roast_curve_points(roast_session_id,time_s,bt,et,ror_bt,ror_et) VALUES(?,?,?,?,?,?)",
            curve_rows,
        )
        all_events = parsed.events.copy()
        if manual_events is not None and not manual_events.empty:
            me = manual_events.copy()
            me["event_name"] = "Manual Setting"
            me["time_s"] = None
            me["et"] = None
            me["drum"] = None
            me["source"] = "Manual CIS"
            all_events = pd.concat([all_events, me[all_events.columns]], ignore_index=True)
        for r in all_events.itertuples(index=False):
            con.execute(
                "INSERT INTO roast_events(roast_session_id,event_name,bt,et,time_s,gas,airflow,drum,source) VALUES(?,?,?,?,?,?,?,?,?)",
                (roast_session_id, r.event_name, r.bt, r.et, r.time_s, r.gas, r.airflow, r.drum, r.source),
            )
        milestones = [
            ("Charge", 0, parsed.summary.get("charge_bt"), parsed.summary.get("charge_et")),
            ("Turning Point", parsed.summary.get("tp_time"), parsed.summary.get("tp_bt"), parsed.summary.get("tp_et")),
            ("Dry End", parsed.summary.get("dry_time"), parsed.summary.get("dry_bt"), parsed.summary.get("dry_et")),
            ("First Crack", parsed.summary.get("fc_time"), parsed.summary.get("fc_bt"), parsed.summary.get("fc_et")),
            ("FC End", parsed.summary.get("fce_time"), parsed.summary.get("fce_bt"), parsed.summary.get("fce_et")),
            ("Drop", parsed.summary.get("drop_time"), parsed.summary.get("drop_bt"), parsed.summary.get("drop_et")),
        ]
        con.executemany(
            "INSERT INTO roast_milestones(roast_session_id,milestone,time_s,bt,et) VALUES(?,?,?,?,?)",
            [(roast_session_id, *m) for m in milestones if m[1] is not None],
        )
    return roast_id



def load_roast_for_edit(roast_id: str) -> dict[str, Any] | None:
    with db() as con:
        row = con.execute(
            """SELECT rs.id AS session_id, rs.roast_id, rs.title, rs.roast_date,
                      rs.roast_purpose, rs.blend_project, rs.profile_version,
                      rs.drum_speed_rpm, rs.green_weight_g, rs.roasted_weight_g,
                      rs.weight_loss_pct, rs.yield_pct, rs.density, rs.moisture,
                      rs.agtron, rs.notes, rs.data_quality,
                      gb.bean_name, gb.species, gb.origin, gb.process, gb.supplier, gb.lot
               FROM roast_sessions rs
               LEFT JOIN green_beans gb ON gb.id=rs.bean_id
               WHERE rs.roast_id=?""",
            (roast_id,),
        ).fetchone()
        if not row:
            return None
        cols = [d[0] for d in con.execute(
            """SELECT rs.id AS session_id, rs.roast_id, rs.title, rs.roast_date,
                      rs.roast_purpose, rs.blend_project, rs.profile_version,
                      rs.drum_speed_rpm, rs.green_weight_g, rs.roasted_weight_g,
                      rs.weight_loss_pct, rs.yield_pct, rs.density, rs.moisture,
                      rs.agtron, rs.notes, rs.data_quality,
                      gb.bean_name, gb.species, gb.origin, gb.process, gb.supplier, gb.lot
               FROM roast_sessions rs
               LEFT JOIN green_beans gb ON gb.id=rs.bean_id
               WHERE 1=0"""
        ).description]
        data = dict(zip(cols, row))
        events = pd.read_sql_query(
            """SELECT bt, gas, airflow FROM roast_events
               WHERE roast_session_id=? AND source='Manual CIS'
               ORDER BY bt""",
            con,
            params=(data["session_id"],),
        )
        data["manual_events"] = events
        data["curves"] = pd.read_sql_query(
            """SELECT time_s, bt, et, ror_bt, ror_et FROM roast_curve_points
               WHERE roast_session_id=? ORDER BY time_s""",
            con, params=(data["session_id"],),
        )
        data["milestones"] = pd.read_sql_query(
            """SELECT milestone, time_s, bt, et FROM roast_milestones
               WHERE roast_session_id=? ORDER BY time_s""",
            con, params=(data["session_id"],),
        )
        return data


def update_existing_roast(roast_id: str, form: dict[str, Any], manual_events: pd.DataFrame) -> None:
    with db() as con:
        row = con.execute("SELECT id FROM roast_sessions WHERE roast_id=?", (roast_id,)).fetchone()
        if not row:
            raise ValueError("Roast tidak ditemukan.")
        session_id = row[0]
        bean_id = ensure_bean(
            con,
            form["bean_name"], form["species"], form["origin"], form["process"],
            form["supplier"], form["lot"], None, None,
        )
        con.execute(
            """UPDATE roast_sessions
               SET bean_id=?, roast_purpose=?, blend_project=?, profile_version=?,
                   drum_speed_rpm=?, agtron=?, notes=?, data_quality=?, parser_version='0.4.4'
               WHERE id=?""",
            (bean_id, form["purpose"], form["blend_project"], form["profile_version"],
             form["drum_speed"], form["agtron"], form["notes"], form["quality"], session_id),
        )
        con.execute("DELETE FROM roast_events WHERE roast_session_id=? AND source='Manual CIS'", (session_id,))
        if manual_events is not None and not manual_events.empty:
            clean = manual_events.copy().dropna(how="all")
            for r in clean.itertuples(index=False):
                if pd.isna(r.bt):
                    continue
                con.execute(
                    """INSERT INTO roast_events
                       (roast_session_id,event_name,bt,et,time_s,gas,airflow,drum,source)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (session_id, "Manual Setting", float(r.bt), None, None,
                     None if pd.isna(r.gas) else float(r.gas),
                     None if pd.isna(r.airflow) else float(r.airflow),
                     None, "Manual CIS"),
                )


def render_existing_roast_overview(current: dict[str, Any]) -> None:
    curves = current.get("curves")
    if curves is not None and not curves.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=curves["time_s"], y=curves["bt"], name="BT", mode="lines"))
        if curves["et"].notna().any():
            fig.add_trace(go.Scatter(x=curves["time_s"], y=curves["et"], name="ET", mode="lines"))
        milestones = current.get("milestones")
        if milestones is not None and not milestones.empty:
            for row in milestones.itertuples(index=False):
                if pd.notna(row.time_s) and row.milestone in {"Dry End", "First Crack", "Drop"}:
                    fig.add_vline(x=float(row.time_s), line_dash="dash", opacity=0.5)
                    fig.add_annotation(x=float(row.time_s), y=1, yref="paper", text=row.milestone, showarrow=False)
        fig.update_layout(height=430, xaxis_title="Time from Charge (s)", yaxis_title="Temperature (°C)", margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig, width="stretch")

    milestones = current.get("milestones")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Milestones")
        if milestones is not None and not milestones.empty:
            view = milestones.copy()
            view["Time"] = view["time_s"].apply(fmt_time)
            view = view.rename(columns={"milestone":"Milestone", "bt":"BT", "et":"ET"})[["Milestone","Time","BT","ET"]]
            st.dataframe(view, width="stretch", hide_index=True)
        else:
            st.caption("No milestone data stored.")
    with right:
        st.markdown("#### Physical Result")
        physical = pd.DataFrame([
            ["Green weight", current.get("green_weight_g"), "g"],
            ["Roasted weight", current.get("roasted_weight_g"), "g"],
            ["Weight loss", current.get("weight_loss_pct"), "%"],
            ["Yield", current.get("yield_pct"), "%"],
            ["Density", current.get("density"), "g/L"],
            ["Moisture", current.get("moisture"), "%"],
        ], columns=["Parameter","Value","Unit"])
        st.dataframe(physical, width="stretch", hide_index=True)


def render_existing_roast_editor(roast_id: str) -> None:
    current = load_roast_for_edit(roast_id)
    if not current:
        st.error("Existing roast tidak dapat dibuka.")
        return
    st.markdown("### Existing Roast")
    st.caption("Edit metadata atau lengkapi event manual tanpa membuat record baru.")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Roast ID", current["roast_id"])
    e2.metric("Date", current["roast_date"] or "—")
    e3.metric("Species", current["species"] or "Unknown")
    e4.metric("Origin", current["origin"] or "Unknown")

    render_existing_roast_overview(current)

    with st.form(f"edit_existing_{roast_id}"):
        c1, c2, c3, c4, c5 = st.columns(5)
        species_options = ["Arabica", "Robusta", "Unknown"]
        species_value = current["species"] if current["species"] in species_options else "Unknown"
        species = c1.selectbox("Species", species_options, index=species_options.index(species_value))
        bean_name = c2.text_input("Bean name", value=current["bean_name"] or current["title"] or "Unknown Bean")
        origin = c3.text_input("Origin", value=current["origin"] or "Unknown")
        process = c4.text_input("Process", value=current["process"] or "Unknown")
        supplier = c5.text_input("Supplier", value=current["supplier"] or "Unknown")

        c6, c7, c8, c9 = st.columns(4)
        lot = c6.text_input("Lot", value=current["lot"] or "")
        purpose_options = ["Filter", "Espresso", "Latte", "Tubruk", "Blend Component", "Sample Roast", "Experimental", "Other"]
        purpose_value = current["roast_purpose"] if current["roast_purpose"] in purpose_options else "Experimental"
        purpose = c7.selectbox("Roast purpose", purpose_options, index=purpose_options.index(purpose_value))
        blend_project = c8.text_input("Blend project", value=current["blend_project"] or "")
        profile_version = c9.text_input("Profile / version", value=current["profile_version"] or current["title"] or "")

        c10, c11, c12 = st.columns(3)
        drum_speed = c10.number_input("Drum speed (rpm)", min_value=0.0, value=float(current["drum_speed_rpm"] or 90), step=1.0)
        agtron = c11.number_input("Agtron (optional)", min_value=0.0, value=float(current["agtron"] or 0), step=0.5)
        quality_options = ["Complete", "Usable", "Limited"]
        quality_value = current["data_quality"] if current["data_quality"] in quality_options else "Usable"
        quality = c12.selectbox("Data quality", quality_options, index=quality_options.index(quality_value))
        notes = st.text_area("Roast note (optional)", value=current["notes"] or "")

        st.markdown("#### Manual Actual Events — based on BT")
        existing_events = current["manual_events"]
        if existing_events.empty:
            existing_events = pd.DataFrame({"bt": [110.0, 130.0, 150.0], "gas": [None, None, None], "airflow": [None, None, None]})
        edited_events = st.data_editor(
            existing_events,
            num_rows="dynamic",
            width='stretch',
            hide_index=True,
            column_config={
                "bt": st.column_config.NumberColumn("BT °C", min_value=0.0, step=1.0, required=True),
                "gas": st.column_config.NumberColumn("Gas mbar", min_value=0.0, step=5.0),
                "airflow": st.column_config.NumberColumn("Air %", min_value=0.0, max_value=100.0, step=5.0),
            },
        )
        submitted = st.form_submit_button("Update Existing Roast", type="primary")
        if submitted:
            try:
                edited_events = edited_events.dropna(how="all")
                if not edited_events.empty:
                    edited_events = edited_events.sort_values("bt")
                update_existing_roast(roast_id, {
                    "bean_name": bean_name.strip(), "species": species, "origin": origin.strip(), "process": process.strip(),
                    "supplier": supplier.strip() or "Unknown", "lot": lot.strip(), "purpose": purpose,
                    "blend_project": blend_project.strip(), "profile_version": profile_version.strip(),
                    "drum_speed": drum_speed, "agtron": None if agtron == 0 else agtron,
                    "notes": notes.strip(), "quality": quality,
                }, edited_events)
                st.success(f"Existing roast updated: {roast_id}")
            except Exception as exc:
                st.error(str(exc))


def roast_chart(parsed: ParsedRoast) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=parsed.curves["time_s"], y=parsed.curves["bt"], name="BT", mode="lines"))
    if parsed.curves["et"].notna().any():
        fig.add_trace(go.Scatter(x=parsed.curves["time_s"], y=parsed.curves["et"], name="ET", mode="lines"))
    for label, key in [("Dry End", "dry_time"), ("FC", "fc_time"), ("Drop", "drop_time")]:
        t = parsed.summary.get(key)
        if t is not None:
            fig.add_vline(x=t, line_dash="dash", annotation_text=label)
    fig.update_layout(height=480, xaxis_title="Time from Charge (s)", yaxis_title="Temperature (°C)", margin=dict(l=10, r=10, t=35, b=10))
    return fig


def app() -> None:
    if FULL_MODE:
        init_db()

    st.title("🔥 Roast Profile")
    st.caption("CIS Roast Log V0.4.4 — integrated module for roast import, database exploration, and profile review.")

    if FULL_MODE:
        st.success(
            "💻 FULL MODE — database SQLite lokal aktif. "
            "Import, penyimpanan, database, edit data, dan grafik tersedia."
        )
    else:
        st.info(
            "📱 FALLBACK MODE — berjalan di Streamlit Cloud. "
            "Single .alog dapat dipreview, tetapi penyimpanan permanen, Bulk Import, "
            "dan Roast Database utama hanya tersedia dari laptop / Remote."
        )

    page = st.radio(
        "Roast Profile Menu",
        ["Home", "Import Roast", "Bulk Import", "Roast Database"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if page == "Home":
        if FULL_MODE:
            with db() as con:
                roasts = con.execute("SELECT COUNT(*) FROM roast_sessions").fetchone()[0]
                arabica = con.execute(
                    "SELECT COUNT(*) FROM roast_sessions rs "
                    "JOIN green_beans gb ON gb.id=rs.bean_id WHERE gb.species='Arabica'"
                ).fetchone()[0]
                robusta = con.execute(
                    "SELECT COUNT(*) FROM roast_sessions rs "
                    "JOIN green_beans gb ON gb.id=rs.bean_id WHERE gb.species='Robusta'"
                ).fetchone()[0]
                origins = con.execute(
                    "SELECT COUNT(DISTINCT origin) FROM green_beans "
                    "WHERE origin IS NOT NULL AND origin<>'' AND origin<>'Unknown'"
                ).fetchone()[0]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Roast Logs", roasts)
            c2.metric("Arabica Logs", arabica)
            c3.metric("Robusta Logs", robusta)
            c4.metric("Total Origins", origins)
            st.info("Use Import Roast for daily files and Bulk Import for your historical .alog archive.")
        else:
            st.markdown("### Mobile Preview")
            st.write(
                "Gunakan **Import Roast** untuk membuka satu file Artisan `.alog` "
                "dan melihat kurva, milestone, physical result, serta event roast."
            )
            st.warning(
                "Data yang dipreview di Fallback Mode tidak disimpan ke database utama. "
                "Gunakan CIS dari laptop atau Remote untuk Save Roast, Bulk Import, "
                "Roast Database, dan edit permanen."
            )
        return

    if page == "Bulk Import":
        if not FULL_MODE:
            st.warning(
                "Bulk Import dinonaktifkan pada Fallback Mode karena hasilnya harus "
                "disimpan langsung ke database lokal laptop."
            )
            st.info("Buka CIS melalui laptop / Remote untuk melakukan Bulk Import.")
            return
        render_bulk_import()
        return

    if page == "Roast Database":
        if not FULL_MODE:
            st.warning(
                "Roast Database utama berada di laptop dan tidak disalin ke Streamlit Cloud."
            )
            st.info("Buka CIS melalui laptop / Remote untuk melihat dan mengedit database.")
            return
        with db() as con:
            df = pd.read_sql_query(
                """SELECT rs.roast_id,rs.roast_date,gb.species,gb.origin,rs.title,gb.bean_name,gb.process,gb.supplier,gb.lot,
                          rs.roast_purpose,rs.drum_speed_rpm,rs.green_weight_g,rs.weight_loss_pct,rs.agtron
                   FROM roast_sessions rs LEFT JOIN green_beans gb ON gb.id=rs.bean_id ORDER BY rs.id DESC""",
                con,
            )
        total = len(df)
        arabica = int((df["species"] == "Arabica").sum()) if not df.empty else 0
        robusta = int((df["species"] == "Robusta").sum()) if not df.empty else 0
        origins = int(df.loc[df["origin"].notna() & ~df["origin"].isin(["", "Unknown"]), "origin"].nunique()) if not df.empty else 0
        oldest = df["roast_date"].dropna().min() if not df.empty and df["roast_date"].notna().any() else "—"
        newest = df["roast_date"].dropna().max() if not df.empty and df["roast_date"].notna().any() else "—"

        st.subheader("Roast Database Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Roast Logs", total)
        m2.metric("Arabica Logs", arabica)
        m3.metric("Robusta Logs", robusta)
        m4.metric("Total Origins", origins)
        m5, m6 = st.columns(2)
        m5.metric("Oldest Roast", oldest)
        m6.metric("Newest Roast", newest)

        if not df.empty:
            a = (df[df["species"] == "Arabica"].groupby("origin").size().reset_index(name="roast_logs").sort_values("roast_logs", ascending=False))
            r = (df[df["species"] == "Robusta"].groupby("origin").size().reset_index(name="roast_logs").sort_values("roast_logs", ascending=False))
            yearly = df.copy()
            yearly["year"] = yearly["roast_date"].astype(str).str[:4]
            yearly = yearly[yearly["year"].str.fullmatch(r"\d{4}", na=False)].groupby("year").size().reset_index(name="roast_logs").sort_values("year")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("#### Arabica by Origin")
                st.dataframe(a, hide_index=True, width='stretch', height=280)
            with c2:
                st.markdown("#### Robusta by Origin")
                st.dataframe(r, hide_index=True, width='stretch', height=280)
            with c3:
                st.markdown("#### Roast Logs by Year")
                st.dataframe(yearly, hide_index=True, width='stretch', height=280)

        st.markdown("#### Find Roast Logs")
        f1, f2, f3 = st.columns([2, 1, 1])
        search = f1.text_input("Search title / bean / roast ID", placeholder="e.g. Gayo, Tirtoyudo, RST2025...")
        species_filter = f2.selectbox("Species", ["All", "Arabica", "Robusta", "Unknown"])
        origin_options = ["All"] + sorted([x for x in df["origin"].dropna().unique().tolist() if x])
        origin_filter = f3.selectbox("Origin", origin_options)
        shown = df.copy()
        if search:
            mask = (
                shown["roast_id"].astype(str).str.contains(search, case=False, na=False)
                | shown["title"].astype(str).str.contains(search, case=False, na=False)
                | shown["bean_name"].astype(str).str.contains(search, case=False, na=False)
            )
            shown = shown[mask]
        if species_filter != "All":
            shown = shown[shown["species"] == species_filter]
        if origin_filter != "All":
            shown = shown[shown["origin"] == origin_filter]
        st.caption(f"Showing {len(shown)} of {len(df)} roast logs")
        st.dataframe(shown, width='stretch', hide_index=True)

        st.markdown("#### Open Roast Detail")
        if shown.empty:
            st.info("No roast log matches the current filter.")
        else:
            detail_options = shown[["roast_id", "roast_date", "title"]].copy()
            detail_options["label"] = detail_options.apply(
                lambda r: f"{r['roast_id']} | {r['roast_date'] or '—'} | {r['title'] or 'Untitled'}", axis=1
            )
            labels = detail_options["label"].tolist()
            label_to_id = dict(zip(detail_options["label"], detail_options["roast_id"]))
            selected_label = st.selectbox(
                "Select a roast from the filtered result",
                labels,
                key="db_roast_detail_selector",
            )
            b_open, b_close = st.columns([1, 1])
            if b_open.button("Open Roast", type="primary", width="stretch"):
                st.session_state["db_open_roast_id"] = label_to_id[selected_label]
            if b_close.button("Close Detail", width="stretch"):
                st.session_state.pop("db_open_roast_id", None)

            open_roast_id = st.session_state.get("db_open_roast_id")
            visible_ids = set(shown["roast_id"].astype(str).tolist())
            if open_roast_id and open_roast_id in visible_ids:
                st.divider()
                st.markdown("## Roast Detail")
                render_existing_roast_editor(open_roast_id)
            elif open_roast_id and open_roast_id not in visible_ids:
                st.info("The opened roast is outside the current filter. Adjust the filter or close the detail.")
        return

    uploaded = st.file_uploader("Upload Artisan .alog", type=["alog"])
    if not uploaded:
        st.info("Choose one .alog file to begin.")
        return
    try:
        parsed = parse_alog(uploaded.name, uploaded.getvalue())
    except ValueError as exc:
        st.error(str(exc))
        return

    duplicate = existing_checksum(parsed.checksum)
    if duplicate:
        st.warning(f"Duplicate detected: already saved as {duplicate[0]} — {duplicate[1]}")
        with st.expander("Open / Edit Existing Roast", expanded=True):
            render_existing_roast_editor(duplicate[0])
        st.info("This file already exists. Use Update Existing Roast above to revise metadata or manual events.")
        return

    s = parsed.summary
    inferred = infer_single_identity(s.get("title") or uploaded.name, s.get("roast_date"))
    st.subheader("Import Preview")
    a, b, c, d = st.columns(4)
    a.metric("Title", s.get("title") or "—")
    b.metric("Date", s.get("roast_date") or "—")
    c.metric("Total Time", fmt_time(s.get("total_time")))
    d.metric("DTR", f"{s.get('dtr_pct'):.1f}%" if s.get("dtr_pct") is not None else "—")

    st.plotly_chart(roast_chart(parsed), width='stretch')

    milestones = pd.DataFrame([
        ["Charge", "0:00", s.get("charge_bt"), s.get("charge_et")],
        ["Turning Point", fmt_time(s.get("tp_time")), s.get("tp_bt"), s.get("tp_et")],
        ["Dry End", fmt_time(s.get("dry_time")), s.get("dry_bt"), s.get("dry_et")],
        ["First Crack", fmt_time(s.get("fc_time")), s.get("fc_bt"), s.get("fc_et")],
        ["FC End", fmt_time(s.get("fce_time")), s.get("fce_bt"), s.get("fce_et")],
        ["Drop", fmt_time(s.get("drop_time")), s.get("drop_bt"), s.get("drop_et")],
    ], columns=["Milestone", "Time", "BT", "ET"])
    x, y = st.columns(2)
    with x:
        st.markdown("#### Milestones")
        st.dataframe(milestones, width='stretch', hide_index=True)
    with y:
        st.markdown("#### Physical Result")
        physical = pd.DataFrame([
            ["Green weight", s.get("green_weight_g"), "g"],
            ["Roasted weight", s.get("roasted_weight_g"), "g"],
            ["Weight loss", s.get("weight_loss_pct"), "%"],
            ["Yield", s.get("yield_pct"), "%"],
            ["Density", s.get("density"), "g/L"],
            ["Moisture", s.get("moisture"), "%"],
        ], columns=["Parameter", "Value", "Unit"])
        st.dataframe(physical, width='stretch', hide_index=True)

    st.markdown("#### Bean & Roast Identity")
    c1, c2, c3, c4, c5a = st.columns(5)
    species_options = ["Arabica", "Robusta", "Unknown"]
    species_default = inferred.get("species", "Unknown")
    species = c1.selectbox("Species", species_options, index=species_options.index(species_default) if species_default in species_options else 2)
    bean_name = c2.text_input("Bean name", value=inferred.get("bean_name") or (s.get("title") or "Unknown Bean"))
    origin = c3.text_input("Origin", value=inferred.get("origin") or "Unknown")
    process = c4.text_input("Process", value=inferred.get("process") or "Unknown")
    supplier = c5a.text_input("Supplier", value=inferred.get("supplier") or "Unknown")
    c5, c6, c7, c8 = st.columns(4)
    lot = c5.text_input("Lot", value=inferred.get("lot") or f"LEGACY-{(s.get('roast_date') or '0000')[:4]}")
    purpose_options = ["Filter", "Espresso", "Latte", "Tubruk", "Blend Component", "Sample Roast", "Experimental", "Other"]
    inferred_purpose = inferred.get("purpose", "Experimental")
    purpose = c6.selectbox("Roast purpose", purpose_options, index=purpose_options.index(inferred_purpose) if inferred_purpose in purpose_options else 6)
    blend_project = c7.text_input("Blend project", value=inferred.get("blend_project") or "")
    profile_version = c8.text_input("Profile / version", value=inferred.get("profile_version") or s.get("title") or "")

    c9, c10, c11 = st.columns(3)
    drum_speed = c9.number_input("Drum speed (rpm)", min_value=0.0, value=float(s.get("drum_speed") or 90), step=1.0)
    agtron = c10.number_input("Agtron (optional)", min_value=0.0, value=0.0, step=0.5)
    quality = c11.selectbox("Data quality", ["Complete", "Usable", "Limited"], index=0 if not parsed.events.empty else 1)
    notes = st.text_area("Roast note (optional)")

    st.markdown("#### Artisan Events")
    if parsed.events.empty:
        st.caption("No machine events detected in Artisan.")
    else:
        st.dataframe(parsed.events, width='stretch', hide_index=True)

    st.markdown("#### Manual Actual Events — based on BT")
    default_manual = pd.DataFrame({"bt": [110.0, 130.0, 150.0], "gas": [None, None, None], "airflow": [None, None, None]})
    manual = st.data_editor(
        default_manual,
        num_rows="dynamic",
        width='stretch',
        hide_index=True,
        column_config={
            "bt": st.column_config.NumberColumn("BT °C", min_value=0.0, step=1.0, required=True),
            "gas": st.column_config.NumberColumn("Gas mbar", min_value=0.0, step=5.0),
            "airflow": st.column_config.NumberColumn("Air %", min_value=0.0, max_value=100.0, step=5.0),
        },
    )
    manual = manual.dropna(how="all")
    if not manual.empty:
        manual = manual.sort_values("bt")

    if FULL_MODE:
        if st.button("Save Roast", type="primary", disabled=bool(duplicate)):
            try:
                roast_id = save_roast(parsed, {
                    "bean_name": bean_name.strip(), "species": species, "origin": origin.strip(), "process": process.strip(),
                    "supplier": supplier.strip() or "Unknown", "lot": lot.strip(), "purpose": purpose,
                    "blend_project": blend_project.strip(), "profile_version": profile_version.strip(),
                    "drum_speed": drum_speed, "agtron": None if agtron == 0 else agtron,
                    "notes": notes.strip(), "quality": quality,
                }, manual)
                st.success(f"Roast saved successfully: {roast_id}")
            except Exception as exc:
                st.error(str(exc))
    else:
        st.warning(
            "Preview selesai. Tombol **Save Roast** tidak tersedia pada Fallback Mode "
            "agar database utama tetap hanya berada di laptop."
        )


# Streamlit multipage: jalankan halaman langsung saat file dibuka dari folder pages.
app()
