import io
from datetime import date, datetime
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "0.1.0"
SCORING_VERSION = "CDP_2026_Readiness_v1"

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
    # Governance
    ["Governance & Accountability", "CDP process owner assigned", "Is there a clearly accountable owner for the full CDP response process?", 1.1, "High", "Sustainability", ""],
    ["Governance & Accountability", "Executive sponsor engaged", "Is there an executive sponsor who can unblock cross-functional issues?", 1.0, "High", "Executive sponsor", ""],
    ["Governance & Accountability", "Board / committee oversight documented", "Is climate/environmental oversight documented and current?", 0.9, "Medium", "Legal / Sustainability", ""],
    ["Governance & Accountability", "Final review and sign-off process defined", "Is there a documented path for legal, finance and executive approval?", 1.0, "High", "PMO", ""],
    # Boundary
    ["Reporting Boundary & Setup", "Financial boundary alignment", "Is the CDP boundary aligned to financial statements or clearly reconciled?", 1.3, "High", "Finance", ""],
    ["Reporting Boundary & Setup", "M&A / divestiture treatment", "Are acquisitions, divestitures, JVs and exclusions identified and documented?", 1.1, "High", "Finance / Legal", ""],
    ["Reporting Boundary & Setup", "Facility master data complete", "Is the facility/site list complete and aligned to the selected boundary?", 1.2, "High", "Facilities / Data", ""],
    ["Reporting Boundary & Setup", "Questionnaire setup logic validated", "Have sector, theme, country and supply-chain setup answers been reviewed before downstream entry?", 1.1, "High", "Sustainability", ""],
    # Financial
    ["Financial Alignment", "Reporting year aligned", "Does environmental reporting align with financial reporting period?", 1.0, "Medium", "Finance", ""],
    ["Financial Alignment", "Revenue/currency inputs confirmed", "Are revenue and reporting currency ready and consistent with CDP setup?", 0.8, "Medium", "Finance", ""],
    ["Financial Alignment", "Financial impact methodology", "Are risk/opportunity financial impact assumptions and data sources defined?", 1.1, "High", "Finance / Risk", ""],
    # Scope 1/2
    ["Scope 1 & 2 Data", "Fuel data complete", "Are stationary and mobile fuel data complete for the reporting year?", 1.1, "High", "Facilities", ""],
    ["Scope 1 & 2 Data", "Refrigerants and fugitive emissions captured", "Are refrigerant inventories, leakage, and service records captured?", 1.0, "High", "Facilities", ""],
    ["Scope 1 & 2 Data", "Utility data complete", "Are electricity/steam/heat/cooling data complete for all in-boundary sites?", 1.3, "High", "Energy / UBM", ""],
    ["Scope 1 & 2 Data", "Market-based Scope 2 support", "Are supplier factors, residual mix, RECs/EACs and market instruments documented?", 1.2, "High", "Energy Procurement", ""],
    ["Scope 1 & 2 Data", "Emission factors version-controlled", "Are emission factor sources, years, and methodologies documented?", 0.9, "Medium", "Data / Sustainability", ""],
    # Scope 3
    ["Scope 3 Data", "Category relevance screening", "Have all Scope 3 categories been assessed for relevance?", 1.2, "High", "Sustainability", ""],
    ["Scope 3 Data", "Purchased goods/services methodology", "Is category 1 methodology documented with spend/activity data and factors?", 1.3, "High", "Procurement / Finance", ""],
    ["Scope 3 Data", "Supplier engagement data", "Are supplier-specific data requests, coverage and quality tracked?", 1.1, "High", "Procurement", ""],
    ["Scope 3 Data", "Historical/restatement approach", "Is there a documented approach for prior-year data and restatements?", 1.0, "Medium", "Sustainability / Finance", ""],
    # Nature
    ["Water / Forests / Nature", "Water relevance and withdrawals", "Are water-relevant sites, withdrawals, discharges and stress indicators available?", 1.0, "Medium", "EHS / Facilities", ""],
    ["Water / Forests / Nature", "Facility geolocation readiness", "Can geolocation data be provided for all or material facilities?", 0.8, "Medium", "Facilities / Data", ""],
    ["Water / Forests / Nature", "Forests/nature applicability", "Have commodity, biodiversity, plastics and ocean applicability questions been reviewed?", 0.8, "Medium", "Sustainability / Procurement", ""],
    # Systems
    ["Systems & Data Architecture", "System of record identified", "Is there a clear system of record for emissions/activity data?", 1.1, "High", "IT / Data", ""],
    ["Systems & Data Architecture", "Data lineage and audit trail", "Can data be traced from source to calculation to disclosure?", 1.2, "High", "Data / Sustainability", ""],
    ["Systems & Data Architecture", "QA/QC workflow", "Is there a repeatable QA/QC process with exception tracking?", 1.1, "High", "PMO / Data", ""],
    # Evidence/Narrative
    ["Evidence & Auditability", "Evidence library defined", "Is there a structured library for invoices, policies, calculations and approvals?", 1.1, "High", "PMO", ""],
    ["Evidence & Auditability", "Third-party assurance status", "Is GHG assurance or verification available/planned?", 1.0, "High", "Sustainability / Assurance", ""],
    ["Disclosure Narrative", "Climate risk and opportunity narrative", "Are risk/opportunity narratives supported by analysis and financial assumptions?", 1.0, "High", "Risk / Sustainability", ""],
    ["Disclosure Narrative", "Transition plan and targets narrative", "Are targets, progress, transition plan and decarbonization actions documented?", 1.2, "High", "Sustainability", ""],
], columns=["Domain", "Assessment Item", "Readiness Question", "Weight", "Scoring Risk", "Default Owner", "Evidence Needed"])
ASSESSMENT_TEMPLATE["Score (0-5)"] = 0
ASSESSMENT_TEMPLATE["Status"] = "Not assessed"
ASSESSMENT_TEMPLATE["Owner"] = ASSESSMENT_TEMPLATE["Default Owner"]
ASSESSMENT_TEMPLATE["Comments / Notes"] = ""
ASSESSMENT_TEMPLATE["Recommended Action"] = ""

TASK_TEMPLATE = pd.DataFrame([
    ["T-001", "Program setup", "Confirm CDP scope, themes and sector setup", "Sustainability", "2026-04-20", "2026-04-30", "High", "Not Started", 0, "Questionnaires & guidance published", "", ""],
    ["T-002", "Governance", "Confirm executive sponsor and CDP RACI", "PMO", "2026-04-27", "2026-05-10", "High", "Not Started", 0, "Scoring methodology published / request lists open", "T-001", ""],
    ["T-003", "Boundary", "Reconcile CDP boundary to financial statements", "Finance", "2026-04-27", "2026-05-17", "High", "Not Started", 0, "Scoring methodology published / request lists open", "T-001", ""],
    ["T-004", "Data", "Finalize facility/site master list and country coverage", "Facilities / Data", "2026-05-01", "2026-05-24", "High", "Not Started", 0, "Response window opens", "T-003", ""],
    ["T-005", "Scope 1", "Collect and validate fuel/refrigerant data", "Facilities", "2026-05-15", "2026-06-21", "High", "Not Started", 0, "Response window opens", "T-004", ""],
    ["T-006", "Scope 2", "Collect and validate utility data and RECs/EACs", "Energy / UBM", "2026-05-15", "2026-06-28", "High", "Not Started", 0, "Response window opens", "T-004", ""],
    ["T-007", "Scope 3", "Complete Scope 3 relevance and data mapping", "Sustainability / Procurement", "2026-05-20", "2026-07-12", "High", "Not Started", 0, "Scoring deadline", "T-003", ""],
    ["T-008", "Nature", "Confirm water/forests/plastics/ocean applicability", "Sustainability / EHS", "2026-05-20", "2026-06-21", "Medium", "Not Started", 0, "Response window opens", "T-001", ""],
    ["T-009", "Evidence", "Build evidence library and source-control calculations", "PMO / Data", "2026-06-01", "2026-07-19", "High", "Not Started", 0, "Scoring deadline", "T-005,T-006,T-007", ""],
    ["T-010", "Drafting", "Draft CDP response narratives", "Sustainability", "2026-06-15", "2026-08-02", "High", "Not Started", 0, "Response window opens", "T-005,T-006,T-007,T-008", ""],
    ["T-011", "QA/QC", "Run data QA/QC and scoring-risk review", "PMO / Sustainability", "2026-07-20", "2026-08-23", "High", "Not Started", 0, "Scoring deadline", "T-009,T-010", ""],
    ["T-012", "Leadership review", "Complete legal, finance and executive review", "Executive sponsor", "2026-08-10", "2026-09-06", "High", "Not Started", 0, "Scoring deadline", "T-011", ""],
    ["T-013", "Submission", "Submit CDP response before scoring deadline", "Sustainability", "2026-09-07", "2026-09-14", "High", "Not Started", 0, "Scoring deadline", "T-012", ""],
    ["T-014", "Post-submission", "Archive final evidence package and lessons learned", "PMO", "2026-09-15", "2026-10-26", "Medium", "Not Started", 0, "Final unscored response / amendments deadline", "T-013", ""],
], columns=["Task ID", "Workstream", "Task Name", "Owner", "Start Date", "Due Date", "Priority", "Status", "% Complete", "CDP Milestone", "Dependencies", "Comments / Notes"])

STATUS_OPTIONS = ["Not assessed", "Not Started", "In Progress", "Blocked", "Complete", "Not Applicable"]
TASK_STATUS_OPTIONS = ["Not Started", "In Progress", "Blocked", "Complete", "Deferred"]
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
RISK_OPTIONS = ["High", "Medium", "Low"]


def init_state():
    if "client_profile" not in st.session_state:
        st.session_state.client_profile = {
            "Client Name": "Example Client",
            "Reporting Year End": "2025-12-31",
            "Primary Sector": "Manufacturing",
            "Reporting Themes": "Climate Change",
            "Currency": "USD",
            "Assessment Date": str(date.today()),
            "Consultant / Team": "",
        }
    if "assessment" not in st.session_state:
        st.session_state.assessment = ASSESSMENT_TEMPLATE.copy()
    if "tasks" not in st.session_state:
        st.session_state.tasks = TASK_TEMPLATE.copy()


def load_workbook(uploaded_file) -> Tuple[Dict, pd.DataFrame, pd.DataFrame]:
    xls = pd.ExcelFile(uploaded_file)
    profile = st.session_state.client_profile.copy()
    if "Client_Profile" in xls.sheet_names:
        p = pd.read_excel(xls, "Client_Profile")
        if {"Field", "Value"}.issubset(p.columns):
            profile.update(dict(zip(p["Field"], p["Value"].astype(str))))
    assessment = ASSESSMENT_TEMPLATE.copy()
    if "Assessment_Inputs" in xls.sheet_names:
        a = pd.read_excel(xls, "Assessment_Inputs")
        for col in assessment.columns:
            if col not in a.columns:
                a[col] = assessment[col].iloc[0] if len(assessment) else ""
        assessment = a[assessment.columns]
    tasks = TASK_TEMPLATE.copy()
    if "Tasks" in xls.sheet_names:
        t = pd.read_excel(xls, "Tasks")
        for col in tasks.columns:
            if col not in t.columns:
                t[col] = ""
        tasks = t[tasks.columns]
    return profile, assessment, tasks


def compute_scores(assessment: pd.DataFrame, tasks: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    a = assessment.copy()
    a["Score (0-5)"] = pd.to_numeric(a["Score (0-5)"], errors="coerce").fillna(0).clip(0, 5)
    a["Weight"] = pd.to_numeric(a["Weight"], errors="coerce").fillna(1)
    module = a.groupby("Domain", as_index=False).apply(
        lambda x: pd.Series({
            "Weighted Score": np.average(x["Score (0-5)"], weights=x["Weight"]) if x["Weight"].sum() else 0,
            "Items": len(x),
            "High Risk Items": int((x["Scoring Risk"] == "High").sum()),
            "Evidence Gaps": int((x["Evidence Needed"].fillna("").str.len() > 0).sum()),
        })
    ).reset_index(drop=True)
    overall = np.average(a["Score (0-5)"], weights=a["Weight"]) if a["Weight"].sum() else 0
    task_status = tasks.copy()
    task_status["% Complete"] = pd.to_numeric(task_status["% Complete"], errors="coerce").fillna(0).clip(0, 100)
    task_status["Due Date"] = pd.to_datetime(task_status["Due Date"], errors="coerce")
    today = pd.Timestamp.today().normalize()
    overdue = int(((task_status["Due Date"] < today) & (~task_status["Status"].isin(["Complete", "Deferred"]))).sum())
    blocked = int((task_status["Status"] == "Blocked").sum())
    high_risk_low_score = int(((a["Scoring Risk"] == "High") & (a["Score (0-5)"] < 3)).sum())
    evidence_completeness = float((a["Evidence Needed"].fillna("").str.len() == 0).mean() * 100) if len(a) else 0
    avg_task_completion = float(task_status["% Complete"].mean()) if len(task_status) else 0
    # Blended submission confidence: readiness, task progress, open risks, evidence.
    penalty = min(25, high_risk_low_score * 2.5 + overdue * 2 + blocked * 3)
    confidence = max(0, min(100, (overall / 5 * 55) + (avg_task_completion * 0.25) + (evidence_completeness * 0.20) - penalty))
    kpis = {
        "Overall Readiness Score": round(float(overall), 2),
        "Overall Readiness %": round(float(overall / 5 * 100), 1),
        "Submission Confidence %": round(confidence, 1),
        "High-Risk Low-Score Items": high_risk_low_score,
        "Overdue Tasks": overdue,
        "Blocked Tasks": blocked,
        "Average Task Completion %": round(avg_task_completion, 1),
        "Evidence Completeness %": round(evidence_completeness, 1),
    }
    return module, kpis


def export_excel(profile: Dict, assessment: pd.DataFrame, tasks: pd.DataFrame) -> bytes:
    module, kpis = compute_scores(assessment, tasks)
    profile_df = pd.DataFrame([{"Field": k, "Value": v} for k, v in profile.items()])
    kpi_df = pd.DataFrame([{"Metric": k, "Value": v} for k, v in kpis.items()])
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
        assessment.to_excel(writer, sheet_name="Assessment_Inputs", index=False)
        module.to_excel(writer, sheet_name="Module_Scores", index=False)
        tasks.to_excel(writer, sheet_name="Tasks", index=False)
        milestones.to_excel(writer, sheet_name="CDP_2026_Timeline", index=False)
        kpi_df.to_excel(writer, sheet_name="Executive_Summary", index=False)
        metadata.to_excel(writer, sheet_name="_Metadata", index=False)
        # basic formatting
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


def main():
    st.set_page_config(page_title="CDP 2026 Readiness Assessment", layout="wide")
    init_state()
    st.title("CDP 2026 Readiness Assessment & Action Plan")
    st.caption("Reusable assessment, dashboard, Excel export/import, and CDP timeline-based project planning.")

    with st.sidebar:
        st.header("Session")
        uploaded = st.file_uploader("Upload prior assessment Excel", type=["xlsx"])
        if uploaded is not None:
            try:
                profile, assessment, tasks = load_workbook(uploaded)
                st.session_state.client_profile = profile
                st.session_state.assessment = assessment
                st.session_state.tasks = tasks
                st.success("Assessment loaded from workbook.")
            except Exception as e:
                st.error(f"Could not load workbook: {e}")
        if st.button("Reset to blank template"):
            st.session_state.assessment = ASSESSMENT_TEMPLATE.copy()
            st.session_state.tasks = TASK_TEMPLATE.copy()
            st.success("Template reset.")

        module, kpis = compute_scores(st.session_state.assessment, st.session_state.tasks)
        st.metric("Overall readiness", f"{kpis['Overall Readiness Score']}/5")
        st.metric("Submission confidence", f"{kpis['Submission Confidence %']}%")
        xlsx = export_excel(st.session_state.client_profile, st.session_state.assessment, st.session_state.tasks)
        st.download_button("Export Excel workbook", data=xlsx, file_name="cdp_2026_readiness_assessment.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    tabs = st.tabs(["Client Profile", "Assessment", "Dashboard", "Action Plan / Gantt", "CDP 2026 Timeline", "Summary Report"])

    with tabs[0]:
        st.subheader("Client Profile")
        p = st.session_state.client_profile.copy()
        cols = st.columns(2)
        for idx, key in enumerate(list(p.keys())):
            p[key] = cols[idx % 2].text_input(key, value=str(p[key]))
        st.session_state.client_profile = p
        st.info("This profile is exported to Excel and reloaded in future sessions.")

    with tabs[1]:
        st.subheader("Readiness Assessment")
        st.write("Score each item from 0 to 5. Use evidence and notes fields to capture the basis for the assessment.")
        edited = st.data_editor(
            st.session_state.assessment,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Score (0-5)": st.column_config.NumberColumn(min_value=0, max_value=5, step=0.5),
                "Status": st.column_config.SelectboxColumn(options=STATUS_OPTIONS),
                "Scoring Risk": st.column_config.SelectboxColumn(options=RISK_OPTIONS),
            },
        )
        st.session_state.assessment = edited

    with tabs[2]:
        st.subheader("Visual Scorecard")
        module, kpis = compute_scores(st.session_state.assessment, st.session_state.tasks)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Readiness", f"{kpis['Overall Readiness %']}%", f"{kpis['Overall Readiness Score']}/5")
        c2.metric("Submission Confidence", f"{kpis['Submission Confidence %']}%")
        c3.metric("High-Risk Gaps", kpis["High-Risk Low-Score Items"])
        c4.metric("Overdue / Blocked", f"{kpis['Overdue Tasks']} / {kpis['Blocked Tasks']}")

        fig = px.bar(module.sort_values("Weighted Score"), x="Weighted Score", y="Domain", orientation="h", range_x=[0,5], title="Readiness by Domain")
        st.plotly_chart(fig, use_container_width=True)

        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(r=module["Weighted Score"], theta=module["Domain"], fill="toself", name="Score"))
        radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), showlegend=False, title="Readiness Radar")
        st.plotly_chart(radar, use_container_width=True)

        gap_df = st.session_state.assessment.copy()
        gap_df["Score (0-5)"] = pd.to_numeric(gap_df["Score (0-5)"], errors="coerce").fillna(0)
        gaps = gap_df[(gap_df["Scoring Risk"] == "High") & (gap_df["Score (0-5)"] < 3)]
        st.subheader("Priority Gaps")
        st.dataframe(gaps[["Domain", "Assessment Item", "Score (0-5)", "Owner", "Recommended Action", "Comments / Notes"]], use_container_width=True)

    with tabs[3]:
        st.subheader("Action Plan & Gantt")
        tasks = st.data_editor(
            st.session_state.tasks,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Start Date": st.column_config.DateColumn(),
                "Due Date": st.column_config.DateColumn(),
                "Status": st.column_config.SelectboxColumn(options=TASK_STATUS_OPTIONS),
                "Priority": st.column_config.SelectboxColumn(options=PRIORITY_OPTIONS),
                "% Complete": st.column_config.NumberColumn(min_value=0, max_value=100, step=5),
            },
        )
        st.session_state.tasks = tasks
        gantt = tasks.copy()
        gantt["Start Date"] = pd.to_datetime(gantt["Start Date"], errors="coerce")
        gantt["Due Date"] = pd.to_datetime(gantt["Due Date"], errors="coerce")
        gantt = gantt.dropna(subset=["Start Date", "Due Date"])
        if not gantt.empty:
            fig = px.timeline(gantt, x_start="Start Date", x_end="Due Date", y="Task Name", color="Status", hover_data=["Owner", "Priority", "CDP Milestone", "Dependencies", "% Complete"])
            fig.update_yaxes(autorange="reversed")
            for _, row in CDP_MILESTONES.iterrows():
                fig.add_vline(x=row["Date"], line_dash="dash", annotation_text=row["Milestone"], annotation_position="top")
            st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        st.subheader("CDP 2026 Timeline Reference")
        st.dataframe(CDP_MILESTONES, use_container_width=True)
        fig = px.scatter(CDP_MILESTONES, x="Date", y=[1]*len(CDP_MILESTONES), text="Milestone", title="CDP 2026 Milestones")
        fig.update_traces(textposition="top center")
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[5]:
        st.subheader("Summary Report")
        module, kpis = compute_scores(st.session_state.assessment, st.session_state.tasks)
        client = st.session_state.client_profile.get("Client Name", "Client")
        st.markdown(f"### {client} — CDP 2026 Readiness Summary")
        st.write(f"Overall readiness is **{kpis['Overall Readiness Score']}/5** ({kpis['Overall Readiness %']}%). Submission confidence is **{kpis['Submission Confidence %']}%** based on readiness scores, evidence completeness, task progress, and delivery risks.")
        summary = module.copy()
        summary["Status"] = summary["Weighted Score"].apply(score_label)
        st.dataframe(summary[["Domain", "Weighted Score", "Status", "Items", "High Risk Items", "Evidence Gaps"]], use_container_width=True)
        st.markdown("#### Recommended management focus")
        gap_df = st.session_state.assessment.copy()
        gap_df["Score (0-5)"] = pd.to_numeric(gap_df["Score (0-5)"], errors="coerce").fillna(0)
        top = gap_df.sort_values(["Score (0-5)", "Scoring Risk"]).head(8)
        for _, r in top.iterrows():
            st.write(f"- **{r['Domain']} — {r['Assessment Item']}**: score {r['Score (0-5)']}/5; owner: {r['Owner']}; action: {r['Recommended Action'] or 'Define remediation action.'}")

if __name__ == "__main__":
    main()
