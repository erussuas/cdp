import io
from datetime import date, datetime
from typing import Dict, Tuple
import html

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "0.1.9"
SCORING_VERSION = "CDP_2026_Climate_Basic_Simulator_v1"

CDP_MILESTONES = pd.DataFrame([
    {"Milestone": "Questionnaires & guidance published", "Date": "2026-04-20", "Notes": "CDP 2026 questionnaires/guidance publication week"},
    {"Milestone": "Scoring methodology published / request lists open", "Date": "2026-04-27", "Notes": "Review scoring updates and final questionnaire logic"},
    {"Milestone": "Request list submission deadline", "Date": "2026-06-08", "Notes": "Requester deadline; useful client planning gate"},
    {"Milestone": "Response window opens", "Date": "2026-06-15", "Notes": "Portal opens for respondents"},
    {"Milestone": "Scoring deadline", "Date": "2026-09-14", "Notes": "Submit by this week for scoring eligibility"},
    {"Milestone": "Final unscored response / amendments deadline", "Date": "2026-10-26", "Notes": "Final close; submissions after scoring deadline are not scored"},
    {"Milestone": "Scores released", "Date": "2026-11-30", "Notes": "Expected private/public score release week"},
])
CDP_MILESTONES["Date"] = pd.to_datetime(CDP_MILESTONES["Date"])

ASSESSMENT_TEMPLATE = pd.DataFrame([
    ["Governance & Oversight", "Governance & Oversight", "Board/executive oversight, accountable owners, management responsibility, and approval/sign-off path for the CDP response. Strong governance reduces scoring risk because CDP evaluates whether climate accountability is embedded beyond the sustainability team.", 1.2, "High", "Sustainability / Executive Sponsor", ""],
    ["Reporting Boundary & Organizational Alignment", "Reporting Boundary & Organizational Alignment", "Alignment between CDP reporting boundary, financial reporting boundary, acquisitions/divestitures, legal entities, sites, and countries. Boundary discipline is a major dependency because early CDP setup answers drive downstream questions and scoring pathways.", 1.3, "High", "Finance / Legal / Sustainability", ""],
    ["Scope 1 & 2 Data Readiness Readiness", "Scope 1 & 2 Data Readiness Readiness", "Completeness and quality of fuel, refrigerant, electricity, steam/heat/cooling, emission factors, market-based Scope 2 support, and QA/QC. This is a core scoring driver for climate disclosure.", 1.4, "High", "Energy / Facilities / Data", ""],
    ["Scope 3 Readiness", "Scope 3 Readiness", "Scope 3 category relevance, coverage, data quality, supplier engagement, methodology documentation, exclusions, and restatement approach. Scope 3 is often the biggest gap between basic disclosure and stronger management/leadership performance.", 1.4, "High", "Sustainability / Procurement / Finance", ""],
    ["Targets & Transition Planning", "Targets & Transition Planning", "Climate targets, target coverage, progress tracking, decarbonization roadmap, transition plan credibility, and linkage to business strategy. This drives the ability to demonstrate forward-looking management and leadership readiness.", 1.2, "High", "Sustainability / Strategy", ""],
    ["Risk & Opportunity Integration", "Risk & Opportunity Integration", "Climate risk and opportunity identification, financial impact assessment, enterprise risk integration, time horizons, controls, and response actions. This captures whether CDP responses are strategic and decision-useful rather than merely descriptive.", 1.1, "High", "Risk / Finance / Sustainability", ""],
    ["Data Systems & QA/QC", "Data Systems & QA/QC", "System of record, data lineage, version control, calculation traceability, exception handling, and repeatable QA/QC workflows. This measures whether the disclosure process is auditable and repeatable.", 1.0, "Medium", "IT / Data / PMO", ""],
    ["Evidence & Documentation", "Evidence & Documentation", "Availability of supporting evidence such as invoices, emission-factor sources, REC/EAC documentation, policies, approvals, calculation files, assurance statements, and workpapers. Evidence quality affects confidence and defensibility.", 1.0, "High", "PMO / Sustainability", ""],
    ["Disclosure Narrative Quality Quality", "Disclosure Narrative Quality Quality", "Ability to produce complete, specific, internally consistent CDP narratives for governance, strategy, risks, opportunities, targets, progress, methodologies, and value-chain engagement. This is where many scoring outcomes depend on quality, not just completion.", 1.0, "Medium", "Sustainability", ""],
    ["Optional Nature/Water Applicability", "Optional Nature/Water Applicability", "Initial readiness for water, forests, biodiversity, plastics, ocean, and facility geolocation where applicable. This should stay lightweight unless the client has relevant CDP themes or high-impact sectors.", 0.8, "Medium", "EHS / Sustainability / Procurement", ""],
], columns=["Domain", "Assessment Item", "Readiness Question", "Weight", "Scoring Risk", "Default Owner", "Evidence Needed"])
ASSESSMENT_TEMPLATE["Score (0-5)"] = 0
ASSESSMENT_TEMPLATE["Target Score"] = 4
ASSESSMENT_TEMPLATE["Status"] = "Not assessed"
ASSESSMENT_TEMPLATE["Owner"] = ASSESSMENT_TEMPLATE["Default Owner"]
ASSESSMENT_TEMPLATE["Comments / Notes"] = ""
ASSESSMENT_TEMPLATE["Recommended Action"] = ""

TASK_TEMPLATE = pd.DataFrame([
    ["T-001", "Program setup", "Confirm CDP scope, themes and sector setup", "Sustainability", "2026-04-20", "2026-04-30", "High", "Not Started", 0, "Questionnaires & guidance published", "T-001", "", "Default template", True, False, 0.30, "Governance & Oversight", ""],
    ["T-002", "Governance", "Confirm executive sponsor and CDP RACI", "PMO", "2026-04-27", "2026-05-10", "High", "Not Started", 0, "Scoring methodology published / request lists open", "T-002", "T-001", "Default template", True, False, 0.40, "Governance & Oversight", ""],
    ["T-003", "Boundary", "Reconcile CDP boundary to financial statements", "Finance", "2026-04-27", "2026-05-17", "High", "Not Started", 0, "Scoring methodology published / request lists open", "T-003", "T-001", "Default template", True, False, 0.50, "Reporting Boundary & Organizational Alignment", ""],
    ["T-004", "Data", "Finalize facility/site master list and country coverage", "Facilities / Data", "2026-05-01", "2026-05-24", "High", "Not Started", 0, "Response window opens", "T-004", "T-003", "Default template", True, False, 0.40, "Reporting Boundary & Organizational Alignment", ""],
    ["T-005", "Scope 1", "Collect and validate fuel/refrigerant data", "Facilities", "2026-05-15", "2026-06-21", "High", "Not Started", 0, "Response window opens", "T-005", "T-004", "Default template", True, False, 0.50, "Scope 1 & 2 Data Readiness", ""],
    ["T-006", "Scope 2", "Collect and validate utility data and RECs/EACs", "Energy / UBM", "2026-05-15", "2026-06-28", "High", "Not Started", 0, "Response window opens", "T-006", "T-004", "Default template", True, False, 0.50, "Scope 1 & 2 Data Readiness", ""],
    ["T-007", "Scope 3", "Complete Scope 3 relevance and data mapping", "Sustainability / Procurement", "2026-05-20", "2026-07-12", "High", "Not Started", 0, "Scoring deadline", "T-007", "T-003", "Default template", True, False, 0.60, "Scope 3 Readiness", ""],
    ["T-008", "Nature", "Confirm water/forests/plastics/ocean applicability", "Sustainability / EHS", "2026-05-20", "2026-06-21", "Medium", "Not Started", 0, "Response window opens", "T-008", "T-001", "Default template", True, False, 0.40, "Optional Nature/Water Applicability", ""],
    ["T-009", "Evidence", "Build evidence library and source-control calculations", "PMO / Data", "2026-06-01", "2026-07-19", "High", "Not Started", 0, "Scoring deadline", "T-009", "T-005,T-006,T-007", "Default template", True, False, 0.50, "Evidence & Documentation", ""],
    ["T-010", "Drafting", "Draft CDP response narratives", "Sustainability", "2026-06-15", "2026-08-02", "High", "Not Started", 0, "Response window opens", "T-010", "T-005,T-006,T-007,T-008", "Default template", True, False, 0.50, "Disclosure Narrative Quality", ""],
    ["T-011", "QA/QC", "Run data QA/QC and scoring-risk review", "PMO / Sustainability", "2026-07-20", "2026-08-23", "High", "Not Started", 0, "Scoring deadline", "T-011", "T-009,T-010", "Default template", True, False, 0.40, "Data Systems & QA/QC", ""],
    ["T-012", "Leadership review", "Complete legal, finance and executive review", "Executive sponsor", "2026-08-10", "2026-09-06", "High", "Not Started", 0, "Scoring deadline", "T-012", "T-011", "Default template", True, False, 0.30, "Governance & Oversight", ""],
    ["T-013", "Submission", "Submit CDP response before scoring deadline", "Sustainability", "2026-09-07", "2026-09-14", "High", "Not Started", 0, "Scoring deadline", "T-013", "T-012", "Default template", True, False, 0.20, "Governance & Oversight", ""],
    ["T-014", "Post-submission", "Archive final evidence package and lessons learned", "PMO", "2026-09-15", "2026-10-26", "Medium", "Not Started", 0, "Final unscored response / amendments deadline", "T-014", "T-013", "Default template", True, False, 0.20, "Evidence & Documentation", ""],
], columns=["Task ID", "Workstream", "Task Name", "Owner", "Start Date", "Due Date", "Priority", "Status", "% Complete", "CDP Milestone", "Assessment Link", "Dependencies", "Source", "Include in Gantt?", "Archived?", "Expected Impact", "Linked Domain", "Comments / Notes"])


CLIMATE_SCORING_TEMPLATE = pd.DataFrame([
    ["C0", "Questionnaire setup & boundary", "Required", "Yes", 6, "Partial", "Adequate", "Partial", "Medium", 0.5, "Disclosure", "High", "Low", "Climate setup answers drive downstream applicability. Boundary, reporting period and currency must be consistent."],
    ["C1", "Governance", "Required", "Yes", 10, "Partial", "Adequate", "Partial", "Medium", 0.5, "Management", "Medium", "High", "Board/executive oversight and management accountability are scored beyond simple completion."],
    ["C2", "Risks & opportunities", "Required", "Yes", 12, "Partial", "Adequate", "Partial", "High", 0.5, "Management", "Medium", "High", "Financial impact, time horizons and risk management response are interpretation-heavy."],
    ["C3", "Strategy & transition plan", "Required", "Yes", 12, "Partial", "Adequate", "Partial", "High", 0.5, "Management", "Medium", "High", "Leadership outcomes usually require credible transition-plan evidence, progress and strategy integration."],
    ["C4", "Emissions methodology & boundary", "Required", "Yes", 10, "Partial", "Adequate", "Partial", "High", 0.5, "Management", "High", "Medium", "Consolidation approach, exclusions, base year and restatement logic create scoring gates."],
    ["C5", "Scope 1 & 2 inventory", "Required", "Yes", 14, "Partial", "Adequate", "Partial", "High", 0.5, "Management", "High", "Medium", "Completeness, method, market-based support and evidence drive confidence."],
    ["C6", "Scope 3 inventory", "Required", "Yes", 14, "Partial", "Adequate", "Partial", "High", 0.5, "Awareness", "Medium", "High", "Category relevance, coverage, supplier data quality and exclusions are often the largest scoring risk."],
    ["C7", "Targets & performance", "Required", "Yes", 10, "Partial", "Adequate", "Partial", "Medium", 0.5, "Management", "Medium", "High", "Target coverage, progress and decarbonization levers influence leadership readiness."],
    ["C8", "Verification & assurance", "Important", "Yes", 6, "Missing", "Weak", "Missing", "Medium", 0.5, "Awareness", "High", "Low", "Assurance status is usually clear, but lack of assurance can cap confidence."],
    ["C9", "Engagement & value chain", "Important", "Yes", 6, "Partial", "Adequate", "Partial", "Medium", 0.5, "Awareness", "Medium", "High", "Supplier/customer engagement and public policy narratives require evidence and specificity."],
], columns=["Section ID", "Climate scoring section", "Applicability Type", "Applicable?", "Weight", "Current Response Status", "Disclosure Quality", "Evidence Strength", "Consistency Risk", "Action Plan Impact", "Minimum Level Needed", "Rule Confidence", "Interpretation Risk", "Simulator Notes"])

RESPONSE_STATUS_OPTIONS = ["Missing", "Started", "Partial", "Mostly Complete", "Complete", "Not Applicable"]
DISCLOSURE_QUALITY_OPTIONS = ["Weak", "Adequate", "Strong", "Leadership-ready"]
EVIDENCE_STRENGTH_OPTIONS = ["Missing", "Partial", "Good", "Verified"]
CONSISTENCY_RISK_OPTIONS = ["Low", "Medium", "High"]
SCORING_LEVEL_OPTIONS = ["Disclosure", "Awareness", "Management", "Leadership"]
APPLICABLE_OPTIONS = ["Yes", "No", "Unclear"]

GRADE_BANDS = [
    (0, 24.99, "D", "Disclosure is likely incomplete or highly inconsistent."),
    (25, 44.99, "C", "Core disclosure is present, but management maturity is limited."),
    (45, 64.99, "B", "Good management-level disclosure with material gaps remaining."),
    (65, 79.99, "A-", "Strong disclosure; remaining gaps likely prevent top leadership outcome."),
    (80, 100, "A", "Leadership-level profile, subject to CDP scorer interpretation and evidence quality."),
]

STATUS_OPTIONS = ["Not assessed", "Not Started", "In Progress", "Blocked", "Complete", "Not Applicable"]
TASK_STATUS_OPTIONS = ["Not Started", "In Progress", "Blocked", "Complete", "Deferred"]
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
RISK_OPTIONS = ["High", "Medium", "Low"]
SCORE_OPTIONS = [0, 1, 2, 3, 4, 5]
SOURCE_OPTIONS = ["Default template", "Gap assessment", "Manual action"]
PROFILE_PLACEHOLDERS = {
    "Client Name": "Enter company / client name",
    "Reporting Year End": "YYYY-MM-DD, e.g., 2025-12-31",
    "Primary Sector": "e.g., Manufacturing",
    "Reporting Themes": "e.g., Climate Change, Water, Forests",
    "Currency": "e.g., USD",
    "Assessment Date": "YYYY-MM-DD",
    "Consultant / Team": "Enter consultant or team name",
}


def safe_bool(series, default=False):
    return series.fillna(default).map(lambda x: bool(x) if isinstance(x, (bool, np.bool_)) else str(x).strip().lower() in ["true", "yes", "1", "y"])


def init_state():
    if "client_profile" not in st.session_state:
        st.session_state.client_profile = {
            "Client Name": "",
            "Reporting Year End": "",
            "Primary Sector": "",
            "Reporting Themes": "",
            "Currency": "",
            "Assessment Date": str(date.today()),
            "Consultant / Team": "",
        }
    if "assessment" not in st.session_state:
        st.session_state.assessment = normalize_assessment(ASSESSMENT_TEMPLATE.copy())
    if "tasks" not in st.session_state:
        st.session_state.tasks = normalize_tasks(TASK_TEMPLATE.copy())
    if "climate_simulator" not in st.session_state:
        st.session_state.climate_simulator = normalize_climate_simulator(CLIMATE_SCORING_TEMPLATE.copy())


def normalize_assessment(assessment: pd.DataFrame) -> pd.DataFrame:
    a = assessment.copy()
    for col in ASSESSMENT_TEMPLATE.columns:
        if col not in a.columns:
            a[col] = ASSESSMENT_TEMPLATE[col].iloc[0] if len(ASSESSMENT_TEMPLATE) else ""
    a = a[list(ASSESSMENT_TEMPLATE.columns)]
    a["Weight"] = pd.to_numeric(a["Weight"], errors="coerce").fillna(1.0)
    a["Score (0-5)"] = pd.to_numeric(a["Score (0-5)"], errors="coerce").fillna(0).round().clip(0, 5).astype(int)
    a["Target Score"] = pd.to_numeric(a["Target Score"], errors="coerce").fillna(4).round().clip(0, 5).astype(int)
    for col in ["Domain", "Assessment Item", "Readiness Question", "Scoring Risk", "Default Owner", "Evidence Needed", "Status", "Owner", "Comments / Notes", "Recommended Action"]:
        a[col] = a[col].fillna("").astype(str)
    a.loc[~a["Status"].isin(STATUS_OPTIONS), "Status"] = "Not assessed"
    a.loc[~a["Scoring Risk"].isin(RISK_OPTIONS), "Scoring Risk"] = "Medium"
    return a


def normalize_tasks(tasks: pd.DataFrame) -> pd.DataFrame:
    t = tasks.copy()
    for col in TASK_TEMPLATE.columns:
        if col not in t.columns:
            if col in ["Include in Gantt?"]:
                t[col] = True
            elif col in ["Archived?"]:
                t[col] = False
            elif col == "Expected Impact":
                t[col] = 0.25
            elif col == "Source":
                t[col] = "Manual action"
            else:
                t[col] = ""
    t = t[list(TASK_TEMPLATE.columns)]
    for col in ["Start Date", "Due Date"]:
        t[col] = pd.to_datetime(t[col], errors="coerce")
    t["% Complete"] = pd.to_numeric(t["% Complete"], errors="coerce").fillna(0).clip(0, 100)
    t["Expected Impact"] = pd.to_numeric(t["Expected Impact"], errors="coerce").fillna(0.25).clip(0, 2)
    t["Include in Gantt?"] = safe_bool(t["Include in Gantt?"], True)
    t["Archived?"] = safe_bool(t["Archived?"], False)
    for col in ["Task ID", "Workstream", "Task Name", "Owner", "Priority", "Status", "CDP Milestone", "Assessment Link", "Dependencies", "Source", "Linked Domain", "Comments / Notes"]:
        t[col] = t[col].fillna("").astype(str)
    t.loc[~t["Status"].isin(TASK_STATUS_OPTIONS), "Status"] = "Not Started"
    t.loc[~t["Priority"].isin(PRIORITY_OPTIONS), "Priority"] = "Medium"
    t.loc[~t["Source"].isin(SOURCE_OPTIONS), "Source"] = "Manual action"
    return t



def normalize_climate_simulator(sim: pd.DataFrame) -> pd.DataFrame:
    c = sim.copy()
    # Backward compatibility with v0.1.6 exports
    if "Current Quality (0-5)" in c.columns and "Current Response Status" not in c.columns:
        def quality_to_status(v):
            try: v = float(v)
            except Exception: v = 0
            if v >= 4.5: return "Complete"
            if v >= 3.5: return "Mostly Complete"
            if v >= 2: return "Partial"
            if v > 0: return "Started"
            return "Missing"
        c["Current Response Status"] = c["Current Quality (0-5)"].map(quality_to_status)
    if "Projected Quality (0-5)" in c.columns and "Action Plan Impact" not in c.columns:
        c["Action Plan Impact"] = (pd.to_numeric(c.get("Projected Quality (0-5)", 0), errors="coerce").fillna(0) - pd.to_numeric(c.get("Current Quality (0-5)", 0), errors="coerce").fillna(0)).clip(0, 2)
    if "Target Quality (0-5)" in c.columns and "Minimum Level Needed" not in c.columns:
        c["Minimum Level Needed"] = "Management"

    for col in CLIMATE_SCORING_TEMPLATE.columns:
        if col not in c.columns:
            c[col] = CLIMATE_SCORING_TEMPLATE[col].iloc[0] if len(CLIMATE_SCORING_TEMPLATE) else ""
    c = c[list(CLIMATE_SCORING_TEMPLATE.columns)]
    c["Weight"] = pd.to_numeric(c["Weight"], errors="coerce").fillna(0).clip(0, 100)
    c["Action Plan Impact"] = pd.to_numeric(c["Action Plan Impact"], errors="coerce").fillna(0).clip(0, 2)
    for col in ["Section ID", "Climate scoring section", "Applicability Type", "Applicable?", "Current Response Status", "Disclosure Quality", "Evidence Strength", "Consistency Risk", "Minimum Level Needed", "Rule Confidence", "Interpretation Risk", "Simulator Notes"]:
        c[col] = c[col].fillna("").astype(str)
    c.loc[~c["Applicable?"].isin(APPLICABLE_OPTIONS), "Applicable?"] = "Yes"
    c.loc[~c["Current Response Status"].isin(RESPONSE_STATUS_OPTIONS), "Current Response Status"] = "Partial"
    c.loc[~c["Disclosure Quality"].isin(DISCLOSURE_QUALITY_OPTIONS), "Disclosure Quality"] = "Adequate"
    c.loc[~c["Evidence Strength"].isin(EVIDENCE_STRENGTH_OPTIONS), "Evidence Strength"] = "Partial"
    c.loc[~c["Consistency Risk"].isin(CONSISTENCY_RISK_OPTIONS), "Consistency Risk"] = "Medium"
    c.loc[~c["Minimum Level Needed"].isin(SCORING_LEVEL_OPTIONS), "Minimum Level Needed"] = "Management"
    c.loc[~c["Rule Confidence"].isin(["High", "Medium", "Low"]), "Rule Confidence"] = "Medium"
    c.loc[~c["Interpretation Risk"].isin(["High", "Medium", "Low"]), "Interpretation Risk"] = "Medium"
    return c


def _section_quality_score(row) -> tuple:
    """Return current/projected score on a 0-5 maturity scale and estimated achieved level."""
    status_map = {"Missing": 0.0, "Started": 1.0, "Partial": 2.5, "Mostly Complete": 3.8, "Complete": 4.5, "Not Applicable": 0.0}
    quality_map = {"Weak": 0.5, "Adequate": 2.6, "Strong": 3.8, "Leadership-ready": 4.7}
    evidence_map = {"Missing": 0.0, "Partial": 2.0, "Good": 3.6, "Verified": 4.7}
    risk_penalty = {"Low": 0.0, "Medium": 0.35, "High": 0.8}
    current = (
        0.45 * status_map.get(str(row.get("Current Response Status")), 0)
        + 0.35 * quality_map.get(str(row.get("Disclosure Quality")), 0)
        + 0.20 * evidence_map.get(str(row.get("Evidence Strength")), 0)
        - risk_penalty.get(str(row.get("Consistency Risk")), 0.35)
    )
    current = max(0, min(5, current))
    projected = max(0, min(5, current + float(row.get("Action Plan Impact", 0) or 0)))
    def level(score):
        if score >= 4.25: return "Leadership"
        if score >= 3.25: return "Management"
        if score >= 2.0: return "Awareness"
        if score > 0: return "Disclosure"
        return "None"
    return current, projected, level(current), level(projected)


def estimate_grade(score: float) -> tuple:
    """Convert a 0-100 directional score into a CDP-style estimated band.

    This is not CDP's official scoring methodology. It provides a simple
    planning-oriented band estimate for the simulator and export workbook.
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0.0
    score = max(0.0, min(100.0, score))
    if score >= 90:
        return "A", "Leadership-ready / very strong estimated position"
    if score >= 80:
        return "A-", "Strong estimated position with limited gaps"
    if score >= 65:
        return "B", "Management-level estimated position with material improvement opportunities"
    if score >= 45:
        return "C", "Awareness-level estimated position with significant gaps"
    if score >= 25:
        return "D", "Disclosure-level estimated position; core response buildout needed"
    return "F / Not scorable", "Very limited readiness or major missing inputs"


def compute_climate_score(sim: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    c = normalize_climate_simulator(sim)
    applicable = c[c["Applicable?"].isin(["Yes", "Unclear"])].copy()
    if applicable.empty:
        c["Current Section Score"] = 0.0
        c["Projected Section Score"] = 0.0
        c["Current Level"] = "N/A"
        c["Projected Level"] = "N/A"
        return c, {"Current Climate Score Estimate": 0, "Projected Climate Score Estimate": 0, "Current Estimated Band": "N/A", "Projected Estimated Band": "N/A", "Simulator Confidence %": 0, "Gate / Level Gaps": 0, "Excluded Sections": int((c["Applicable?"] == "No").sum())}

    rows = []
    for _, row in c.iterrows():
        if str(row["Applicable?"]) == "No":
            cur = proj = 0.0; cur_level = proj_level = "N/A"
        else:
            cur, proj, cur_level, proj_level = _section_quality_score(row)
        rows.append((cur, proj, cur_level, proj_level))
    c[["Current Section Score", "Projected Section Score", "Current Level", "Projected Level"]] = pd.DataFrame(rows, index=c.index)

    applicable = c[c["Applicable?"].isin(["Yes", "Unclear"])].copy()
    total_weight = float(applicable["Weight"].sum()) or 1.0
    c["Current Weighted Points"] = np.where(c["Applicable?"].isin(["Yes", "Unclear"]), c["Weight"] * c["Current Section Score"] / 5, 0)
    c["Projected Weighted Points"] = np.where(c["Applicable?"].isin(["Yes", "Unclear"]), c["Weight"] * c["Projected Section Score"] / 5, 0)

    current = float(c["Current Weighted Points"].sum() / total_weight * 100)
    projected = float(c["Projected Weighted Points"].sum() / total_weight * 100)

    level_rank = {"None": 0, "Disclosure": 1, "Awareness": 2, "Management": 3, "Leadership": 4, "N/A": 99}
    needed_rank = {"Disclosure": 1, "Awareness": 2, "Management": 3, "Leadership": 4}
    c["Gate / Level Gap"] = c.apply(lambda r: bool(r["Applicable?"] in ["Yes", "Unclear"] and level_rank.get(r["Current Level"], 0) < needed_rank.get(r["Minimum Level Needed"], 3)), axis=1)
    c["Projected Gate / Level Gap"] = c.apply(lambda r: bool(r["Applicable?"] in ["Yes", "Unclear"] and level_rank.get(r["Projected Level"], 0) < needed_rank.get(r["Minimum Level Needed"], 3)), axis=1)
    c["Scoring Risk Flag"] = c.apply(lambda r: "High" if r["Gate / Level Gap"] or r["Consistency Risk"] == "High" or r["Interpretation Risk"] == "High" else ("Medium" if r["Applicable?"] == "Unclear" or r["Rule Confidence"] == "Medium" else "Low"), axis=1)

    conf_map = {"High": 1.0, "Medium": 0.7, "Low": 0.4}
    interp_map = {"Low": 1.0, "Medium": 0.75, "High": 0.5}
    applicable_weights = applicable["Weight"].replace(0, 1)
    confidence_factor = float(np.average(applicable["Rule Confidence"].map(conf_map), weights=applicable_weights))
    interpretation_factor = float(np.average(applicable["Interpretation Risk"].map(interp_map), weights=applicable_weights))
    unclear_penalty = int((c["Applicable?"] == "Unclear").sum()) * 3
    gate_penalty = int(c["Gate / Level Gap"].sum()) * 2.5
    confidence_pct = max(0, min(100, 100 * confidence_factor * interpretation_factor - unclear_penalty - gate_penalty))

    current_grade, current_desc = estimate_grade(current)
    projected_grade, projected_desc = estimate_grade(projected)
    kpis = {
        "Current Climate Score Estimate": round(current, 1),
        "Projected Climate Score Estimate": round(projected, 1),
        "Current Estimated Band": current_grade,
        "Projected Estimated Band": projected_grade,
        "Current Band Description": current_desc,
        "Projected Band Description": projected_desc,
        "Simulator Confidence %": round(confidence_pct, 1),
        "Gate / Level Gaps": int(c["Gate / Level Gap"].sum()),
        "Projected Gate / Level Gaps": int(c["Projected Gate / Level Gap"].sum()),
        "Excluded Sections": int((c["Applicable?"] == "No").sum()),
        "Unclear Applicability Sections": int((c["Applicable?"] == "Unclear").sum()),
    }
    return c, kpis

def load_workbook(uploaded_file) -> Tuple[Dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    xls = pd.ExcelFile(uploaded_file)
    profile = st.session_state.client_profile.copy()
    if "Client_Profile" in xls.sheet_names:
        p = pd.read_excel(xls, "Client_Profile")
        if {"Field", "Value"}.issubset(p.columns):
            profile.update(dict(zip(p["Field"], p["Value"].astype(str))))
    assessment = ASSESSMENT_TEMPLATE.copy()
    if "Assessment_Inputs" in xls.sheet_names:
        a = pd.read_excel(xls, "Assessment_Inputs")
        assessment = a
    tasks = TASK_TEMPLATE.copy()
    if "Tasks" in xls.sheet_names:
        t = pd.read_excel(xls, "Tasks")
        tasks = t
    climate_simulator = CLIMATE_SCORING_TEMPLATE.copy()
    if "Climate_Score_Simulator" in xls.sheet_names:
        cs = pd.read_excel(xls, "Climate_Score_Simulator")
        climate_simulator = cs
    return profile, normalize_assessment(assessment), normalize_tasks(tasks), normalize_climate_simulator(climate_simulator)


def status_weight(status: str) -> float:
    return {"Not Started": 0.0, "In Progress": 0.5, "Blocked": 0.0, "Complete": 1.0, "Deferred": 0.0}.get(str(status), 0.0)


def compute_domain_projection(assessment: pd.DataFrame, tasks: pd.DataFrame) -> pd.DataFrame:
    a = normalize_assessment(assessment)
    t = normalize_tasks(tasks)
    current = a.groupby("Domain", as_index=False).apply(
        lambda x: pd.Series({
            "Current Readiness": np.average(x["Score (0-5)"], weights=x["Weight"]) if x["Weight"].sum() else 0,
            "Readiness Goal": np.average(x["Target Score"], weights=x["Weight"]) if x["Weight"].sum() else 4,
            "Items": len(x),
            "High Risk Items": int((x["Scoring Risk"] == "High").sum()),
            "Evidence Gaps": int((x["Evidence Needed"].fillna("").str.len() > 0).sum()),
        })
    ).reset_index(drop=True)
    t = t[(~t["Archived?"]) & (t["Linked Domain"].astype(str).str.len() > 0)]
    if len(t):
        t["Weighted Impact"] = t["Expected Impact"] * t["Status"].map(status_weight).fillna(0)
        impact = t.groupby("Linked Domain", as_index=False)["Weighted Impact"].sum().rename(columns={"Linked Domain": "Domain"})
        current = current.merge(impact, on="Domain", how="left")
    else:
        current["Weighted Impact"] = 0.0
    current["Weighted Impact"] = current["Weighted Impact"].fillna(0)
    current["Projected After Action Plan"] = (current["Current Readiness"] + current["Weighted Impact"]).clip(upper=5)
    current["Projected After Action Plan"] = np.minimum(current["Projected After Action Plan"], current["Readiness Goal"].clip(upper=5))
    return current


def compute_scores(assessment: pd.DataFrame, tasks: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    module = compute_domain_projection(assessment, tasks)
    a = normalize_assessment(assessment)
    t = normalize_tasks(tasks)
    overall = np.average(a["Score (0-5)"], weights=a["Weight"]) if a["Weight"].sum() else 0
    goal = np.average(a["Target Score"], weights=a["Weight"]) if a["Weight"].sum() else 4
    projected = module["Projected After Action Plan"].mean() if len(module) else overall
    today = pd.Timestamp.today().normalize()
    open_tasks = t[(~t["Archived?"]) & (~t["Status"].isin(["Complete", "Deferred"]))]
    overdue = int(((open_tasks["Due Date"] < today)).sum())
    blocked = int((t["Status"] == "Blocked").sum())
    high_risk_low_score = int(((a["Scoring Risk"] == "High") & (a["Score (0-5)"] < 3)).sum())
    evidence_completeness = float((a["Evidence Needed"].fillna("").str.len() == 0).mean() * 100) if len(a) else 0
    avg_task_completion = float(t.loc[~t["Archived?"], "% Complete"].mean()) if len(t.loc[~t["Archived?"]]) else 0
    penalty = min(25, high_risk_low_score * 2.5 + overdue * 2 + blocked * 3)
    confidence = max(0, min(100, (overall / 5 * 45) + (projected / 5 * 20) + (avg_task_completion * 0.20) + (evidence_completeness * 0.15) - penalty))
    kpis = {
        "Overall Readiness Score": round(float(overall), 2),
        "Overall Readiness %": round(float(overall / 5 * 100), 1),
        "Readiness Goal Score": round(float(goal), 2),
        "Projected Readiness Score": round(float(projected), 2),
        "Projected Readiness %": round(float(projected / 5 * 100), 1),
        "Submission Confidence %": round(confidence, 1),
        "High-Risk Low-Score Items": high_risk_low_score,
        "Overdue Tasks": overdue,
        "Blocked Tasks": blocked,
        "Average Task Completion %": round(avg_task_completion, 1),
        "Evidence Completeness %": round(evidence_completeness, 1),
    }
    return module, kpis


def next_task_id(tasks: pd.DataFrame) -> str:
    nums = []
    for val in tasks.get("Task ID", []):
        s = str(val)
        if s.startswith("T-"):
            try:
                nums.append(int(s.split("-")[1]))
            except Exception:
                pass
    return f"T-{(max(nums) + 1 if nums else 1):03d}"


def build_gap_bucket(assessment: pd.DataFrame, tasks: pd.DataFrame) -> pd.DataFrame:
    a = normalize_assessment(assessment)
    t = normalize_tasks(tasks)
    existing_links = set(t.loc[~t["Archived?"], "Assessment Link"].astype(str))
    gaps = a[(a["Score (0-5)"] < a["Target Score"]) & (a["Status"] != "Not Applicable")].copy()
    rows = []
    for _, r in gaps.iterrows():
        link = str(r["Assessment Item"])
        if link in existing_links:
            continue
        action = str(r["Recommended Action"]).strip() or f"Address readiness gap: {r['Assessment Item']}"
        gap = max(0, float(r["Target Score"]) - float(r["Score (0-5)"]))
        rows.append({
            "Add?": False,
            "Domain": r["Domain"],
            "Assessment Item": r["Assessment Item"],
            "Suggested Task": action,
            "Owner": r["Owner"] or r["Default Owner"],
            "Priority": r["Scoring Risk"] if r["Scoring Risk"] in PRIORITY_OPTIONS else "Medium",
            "Expected Impact": min(1.0, max(0.25, round(gap * 0.5, 2))),
            "Suggested Due Date": pd.Timestamp("2026-08-15") if r["Scoring Risk"] == "High" else pd.Timestamp("2026-08-31"),
        })
    return pd.DataFrame(rows)


def export_excel(profile: Dict, assessment: pd.DataFrame, tasks: pd.DataFrame, climate_simulator: pd.DataFrame) -> bytes:
    module, kpis = compute_scores(assessment, tasks)
    climate_scoring, climate_kpis = compute_climate_score(climate_simulator)
    profile_df = pd.DataFrame([{"Field": k, "Value": v} for k, v in profile.items()])
    kpi_df = pd.DataFrame([{"Metric": k, "Value": v} for k, v in kpis.items()])
    climate_kpi_df = pd.DataFrame([{"Metric": k, "Value": v} for k, v in climate_kpis.items()])
    milestones = CDP_MILESTONES.copy()
    milestones["Date"] = milestones["Date"].dt.strftime("%Y-%m-%d")
    metadata = pd.DataFrame([
        {"Field": "App Version", "Value": APP_VERSION},
        {"Field": "Scoring Version", "Value": SCORING_VERSION},
        {"Field": "Export Timestamp", "Value": datetime.now().isoformat(timespec="seconds")},
    ])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        profile_df.to_excel(writer, sheet_name="Client_Profile", index=False)
        normalize_assessment(assessment).to_excel(writer, sheet_name="Assessment_Inputs", index=False)
        module.to_excel(writer, sheet_name="Module_Scores", index=False)
        normalize_tasks(tasks).to_excel(writer, sheet_name="Tasks", index=False)
        climate_scoring.to_excel(writer, sheet_name="Climate_Score_Simulator", index=False)
        climate_kpi_df.to_excel(writer, sheet_name="Climate_Score_Summary", index=False)
        milestones.to_excel(writer, sheet_name="CDP_2026_Timeline", index=False)
        kpi_df.to_excel(writer, sheet_name="Executive_Summary", index=False)
        metadata.to_excel(writer, sheet_name="_Metadata", index=False)
        wb = writer.book
        for ws in wb.worksheets:
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.style = "Headline 4"
            for col in ws.columns:
                max_len = 10
                col_letter = col[0].column_letter
                for cell in col:
                    max_len = max(max_len, min(45, len(str(cell.value)) if cell.value is not None else 0))
                ws.column_dimensions[col_letter].width = max_len + 2
    return buffer.getvalue()


def score_label(score):
    if score >= 4: return "Strong"
    if score >= 3: return "Functional"
    if score >= 2: return "Needs Work"
    if score > 0: return "High Risk"
    return "Not Assessed"


def add_gap_tasks(selected_rows: pd.DataFrame):
    tasks = normalize_tasks(st.session_state.tasks)
    new_rows = []
    for _, r in selected_rows.iterrows():
        new_rows.append({
            "Task ID": next_task_id(pd.concat([tasks, pd.DataFrame(new_rows)], ignore_index=True)),
            "Workstream": str(r["Domain"]).split(" & ")[0],
            "Task Name": r["Suggested Task"],
            "Owner": r["Owner"],
            "Start Date": pd.Timestamp.today().normalize(),
            "Due Date": pd.to_datetime(r["Suggested Due Date"], errors="coerce"),
            "Priority": r["Priority"],
            "Status": "Not Started",
            "% Complete": 0,
            "CDP Milestone": "Scoring deadline",
            "Assessment Link": r["Assessment Item"],
            "Dependencies": "",
            "Source": "Gap assessment",
            "Include in Gantt?": True,
            "Archived?": False,
            "Expected Impact": r["Expected Impact"],
            "Linked Domain": r["Domain"],
            "Comments / Notes": "Created from readiness gap assessment.",
        })
    if new_rows:
        st.session_state.tasks = normalize_tasks(pd.concat([tasks, pd.DataFrame(new_rows)], ignore_index=True))


def main():
    st.set_page_config(page_title="CDP 2026 Readiness Assessment", layout="wide")
    init_state()
    st.title("CDP 2026 Readiness Assessment & Action Plan")
    st.caption("Simplified readiness assessment, action planning, Gantt-style timeline, radar forecast, climate score simulator, and Excel import/export.")

    with st.sidebar:
        st.header("Session")
        uploaded = st.file_uploader("Upload prior assessment Excel", type=["xlsx"])
        if uploaded is not None:
            try:
                profile, assessment, tasks, climate_simulator = load_workbook(uploaded)
                st.session_state.client_profile = profile
                st.session_state.assessment = assessment
                st.session_state.tasks = tasks
                st.session_state.climate_simulator = climate_simulator
                st.success("Assessment loaded from workbook.")
            except Exception as e:
                st.error(f"Could not load workbook: {e}")
        if st.button("Reset to blank template"):
            st.session_state.assessment = normalize_assessment(ASSESSMENT_TEMPLATE.copy())
            st.session_state.tasks = normalize_tasks(TASK_TEMPLATE.copy())
            st.session_state.climate_simulator = normalize_climate_simulator(CLIMATE_SCORING_TEMPLATE.copy())
            st.success("Template reset.")
        module, kpis = compute_scores(st.session_state.assessment, st.session_state.tasks)
        st.metric("Current readiness", f"{kpis['Overall Readiness Score']}/5")
        st.metric("Projected readiness", f"{kpis['Projected Readiness Score']}/5")
        st.metric("Submission confidence", f"{kpis['Submission Confidence %']}%")
        xlsx = export_excel(st.session_state.client_profile, st.session_state.assessment, st.session_state.tasks, st.session_state.climate_simulator)
        st.download_button("Export Excel workbook", data=xlsx, file_name="cdp_2026_readiness_assessment.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    tabs = st.tabs(["Client Profile", "Assessment", "Dashboard", "Action Plan / Gantt", "CDP 2026 Timeline", "Summary Report", "Climate Score Simulator"])

    with tabs[0]:
        st.subheader("Client Profile")
        p = st.session_state.client_profile.copy()
        cols = st.columns(2)
        for idx, key in enumerate(list(p.keys())):
            current_value = "" if pd.isna(p[key]) else str(p[key])
            p[key] = cols[idx % 2].text_input(key, value=current_value, placeholder=PROFILE_PLACEHOLDERS.get(key, "Enter value"), key=f"profile_{key}")
        st.session_state.client_profile = p
        st.info("This profile is exported to Excel and reloaded in future sessions.")

    with tabs[1]:
        st.subheader("Readiness Assessment")
        st.write("Score each item from 0 to 5 and set a target readiness level. Recommended actions can be pulled into the action plan from the gap-action bucket.")
        st.session_state.assessment = normalize_assessment(st.session_state.assessment)
        assessment_df = st.session_state.assessment.copy().reset_index(drop=True)
        domain_options = ["All domains"] + sorted(assessment_df["Domain"].dropna().unique().tolist())
        selected_domain = st.selectbox("Filter by domain", domain_options, key="assessment_filter_domain")
        visible_indices = assessment_df.index.tolist() if selected_domain == "All domains" else assessment_df.index[assessment_df["Domain"] == selected_domain].tolist()
        header = st.columns([1.2, 1.55, 0.65, 0.65, 1.0, 0.8, 1.0, 1.6, 1.6, 1.8])
        labels = ["Domain", "Assessment Item", "Current", "Goal", "Status", "Risk", "Owner", "Evidence Needed", "Comments / Notes", "Recommended Action"]
        for h, label in zip(header, labels):
            h.markdown(f"**{label}**")
        for idx in visible_indices:
            row = assessment_df.loc[idx]
            cols = st.columns([1.2, 1.55, 0.65, 0.65, 1.0, 0.8, 1.0, 1.6, 1.6, 1.8])
            rationale = html.escape(str(row.get("Readiness Question", "")))
            item = html.escape(str(row.get("Assessment Item", "")))
            domain = html.escape(str(row.get("Domain", "")))
            cols[0].markdown(f"<span title='{rationale}'>{domain}</span>", unsafe_allow_html=True)
            cols[1].markdown(f"<span title='{rationale}'>ℹ️ {item}</span>", unsafe_allow_html=True)
            for colname, cidx, keyprefix in [("Score (0-5)", 2, "score_select"), ("Target Score", 3, "target_select")]:
                value = int(round(float(row.get(colname, 0))))
                index = SCORE_OPTIONS.index(value) if value in SCORE_OPTIONS else 0
                assessment_df.at[idx, colname] = cols[cidx].selectbox(colname, SCORE_OPTIONS, index=index, key=f"{keyprefix}_{idx}", label_visibility="collapsed")
            status_value = str(row.get("Status", "Not assessed"))
            assessment_df.at[idx, "Status"] = cols[4].selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(status_value) if status_value in STATUS_OPTIONS else 0, key=f"status_select_{idx}", label_visibility="collapsed")
            risk_value = str(row.get("Scoring Risk", "Medium"))
            assessment_df.at[idx, "Scoring Risk"] = cols[5].selectbox("Risk", RISK_OPTIONS, index=RISK_OPTIONS.index(risk_value) if risk_value in RISK_OPTIONS else 1, key=f"risk_select_{idx}", label_visibility="collapsed")
            assessment_df.at[idx, "Owner"] = cols[6].text_input("Owner", value="" if pd.isna(row.get("Owner", "")) else str(row.get("Owner", "")), key=f"owner_input_{idx}", label_visibility="collapsed")
            assessment_df.at[idx, "Evidence Needed"] = cols[7].text_area("Evidence Needed", value="" if pd.isna(row.get("Evidence Needed", "")) else str(row.get("Evidence Needed", "")), key=f"evidence_input_{idx}", height=70, label_visibility="collapsed")
            assessment_df.at[idx, "Comments / Notes"] = cols[8].text_area("Comments / Notes", value="" if pd.isna(row.get("Comments / Notes", "")) else str(row.get("Comments / Notes", "")), key=f"notes_input_{idx}", height=70, label_visibility="collapsed")
            assessment_df.at[idx, "Recommended Action"] = cols[9].text_area("Recommended Action", value="" if pd.isna(row.get("Recommended Action", "")) else str(row.get("Recommended Action", "")), key=f"action_input_{idx}", height=70, label_visibility="collapsed")
        st.session_state.assessment = normalize_assessment(assessment_df)
        with st.expander("Show readiness question details"):
            st.dataframe(st.session_state.assessment[["Domain", "Assessment Item", "Readiness Question", "Default Owner", "Weight"]], use_container_width=True)

    with tabs[2]:
        st.subheader("Visual Scorecard")
        module, kpis = compute_scores(st.session_state.assessment, st.session_state.tasks)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Readiness", f"{kpis['Overall Readiness %']}%", f"{kpis['Overall Readiness Score']}/5")
        c2.metric("Projected Readiness", f"{kpis['Projected Readiness %']}%", f"{kpis['Projected Readiness Score']}/5")
        c3.metric("Submission Confidence", f"{kpis['Submission Confidence %']}%")
        c4.metric("High-Risk Gaps", kpis["High-Risk Low-Score Items"])
        radar = go.Figure()
        theta = module["Domain"].tolist()
        for col, name in [("Current Readiness", "Current readiness state"), ("Readiness Goal", "Readiness goal"), ("Projected After Action Plan", "Projected impact of action plan")]:
            radar.add_trace(go.Scatterpolar(r=module[col].tolist(), theta=theta, fill="toself", name=name))
        radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), showlegend=True, title="Readiness Radar: Current vs Goal vs Action Plan Impact")
        st.plotly_chart(radar, use_container_width=True)
        fig = px.bar(module.sort_values("Current Readiness"), x="Current Readiness", y="Domain", orientation="h", range_x=[0,5], title="Current Readiness by Domain")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Priority Gaps")
        gap_df = st.session_state.assessment.copy()
        gaps = gap_df[(gap_df["Scoring Risk"] == "High") & (gap_df["Score (0-5)"] < gap_df["Target Score"])]
        st.dataframe(gaps[["Domain", "Assessment Item", "Score (0-5)", "Target Score", "Owner", "Recommended Action", "Comments / Notes"]], use_container_width=True)

    with tabs[3]:
        st.subheader("Action Plan & Gantt")
        st.caption("Keep this at an aggregated CDP program level. Use workstreams and major tasks rather than replacing a detailed PM tool.")
        st.session_state.tasks = normalize_tasks(st.session_state.tasks)
        with st.expander("Add actions from readiness gaps", expanded=True):
            gap_bucket = build_gap_bucket(st.session_state.assessment, st.session_state.tasks)
            if gap_bucket.empty:
                st.success("No new gap-derived actions available, or all current gaps already have linked tasks.")
            else:
                if "gap_bucket_select_all" not in st.session_state:
                    st.session_state.gap_bucket_select_all = False
                b1, b2 = st.columns([1, 5])
                if b1.button("Select all"):
                    st.session_state.gap_bucket_select_all = True
                    st.session_state.gap_bucket_editor_version = st.session_state.get("gap_bucket_editor_version", 0) + 1
                if b2.button("Unselect all"):
                    st.session_state.gap_bucket_select_all = False
                    st.session_state.gap_bucket_editor_version = st.session_state.get("gap_bucket_editor_version", 0) + 1
                gap_bucket["Add?"] = bool(st.session_state.gap_bucket_select_all)
                edited_bucket = st.data_editor(
                    gap_bucket,
                    use_container_width=True,
                    key=f"gap_bucket_editor_{st.session_state.get('gap_bucket_editor_version', 0)}",
                    column_config={
                        "Add?": st.column_config.CheckboxColumn("Add?"),
                        "Priority": st.column_config.SelectboxColumn(options=PRIORITY_OPTIONS),
                        "Expected Impact": st.column_config.NumberColumn(min_value=0.0, max_value=2.0, step=0.25),
                        "Suggested Due Date": st.column_config.DateColumn(),
                    },
                    disabled=["Domain", "Assessment Item"],
                )
                selected = edited_bucket[edited_bucket["Add?"] == True]
                if st.button("Add selected gap actions to action plan", disabled=selected.empty):
                    add_gap_tasks(selected)
                    st.success(f"Added {len(selected)} action(s) to the plan.")
                    st.rerun()
        with st.expander("Create a brand new action"):
            domains = sorted(st.session_state.assessment["Domain"].dropna().unique().tolist())
            c1, c2, c3 = st.columns(3)
            new_task_name = c1.text_input("Task name", key="new_task_name")
            new_workstream = c2.text_input("Workstream", key="new_workstream", placeholder="e.g., Scope 3")
            new_owner = c3.text_input("Owner", key="new_owner")
            c4, c5, c6 = st.columns(3)
            new_start = c4.date_input("Start date", value=date.today(), key="new_start")
            new_due = c5.date_input("Due date", value=date(2026, 8, 31), key="new_due")
            new_priority = c6.selectbox("Priority", PRIORITY_OPTIONS, key="new_priority")
            c7, c8, c9 = st.columns(3)
            new_domain = c7.selectbox("Linked readiness domain", [""] + domains, key="new_domain")
            new_impact = c8.number_input("Expected impact", min_value=0.0, max_value=2.0, step=0.25, value=0.25, key="new_impact")
            new_include = c9.checkbox("Include in Gantt?", value=True, key="new_include")
            new_comments = st.text_area("Comments / Notes", key="new_comments")
            if st.button("Create manual action", disabled=(not new_task_name.strip())):
                tasks = normalize_tasks(st.session_state.tasks)
                new_row = pd.DataFrame([{
                    "Task ID": next_task_id(tasks), "Workstream": new_workstream or "Manual", "Task Name": new_task_name, "Owner": new_owner,
                    "Start Date": pd.Timestamp(new_start), "Due Date": pd.Timestamp(new_due), "Priority": new_priority, "Status": "Not Started", "% Complete": 0,
                    "CDP Milestone": "Scoring deadline", "Assessment Link": "", "Dependencies": "", "Source": "Manual action", "Include in Gantt?": new_include,
                    "Archived?": False, "Expected Impact": new_impact, "Linked Domain": new_domain, "Comments / Notes": new_comments,
                }])
                st.session_state.tasks = normalize_tasks(pd.concat([tasks, new_row], ignore_index=True))
                st.success("Manual action created.")
                st.rerun()
        sort_choice = st.radio("Sort action plan by", ["Start Date", "Due Date"], horizontal=True)
        tasks_view = normalize_tasks(st.session_state.tasks).sort_values([sort_choice, "Task ID"], na_position="last").reset_index(drop=True)
        tasks = st.data_editor(
            tasks_view,
            num_rows="dynamic",
            use_container_width=True,
            key="tasks_editor_v015",
            column_config={
                "Start Date": st.column_config.DateColumn(),
                "Due Date": st.column_config.DateColumn(),
                "Status": st.column_config.SelectboxColumn(options=TASK_STATUS_OPTIONS),
                "Priority": st.column_config.SelectboxColumn(options=PRIORITY_OPTIONS),
                "Source": st.column_config.SelectboxColumn(options=SOURCE_OPTIONS),
                "% Complete": st.column_config.NumberColumn(min_value=0, max_value=100, step=5),
                "Expected Impact": st.column_config.NumberColumn(min_value=0.0, max_value=2.0, step=0.25),
                "Include in Gantt?": st.column_config.CheckboxColumn(),
                "Archived?": st.column_config.CheckboxColumn(),
            },
        )
        st.session_state.tasks = normalize_tasks(tasks)
        gantt = st.session_state.tasks.copy()
        gantt = gantt[(gantt["Include in Gantt?"]) & (~gantt["Archived?"])]
        gantt = gantt.dropna(subset=["Start Date", "Due Date"])
        if not gantt.empty:
            fig = px.timeline(gantt, x_start="Start Date", x_end="Due Date", y="Task Name", color="Workstream", hover_data=["Owner", "Priority", "Status", "CDP Milestone", "Source", "Expected Impact"])
            fig.update_yaxes(autorange="reversed")
            for _, row in CDP_MILESTONES.iterrows():
                milestone_date = pd.to_datetime(row["Date"]).strftime("%Y-%m-%d")
                fig.add_vline(x=milestone_date, line_dash="dash")
                fig.add_annotation(x=milestone_date, y=1, yref="paper", text=str(row["Milestone"]), showarrow=False, textangle=-45, yanchor="bottom", font=dict(size=10))
            st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        st.subheader("CDP 2026 Timeline Reference")
        milestone_plot = CDP_MILESTONES.copy()
        # Stagger milestone points vertically so labels do not overlap.
        milestone_plot["Lane"] = [0, 1, 0.35, 1.35, 0.7, 1.7, 0.15][:len(milestone_plot)]
        text_positions = ["top center", "bottom center", "top center", "bottom center", "top center", "bottom center", "top center"][:len(milestone_plot)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=milestone_plot["Date"],
            y=milestone_plot["Lane"],
            mode="lines+markers+text",
            text=milestone_plot["Milestone"],
            textposition=text_positions,
            hovertext=milestone_plot["Notes"],
            hoverinfo="text+x",
            marker=dict(size=11),
            line=dict(width=2),
        ))
        fig.update_layout(title="CDP 2026 Milestones", height=500, yaxis=dict(visible=False, range=[-0.45, 2.15]), margin=dict(t=70, b=40))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(CDP_MILESTONES, use_container_width=True)

    with tabs[5]:
        st.subheader("Summary Report")
        module, kpis = compute_scores(st.session_state.assessment, st.session_state.tasks)
        client = st.session_state.client_profile.get("Client Name", "Client") or "Client"
        st.markdown(f"### {client} — CDP 2026 Readiness Summary")
        st.write(f"Current readiness is **{kpis['Overall Readiness Score']}/5** ({kpis['Overall Readiness %']}%). If the defined action plan is executed as currently statused, projected readiness is **{kpis['Projected Readiness Score']}/5** ({kpis['Projected Readiness %']}%). Submission confidence is **{kpis['Submission Confidence %']}%**.")
        summary = module.copy()
        summary["Status"] = summary["Current Readiness"].apply(score_label)
        st.dataframe(summary[["Domain", "Current Readiness", "Projected After Action Plan", "Readiness Goal", "Status", "Items", "High Risk Items", "Evidence Gaps"]], use_container_width=True)
        st.markdown("#### Recommended management focus")
        gap_df = normalize_assessment(st.session_state.assessment)
        top = gap_df.sort_values(["Score (0-5)", "Scoring Risk"]).head(8)
        for _, r in top.iterrows():
            st.write(f"- **{r['Domain']} — {r['Assessment Item']}**: current {r['Score (0-5)']}/5; goal {r['Target Score']}/5; owner: {r['Owner']}; action: {r['Recommended Action'] or 'Define remediation action.'}")

    with tabs[6]:
        st.subheader("Climate Change Score Simulator")
        st.caption("Basic directional simulator for CDP 2026 climate disclosure. It models applicability, response completeness, disclosure quality, evidence strength, consistency risk, action-plan uplift, and practical score-level gates. It is not an official CDP score prediction.")
        st.session_state.climate_simulator = normalize_climate_simulator(st.session_state.climate_simulator)
        sim, sim_kpis = compute_climate_score(st.session_state.climate_simulator)

        left, right = st.columns([0.36, 0.64])
        with left:
            m1, m2 = st.columns(2)
            m1.metric("Current estimate", f"{sim_kpis['Current Estimated Band']}", f"{sim_kpis['Current Climate Score Estimate']}/100")
            m2.metric("Projected estimate", f"{sim_kpis['Projected Estimated Band']}", f"{sim_kpis['Projected Climate Score Estimate']}/100")
            m3, m4 = st.columns(2)
            m3.metric("Confidence", f"{sim_kpis['Simulator Confidence %']}%")
            m4.metric("Gate / level gaps", sim_kpis["Gate / Level Gaps"])
        with right:
            radar_df_top = sim[sim["Applicable?"].isin(["Yes", "Unclear"])].copy()
            if not radar_df_top.empty:
                radar_top = go.Figure()
                theta_top = radar_df_top["Climate scoring section"].tolist()
                radar_top.add_trace(go.Scatterpolar(r=radar_df_top["Current Section Score"].tolist(), theta=theta_top, fill="toself", name="Current"))
                radar_top.add_trace(go.Scatterpolar(r=radar_df_top["Projected Section Score"].tolist(), theta=theta_top, fill="toself", name="Projected"))
                level_to_score_top = {"Disclosure": 1.5, "Awareness": 2.5, "Management": 3.5, "Leadership": 4.5}
                radar_top.add_trace(go.Scatterpolar(r=radar_df_top["Minimum Level Needed"].map(level_to_score_top).fillna(3.5).tolist(), theta=theta_top, fill="toself", name="Target/gate"))
                radar_top.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), showlegend=True, title="Climate scoring radar", height=360, margin=dict(t=50, b=20))
                st.plotly_chart(radar_top, use_container_width=True)

        st.markdown("#### How to use this table")
        st.write("Adjust the editable fields to reflect what you expect the company can support in its CDP Climate response. The tool calculates current and projected scoring contribution, highlights practical scoring gates, and estimates the likely band.")
        st.info("Keep this basic version at the section level. It is meant for planning and advisory judgment, not question-by-question official scoring replication.")

        editable_cols = [
            "Section ID", "Climate scoring section", "Applicability Type", "Applicable?", "Weight",
            "Current Response Status", "Disclosure Quality", "Evidence Strength", "Consistency Risk",
            "Action Plan Impact", "Minimum Level Needed", "Rule Confidence", "Interpretation Risk", "Simulator Notes"
        ]
        edited_sim = st.data_editor(
            sim[editable_cols],
            use_container_width=True,
            key="climate_score_simulator_editor_v017_basic",
            column_config={
                "Applicable?": st.column_config.SelectboxColumn(options=APPLICABLE_OPTIONS),
                "Current Response Status": st.column_config.SelectboxColumn(options=RESPONSE_STATUS_OPTIONS),
                "Disclosure Quality": st.column_config.SelectboxColumn(options=DISCLOSURE_QUALITY_OPTIONS),
                "Evidence Strength": st.column_config.SelectboxColumn(options=EVIDENCE_STRENGTH_OPTIONS),
                "Consistency Risk": st.column_config.SelectboxColumn(options=CONSISTENCY_RISK_OPTIONS),
                "Action Plan Impact": st.column_config.NumberColumn(min_value=0.0, max_value=2.0, step=0.25, help="Expected 0-2 point maturity uplift from the selected action plan."),
                "Minimum Level Needed": st.column_config.SelectboxColumn(options=SCORING_LEVEL_OPTIONS, help="Practical score level this section likely needs to support the desired overall result."),
                "Weight": st.column_config.NumberColumn(min_value=0, max_value=100, step=1),
                "Rule Confidence": st.column_config.SelectboxColumn(options=["High", "Medium", "Low"]),
                "Interpretation Risk": st.column_config.SelectboxColumn(options=["High", "Medium", "Low"]),
            },
            disabled=["Section ID", "Applicability Type"],
        )
        st.session_state.climate_simulator = normalize_climate_simulator(edited_sim)
        sim, sim_kpis = compute_climate_score(st.session_state.climate_simulator)

        st.markdown("#### Calculated scoring view")
        calc_cols = [
            "Climate scoring section", "Applicable?", "Current Section Score", "Projected Section Score",
            "Current Level", "Projected Level", "Minimum Level Needed", "Gate / Level Gap",
            "Projected Gate / Level Gap", "Scoring Risk Flag", "Current Weighted Points", "Projected Weighted Points"
        ]
        st.dataframe(sim[calc_cols], use_container_width=True)


        st.markdown("#### Priority scoring risks")
        risks = sim[(sim["Applicable?"].isin(["Yes", "Unclear"])) & ((sim["Gate / Level Gap"]) | (sim["Scoring Risk Flag"] == "High"))].copy()
        if risks.empty:
            st.success("No high scoring-risk sections are flagged under current assumptions.")
        else:
            st.dataframe(risks[["Climate scoring section", "Current Level", "Minimum Level Needed", "Current Response Status", "Disclosure Quality", "Evidence Strength", "Consistency Risk", "Interpretation Risk", "Simulator Notes"]], use_container_width=True)

        st.markdown("#### Interpretation")
        st.write(f"Current estimated band is **{sim_kpis['Current Estimated Band']}**: {sim_kpis['Current Band Description']}")
        st.write(f"Projected estimated band is **{sim_kpis['Projected Estimated Band']}**: {sim_kpis['Projected Band Description']}")
        st.write("The confidence score is reduced when applicability is unclear, rule confidence is low, interpretation risk is high, or practical gates are not met.")

if __name__ == "__main__":
    main()
