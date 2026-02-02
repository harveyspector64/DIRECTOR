# Director Radar

Director Radar is a static Next.js application and data pipeline for tracking directors, availability, and adjacency.

## Key folders
- `data/`: canonical JSON datasets and overrides.
- `public/data/`: bundled payload for the web app.
- `schemas/`: JSON Schemas for core entities.
- `scripts/`: weekly update pipeline.

## Quick start
```bash
npm install
npm run dev
```

## Weekly pipeline
```bash
python scripts/bootstrap_atlas.py --min_year 2008 --target 3000
python scripts/ingest_sources.py --days 14
python scripts/ingest_search.py --days 14
python scripts/extract_events.py
python scripts/merge_events.py
python scripts/build_bundle.py
python scripts/quality_report.py
```
