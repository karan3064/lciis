# LCIIS — Longitudinal Clinical Investigation Intelligence System

Team NurvoSync · BioMed Bharat 2026 · GITAM / GIMSR
Yash Agarwal · Karanjeet Singh

LCIIS ingests hospital lab results in real time, tracks how a patient's
values trend across admissions, and pushes actionable alerts to bedside
devices before gradual deterioration (rising creatinine, climbing lactate,
multi-parameter AKI patterns) becomes clinically obvious. This repo is the
software half of the system described in `LCIIS_System_Overview.pdf`
(section 3); the hardware half (ESP32 bedside pager + vitals node) is out
of scope here but the backend already exposes the MQTT and `/api/vitals`
contracts it talks to.

## Architecture

```
Hospital LIS --HL7 ORU/MLLP--> HL7 bridge --JSON/HTTP--> FastAPI backend --> TimescaleDB
                                                              |    \
                                                     Rule engine   ML engine (scikit-learn)
                                                              |
                                                        MQTT broker (Mosquitto)
                                                              |
                                                   Bedside pager (ESP32, hardware)

FastAPI backend <--REST--> React/Chart.js dashboard
```

| Layer | Directory | Tech |
|---|---|---|
| HL7 ingestion | `hl7/` | Standalone MLLP bridge (dev) + Mirth Connect reference config (prod) |
| Backend API | `backend/` | FastAPI, SQLAlchemy |
| Database | `backend/app/db/init.sql` | TimescaleDB (Postgres extension) |
| Trend/ML engine | `backend/app/services/` | Rule-based thresholds + scikit-learn gradient boosting |
| ML training | `ml/` | `train_model.py` |
| Dashboard | `dashboard/` | React + Vite + Chart.js |
| Alerting | `backend/app/services/mqtt_client.py` | Mosquitto MQTT |

## Quick start (Docker Compose)

```bash
docker compose up --build
```

- Backend API: http://localhost:8000 (docs at `/docs`)
- Dashboard: http://localhost:5173
- HL7 MLLP bridge: `localhost:6661`
- TimescaleDB: `localhost:5432` (user/pass/db: `lciis`)
- Mosquitto: `localhost:1883`

The backend trains the ML risk model on first boot if `ml/risk_model.joblib`
doesn't already exist, and creates/hypertable-izes the schema automatically.

Feed it the demo scenario:

```bash
cd hl7
python send_hl7.py samples/oru_day1_baseline.hl7 --port 6661
python send_hl7.py samples/oru_day3_amber.hl7 --port 6661
python send_hl7.py samples/oru_day5_red.hl7 --port 6661
```

Open the dashboard, select **Ravi Kumar**, and you should see the
creatinine/BUN/potassium trend lines climbing plus an amber alert (Day 3)
and a red multi-parameter ML alert (Day 5) in the Active Alerts panel.

## Running components individually (no Docker)

```bash
# 1. Backend (defaults to a local sqlite file if DATABASE_URL isn't set to Postgres)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ../ml/train_model.py           # trains ml/risk_model.joblib
uvicorn app.main:app --reload

# 2. HL7 MLLP bridge
cd hl7
python mllp_bridge.py --port 6661 --api-url http://localhost:8000

# 3. Dashboard
cd dashboard
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

A local Mosquitto broker is optional for this path — if it's unreachable,
alerts are still computed and stored, just not published to bedside
devices (logged instead).

## Tests

```bash
cd backend && python -m pytest        # rule engine + API integration tests
cd hl7 && python -m pytest            # HL7 parser tests
```

## Repository layout

```
backend/          FastAPI app, SQLAlchemy models, rule/ML engines, MQTT publisher
  app/services/    trend_engine.py (Layer 1 rules), ml_engine.py (Layer 2 ML), mqtt_client.py
  app/routers/     lab_results.py, patients.py, alerts.py, vitals.py
  app/db/init.sql  TimescaleDB hypertables + continuous aggregates + compression policy
  tests/
hl7/              HL7 ingestion: standalone MLLP bridge + Mirth Connect reference config
  mirth/           transformer.js + production channel notes
  samples/         Sample ORU/ADT messages matching the demo scenario
ml/               train_model.py — trains the Layer 2 multi-parameter risk model
dashboard/        React + Vite + Chart.js clinical dashboard
docker-compose.yml
```

## Design notes / where this diverges from the architecture doc

- **Two creatinine rules, not one.** Section 3.3 defines "rising >20%
  across 3 consecutive tests"; the Day 3 demo narrative in section 7 fires
  after only 2 data points. Both are real, distinct clinical signals, so
  both are implemented (`creatinine_rising_3_consecutive` and
  `creatinine_rapid_rise_48h`) rather than picking one.
- **Alert de-duplication.** A 30-minute cooldown per (patient, source,
  rule) suppresses duplicate pages when several lab results from the same
  draw arrive in quick succession and each independently re-triggers the
  same rule or ML finding — otherwise a single blood draw with 3 abnormal
  analytes can page the bedside device 3 times.
- **ML model is trained on synthetic data.** There's no real hospital
  dataset yet; `ml/train_model.py` generates a clinically-plausible
  synthetic distribution matching the demo scenario's AKI pattern. Swap in
  a real historical-labs loader before any clinical use.
