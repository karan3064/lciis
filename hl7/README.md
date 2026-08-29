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

For a real hospital deployment, replace the bridge with a Mirth Connect
channel:

1. **Source connector** — TCP Listener, MLLP framing (`0x0B`/`0x1C 0x0D`),
   listening on the port the hospital LIS is configured to send to.
2. **Transformer** — paste `mirth/transformer.js`. It walks the PID/PV1/OBX
   segments and builds the same JSON shape `hl7_parser.py` produces.
3. **Destination** — HTTP Sender, `POST` to
   `http://<lciis-host>:8000/api/lab-result`, one request per OBX row
   (iterate over `channelMap.get('labResultPayloads')`), Content-Type
   `application/json`.
4. **Error handling** — enable Mirth's built-in destination queue with
   retry-on-failure so a transient LCIIS outage doesn't drop results;
   messages that fail to parse land in the channel's error queue for
   manual review.
5. **ADT^A01** — a second, simpler channel (Transformer just maps PID/PV1
   to `POST /api/patients`) keeps patient demographics/bed assignment in
   sync as patients are admitted/transferred.

Both paths converge on the same backend contract, so the trend engine,
ML engine, and dashboard behave identically regardless of which one feeds
them.
