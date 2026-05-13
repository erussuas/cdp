# CDP 2026 Readiness Assessment & Action Plan App

A Streamlit-based advisory tool for conducting CDP readiness assessments, tracking action plans, creating visual scorecards, exporting the assessment to Excel, and reimporting the workbook in a future session.

## Features

- Client profile capture
- Readiness assessment with scores, owners, evidence needs, recommended actions, and notes
- Dashboard with readiness scorecard, domain bar chart, radar chart, and priority gaps
- Action plan with owner, due date, status, comments, dependencies, priority, and % complete
- Gantt-style timeline mapped against CDP 2026 milestones
- Excel export/import so each client assessment can be stored and resumed

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Excel persistence

Use the **Export Excel workbook** button in the sidebar to download the assessment workbook. At the next session, upload that workbook using **Upload prior assessment Excel** and the app will rehydrate the profile, assessment inputs, tasks, scores, and timeline data.

## CDP 2026 timeline included

The app includes these planning milestones:

- Week of April 20, 2026: Questionnaires and guidance published
- Week of April 27, 2026: Scoring methodology published / request lists open
- Week of June 8, 2026: Request list submission deadline
- Week of June 15, 2026: Response window opens
- Week of September 14, 2026: Scoring deadline
- Week of October 26, 2026: Final unscored response / amendments deadline
- Week of November 30, 2026: Scores released

## Notes

This is an MVP scaffold designed to be customized with client-specific CDP modules, question mappings, scoring logic, and evidence templates.
