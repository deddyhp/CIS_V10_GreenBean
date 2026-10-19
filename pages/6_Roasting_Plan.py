from __future__ import annotations

import html
import json
import re

import pandas as pd
import streamlit as st

from utils.cis_theme import apply_cis_theme
import utils.roasting_plan_database as rpdb


# ============================================================
# CIS ROASTING PLAN V10.25 — NEXT UI
# Presentation upgrade only:
# - Dashboard visual
# - Phase cards
# - Guide Mode
# - Attention & PRAS / S³
# - Mobile responsive
# Database contract remains V10.24-compatible.
# ============================================================

st.set_page_config(page_title="Roasting Plan", page_icon="🔥", layout="wide")
apply_cis_theme()

st.markdown("""
<style>
:root{
  --rp-line:rgba(255,255,255,.08);
  --rp-muted:#9ca39f;
  --rp-green:#67f2aa;
  --rp-amber:#efc36d;
}
.plan-hero,.guide-card,.phase-card{
  border:1px solid var(--rp-line);
  border-radius:18px;
  background:linear-gradient(180deg,rgba(13,16,14,.98),rgba(6,8,7,.98));
  box-shadow:0 12px 34px rgba(0,0,0,.24);
}
.plan-hero{padding:1.05rem 1.15rem;margin-bottom:.9rem}
.plan-kicker{color:#8f9692;font-size:.68rem;letter-spacing:.13em;font-weight:850}
.muted{color:var(--rp-muted)}
.rating{color:#ffd75e;font-size:1.05rem}

.rp-shell{
  border:1px solid var(--rp-line);
  border-radius:22px;
  overflow:hidden;
  background:#050705;
  margin:.45rem 0 1rem;
  box-shadow:0 18px 44px rgba(0,0,0,.24);
}
.rp-head{padding:1rem 1.08rem .72rem}
.rp-brand{font-size:.82rem;color:#8b918d;letter-spacing:.12em;font-weight:850}
.rp-title{font-size:2.05rem;font-weight:850;color:#fff;margin:.22rem 0 .24rem;line-height:1.12}
.rp-meta{font-size:1.05rem;color:#a5aaa7}
.rp-status{
  display:inline-block;padding:.16rem .48rem;border-radius:999px;
  background:rgba(71,230,136,.12);color:var(--rp-green);
  font-size:.88rem;font-weight:850;border:1px solid rgba(102,245,168,.18);
  margin-right:.35rem
}
.rp-target-title{
  padding:.12rem 1.08rem .48rem;
  color:#f4f4f4;font-weight:820;font-size:1.16rem;
}
.rp-milestones{
  display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.48rem;padding:0 1.02rem .88rem;
}
.rp-mile{
  border-radius:13px;background:#242524;
  border:1px solid rgba(255,255,255,.04);
  padding:.60rem .44rem;text-align:center;min-height:74px;
}
.rp-mile-label{color:#b9bbb9;font-size:.82rem;letter-spacing:.035em;text-transform:uppercase}
.rp-mile-temp{color:#c4c6c4;font-size:.96rem;margin-top:.10rem}
.rp-mile-main{font-size:1.85rem;font-weight:850;color:#fff;line-height:1.05;margin-top:.14rem}
.rp-info-grid{
  display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.38rem;padding:0 1.02rem .85rem;
}
.rp-info{border-top:1px solid var(--rp-line);padding:.50rem .16rem .10rem;text-align:center}
.rp-info-label{color:#868b88;font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}
.rp-info-value{color:#f4f5f4;font-size:1.18rem;font-weight:760;margin-top:.08rem}

.rp-guide{
  margin:.70rem 1.02rem .86rem;padding:.72rem .78rem;border-radius:13px;
  background:linear-gradient(90deg,rgba(102,245,168,.10),rgba(102,245,168,.035));
  border:1px solid rgba(102,245,168,.20)
}
.rp-guide-kicker{font-size:.82rem;color:#83d9aa;letter-spacing:.09em;font-weight:850}
.rp-guide-main{font-size:1.38rem;color:#fff;font-weight:850;margin-top:.20rem}
.rp-guide-sub{font-size:.96rem;color:#aeb6b1;margin-top:.15rem}

.rp-phase{padding:.84rem 1.02rem;border-top:1px solid var(--rp-line)}
.rp-phase-head{display:flex;align-items:baseline;justify-content:space-between;gap:.8rem;margin-bottom:.42rem}
.rp-phase-title{font-size:1.28rem;font-weight:850;color:#fff}
.rp-phase-target{font-size:.92rem;color:#959a97;white-space:nowrap}
.rp-table{width:100%;border-collapse:collapse;font-size:1.06rem}
.rp-table th{color:#bfc3c0;font-weight:720;text-align:left;padding:.34rem .05rem;border-bottom:1px solid var(--rp-line)}
.rp-table th:nth-child(2),.rp-table th:nth-child(3),
.rp-table td:nth-child(2),.rp-table td:nth-child(3){text-align:right}
.rp-table td{padding:.40rem .05rem;border-bottom:1px solid rgba(255,255,255,.055);color:#e9eae9}
.rp-table tr:last-child td{border-bottom:none}
.rp-event{font-weight:730}
.rp-ga{font-variant-numeric:tabular-nums;color:#f6f6f6}
.rp-attention{
  margin-top:.52rem;padding:.50rem .60rem;border-radius:10px;
  background:rgba(240,191,98,.07);
  border-left:3px solid rgba(240,191,98,.60);
  color:#c9cbc9;font-size:.98rem;line-height:1.42
}
.rp-attention strong{color:#f0c97e}

.rp-result-grid{
  display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.30rem;padding:.82rem 1.02rem;border-top:1px solid var(--rp-line)
}
.rp-result{text-align:center}
.rp-result-label{font-size:.78rem;color:#858986;letter-spacing:.05em;text-transform:uppercase}
.rp-result-value{font-size:1.42rem;color:#fff;font-weight:850;margin-top:.14rem}
.rp-cup{padding:0 1.02rem .86rem;color:#aeb2af;font-size:1.02rem;line-height:1.42}
.rp-cup strong{display:block;color:#e8eae8;margin-bottom:.10rem}

.structured-section{
  padding:.78rem .88rem;margin:.52rem 0;border-radius:13px;
  border:1px solid var(--rp-line);background:#0b0e0c
}
.structured-section h4{margin:0 0 .42rem;color:#eceeed;font-size:1.10rem;letter-spacing:.035em}
.structured-body{font-size:1.02rem;line-height:1.58;color:#d7dad8}
.structured-target{border-left:3px solid rgba(102,245,168,.65)}
.structured-dont{border-left:3px solid rgba(255,141,130,.70);background:rgba(50,14,12,.22)}
.structured-dont h4{color:#ffb4ac}

.guide-card{padding:1rem 1.05rem;margin:.62rem 0}
.phase-title{color:#fff;font-size:1.22rem;font-weight:820}
.phase-line{font-size:1.02rem;color:#eceeed;line-height:1.58}
.guide-goal{font-size:1.08rem;color:#e7e9e8;line-height:1.5}
.s3{border-left:3px solid rgba(102,245,168,.62)}
.bt-em{font-weight:850;color:#fff}
.ga-em{font-weight:820;color:#eef3f0}

.stButton>button{border-radius:12px;font-weight:800}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{
  color:#04150d!important;-webkit-text-fill-color:#04150d!important;
  background:linear-gradient(90deg,#37f3a5,#4cf0c7)!important;
  border:1px solid rgba(160,255,220,.75)!important;
}
.stButton>button[kind="primary"] p,.stFormSubmitButton>button[kind="primary"] p{
  color:#04150d!important;-webkit-text-fill-color:#04150d!important;font-weight:850!important
}
@media(max-width:768px){
  .plan-hero{padding:.90rem}
  .rp-head{padding:.90rem .82rem .66rem}
  .rp-brand{font-size:.78rem}
  .rp-title{font-size:1.72rem}
  .rp-meta{font-size:1rem}
  .rp-target-title{font-size:1.08rem}
  .rp-milestones{gap:.34rem;padding:0 .72rem .82rem}
  .rp-mile{padding:.58rem .26rem;min-height:76px}
  .rp-mile-label{font-size:.72rem}
  .rp-mile-temp{font-size:.86rem}
  .rp-mile-main{font-size:1.48rem}
  .rp-info-grid{padding:0 .72rem .76rem;gap:.26rem}
  .rp-info-label{font-size:.70rem}
  .rp-info-value{font-size:1.02rem}
  .rp-guide{margin:.62rem .72rem .82rem;padding:.78rem .78rem}
  .rp-guide-kicker{font-size:.74rem}
  .rp-guide-main{font-size:1.22rem}
  .rp-guide-sub{font-size:.92rem}
  .rp-phase{padding:.82rem .72rem}
  .rp-phase-title{font-size:1.18rem}
  .rp-phase-target{font-size:.88rem}
  .rp-table{font-size:1.02rem}
  .rp-table th,.rp-table td{padding:.48rem .06rem}
  .rp-attention{font-size:.94rem}
  .rp-result-grid{padding:.78rem .72rem}
  .rp-result-label{font-size:.72rem}
  .rp-result-value{font-size:1.26rem}
  .rp-cup{padding:0 .72rem .82rem;font-size:1rem}
  .structured-section h4{font-size:1.03rem}
  .structured-body{font-size:1rem}
  .phase-title{font-size:1.15rem}
  .phase-line{font-size:1rem}
  .block-container{padding-top:.8rem!important;padding-left:.65rem!important;padding-right:.65rem!important}
}
</style>
""", unsafe_allow_html=True)

st.markdown(r"""
<style>
/* V10.25.3 — SELECTIVE XL
   Keep the UI elegant. Enlarge ONLY BTxx checkpoints and G/A values. */

.rp-key-event{
  font-size:2.25rem!important;
  line-height:1.0!important;
  font-weight:900!important;
  letter-spacing:-.02em!important;
}

.rp-key-ga{
  font-size:2.25rem!important;
  line-height:1.0!important;
  font-weight:850!important;
  letter-spacing:-.02em!important;
}

/* Give the emphasized values breathing room without enlarging the rest of the UI. */
.rp-table td{
  vertical-align:middle!important;
}
.rp-table tr:has(.rp-key-event),
.rp-table tr:has(.rp-key-ga){
  height:4.0rem!important;
}

/* Tablet/mobile: still big, but keep layout clean. */
@media(max-width:1100px){
  .rp-key-event,
  .rp-key-ga{
    font-size:2.10rem!important;
  }
  .rp-table tr:has(.rp-key-event),
  .rp-table tr:has(.rp-key-ga){
    height:3.8rem!important;
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown(r"""
<style>
/* V10.25.5 — Complete 4-card dashboard + Selective 2.5X BT/G/A */
@media(max-width:760px){
  .rp-milestones{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
}
</style>
""", unsafe_allow_html=True)

try:
    rpdb.create_database()
except Exception as exc:
    st.error(f"Roasting Plan database belum siap: {exc}")
    st.stop()

st.caption(f"Roasting Plan page V10.25.5 · 4-Card Dashboard · Selective 2.5X BT/G/A · DB module V{getattr(rpdb, 'MODULE_VERSION', 'unknown')}")


def save_chaty_plan_direct(metadata: dict, plan_data: dict) -> str:
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
    ws.append_row([record.get(h, "") for h in headers], value_input_option="USER_ENTERED")
    return plan_id


PHASES = ["Preheat", "Drying", "Maillard", "First Crack", "Development", "Drop"]
PURPOSES = ["Filter", "Espresso", "Latte", "Tubruk", "Blend Component", "Experimental", "Other"]
STATUSES = ["Draft", "Trial", "Recommended", "Locked", "Archived"]

DEFAULT_PHASES = {
    "Preheat": {
        "bt": "200°C", "gas": "", "air": "40", "drum": "90", "target_time": "",
        "steps": "Charge 500 g\nCharge → G45 · A40",
        "notes": "Stabilkan suhu sekitar 2–3 menit sebelum charge.",
    },
    "Drying": {
        "bt": "147–149°C", "gas": "", "air": "", "drum": "90", "target_time": "4:05–4:20",
        "steps": "Charge → G45 · A40\nTP → G55 · A40\nBT110 → G65 · A40\nBT130 → G65 · A50\nDry End → BT 147–149°C @ 4:05–4:20",
        "notes": "Jaga momentum drying tetap stabil. Koreksi hanya bila keluar dari rentang target.",
    },
    "Maillard": {
        "bt": "150–185°C", "gas": "60→45", "air": "60→80", "drum": "90",
        "target_time": "Dry End → FC 4:15–4:30",
        "steps": "BT150 → G60 · A60\nBT170 → G50 · A70\nBT185 → G45 · A80\nTarget FC → BT 194–195°C @ 8:30–8:50",
        "notes": "Bangun sweetness tanpa menahan energi terlalu lama. Jaga RoR turun bertahap.",
    },
    "First Crack": {
        "bt": "194–195°C", "gas": "25", "air": "90", "drum": "90", "target_time": "8:30–8:50",
        "steps": "FC mulai → G25 · A90\nKonfirmasi crack terdengar jelas dan merata\nMulai hitung development dari FC yang valid",
        "notes": "Jangan bereaksi pada satu-dua crack awal.",
    },
    "Development": {
        "bt": "194–203°C", "gas": "25", "air": "90", "drum": "90",
        "target_time": "1:15–1:35 · DTR 13–15%",
        "steps": "Pertahankan G25 · A90\nPantau RoR tetap menurun halus\nJangan tambah gas kecuali roast benar-benar kehilangan momentum",
        "notes": "Fokus pada kestabilan. Koreksi kecil hanya bila keluar dari rentang.",
    },
    "Drop": {
        "bt": "202.5–203.5°C", "gas": "0", "air": "100", "drum": "90",
        "target_time": "±9:45–10:25",
        "steps": "Drop pada target BT / development\nGas 0 · masuk cooling penuh\nCatat total time, DTR, weight loss, Agtron, dan respons aroma",
        "notes": "Prioritaskan target sensori dan development.",
    },
}


def phase_form(phase: str, values: dict, key_prefix: str) -> dict:
    st.markdown(f"#### {phase}")
    c1, c2, c3, c4 = st.columns(4)
    bt = c1.text_input("BT / Target BT", value=str(values.get("bt", "")), key=f"{key_prefix}_{phase}_bt")
    gas = c2.text_input("Gas (G)", value=str(values.get("gas", "")), key=f"{key_prefix}_{phase}_gas")
    air = c3.text_input("Airflow (A)", value=str(values.get("air", "")), key=f"{key_prefix}_{phase}_air")
    drum = c4.text_input("Drum rpm", value=str(values.get("drum", "")), key=f"{key_prefix}_{phase}_drum")
    target_time = st.text_input("Target waktu / rentang", value=str(values.get("target_time", "")), key=f"{key_prefix}_{phase}_time")
    steps = st.text_area("Juklak / checkpoint manual", value=str(values.get("steps", "")), key=f"{key_prefix}_{phase}_steps", height=110)
    notes = st.text_area("Attention", value=str(values.get("notes", "")), key=f"{key_prefix}_{phase}_notes", height=80)
    return {"bt": bt, "gas": gas, "air": air, "drum": drum, "target_time": target_time, "steps": steps, "notes": notes}


def stars(value: float) -> str:
    full = int(value)
    half = value - full >= .5
    return "★" * full + ("½" if half else "") + "☆" * max(0, 5 - full - (1 if half else 0))


def esc(value) -> str:
    return html.escape(str(value or "—")).replace("\n", "<br>")


def roast_text(value) -> str:
    safe = html.escape(str(value or "—")).replace("\n", "<br>")
    safe = re.sub(
        r"\bBT\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–-]\s*[0-9]+(?:[.,][0-9]+)?)?\s*°?C?)",
        r'<span class="bt-em">BT \1</span>', safe, flags=re.IGNORECASE)
    safe = re.sub(
        r"\b([GA])\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–-]\s*[0-9]+(?:[.,][0-9]+)?)?)",
        r'<span class="ga-em">\1\2</span>', safe, flags=re.IGNORECASE)
    return safe


def compact_line(p: dict) -> str:
    parts = []
    if p.get("bt"): parts.append(f"BT {p.get('bt')}")
    if p.get("gas"): parts.append(f"G{p.get('gas')}")
    if p.get("air"): parts.append(f"A{p.get('air')}")
    if p.get("drum"): parts.append(f"Drum {p.get('drum')} rpm")
    if p.get("target_time"): parts.append(f"@ {p.get('target_time')}")
    return " · ".join(parts)


STRUCTURED_SECTION_ORDER = [
    "Reference / Context", "Preheat", "Drying", "Maillard", "First Crack",
    "Development", "Drop / Cooling", "Expected Cup", "Main Philosophy",
    "S³ Execution", "Don't",
]


def _clean_value(value: str) -> str:
    return value.strip().strip("`*-• ")


def _extract_chaty_block(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(
        r"\[CIS\s+ROASTING\s+PLAN\](.*?)\[/CIS\s+ROASTING\s+PLAN\]",
        text, flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else text.strip()


def _first_number(value: str) -> float:
    match = re.search(r"-?\d+(?:[.,]\d+)?", value or "")
    return float(match.group(0).replace(",", ".")) if match else 0.0


def _normalize_status(raw: str) -> str:
    up = (raw or "").upper()
    for status in STATUSES:
        if status.upper() in up:
            return status
    return "Trial"


def parse_chaty_structured(raw_text: str) -> dict:
    body = _extract_chaty_block(raw_text)
    if not body:
        raise ValueError("Teks Roasting Plan masih kosong.")

    metadata_aliases = {
        "PLAN NAME": "plan_name", "NAME": "plan_name", "BEAN": "bean",
        "PURPOSE": "purpose", "ROAST PURPOSE": "purpose", "GOAL": "goal",
        "BATCH": "batch_size_g", "BATCH SIZE": "batch_size_g", "DENSITY": "density",
        "MOISTURE": "moisture", "STATUS": "status_raw",
    }
    section_patterns = [
        (r"PREHEAT", "Preheat"),
        (r"DRYING", "Drying"),
        (r"MAILLARD", "Maillard"),
        (r"FIRST\s+CRACK|FC(?=\s*:|\s*$)", "First Crack"),
        (r"DEVELOPMENT|DEV", "Development"),
        (r"DROP(?:\s*/\s*COOLING)?|COOLING", "Drop / Cooling"),
        (r"EXPECTED\s+CUP|CUP\s+TARGET|TARGET\s+CUP", "Expected Cup"),
        (r"MAIN\s+PHILOSOPHY|PHILOSOPHY", "Main Philosophy"),
        (r"S[³3]\s+(?:EXECUTION|SUMMARY|CONTROL|PRACTICAL\s+GUIDE)", "S³ Execution"),
        (r"HAL\s+YANG\s+TIDAK\s+KITA\s+LAKUKAN|DON'?T|DO\s+NOT", "Don't"),
    ]
    section_re = re.compile(
        r"^(" + "|".join(f"(?:{p})" for p, _ in section_patterns) + r")\b\s*:?[ \t]*(.*)$",
        re.IGNORECASE,
    )
    result = {
        "plan_name": "", "bean": "", "purpose": "", "goal": "",
        "status": "Trial", "status_raw": "", "batch_size_g": 500.0,
        "density": 0.0, "moisture": 0.0, "source": "Chaty Import",
        "raw_text": raw_text.strip(),
        "sections": {k: [] for k in STRUCTURED_SECTION_ORDER},
    }

    def section_name(token: str) -> str | None:
        for pat, name in section_patterns:
            if re.fullmatch(pat, token.strip(), flags=re.IGNORECASE):
                return name
        return None

    current_section = None
    pending_meta = None
    pre_section_context = []

    for raw_line in body.splitlines():
        original = raw_line.strip()
        if not original:
            if current_section and result["sections"][current_section] and result["sections"][current_section][-1] != "":
                result["sections"][current_section].append("")
            continue

        clean = _clean_value(original)
        heading = re.sub(r"[:\s]+$", "", clean).upper()

        if pending_meta:
            if pending_meta in {"batch_size_g", "density", "moisture"}:
                result[pending_meta] = _first_number(clean)
            elif pending_meta == "status_raw":
                result["status_raw"] = clean
                result["status"] = _normalize_status(clean)
            else:
                result[pending_meta] = clean
            pending_meta = None
            continue

        km = re.match(r"^([^:]+?)\s*:\s*(.*)$", clean)
        if current_section is None and km:
            key = km.group(1).strip().upper()
            if key in metadata_aliases:
                field = metadata_aliases[key]
                value = km.group(2).strip()
                if not value:
                    pending_meta = field
                elif field in {"batch_size_g", "density", "moisture"}:
                    result[field] = _first_number(value)
                elif field == "status_raw":
                    result["status_raw"] = value
                    result["status"] = _normalize_status(value)
                else:
                    result[field] = value
                continue

        if current_section is None and heading in metadata_aliases:
            pending_meta = metadata_aliases[heading]
            continue

        sm = section_re.match(clean)
        if sm:
            token, remainder = sm.group(1), sm.group(2).strip()
            current_section = section_name(token)
            if current_section and remainder:
                result["sections"][current_section].append(remainder)
            continue

        if current_section:
            result["sections"][current_section].append(clean)
        else:
            pre_section_context.append(clean)

    if pre_section_context:
        result["sections"]["Reference / Context"] = pre_section_context

    result["sections"] = {
        k: "\n".join(v).strip() if isinstance(v, list) else str(v)
        for k, v in result["sections"].items()
    }
    if not result["plan_name"]:
        result["plan_name"] = f"{result['bean'] or 'Roasting'} Plan"
    if not result["bean"] or not result["goal"]:
        raise ValueError("Blok Chaty minimal harus memuat BEAN dan GOAL.")
    return result


def _section_card(title: str, body: str) -> str:
    if not body:
        return ""
    cls = "structured-section"
    if title in {"First Crack", "Development", "Drop / Cooling", "S³ Execution"}:
        cls += " structured-target"
    if title == "Don't":
        cls += " structured-dont"
    return f'<div class="{cls}"><h4>{esc(title).upper()}</h4><div class="structured-body">{roast_text(body)}</div></div>'


def _clean_metric(value, fallback="—") -> str:
    value = str(value or "").strip()
    return value if value else fallback


def _first_temp(text: str) -> str:
    m = re.search(
        r"(\d{2,3}(?:[.,]\d+)?(?:\s*[–-]\s*\d{2,3}(?:[.,]\d+)?)?)\s*°?\s*C",
        text or "", re.I)
    return (m.group(1).replace(" ", "") + "°C") if m else "—"


def _time_after_keyword(text: str, keyword: str = "") -> str:
    src = text or ""
    if keyword:
        m = re.search(keyword + r".{0,100}?\b(\d{1,2}:\d{2}(?:\s*[–-]\s*\d{1,2}:\d{2})?)\b",
                      src, re.I | re.S)
        if m:
            return m.group(1)
    m = re.search(r"\b(\d{1,2}:\d{2}(?:\s*[–-]\s*\d{1,2}:\d{2})?)\b", src)
    return m.group(1) if m else "—"


def _metric_from_text(text: str, patterns: list[str]) -> str:
    for pat in patterns:
        m = re.search(pat, text or "", re.I)
        if m:
            return m.group(1).strip()
    return "—"


def _parse_event_rows(text: str) -> list[tuple[str, str, str]]:
    rows = []
    for raw in str(text or "").splitlines():
        line = raw.strip().strip("•*- ")
        if not line:
            continue
        gas = re.search(r"\bG\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–→-]\s*[0-9]+(?:[.,][0-9]+)?)?)", line, re.I)
        air = re.search(r"\bA\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–→-]\s*[0-9]+(?:[.,][0-9]+)?)?)", line, re.I)
        if not gas and not air:
            continue
        event = re.split(r"(?:→|\||\bG\s*\d|\bA\s*\d)", line, maxsplit=1, flags=re.I)[0]
        event = re.sub(r"\s*[:\-–]\s*$", "", event).strip() or "Checkpoint"
        rows.append((event, f"G{gas.group(1)}" if gas else "—", f"A{air.group(1)}" if air else "—"))
    return rows


def _rows_html(rows) -> str:
    if not rows:
        return '<tr><td class="rp-event">—</td><td class="rp-ga">—</td><td class="rp-ga">—</td></tr>'

    rendered = []
    for e, g, a in rows:
        event_text = str(e or "")
        # Only BT checkpoints get XL emphasis. Charge, TP, DE, FC, DROP stay normal.
        event_class = "rp-event rp-key-event" if re.match(r"^BT\s*\d", event_text, re.I) else "rp-event"

        gas_class = "rp-ga rp-key-ga" if re.match(r"^G\d", str(g or ""), re.I) else "rp-ga"
        air_class = "rp-ga rp-key-ga" if re.match(r"^A\d", str(a or ""), re.I) else "rp-ga"

        rendered.append(
            f'<tr><td class="{event_class}">{esc(e)}</td>'
            f'<td class="{gas_class}">{esc(g)}</td>'
            f'<td class="{air_class}">{esc(a)}</td></tr>'
        )
    return "".join(rendered)


def _phase_html(number, title, target, rows, attention="") -> str:
    att = (
        f'<div class="rp-attention"><strong>ATTENTION</strong> · {esc(attention)}</div>'
        if str(attention or "").strip() else ""
    )
    return f"""
    <div class="rp-phase">
      <div class="rp-phase-head">
        <div class="rp-phase-title">{esc(number)} · {esc(title).upper()}</div>
        <div class="rp-phase-target">Target {esc(target)}</div>
      </div>
      <table class="rp-table">
        <thead><tr><th>Event</th><th>Gas</th><th>Air</th></tr></thead>
        <tbody>{_rows_html(rows)}</tbody>
      </table>
      {att}
    </div>
    """


def _header_html(plan, milestones) -> str:
    cards = "".join(
        f'<div class="rp-mile"><div class="rp-mile-label">{esc(label)}</div>'
        f'<div class="rp-mile-temp">{esc(temp)}</div>'
        f'<div class="rp-mile-main">{esc(main)}</div></div>'
        for label, temp, main in milestones
    )
    return f"""
    <div class="rp-head">
      <div class="rp-brand">CIS · PAGERWATU ROASTING PLAN</div>
      <div class="rp-title">{esc(plan.get('plan_name'))}</div>
      <div class="rp-meta">
        <span class="rp-status">{esc(plan.get('status'))}</span>
        {esc(plan.get('purpose'))} · {plan.get('batch_size_g',0):g} g
      </div>
    </div>
    <div class="rp-target-title">Target utama yang harus direplikasi</div>
    <div class="rp-milestones">{cards}</div>
    <div class="rp-info-grid">
      <div class="rp-info"><div class="rp-info-label">Density</div><div class="rp-info-value">{plan.get('density',0):g} g/L</div></div>
      <div class="rp-info"><div class="rp-info-label">Moisture</div><div class="rp-info-value">{plan.get('moisture',0):g}%</div></div>
      <div class="rp-info"><div class="rp-info-label">Bean</div><div class="rp-info-value">{esc(plan.get('bean'))}</div></div>
    </div>
    """


def _guide_mode_html(next_event, ga, note="") -> str:
    return f"""
    <div class="rp-guide">
      <div class="rp-guide-kicker">GUIDE MODE · NEXT CHECKPOINT</div>
      <div class="rp-guide-main">{esc(next_event)} · {esc(ga)}</div>
      <div class="rp-guide-sub">{esc(note)}</div>
    </div>
    """


def render_chaty_structured_guide(plan: dict) -> None:
    data = plan.get("plan_data", {}) or {}
    s = data.get("sections", {}) or {}

    dry_txt = s.get("Drying", "")
    mail_txt = s.get("Maillard", "")
    fc_txt = s.get("First Crack", "")
    dev_txt = s.get("Development", "")
    drop_txt = s.get("Drop / Cooling", "")

    de_line = re.search(r"(?:DRY\s*END|DE).*", dry_txt or "", re.I)
    de_temp = _first_temp(de_line.group(0)) if de_line else _first_temp(dry_txt)
    de_time = _time_after_keyword(dry_txt, r"(?:DRY\s*END|DE)")
    fc_source = fc_txt or mail_txt

    preheat_txt = s.get("Preheat", "")
    milestones = [
        ("PREHEAT", _first_temp(preheat_txt), ""),
        ("DRY END", de_temp, de_time),
        ("FIRST CRACK", _first_temp(fc_source), _time_after_keyword(fc_source, r"(?:FIRST\s*CRACK|FC)")),
        ("DROP", _first_temp(drop_txt), _time_after_keyword(drop_txt, r"DROP")),
    ]

    dry_rows = _parse_event_rows(dry_txt)
    mail_rows = _parse_event_rows(mail_txt)
    dev_rows = _parse_event_rows("\n".join([fc_txt, dev_txt, drop_txt]))
    all_rows = dry_rows + mail_rows + dev_rows

    if all_rows:
        e, g, a = all_rows[0]
        next_event, next_ga = e, f"{g} · {a}"
    else:
        next_event, next_ga = "Charge", "—"

    all_text = "\n".join(str(v or "") for v in s.values())
    dtr = _metric_from_text(all_text, [r"\bDTR\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–-]\s*[0-9]+(?:[.,][0-9]+)?)?%)"])
    wl = _metric_from_text(all_text, [r"(?:WEIGHT\s*LOSS|WL)\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?%)"])
    agtron = _metric_from_text(all_text, [r"AGTRON\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)"])
    expected = s.get("Expected Cup", "") or plan.get("goal", "")

    st.markdown('<div class="rp-shell">' + _header_html(plan, milestones), unsafe_allow_html=True)
    st.markdown(_guide_mode_html(
        next_event, next_ga,
        "Display guide membaca juklak asli; BT/G/A tidak diinterpretasikan ulang."
    ), unsafe_allow_html=True)
    st.markdown(_phase_html("01", "Drying", de_time, dry_rows), unsafe_allow_html=True)
    st.markdown(_phase_html("02", "Maillard", _time_after_keyword(mail_txt), mail_rows), unsafe_allow_html=True)
    st.markdown(_phase_html("03", "Development", _time_after_keyword(dev_txt), dev_rows), unsafe_allow_html=True)
    st.markdown(f"""
      <div class="rp-result-grid">
        <div class="rp-result"><div class="rp-result-label">DTR</div><div class="rp-result-value">{esc(dtr)}</div></div>
        <div class="rp-result"><div class="rp-result-label">Weight Loss</div><div class="rp-result-value">{esc(wl)}</div></div>
        <div class="rp-result"><div class="rp-result-label">Agtron</div><div class="rp-result-value">{esc(agtron)}</div></div>
      </div>
      <div class="rp-cup"><strong>Expected Cup</strong>{esc(expected)}</div>
    </div>
    """, unsafe_allow_html=True)

    for title in ["Reference / Context", "Preheat", "First Crack", "Drop / Cooling",
                  "Main Philosophy", "S³ Execution", "Don't"]:
        card = _section_card(title, s.get(title, ""))
        if card:
            st.markdown(card, unsafe_allow_html=True)

    st.caption("V10.25 Visual Guide: database dan teks juklak V10.24 tetap menjadi source of truth.")


def render_practical_summary(plan: dict) -> None:
    data = plan.get("plan_data", {}) or {}
    phases = data.get("phases", {}) or {}
    pre = phases.get("Preheat", {}) or {}
    dry = phases.get("Drying", {}) or {}
    mail = phases.get("Maillard", {}) or {}
    fc = phases.get("First Crack", {}) or {}
    dev = phases.get("Development", {}) or {}
    drop = phases.get("Drop", {}) or {}

    milestones = [
        ("PREHEAT", "", _clean_metric(pre.get("bt"))),
        ("DRY END", _clean_metric(dry.get("bt")), _clean_metric(dry.get("target_time"))),
        ("FIRST CRACK", _clean_metric(fc.get("bt")), _clean_metric(fc.get("target_time"))),
        ("DROP", _clean_metric(drop.get("bt")), _clean_metric(drop.get("target_time"))),
    ]

    dry_rows = _parse_event_rows(dry.get("steps"))
    mail_rows = _parse_event_rows(mail.get("steps"))
    dev_rows = _parse_event_rows("\n".join([
        fc.get("steps", ""), dev.get("steps", ""), drop.get("steps", "")
    ]))
    all_rows = dry_rows + mail_rows + dev_rows
    if all_rows:
        e, g, a = all_rows[0]
        next_event, next_ga = e, f"{g} · {a}"
    else:
        next_event, next_ga = "Charge", "—"

    all_text = "\n".join([str(dev), str(drop), str(data)])
    dtr = _metric_from_text(all_text, [r"\bDTR\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?(?:\s*[–-]\s*[0-9]+(?:[.,][0-9]+)?)?%)"])
    wl = _metric_from_text(all_text, [r"(?:WEIGHT\s*LOSS|WL)\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?%)"])
    agtron = _metric_from_text(all_text, [r"AGTRON\s*[:=]?\s*([0-9]+(?:[.,][0-9]+)?)"])

    st.markdown('<div class="rp-shell">' + _header_html(plan, milestones), unsafe_allow_html=True)
    st.markdown(_guide_mode_html(
        next_event, next_ga,
        "Gunakan checkpoint sebagai gate; koreksi hanya bila roast keluar dari range."
    ), unsafe_allow_html=True)
    st.markdown(_phase_html("01", "Drying", _clean_metric(dry.get("target_time")), dry_rows, dry.get("notes", "")), unsafe_allow_html=True)
    st.markdown(_phase_html("02", "Maillard", _clean_metric(mail.get("target_time")), mail_rows, mail.get("notes", "")), unsafe_allow_html=True)
    st.markdown(_phase_html("03", "Development", _clean_metric(dev.get("target_time")), dev_rows, dev.get("notes", "")), unsafe_allow_html=True)
    st.markdown(f"""
      <div class="rp-result-grid">
        <div class="rp-result"><div class="rp-result-label">DTR</div><div class="rp-result-value">{esc(dtr)}</div></div>
        <div class="rp-result"><div class="rp-result-label">Weight Loss</div><div class="rp-result-value">{esc(wl)}</div></div>
        <div class="rp-result"><div class="rp-result-label">Agtron</div><div class="rp-result-value">{esc(agtron)}</div></div>
      </div>
      <div class="rp-cup"><strong>Goal / Expected Cup</strong>{esc(plan.get('goal'))}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="guide-card s3">
      <div class="phase-title">ATTENTION & PRAS / S³</div>
      <div class="phase-line">{esc(data.get('s3_attention'))}</div>
      <div class="muted" style="margin-top:.45rem"><strong>Roast terlalu cepat:</strong> {esc(data.get('too_fast'))}</div>
      <div class="muted"><strong>Roast tertinggal:</strong> {esc(data.get('too_slow'))}</div>
    </div>
    """, unsafe_allow_html=True)


def render_guide(plan: dict) -> None:
    data = plan.get("plan_data", {}) or {}
    if data.get("mode") == "chaty_structured":
        render_chaty_structured_guide(plan)
    else:
        render_practical_summary(plan)


# ============================================================
# PAGE
# ============================================================

st.markdown("""
<div class="plan-hero">
  <div class="plan-kicker">CIS UTILITY · S³ ROAST COMPANION</div>
  <h1 style="margin:.22rem 0">🔥 Roasting Plan</h1>
  <div class="muted">Create / Chaty Import → visual target → Guide Mode → evaluate → recall.</div>
</div>
""", unsafe_allow_html=True)

manual_tab, chaty_tab, library_tab = st.tabs(
    ["✍ Create Manual", "🤖 Update Chaty", "📚 Plan Library"]
)


# ============================================================
# MANUAL CREATE / EDIT
# ============================================================
with manual_tab:
    existing = rpdb.get_all_plans()
    edit_options = {"➕ New Manual Plan": None}
    if not existing.empty:
        edit_options.update({
            f"Edit · {r.plan_id} · {r.plan_name}": r.plan_id
            for r in existing.itertuples(index=False)
        })

    selected_label = st.selectbox("Mode", list(edit_options.keys()), key="manual_mode")
    selected_id = edit_options[selected_label]
    current = rpdb.get_plan(selected_id) if selected_id else None
    pdata = (current or {}).get("plan_data", {}) or {}

    with st.form("roasting_plan_form"):
        c1, c2 = st.columns(2)
        with c1:
            plan_name = st.text_input("Plan Name", value=(current or {}).get("plan_name", ""))
            bean = st.text_input("Bean", value=(current or {}).get("bean", ""))
            cur_purpose = (current or {}).get("purpose")
            purpose = st.selectbox(
                "Roast Purpose", PURPOSES,
                index=PURPOSES.index(cur_purpose) if cur_purpose in PURPOSES else 0
            )
            cur_status = (current or {}).get("status")
            status = st.selectbox(
                "Status", STATUSES,
                index=STATUSES.index(cur_status) if cur_status in STATUSES else 0
            )
        with c2:
            batch_size = st.number_input("Batch Size (g)", min_value=0.0, value=float((current or {}).get("batch_size_g") or 500), step=50.0)
            density = st.number_input("Density (g/L)", min_value=0.0, value=float((current or {}).get("density") or 0), step=1.0)
            moisture = st.number_input("Moisture (%)", min_value=0.0, value=float((current or {}).get("moisture") or 0), step=.1)

        goal = st.text_area("Goal rasa / aroma / body / finish", value=(current or {}).get("goal", ""), height=100)

        if not current:
            st.info("Template awal editable. Ubah seluruh angka sesuai bean dan target roast aktual.")

        phases = {}
        stored_phases = pdata.get("phases", {}) or {}
        for phase in PHASES:
            with st.expander(phase, expanded=phase in ["Preheat", "Drying"]):
                vals = stored_phases.get(phase, {}) if current else DEFAULT_PHASES.get(phase, {})
                phases[phase] = phase_form(phase, vals, selected_id or "new_manual")

        st.markdown("#### S³ Control")
        s3_attention = st.text_area(
            "S³ Attention",
            value=pdata.get("s3_attention",
                "Simple: perubahan hanya pada checkpoint.\n"
                "Flexible: koreksi hanya bila roast keluar dari rentang.\n"
                "Sustainable: jangan mengejar angka dengan adjustment berulang."),
            height=110
        )
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
                    {
                        "plan_name": plan_name.strip(), "bean": bean.strip(),
                        "purpose": purpose, "goal": goal.strip(), "status": status,
                        "batch_size_g": batch_size, "density": density, "moisture": moisture,
                        "source": ((current or {}).get("source") or "Manual Plan"),
                    },
                    {
                        "phases": phases, "s3_attention": s3_attention.strip(),
                        "too_fast": too_fast.strip(), "too_slow": too_slow.strip(),
                    },
                    selected_id,
                )
                st.success(f"Roasting Plan tersimpan: {plan_id}")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menyimpan plan: {exc}")


# ============================================================
# CHATY IMPORT
# ============================================================
with chaty_tab:
    if st.session_state.pop("clear_chaty_raw_text", False):
        st.session_state["chaty_raw_text"] = ""
    if st.session_state.get("chaty_save_success"):
        st.success(st.session_state.pop("chaty_save_success"))

    st.markdown("### Copy–paste Juklak Chaty")
    st.caption("V10.25 mempertahankan juklak asli. CIS membaca metadata aman dan tidak menebak BT/G/A.")

    chaty_text = st.text_area(
        "Update Chaty",
        value=st.session_state.get("chaty_raw_text", ""),
        height=360,
        placeholder="[CIS ROASTING PLAN]\nPLAN NAME: ...\nBEAN: ...\nGOAL: ...\nPREHEAT ...\nDRYING ...\n...\n[/CIS ROASTING PLAN]",
        key="chaty_raw_text",
    )

    if st.button("🔎 Parse & Preview", type="primary", use_container_width=True):
        try:
            st.session_state["chaty_parsed_plan"] = parse_chaty_structured(chaty_text)
            st.success("Juklak berhasil dibaca tanpa reinterpretasi angka. Periksa preview sebelum disimpan.")
        except Exception as exc:
            st.session_state.pop("chaty_parsed_plan", None)
            st.error(f"Gagal membaca juklak: {exc}")

    parsed = st.session_state.get("chaty_parsed_plan")
    if parsed:
        st.markdown("### Preview Structured Chaty Guide")
        with st.form("chaty_import_form_v1025"):
            c1, c2 = st.columns(2)
            with c1:
                cp_name = st.text_input("Plan Name", value=parsed.get("plan_name", ""), key="chaty_plan_name_25")
                cp_bean = st.text_input("Bean", value=parsed.get("bean", ""), key="chaty_bean_25")
                cp_purpose = st.text_input("Purpose", value=parsed.get("purpose", ""), key="chaty_purpose_25")
                cp_status = st.selectbox(
                    "Status", STATUSES,
                    index=STATUSES.index(parsed.get("status")) if parsed.get("status") in STATUSES else 1,
                    key="chaty_status_25"
                )
            with c2:
                cp_batch = st.number_input("Batch Size (g)", min_value=0.0, value=float(parsed.get("batch_size_g") or 500), step=50.0, key="chaty_batch_25")
                cp_density = st.number_input("Density (g/L)", min_value=0.0, value=float(parsed.get("density") or 0), step=1.0, key="chaty_density_25")
                cp_moisture = st.number_input("Moisture (%)", min_value=0.0, value=float(parsed.get("moisture") or 0), step=.1, key="chaty_moisture_25")

            cp_goal = st.text_area("Goal", value=parsed.get("goal", ""), height=110, key="chaty_goal_25")

            st.markdown("#### Juklak yang akan masuk Library")
            for title in STRUCTURED_SECTION_ORDER:
                body = parsed.get("sections", {}).get(title, "")
                if body:
                    st.markdown(_section_card(title, body), unsafe_allow_html=True)

            st.info("BT/G/A di atas adalah teks asli dari juklak Chaty.")
            save_chaty = st.form_submit_button(
                "🤖 Save Structured Chaty Plan to Library",
                type="primary", use_container_width=True
            )

        if save_chaty:
            if not cp_name.strip() or not cp_bean.strip() or not cp_goal.strip():
                st.error("Plan Name, Bean, dan Goal wajib diisi.")
            else:
                try:
                    structured_data = {
                        "mode": "chaty_structured",
                        "raw_text": parsed.get("raw_text", chaty_text),
                        "sections": parsed.get("sections", {}),
                        "status_raw": parsed.get("status_raw", ""),
                    }
                    plan_id = save_chaty_plan_direct(
                        {
                            "plan_name": cp_name.strip(), "bean": cp_bean.strip(),
                            "purpose": cp_purpose.strip(), "goal": cp_goal.strip(),
                            "status": cp_status, "batch_size_g": cp_batch,
                            "density": cp_density, "moisture": cp_moisture,
                            "source": "Chaty Import",
                        },
                        structured_data,
                    )
                    st.session_state.pop("chaty_parsed_plan", None)
                    st.session_state["clear_chaty_raw_text"] = True
                    st.session_state["chaty_save_success"] = f"Structured Chaty Plan masuk Plan Library: {plan_id}"
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal menyimpan Chaty Plan: {exc}")


# ============================================================
# PLAN LIBRARY
# ============================================================
with library_tab:
    plans = rpdb.get_all_plans()
    if plans.empty:
        st.info("Belum ada Roasting Plan.")
    else:
        q1, q2, q3, q4 = st.columns([2, 1, 1, 1])
        query = q1.text_input("Search", placeholder="Bean, plan, goal, purpose", key="library_search")
        purpose_filter = q2.selectbox(
            "Purpose",
            ["All"] + sorted(plans["purpose"].dropna().astype(str).unique().tolist()),
            key="library_purpose"
        )
        status_filter = q3.selectbox("Status", ["All"] + STATUSES, key="library_status")
        source_values = sorted(
            x for x in plans.get("source", pd.Series(dtype=str)).fillna("").astype(str).unique().tolist() if x
        )
        source_filter = q4.selectbox("Source", ["All"] + source_values, key="library_source")

        filtered = plans.copy()
        if query.strip():
            hay = filtered[["plan_name", "bean", "goal", "purpose"]].fillna("").astype(str)
            mask = hay.apply(
                lambda col: col.str.contains(query.strip(), case=False, regex=False)
            ).any(axis=1)
            filtered = filtered[mask]
        if purpose_filter != "All":
            filtered = filtered[filtered["purpose"] == purpose_filter]
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
        if source_filter != "All":
            filtered = filtered[filtered["source"] == source_filter]

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
                st.caption(
                    f"Used {int(plan.get('usage_count') or 0)}× · "
                    f"Last used: {plan.get('last_used_at') or '—'} · "
                    f"Updated: {plan.get('updated_at') or '—'}"
                )

                with st.expander("✏️ Edit Plan", expanded=False):
                    st.caption("Ralat langsung dari Plan Library. Rating, usage count, dan evaluation tetap dipertahankan.")
                    edit_data = plan.get("plan_data", {}) or {}
                    is_structured = edit_data.get("mode") == "chaty_structured"

                    if is_structured:
                        st.info("🤖 Structured Chaty Plan — edit metadata atau teks juklak asli.")
                        with st.form(f"structured_edit_form_{plan['plan_id']}"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                e_name = st.text_input("Plan Name", value=str(plan.get("plan_name") or ""), key=f"se_name_{plan['plan_id']}")
                                e_bean = st.text_input("Bean", value=str(plan.get("bean") or ""), key=f"se_bean_{plan['plan_id']}")
                                e_purpose = st.text_input("Purpose", value=str(plan.get("purpose") or ""), key=f"se_purpose_{plan['plan_id']}")
                                current_status = str(plan.get("status") or "Trial")
                                e_status = st.selectbox(
                                    "Status", STATUSES,
                                    index=STATUSES.index(current_status) if current_status in STATUSES else 1,
                                    key=f"se_status_{plan['plan_id']}"
                                )
                            with ec2:
                                e_batch = st.number_input("Batch Size (g)", min_value=0.0, value=float(plan.get("batch_size_g") or 0), step=50.0, key=f"se_batch_{plan['plan_id']}")
                                e_density = st.number_input("Density (g/L)", min_value=0.0, value=float(plan.get("density") or 0), step=1.0, key=f"se_density_{plan['plan_id']}")
                                e_moisture = st.number_input("Moisture (%)", min_value=0.0, value=float(plan.get("moisture") or 0), step=.1, key=f"se_moisture_{plan['plan_id']}")

                            e_goal = st.text_area("Goal", value=str(plan.get("goal") or ""), height=100, key=f"se_goal_{plan['plan_id']}")
                            raw_default = str(edit_data.get("raw_text") or "")
                            e_raw = st.text_area("Juklak Chaty asli", value=raw_default, height=420, key=f"se_raw_{plan['plan_id']}")
                            save_edit = st.form_submit_button("💾 Save Structured Changes", type="primary", use_container_width=True)

                        if save_edit:
                            try:
                                reparsed = parse_chaty_structured(e_raw)
                                rpdb.save_plan(
                                    {
                                        "plan_name": e_name.strip(), "bean": e_bean.strip(),
                                        "purpose": e_purpose.strip(), "goal": e_goal.strip(),
                                        "status": e_status, "batch_size_g": e_batch,
                                        "density": e_density, "moisture": e_moisture,
                                        "source": source,
                                    },
                                    {
                                        "mode": "chaty_structured",
                                        "raw_text": e_raw.strip(),
                                        "sections": reparsed.get("sections", {}),
                                        "status_raw": reparsed.get("status_raw", ""),
                                    },
                                    plan["plan_id"],
                                )
                                st.success(f"Structured plan berhasil diralat: {plan['plan_id']}")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Gagal meralat structured plan: {exc}")

                    else:
                        edit_phases_stored = edit_data.get("phases", {}) or {}
                        with st.form(f"library_edit_form_{plan['plan_id']}"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                e_name = st.text_input("Plan Name", value=str(plan.get("plan_name") or ""), key=f"lib_edit_name_{plan['plan_id']}")
                                e_bean = st.text_input("Bean", value=str(plan.get("bean") or ""), key=f"lib_edit_bean_{plan['plan_id']}")
                                current_purpose = str(plan.get("purpose") or PURPOSES[0])
                                e_purpose = st.selectbox(
                                    "Roast Purpose", PURPOSES,
                                    index=PURPOSES.index(current_purpose) if current_purpose in PURPOSES else 0,
                                    key=f"lib_edit_purpose_{plan['plan_id']}"
                                )
                                current_status = str(plan.get("status") or "Draft")
                                e_status = st.selectbox(
                                    "Status", STATUSES,
                                    index=STATUSES.index(current_status) if current_status in STATUSES else 0,
                                    key=f"lib_edit_status_{plan['plan_id']}"
                                )
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
                                            "plan_name": e_name.strip(), "bean": e_bean.strip(),
                                            "purpose": e_purpose, "goal": e_goal.strip(),
                                            "status": e_status, "batch_size_g": e_batch,
                                            "density": e_density, "moisture": e_moisture,
                                            "source": source,
                                        },
                                        {
                                            "phases": e_phases, "s3_attention": e_s3.strip(),
                                            "too_fast": e_fast.strip(), "too_slow": e_slow.strip(),
                                        },
                                        plan["plan_id"],
                                    )
                                    st.success(f"Plan berhasil diralat: {plan['plan_id']}")
                                    st.rerun()
                                except Exception as exc:
                                    st.error(f"Gagal meralat plan: {exc}")

                with st.expander("⭐ Rate & Evaluation", expanded=False):
                    with st.form("evaluation_form"):
                        rating = st.select_slider(
                            "Rating",
                            options=[0, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
                            value=float(plan.get("rating") or 0)
                        )
                        result_notes = st.text_area("Actual roast result", value=plan.get("result_notes") or "")
                        cupping_notes = st.text_area("Cupping notes", value=plan.get("cupping_notes") or "")
                        mark_used = st.checkbox("Tandai plan dipakai pada roast ini")
                        save_eval = st.form_submit_button("Save Evaluation", type="primary")

                    if save_eval:
                        rpdb.save_evaluation(
                            plan["plan_id"], rating,
                            result_notes.strip(), cupping_notes.strip(), mark_used
                        )
                        st.success("Evaluation tersimpan.")
                        st.rerun()

                with st.expander("Duplicate / Delete", expanded=False):
                    new_name = st.text_input(
                        "New duplicated plan name",
                        value=f"{plan.get('plan_name','')} V2"
                    )
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
