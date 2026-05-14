# CDP 2026 Readiness Assessment App

Streamlit MVP for CDP 2026 readiness assessment, action planning, Gantt-style timeline, readiness radar forecasting, and Excel import/export.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## v0.1.5 updates

- Aggregated action plan intended for CDP readiness coordination, not detailed project management replacement.
- Default editable CDP action template with suggested timing.
- Gap-derived action bucket that pulls from low-scoring readiness assessment items.
- Manual action creation form.
- Action plan sorting by start date or due date.
- Source tracking: default template, gap assessment, manual action.
- Optional Gantt inclusion and archive flags.
- Linked readiness domain and expected action impact.
- Three-layer radar chart: current readiness, readiness goal, projected readiness after action plan.
- Excel export/import supports assessment, targets, tasks, projections, and metadata.
