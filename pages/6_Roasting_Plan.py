from __future__ import annotations

import html
import json
import re

import pandas as pd
import streamlit as st

from utils.cis_theme import apply_cis_theme
import utils.roasting_plan_database as rpdb

st.set_page_config(page_title="Roasting Plan", page_icon="🔥", layout="wide")
apply_cis_theme()

st.markdown("""
<style>
.plan-hero,.guide-card,.phase-card{border:1px solid rgba(92,255,174,.28);border-radius:18px;background:linear-gradient(180deg,rgba(13,35,25,.94),rgba(7,22,15,.94));box-shadow:0 0 16px rgba(72,245,163,.10)}
.plan-hero{padding:1.25rem 1.35rem;margin-bottom:1rem}.plan-kicker{color:#95ffd0;font-size:.76rem;letter-spacing:.16em;font-weight:800}.guide-card{padding:1.2rem 1.3rem;margin:.7rem 0}.phase-card{padding:1rem 1.1rem;margin:.65rem 0}.phase-title{color:#95ffd0;font-size:1.15rem;font-weight:800;margin-bottom:.45rem}.phase-line{font-size:1rem;color:#f2fff7;line-height:1.72}.bt-em{font-size:1.32em;font-weight:900;color:#ffffff;letter-spacing:.01em}.ga-em{font-size:1.16em;font-weight:850;color:#eafff4;letter-spacing:.01em}.muted{color:#b8d2c1}.rating{color:#ffd75e;font-size:1.2rem}.guide-goal{font-size:1.08rem;color:#f2fff7;line-height:1.6}.s3{border-left:4px solid #95ffd0;padding-left:1rem}.stButton>button{border-radius:12px;font-weight:800}.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{color:#04150d!important;-webkit-text-fill-color:#04150d!important;opacity:1!important;text-shadow:none!important;background:linear-gradient(90deg,#37f3a5,#4cf0c7)!important;border:1px solid rgba(160,255,220,.75)!important;box-shadow:0 0 18px rgba(72,245,163,.22)!important}.stButton>button[kind="primary"] p,.stFormSubmitButton>button[kind="primary"] p{color:#04150d!important;-webkit-text-fill-color:#04150d!important;font-weight:850!important;opacity:1!important}.stButton>button:disabled,.stFormSubmitButton>button:disabled{opacity:.48!important;box-shadow:none!important}
@media(max-width:768px){.plan-hero{padding:1rem}.guide-card{padding:1rem}.phase-card{padding:.85rem}.phase-line{font-size:1rem}.bt-em{font-size:1.38em}.ga-em{font-size:1.20em}.block-container{padding-top:1rem!important}}
</style>
""", unsafe_allow_html=True)

try:
    rpdb.create_database()
except Exception as exc:
    st.error(f"Roasting Plan database belum siap: {exc}")
    st.stop()

st.caption(f"Roasting Plan page V10.23 · DB module V{getattr(rpdb, 'MODULE_VERSION', 'unknown')}")



def save_chaty_plan_direct(metadata: dict, plan_data: dict) -> str:
    """Save a brand-new Chaty plan directly, independent of older DB module save helpers."""
    ws = rpdb._worksheet()
    now = rpdb._now()
    plan_id = rpdb._generate_id()
    headers = list(getattr(rpdb, "HEADERS", []))
    if not headers:
        raise RuntimeError("Header database Roasting Plan tidak ditemukan.")

    record = {
        "plan_id": plan_id,
        "plan_name": metadata.get("plan_name", ""),
        "bean": metadata.get("bean", ""),
        "purpose": metadata.get("purpose", ""),
        "goal": metadata.get("goal", ""),
        "status": metadata.get("status", "Draft"),
        "batch_size_g": float(metadata.get("batch_size_g") or 0),
        "density": float(metadata.get("density") or 0),
        "moisture": float(metadata.get("moisture") or 0),
        "plan_json": json.dumps(plan_data, ensure_ascii=False),
        "rating": 0,
        "usage_count": 0,
        "last_used_at": "",
        "result_notes": "",
        "cupping_notes": "",
        "created_at": now,
        "updated_at": now,
        "source": metadata.get("source") or "Chaty Import",
    }
    row = [record.get(header, "") for header in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")
    return plan_id

PHASES = ["Preheat", "Drying", "Maillard", "First Crack", "Development", "Drop"]
PURPOSES = ["Filter", "Espresso", "Latte", "Tubruk", "Blend Component", "Experimental", "Other"]
STATUSES = ["Draft", "Trial", "Recommended", "Locked", "Archived"]

DEFAULT_PHASES = {
    "Preheat": {
        "bt": "200°C",
        "gas": "",
        "air": "40",
        "drum": "90",
        "target_time": "",
        "steps": "Charge 500 g\nCharge → G45 · A40",
        "notes": "Stabilkan suhu sekitar 2–3 menit sebelum charge.",
    },
    "Drying": {
        "bt": "147–149°C",
        "gas": "",
        "air": "",
        "drum": "90",
        "target_time": "4:05–4:20",
        "steps": "Charge → G45 · A40\nTP → G55 · A40\nBT110 → G65 · A40\nBT130 → G65 · A50\nDry End → BT 147–149°C @ 4:05–4:20",
        "notes": "Jaga momentum drying tetap stabil. Koreksi hanya bila keluar dari rentang target.",
    },
    "Maillard": {
        "bt": "150–185°C",
        "gas": "60→45",
        "air": "60→80",
        "drum": "90",
        "target_time": "Dry End → FC 4:15–4:30",
        "steps": "BT150 → G60 · A60\nBT170 → G50 · A70\nBT185 → G45 · A80\nTarget FC → BT 194–195°C @ 8:30–8:50",
        "notes": "Bangun sweetness tanpa menahan energi terlalu lama. Jaga RoR turun bertahap dan hindari perubahan bertumpuk.",
    },
    "First Crack": {
        "bt": "194–195°C",
        "gas": "25",
        "air": "90",
        "drum": "90",
        "target_time": "8:30–8:50",
        "steps": "FC mulai → G25 · A90\nKonfirmasi crack terdengar jelas dan merata\nMulai hitung development dari FC yang valid",
        "notes": "Jangan bereaksi pada satu-dua crack awal. Pastikan FC benar-benar mulai sebelum menghitung development.",
    },
    "Development": {
        "bt": "194–203°C",
        "gas": "25",
        "air": "90",
        "drum": "90",
        "target_time": "1:15–1:35 · DTR 13–15%",
        "steps": "Pertahankan G25 · A90\nPantau RoR tetap menurun halus\nJangan tambah gas kecuali roast benar-benar kehilangan momentum",
        "notes": "Fokus pada kestabilan, bukan mengejar angka setiap beberapa detik. Koreksi kecil hanya bila keluar dari rentang.",
    },
    "Drop": {
        "bt": "202.5–203.5°C",
        "gas": "0",
        "air": "100",
        "drum": "90",
        "target_time": "±9:45–10:25",
        "steps": "Drop pada target BT / development\nGas 0 · masuk cooling penuh\nCatat total time, DTR, weight loss, Agtron, dan respons aroma",
        "notes": "Prioritaskan target sensori dan development. Jangan memperpanjang roast hanya demi mengejar satu angka.",
    },
}


def phase_form(phase: str, values: dict, key_prefix: str) -> dict:
    st.markdown(f"#### {phase}")
    c1, c2, c3, c4 = st.columns(4)
    bt = c1.text_input("BT / Target BT", value=str(values.get("bt", "")), key=f"{key_prefix}_{phase}_bt")
    gas = c2.text_input("Gas (G)", value=str(values.get("gas", "")), key=f"{key_prefix}_{phase}_gas")
    air = c3.text_input("Airflow (A)", value=str(values.get("air", "")), key=f"{key_prefix}_{phase}_air")
    drum = c4.text_input("Drum rpm", value=str(values.get("drum", "")), key=f"{key_prefix}_{phase}_drum")
    target_time = st.text_input("Target waktu / rentang", value=str(values.get("target_time", "")), key=f"{key_prefix}_{phase}_time", placeholder="Contoh 4:10–4:25")
    steps = st.text_area("Juklak / checkpoint manual", value=str(values.get("steps", "")), key=f"{key_prefix}_{phase}_steps", height=110, placeholder="Satu checkpoint per baris. Contoh: BT110 → G60 · A40")
    notes = st.text_area("Attention", value=str(values.get("notes", "")), key=f"{key_prefix}_{phase}_notes", height=80)
    return {"bt": bt, "gas": gas, "air": air, "drum": drum, "target_time": target_time, "steps": steps, "notes": notes}


def stars(value: float) -> str:
    full = int(value)
    half = value - full >= .5
    return "★" * full + ("½" if half else "") + "☆" * max(0, 5 - full - (1 if half else 0))


def esc(value) -> str:
    return html.escape(str(value or "—")).replace("\n", "<br>")


def roast_text(value) -> str:
    """Escape text, then enlarge BT tokens and G/A settings for Guide Mode readability."""
    safe = html.escape(str(value or "—")).replace("\n", "<br>")
    safe = re.sub(
        r"\bBT\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–-]\s*[0-9]+(?:[.,][0-9]+)?)?\s*°?C?)",
        r'<span class="bt-em">BT \1</span>',
        safe,
        flags=re.IGNORECASE,
    )
    safe = re.sub(
        r"\b([GA])\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–-]\s*[0-9]+(?:[.,][0-9]+)?)?)",
        r'<span class="ga-em">\1\2</span>',
        safe,
        flags=re.IGNORECASE,
    )
    return safe


def compact_line(p: dict) -> str:
    parts = []
    if p.get("bt"): parts.append(f"BT {p.get('bt')}")
    if p.get("gas"): parts.append(f"G{p.get('gas')}")
    if p.get("air"): parts.append(f"A{p.get('air')}")
    if p.get("drum"): parts.append(f"Drum {p.get('drum')} rpm")
    if p.get("target_time"): parts.append(f"@ {p.get('target_time')}")
    return " · ".join(parts)


def render_practical_summary(plan: dict) -> None:
    data = plan.get("plan_data", {})
    phases = data.get("phases", {})
    preheat = phases.get("Preheat", {})
    drying = phases.get("Drying", {})
    maillard = phases.get("Maillard", {})
    fc = phases.get("First Crack", {})
    development = phases.get("Development", {})
    drop = phases.get("Drop", {})

    st.markdown(f"""
    <div class="guide-card">
      <div class="plan-kicker">JUKLAK PRAKTIS S³ · BUKA SAAT ROASTING</div>
      <div class="phase-line"><strong>1 · PREHEAT / CHARGE</strong><br>{roast_text(compact_line(preheat))}<br>{esc(preheat.get('notes'))}</div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>2 · DRYING GATES</strong><br>{roast_text(drying.get('steps'))}<br><span class="muted">Target: {roast_text(compact_line(drying))}</span></div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>3 · MAILLARD GATES</strong><br>{roast_text(maillard.get('steps'))}<br><span class="muted">Target: {roast_text(compact_line(maillard))}</span></div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>4 · FIRST CRACK → DEVELOPMENT</strong><br>FC: {roast_text(compact_line(fc))}<br>DEV: {roast_text(compact_line(development))}</div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>5 · DROP / COOLING</strong><br>{roast_text(compact_line(drop))}<br>{roast_text(drop.get('steps'))}</div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>S³ CONTROL</strong><br>{esc(data.get('s3_attention'))}</div>
    </div>
    """, unsafe_allow_html=True)


def render_guide(plan: dict) -> None:
    data = plan.get("plan_data", {})
    st.markdown(f"""
    <div class="guide-card">
      <div class="plan-kicker">S³ ROASTING GUIDE · {esc(plan.get('plan_id'))}</div>
      <h2 style="margin:.35rem 0 .2rem">🔥 {esc(plan.get('plan_name'))}</h2>
      <div class="muted">{esc(plan.get('bean'))} · {esc(plan.get('purpose'))} · Status: {esc(plan.get('status'))}</div>
      <div class="rating">{stars(float(plan.get('rating') or 0))} &nbsp; {float(plan.get('rating') or 0):.1f}/5</div>
    </div>
    <div class="guide-card">
      <div class="phase-title">GOAL</div><div class="guide-goal">{esc(plan.get('goal'))}</div>
      <div class="muted" style="margin-top:.6rem">Batch {plan.get('batch_size_g',0):g} g · Density {plan.get('density',0):g} g/L · Moisture {plan.get('moisture',0):g}%</div>
    </div>
    """, unsafe_allow_html=True)

    render_practical_summary(plan)

    phases = data.get("phases", {})
    st.markdown("### Detail Lengkap per Fase")
    for phase in PHASES:
        p = phases.get(phase, {})
        headline = " · ".join(x for x in [f"BT {p.get('bt')}" if p.get('bt') else "", f"G{p.get('gas')}" if p.get('gas') else "", f"A{p.get('air')}" if p.get('air') else "", f"Drum {p.get('drum')} rpm" if p.get('drum') else "", f"@ {p.get('target_time')}" if p.get('target_time') else ""] if x)
        st.markdown(f"""
        <div class="phase-card">
          <div class="phase-title">{esc(phase).upper()}</div>
          <div class="phase-line"><strong>{roast_text(headline)}</strong></div>
          <div class="phase-line">{roast_text(p.get('steps'))}</div>
          <div class="muted"><strong>Attention:</strong> {esc(p.get('notes'))}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="guide-card s3">
      <div class="phase-title">S³ ATTENTION</div>
      <div class="phase-line">{esc(data.get('s3_attention'))}</div>
      <div class="muted"><strong>Roast terlalu cepat:</strong> {esc(data.get('too_fast'))}</div>
      <div class="muted"><strong>Roast tertinggal:</strong> {esc(data.get('too_slow'))}</div>
    </div>
    """, unsafe_allow_html=True)


def _clean_value(value: str) -> str:
    return value.strip().strip("`*-• ")


def _extract_chaty_block(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(
        r"\[CIS\s+ROASTING\s+PLAN\](.*?)\[/CIS\s+ROASTING\s+PLAN\]",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else text.strip()


def _first_number(value: str) -> float:
    match = re.search(r"-?\d+(?:[.,]\d+)?", value or "")
    return float(match.group(0).replace(",", ".")) if match else 0.0


def parse_chaty_plan(raw_text: str) -> dict:
    body = _extract_chaty_block(raw_text)
    if not body:
        raise ValueError("Teks Roasting Plan masih kosong.")

    section_aliases = {
        "PREHEAT": "Preheat",
        "CHARGE": "Preheat",
        "DRYING": "Drying",
        "MAILLARD": "Maillard",
        "FIRST CRACK": "First Crack",
        "FC": "First Crack",
        "DEVELOPMENT": "Development",
        "DEV": "Development",
        "DROP": "Drop",
        "DROP / COOLING": "Drop",
        "COOLING": "Drop",
        "S3 SUMMARY": "S3 Summary",
        "S³ SUMMARY": "S3 Summary",
        "S3 CONTROL": "S3 Summary",
        "S³ CONTROL": "S3 Summary",
        "ATTENTION": "Attention",
    }
    metadata_aliases = {
        "PLAN NAME": "plan_name",
        "NAME": "plan_name",
        "BEAN": "bean",
        "PURPOSE": "purpose",
        "ROAST PURPOSE": "purpose",
        "GOAL": "goal",
        "BATCH": "batch_size_g",
        "BATCH SIZE": "batch_size_g",
        "DENSITY": "density",
        "MOISTURE": "moisture",
        "STATUS": "status",
    }
    phase_key_aliases = {
        "BT": "bt",
        "TARGET BT": "bt",
        "GAS": "gas",
        "G": "gas",
        "AIR": "air",
        "AIRFLOW": "air",
        "A": "air",
        "DRUM": "drum",
        "DRUM RPM": "drum",
        "TARGET TIME": "target_time",
        "TIME": "target_time",
        "WAKTU": "target_time",
        "ATTENTION": "notes",
        "NOTES": "notes",
        "NOTE": "notes",
    }

    result = {
        "plan_name": "",
        "bean": "",
        "purpose": "Filter",
        "goal": "",
        "status": "Trial",
        "batch_size_g": 500.0,
        "density": 0.0,
        "moisture": 0.0,
        "source": "Chaty Import",
        "phases": {phase: {k: "" for k in ["bt", "gas", "air", "drum", "target_time", "steps", "notes"]} for phase in PHASES},
        "s3_attention": "",
        "too_fast": "",
        "too_slow": "",
    }

    current_section = None
    pending_metadata_field = None
    phase_step_lines = {phase: [] for phase in PHASES}
    s3_lines, attention_lines = [], []

    for raw_line in body.splitlines():
        line = _clean_value(raw_line)
        if not line:
            continue
        heading = re.sub(r"[:\s]+$", "", line).upper()

        # Mendukung dua format metadata Chaty:
        # BEAN: Arabika Gayo atau label BEAN diikuti nilai pada baris berikutnya
        if pending_metadata_field is not None:
            if pending_metadata_field in {"batch_size_g", "density", "moisture"}:
                result[pending_metadata_field] = _first_number(line)
            else:
                result[pending_metadata_field] = line
            pending_metadata_field = None
            continue

        if heading in section_aliases:
            current_section = section_aliases[heading]
            continue

        if current_section is None and heading in metadata_aliases:
            pending_metadata_field = metadata_aliases[heading]
            continue

        key_match = re.match(r"^([^:|]+?)\s*:\s*(.+)$", line)
        if current_section is None and key_match:
            key = key_match.group(1).strip().upper()
            value = _clean_value(key_match.group(2))
            field = metadata_aliases.get(key)
            if field:
                if field in {"batch_size_g", "density", "moisture"}:
                    result[field] = _first_number(value)
                else:
                    result[field] = value
                continue

        if current_section in PHASES:
            if key_match:
                key = key_match.group(1).strip().upper()
                value = _clean_value(key_match.group(2))
                field = phase_key_aliases.get(key)
                if field:
                    old = result["phases"][current_section].get(field, "")
                    result["phases"][current_section][field] = f"{old}\n{value}".strip() if old else value
                    continue
            phase_step_lines[current_section].append(line)
        elif current_section == "S3 Summary":
            s3_lines.append(line)
        elif current_section == "Attention":
            lower = line.lower()
            if "terlalu cepat" in lower:
                result["too_fast"] = line.split(":", 1)[1].strip() if ":" in line else line
            elif "tertinggal" in lower or "terlalu lambat" in lower:
                result["too_slow"] = line.split(":", 1)[1].strip() if ":" in line else line
            else:
                attention_lines.append(line)
        else:
            # Toleransi format Chaty tanpa tanda titik dua pada metadata.
            loose = re.match(r"^(PLAN NAME|BEAN|PURPOSE|GOAL|BATCH|DENSITY|MOISTURE|STATUS)\s+(.+)$", line, flags=re.IGNORECASE)
            if loose:
                field = metadata_aliases[loose.group(1).upper()]
                value = loose.group(2).strip()
                result[field] = _first_number(value) if field in {"batch_size_g", "density", "moisture"} else value

    for phase in PHASES:
        result["phases"][phase]["steps"] = "\n".join(phase_step_lines[phase]).strip()

    # Ekstraksi ringan dari checkpoint agar kartu ringkas tetap terisi.
    for phase, pdata in result["phases"].items():
        combined = "\n".join([pdata.get("steps", ""), pdata.get("target_time", ""), pdata.get("bt", "")])
        if not pdata.get("bt"):
            bt_match = re.search(r"(?:TARGET\s+BT|DROP\s+BT|DRY\s+END|FC).*?((?:\d{2,3}(?:[.,]\d+)?)\s*[–-]\s*(?:\d{2,3}(?:[.,]\d+)?)|\d{2,3}(?:[.,]\d+)?)\s*°?C?", combined, flags=re.IGNORECASE)
            if bt_match:
                pdata["bt"] = bt_match.group(1).replace(" ", "") + "°C"
        if not pdata.get("target_time"):
            time_match = re.search(r"\b(\d{1,2}:\d{2}\s*[–-]\s*\d{1,2}:\d{2}|\d{1,2}:\d{2})\b", combined)
            if time_match:
                pdata["target_time"] = time_match.group(1)

    result["s3_attention"] = "\n".join(s3_lines).strip() or (
        "Simple: ikuti perubahan hanya pada gate.\n"
        "Flexible: koreksi kecil bila roast keluar dari range.\n"
        "Sustainable: hindari adjustment berulang menjelang FC."
    )
    if attention_lines:
        result["s3_attention"] += "\n" + "\n".join(attention_lines)
    result["too_fast"] = result["too_fast"] or "Turunkan energi satu tingkat pada gate berikutnya; jangan melakukan koreksi bertumpuk."
    result["too_slow"] = result["too_slow"] or "Tahan setting atau koreksi kecil pada gate berikutnya; jangan mengejar dengan lonjakan gas besar."

    if not result["plan_name"]:
        result["plan_name"] = f"{result['bean'] or 'Roasting'} Plan"
    if result["purpose"] not in PURPOSES:
        result["purpose"] = "Other"
    if result["status"] not in STATUSES:
        result["status"] = "Trial"
    if not result["bean"] or not result["goal"]:
        raise ValueError("Blok Chaty minimal harus memuat BEAN dan GOAL.")
    return result


st.markdown("""
<div class="plan-hero"><div class="plan-kicker">CIS UTILITY · TABLET ROAST COMPANION</div>
<h1 style="margin:.25rem 0">🔥 Roasting Plan</h1>
<div class="muted">Manual Create atau Chaty Import → S³ Guide Mode → evaluate → rate → recall.</div></div>
""", unsafe_allow_html=True)

manual_tab, chaty_tab, library_tab = st.tabs(["✍ Create Manual", "🤖 Update Chaty", "📚 Plan Library"])

with manual_tab:
    existing = rpdb.get_all_plans()
    edit_options = {"➕ New Manual Plan": None}
    if not existing.empty:
        edit_options.update({f"Edit · {r.plan_id} · {r.plan_name}": r.plan_id for r in existing.itertuples(index=False)})
    selected_label = st.selectbox("Mode", list(edit_options.keys()), key="manual_mode")
    selected_id = edit_options[selected_label]
    current = rpdb.get_plan(selected_id) if selected_id else None
    pdata = (current or {}).get("plan_data", {})

    with st.form("roasting_plan_form"):
        c1, c2 = st.columns(2)
        with c1:
            plan_name = st.text_input("Plan Name", value=(current or {}).get("plan_name", ""))
            bean = st.text_input("Bean", value=(current or {}).get("bean", ""))
            purpose = st.selectbox("Roast Purpose", PURPOSES, index=PURPOSES.index((current or {}).get("purpose")) if (current or {}).get("purpose") in PURPOSES else 0)
            status = st.selectbox("Status", STATUSES, index=STATUSES.index((current or {}).get("status")) if (current or {}).get("status") in STATUSES else 0)
        with c2:
            batch_size = st.number_input("Batch Size (g)", min_value=0.0, value=float((current or {}).get("batch_size_g") or 500), step=50.0)
            density = st.number_input("Density (g/L)", min_value=0.0, value=float((current or {}).get("density") or 0), step=1.0)
            moisture = st.number_input("Moisture (%)", min_value=0.0, value=float((current or {}).get("moisture") or 0), step=.1)
        goal = st.text_area("Goal rasa / aroma / body / finish", value=(current or {}).get("goal", ""), height=100)
        if not current:
            st.info("Template awal memakai baseline Arabika Aroma yang editable. Ubah seluruh angka sesuai bean dan target roast aktual.")

        phases = {}
        stored_phases = pdata.get("phases", {})
        for phase in PHASES:
            with st.expander(phase, expanded=phase in ["Preheat", "Drying"]):
                phase_values = stored_phases.get(phase, {}) if current else DEFAULT_PHASES.get(phase, {})
                phases[phase] = phase_form(phase, phase_values, selected_id or "new_manual")

        st.markdown("#### S³ Control")
        s3_attention = st.text_area("S³ Attention", value=pdata.get("s3_attention", "Simple: perubahan hanya pada checkpoint.\nFlexible: koreksi hanya bila roast keluar dari rentang.\nSustainable: jangan mengejar angka dengan adjustment berulang."), height=110)
        cfast, cslow = st.columns(2)
        too_fast = cfast.text_area("Jika roast terlalu cepat", value=pdata.get("too_fast", ""), height=100)
        too_slow = cslow.text_area("Jika roast tertinggal", value=pdata.get("too_slow", ""), height=100)
        submitted = st.form_submit_button("💾 Save Manual Plan", type="primary", use_container_width=True)

    if submitted:
        if not plan_name.strip() or not bean.strip() or not goal.strip():
            st.error("Plan Name, Bean, dan Goal wajib diisi.")
        else:
            try:
                plan_id = rpdb.save_plan(
                    {"plan_name": plan_name.strip(), "bean": bean.strip(), "purpose": purpose, "goal": goal.strip(), "status": status, "batch_size_g": batch_size, "density": density, "moisture": moisture, "source": ((current or {}).get("source") or "Manual Plan")},
                    {"phases": phases, "s3_attention": s3_attention.strip(), "too_fast": too_fast.strip(), "too_slow": too_slow.strip()},
                    selected_id,
                )
                st.success(f"Roasting Plan tersimpan: {plan_id}")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menyimpan plan: {exc}")

with chaty_tab:
    if st.session_state.pop("clear_chaty_raw_text", False):
        st.session_state["chaty_raw_text"] = ""
    if st.session_state.get("chaty_save_success"):
        st.success(st.session_state.pop("chaty_save_success"))
    st.markdown("### Copy–paste Juklak Chaty")
    st.caption("Tempel blok `[CIS ROASTING PLAN] ... [/CIS ROASTING PLAN]`. CIS akan membaca isinya, lalu menampilkan preview editable sebelum disimpan ke library yang sama.")
    chaty_text = st.text_area(
        "Update Chaty",
        value=st.session_state.get("chaty_raw_text", ""),
        height=330,
        placeholder="[CIS ROASTING PLAN]\nPLAN NAME: ...\nBEAN: ...\nGOAL: ...\n...\n[/CIS ROASTING PLAN]",
        key="chaty_raw_text",
    )
    if st.button("🔎 Parse & Preview", type="primary", use_container_width=True):
        try:
            st.session_state["chaty_parsed_plan"] = parse_chaty_plan(chaty_text)
            st.success("Juklak berhasil dibaca. Periksa preview di bawah sebelum disimpan.")
        except Exception as exc:
            st.session_state.pop("chaty_parsed_plan", None)
            st.error(f"Gagal membaca juklak: {exc}")

    parsed = st.session_state.get("chaty_parsed_plan")
    if parsed:
        st.markdown("### Preview Editable")
        with st.form("chaty_import_form"):
            c1, c2 = st.columns(2)
            with c1:
                cp_name = st.text_input("Plan Name", value=parsed.get("plan_name", ""), key="chaty_plan_name")
                cp_bean = st.text_input("Bean", value=parsed.get("bean", ""), key="chaty_bean")
                cp_purpose = st.selectbox("Roast Purpose", PURPOSES, index=PURPOSES.index(parsed.get("purpose")) if parsed.get("purpose") in PURPOSES else 0, key="chaty_purpose")
                cp_status = st.selectbox("Status", STATUSES, index=STATUSES.index(parsed.get("status")) if parsed.get("status") in STATUSES else 1, key="chaty_status")
            with c2:
                cp_batch = st.number_input("Batch Size (g)", min_value=0.0, value=float(parsed.get("batch_size_g") or 500), step=50.0, key="chaty_batch")
                cp_density = st.number_input("Density (g/L)", min_value=0.0, value=float(parsed.get("density") or 0), step=1.0, key="chaty_density")
                cp_moisture = st.number_input("Moisture (%)", min_value=0.0, value=float(parsed.get("moisture") or 0), step=.1, key="chaty_moisture")
            cp_goal = st.text_area("Goal", value=parsed.get("goal", ""), height=100, key="chaty_goal")

            cp_phases = {}
            for phase in PHASES:
                with st.expander(phase, expanded=phase in ["Preheat", "Drying"]):
                    cp_phases[phase] = phase_form(phase, parsed.get("phases", {}).get(phase, {}), "chaty_import")

            cp_s3 = st.text_area("S³ Attention", value=parsed.get("s3_attention", ""), height=120, key="chaty_s3")
            cf, cs = st.columns(2)
            cp_fast = cf.text_area("Jika roast terlalu cepat", value=parsed.get("too_fast", ""), height=100, key="chaty_fast")
            cp_slow = cs.text_area("Jika roast tertinggal", value=parsed.get("too_slow", ""), height=100, key="chaty_slow")
            save_chaty = st.form_submit_button("🤖 Save Chaty Plan to Library", type="primary", use_container_width=True)

        if save_chaty:
            if not cp_name.strip() or not cp_bean.strip() or not cp_goal.strip():
                st.error("Plan Name, Bean, dan Goal wajib diisi.")
            else:
                try:
                    plan_id = save_chaty_plan_direct(
                        {"plan_name": cp_name.strip(), "bean": cp_bean.strip(), "purpose": cp_purpose, "goal": cp_goal.strip(), "status": cp_status, "batch_size_g": cp_batch, "density": cp_density, "moisture": cp_moisture, "source": "Chaty Import"},
                        {"phases": cp_phases, "s3_attention": cp_s3.strip(), "too_fast": cp_fast.strip(), "too_slow": cp_slow.strip()},
                    )
                    st.session_state.pop("chaty_parsed_plan", None)
                    st.session_state["clear_chaty_raw_text"] = True
                    st.session_state["chaty_save_success"] = f"Chaty Plan masuk Plan Library: {plan_id}"
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal menyimpan Chaty Plan: {exc}")

with library_tab:
    plans = rpdb.get_all_plans()
    if plans.empty:
        st.info("Belum ada Roasting Plan.")
    else:
        q1, q2, q3, q4 = st.columns([2,1,1,1])
        query = q1.text_input("Search", placeholder="Bean, plan, goal, purpose", key="library_search")
        purpose_filter = q2.selectbox("Purpose", ["All"] + sorted(plans["purpose"].dropna().astype(str).unique().tolist()), key="library_purpose")
        status_filter = q3.selectbox("Status", ["All"] + STATUSES, key="library_status")
        source_values = sorted(x for x in plans.get("source", pd.Series(dtype=str)).fillna("").astype(str).unique().tolist() if x)
        source_filter = q4.selectbox("Source", ["All"] + source_values, key="library_source")
        filtered = plans.copy()
        if query.strip():
            hay = filtered[["plan_name","bean","goal","purpose"]].fillna("").astype(str)
            mask = hay.apply(lambda col: col.str.contains(query.strip(), case=False, regex=False)).any(axis=1)
            filtered = filtered[mask]
        if purpose_filter != "All": filtered = filtered[filtered["purpose"] == purpose_filter]
        if status_filter != "All": filtered = filtered[filtered["status"] == status_filter]
        if source_filter != "All": filtered = filtered[filtered["source"] == source_filter]

        labels = {}
        for r in filtered.itertuples(index=False):
            source = getattr(r, "source", "") or "Manual Plan"
            badge = "🤖" if source == "Chaty Import" else "✍"
            labels[f"{badge} {r.plan_id} · {r.plan_name} · {r.bean} · ⭐ {float(r.rating):.1f}"] = r.plan_id
        if not labels:
            st.warning("Tidak ada plan yang cocok.")
        else:
            chosen = st.selectbox("Open Plan", list(labels.keys()), key="library_open")
            plan = rpdb.get_plan(labels[chosen])
            if plan:
                source = plan.get("source") or "Manual Plan"
                st.info(f"Source: {'🤖 Chaty Import' if source == 'Chaty Import' else '✍ Manual Plan'}")
                render_guide(plan)
                st.caption(f"Used {int(plan.get('usage_count') or 0)}× · Last used: {plan.get('last_used_at') or '—'} · Updated: {plan.get('updated_at') or '—'}")

                with st.expander("✏️ Edit Plan", expanded=False):
                    st.caption("Ralat langsung dari Plan Library. Save Changes akan memperbarui plan yang sama; rating, usage count, dan evaluation tetap dipertahankan.")
                    edit_data = plan.get("plan_data", {}) or {}
                    edit_phases_stored = edit_data.get("phases", {}) or {}
                    with st.form(f"library_edit_form_{plan['plan_id']}"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_name = st.text_input("Plan Name", value=str(plan.get("plan_name") or ""), key=f"lib_edit_name_{plan['plan_id']}")
                            e_bean = st.text_input("Bean", value=str(plan.get("bean") or ""), key=f"lib_edit_bean_{plan['plan_id']}")
                            current_purpose = str(plan.get("purpose") or PURPOSES[0])
                            e_purpose = st.selectbox("Roast Purpose", PURPOSES, index=PURPOSES.index(current_purpose) if current_purpose in PURPOSES else 0, key=f"lib_edit_purpose_{plan['plan_id']}")
                            current_status = str(plan.get("status") or "Draft")
                            e_status = st.selectbox("Status", STATUSES, index=STATUSES.index(current_status) if current_status in STATUSES else 0, key=f"lib_edit_status_{plan['plan_id']}")
                        with ec2:
                            e_batch = st.number_input("Batch Size (g)", min_value=0.0, value=float(plan.get("batch_size_g") or 0), step=50.0, key=f"lib_edit_batch_{plan['plan_id']}")
                            e_density = st.number_input("Density (g/L)", min_value=0.0, value=float(plan.get("density") or 0), step=1.0, key=f"lib_edit_density_{plan['plan_id']}")
                            e_moisture = st.number_input("Moisture (%)", min_value=0.0, value=float(plan.get("moisture") or 0), step=.1, key=f"lib_edit_moisture_{plan['plan_id']}")
                        e_goal = st.text_area("Goal", value=str(plan.get("goal") or ""), height=100, key=f"lib_edit_goal_{plan['plan_id']}")

                        e_phases = {}
                        for phase in PHASES:
                            with st.expander(phase, expanded=False):
                                vals = edit_phases_stored.get(phase, DEFAULT_PHASES.get(phase, {}))
                                e_phases[phase] = phase_form(phase, vals, f"libedit_{plan['plan_id']}")

                        e_s3 = st.text_area("S³ Attention", value=str(edit_data.get("s3_attention") or ""), height=110, key=f"lib_edit_s3_{plan['plan_id']}")
                        ef, es = st.columns(2)
                        e_fast = ef.text_area("Jika roast terlalu cepat", value=str(edit_data.get("too_fast") or ""), height=95, key=f"lib_edit_fast_{plan['plan_id']}")
                        e_slow = es.text_area("Jika roast tertinggal", value=str(edit_data.get("too_slow") or ""), height=95, key=f"lib_edit_slow_{plan['plan_id']}")
                        save_edit = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)

                    if save_edit:
                        if not e_name.strip() or not e_bean.strip() or not e_goal.strip():
                            st.error("Plan Name, Bean, dan Goal wajib diisi.")
                        else:
                            try:
                                rpdb.save_plan(
                                    {
                                        "plan_name": e_name.strip(),
                                        "bean": e_bean.strip(),
                                        "purpose": e_purpose,
                                        "goal": e_goal.strip(),
                                        "status": e_status,
                                        "batch_size_g": e_batch,
                                        "density": e_density,
                                        "moisture": e_moisture,
                                        "source": source,
                                    },
                                    {
                                        "phases": e_phases,
                                        "s3_attention": e_s3.strip(),
                                        "too_fast": e_fast.strip(),
                                        "too_slow": e_slow.strip(),
                                    },
                                    plan["plan_id"],
                                )
                                st.success(f"Plan berhasil diralat: {plan['plan_id']}")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Gagal meralat plan: {exc}")

                with st.expander("⭐ Rate & Evaluation", expanded=False):
                    with st.form("evaluation_form"):
                        rating = st.select_slider("Rating", options=[0,.5,1,1.5,2,2.5,3,3.5,4,4.5,5], value=float(plan.get("rating") or 0))
                        result_notes = st.text_area("Actual roast result", value=plan.get("result_notes") or "")
                        cupping_notes = st.text_area("Cupping notes", value=plan.get("cupping_notes") or "")
                        mark_used = st.checkbox("Tandai plan dipakai pada roast ini")
                        save_eval = st.form_submit_button("Save Evaluation", type="primary")
                    if save_eval:
                        rpdb.save_evaluation(plan["plan_id"], rating, result_notes.strip(), cupping_notes.strip(), mark_used)
                        st.success("Evaluation tersimpan.")
                        st.rerun()

                with st.expander("Duplicate / Delete", expanded=False):
                    new_name = st.text_input("New duplicated plan name", value=f"{plan.get('plan_name','')} V2")
                    cdup, cdel = st.columns(2)
                    if cdup.button("Duplicate as New Version", use_container_width=True):
                        new_id = rpdb.duplicate_plan(plan["plan_id"], new_name.strip())
                        st.success(f"Plan diduplikasi: {new_id}")
                        st.rerun()
                    confirm = cdel.checkbox("Confirm delete")
                    if cdel.button("Delete Plan", use_container_width=True, disabled=not confirm):
                        rpdb.delete_plan(plan["plan_id"])
                        st.success("Plan dihapus.")
                        st.rerun()
