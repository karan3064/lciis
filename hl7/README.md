# HL7 Ingestion

LCIIS ingests HL7 v2.x `ORU^R01` (lab results) and `ADT^A01` (patient
admission) messages over TCP/MLLP, per architecture doc section 3.1. There
are two equivalent ways to run this layer:

## 1. Standalone bridge (used in this dev/demo environment)

`mllp_bridge.py` is a real MLLP listener (no Mirth installation required)
that parses inbound HL7 with `hl7_parser.py` and POSTs the resulting JSON
to the LCIIS backend's `/api/lab-result` endpoint — the identical wire
contract a Mirth channel produces.

```bash
# terminal 1: backend
cd backend && uvicorn app.main:app --reload

# terminal 2: MLLP bridge
cd hl7 && python mllp_bridge.py --port 6661 --api-url http://localhost:8000

# terminal 3: simulate the hospital LIS sending a result
cd hl7 && python send_hl7.py samples/oru_day1_baseline.hl7
```

`samples/` contains the three ORU messages from the BioMed Bharat demo
scenario (Day 1 baseline, Day 3 amber, Day 5 red) plus a sample ADT^A01
admission message.

## 2. Production: Mirth Connect

For a real hospital deployment, replace the bridge with a real Mirth
Connect (NextGen Connect) channel. `mirth/` has two ready-to-import
channel exports plus a manual fallback:

- `mirth/LCIIS_ORU_Ingestion.xml` — TCP Listener (MLLP) → JavaScript
  Transformer (parses PID/PV1/OBX) → JavaScript Writer destination that
  POSTs one request per OBX row to `/api/lab-result`.
- `mirth/LCIIS_ADT_PatientSync.xml` — same pattern for `ADT^A01` →
  `POST /api/patients`.
- `mirth/transformer.js` — the transformer script alone, for reference or
  copy-paste.
- `mirth/MANUAL_CHANNEL_SETUP.md` — click-by-click instructions to build
  either channel by hand in Mirth Administrator, in case the XML import
  doesn't take cleanly on your Mirth version (these exports target 4.5.x
  and were hand-built against the documented schema, not validated
  against a running Mirth instance — see that file for why).

**Import:** Mirth Administrator → **Channels → Import Channel** → select
the `.xml` file → set the destination's `LCIIS_API_URL` via **Settings →
Configuration Map** (defaults to `http://localhost:8000` if unset) → set
the destination queue to retry-on-failure → **Deploy**.

Both paths converge on the same backend contract, so the trend engine,
ML engine, and dashboard behave identically regardless of which one feeds
them.
