from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from utils.cis_theme import apply_cis_theme
import utils.roasting_plan_database as rpdb

st.set_page_config(page_title="Roasting Plan", page_icon="🔥", layout="wide")
apply_cis_theme()

st.markdown("""
<style>
.plan-hero,.guide-card,.phase-card{border:1px solid rgba(92,255,174,.28);border-radius:18px;background:linear-gradient(180deg,rgba(13,35,25,.94),rgba(7,22,15,.94));box-shadow:0 0 16px rgba(72,245,163,.10)}
.plan-hero{padding:1.25rem 1.35rem;margin-bottom:1rem}.plan-kicker{color:#95ffd0;font-size:.76rem;letter-spacing:.16em;font-weight:800}.guide-card{padding:1.2rem 1.3rem;margin:.7rem 0}.phase-card{padding:1rem 1.1rem;margin:.65rem 0}.phase-title{color:#95ffd0;font-size:1.15rem;font-weight:800;margin-bottom:.45rem}.phase-line{font-size:1rem;color:#f2fff7;line-height:1.65}.muted{color:#b8d2c1}.rating{color:#ffd75e;font-size:1.2rem}.guide-goal{font-size:1.08rem;color:#f2fff7;line-height:1.6}.s3{border-left:4px solid #95ffd0;padding-left:1rem}.stButton>button{border-radius:12px;font-weight:750}
@media(max-width:768px){.plan-hero{padding:1rem}.guide-card{padding:1rem}.phase-card{padding:.85rem}.phase-line{font-size:.96rem}.block-container{padding-top:1rem!important}}
</style>
""", unsafe_allow_html=True)

try:
    rpdb.create_database()
except Exception as exc:
    st.error(f"Roasting Plan database belum siap: {exc}")
    st.stop()

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
      <div class="phase-line"><strong>1 · PREHEAT / CHARGE</strong><br>{esc(compact_line(preheat))}<br>{esc(preheat.get('notes'))}</div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>2 · DRYING GATES</strong><br>{esc(drying.get('steps'))}<br><span class="muted">Target: {esc(compact_line(drying))}</span></div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>3 · MAILLARD GATES</strong><br>{esc(maillard.get('steps'))}<br><span class="muted">Target: {esc(compact_line(maillard))}</span></div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>4 · FIRST CRACK → DEVELOPMENT</strong><br>FC: {esc(compact_line(fc))}<br>DEV: {esc(compact_line(development))}</div>
      <hr style="border-color:rgba(92,255,174,.18)">
      <div class="phase-line"><strong>5 · DROP / COOLING</strong><br>{esc(compact_line(drop))}<br>{esc(drop.get('steps'))}</div>
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
          <div class="phase-line"><strong>{esc(headline)}</strong></div>
          <div class="phase-line">{esc(p.get('steps'))}</div>
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


st.markdown("""
<div class="plan-hero"><div class="plan-kicker">CIS UTILITY · TABLET ROAST COMPANION</div>
<h1 style="margin:.25rem 0">🔥 Roasting Plan</h1>
<div class="muted">Plan manual → S³ Guide Mode → evaluate → rate → recall.</div></div>
""", unsafe_allow_html=True)

create_tab, library_tab = st.tabs(["➕ Create / Edit Plan", "📚 Plan Library & Guide"])

with create_tab:
    plans = rpdb.get_all_plans()
    edit_options = {"New Plan": None}
    if not plans.empty:
        edit_options.update({f"{r.plan_id} · {r.plan_name}": r.plan_id for r in plans.itertuples(index=False)})
    selected_label = st.selectbox("Mode", list(edit_options.keys()))
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
            st.info("Template awal terisi lengkap memakai baseline Arabika Aroma yang editable. Ubah setiap angka sesuai bean, purpose, density, moisture, dan target roast aktual.")

        phases = {}
        stored_phases = pdata.get("phases", {})
        for phase in PHASES:
            with st.expander(phase, expanded=phase in ["Preheat", "Drying"]):
                phase_values = stored_phases.get(phase, {}) if current else DEFAULT_PHASES.get(phase, {})
                phases[phase] = phase_form(phase, phase_values, selected_id or "new")

        st.markdown("#### S³ Control")
        s3_attention = st.text_area("S³ Attention", value=pdata.get("s3_attention", "Simple: perubahan hanya pada checkpoint.\nFlexible: koreksi hanya bila roast keluar dari rentang.\nSustainable: jangan mengejar angka dengan adjustment berulang."), height=110)
        cfast, cslow = st.columns(2)
        too_fast = cfast.text_area("Jika roast terlalu cepat", value=pdata.get("too_fast", ""), height=100)
        too_slow = cslow.text_area("Jika roast tertinggal", value=pdata.get("too_slow", ""), height=100)
        submitted = st.form_submit_button("💾 Save Roasting Plan", type="primary", use_container_width=True)

    if submitted:
        if not plan_name.strip() or not bean.strip() or not goal.strip():
            st.error("Plan Name, Bean, dan Goal wajib diisi.")
        else:
            try:
                plan_id = rpdb.save_plan(
                    {"plan_name": plan_name.strip(), "bean": bean.strip(), "purpose": purpose, "goal": goal.strip(), "status": status, "batch_size_g": batch_size, "density": density, "moisture": moisture},
                    {"phases": phases, "s3_attention": s3_attention.strip(), "too_fast": too_fast.strip(), "too_slow": too_slow.strip()},
                    selected_id,
                )
                st.success(f"Roasting Plan tersimpan: {plan_id}")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menyimpan plan: {exc}")

with library_tab:
    plans = rpdb.get_all_plans()
    if plans.empty:
        st.info("Belum ada Roasting Plan.")
    else:
        q1, q2, q3 = st.columns([2,1,1])
        query = q1.text_input("Search", placeholder="Bean, plan, goal, purpose")
        purpose_filter = q2.selectbox("Purpose", ["All"] + sorted(plans["purpose"].dropna().astype(str).unique().tolist()))
        status_filter = q3.selectbox("Status", ["All"] + STATUSES)
        filtered = plans.copy()
        if query.strip():
            hay = filtered[["plan_name","bean","goal","purpose"]].fillna("").astype(str)
            mask = hay.apply(lambda col: col.str.contains(query.strip(), case=False, regex=False)).any(axis=1)
            filtered = filtered[mask]
        if purpose_filter != "All": filtered = filtered[filtered["purpose"] == purpose_filter]
        if status_filter != "All": filtered = filtered[filtered["status"] == status_filter]

        labels = {f"{r.plan_id} · {r.plan_name} · {r.bean} · ⭐ {float(r.rating):.1f}": r.plan_id for r in filtered.itertuples(index=False)}
        if not labels:
            st.warning("Tidak ada plan yang cocok.")
        else:
            chosen = st.selectbox("Open Plan", list(labels.keys()))
            plan = rpdb.get_plan(labels[chosen])
            if plan:
                render_guide(plan)
                st.caption(f"Used {int(plan.get('usage_count') or 0)}× · Last used: {plan.get('last_used_at') or '—'} · Updated: {plan.get('updated_at') or '—'}")

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
