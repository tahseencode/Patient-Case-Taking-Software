# MediKiosk / AyurKiosk

**SIH26047** — AI-powered clinical intake platform for Indian OPD and AYUSH institutions. Patients complete a multilingual self-intake at a kiosk; the platform turns it into a structured clinical summary, flags emergencies in real time, and generates an ABDM-style FHIR record for the doctor.

## Features

- **Kiosk intake:** registration (optional ABHA ID), DPDP-2023 consent, chief complaint in 8 Indian languages, SOCRATES symptom questionnaire, simulated OCR for prescriptions/lab reports
- **AYUSH stream:** Prakriti questionnaire with Vata/Pitta/Kapha scoring
- **Doctor desk:** live OPD queue, red-flag triage alerts, editable AI summary with ICD-10 / NAMASTE codes, prescription + FHIR R4 bundle on completion
- **Live updates** via WebSocket (`/ws/live-feed`)

## Tech Stack

- **Backend:** FastAPI + Uvicorn, rule-based offline engines (no LLM needed)
- **Frontend:** static HTML/CSS/vanilla JS, served by FastAPI
- **Database:** SQLite (WAL mode, foreign keys, 9 tables, see `schema.sql`)

## Quick Start

```bash
git clone https://github.com/tahseencode/Patient-Case-Taking-Software.git
cd Patient-Case-Taking-Software
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
python -m backend.main                            # run from project root
```

| URL | Page |
|---|---|
| `localhost:8000/` | Patient kiosk |
| `localhost:8000/app.html` | Doctor desk |
| `localhost:8000/docs` | Swagger API docs |

No `.env` needed. `GEMINI_API_KEY` / `OPENAI_API_KEY` are optional placeholders.

## API Overview

All routes are under `/api/v1`.

| Prefix | Purpose |
|---|---|
| `/kiosk` | complaints, SOCRATES steps, start session, submit, finalize |
| `/ayush` | Prakriti questions and scoring |
| `/documents` | sample library, load sample, OCR upload |
| `/doctor` | OPD queue, triage alerts, summary, prescribe and complete |
| `/abdm` | ABHA verification, FHIR bundle, DPDP audit, hospital stats |

Full schemas at `/docs`.

## Project Structure

```
backend/
  main.py
  app/
    api/        # routes
    core/       # triage, dialogue, summarizer, FHIR, OCR, consent engines
    database/   # SQLite db, schema.sql, seed.sql, init_db.py
    models/     # Pydantic schemas
frontend/       # index.html (kiosk), app.html (doctor), js/
test_platform_api.py
```

## Database CLI

```bash
python -m backend.app.database.init_db --status   # health + row counts
python -m backend.app.database.init_db --reset    # reset with seed data
```

## Tests

```bash
python -m unittest test_platform_api.py -v
```

## Notes & Limitations

Hackathon demo, not production software.

- ABHA verification and FHIR submission are simulated
- OCR works on provided text, not real scans
- No authentication; CORS is open
- SQLite is single-node
