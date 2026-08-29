# Manual channel build (fallback if XML import fails)

Mirth's channel export format is version-specific XStream-serialized XML.
`LCIIS_ORU_Ingestion.xml` and `LCIIS_ADT_PatientSync.xml` in this directory
target Mirth Connect (NextGen Connect) **4.5.x** and were built by hand
against that version's documented schema — they were not validated against
a running Mirth instance (not installable in the environment that produced
this repo). If **Channels → Import Channel** rejects one, or it imports
with blank/wrong connector settings, build it by hand instead — takes about
5 minutes and has zero format risk.

## LCIIS - HL7 ORU Ingestion

1. **Channels → + (Create New Channel)** → source connector type **TCP
   Listener**, name it `LCIIS - HL7 ORU Ingestion`.
2. **Source tab:**
   - Listener host: `0.0.0.0`, port: `6661` (or whatever the hospital LIS
     is configured to send ORU messages to).
   - Data Type: **HL7 v2.x**.
   - Frame Encoding: click into it and confirm MLLP framing — Start of
     Message `0x0B`, End of Message `0x1C 0x0D` (this is Mirth's default
     for a TCP Listener, so usually nothing to change).
3. **Source → Filter** (optional but recommended): add a JavaScript Rule
   so this channel ignores any non-ORU^R01 message instead of erroring:
   ```js
   var messageType = msg['MSH']['MSH.9']['MSH.9.1'].toString();
   var triggerEvent = msg['MSH']['MSH.9']['MSH.9.2'].toString();
   return (messageType == 'ORU' && triggerEvent == 'R01');
   ```
4. **Source → Transformer:** add one JavaScript Step, paste the script
   from `transformer.js` in this directory (the "Parse HL7 ORU..." step —
   it's the same script embedded in the XML export). It builds a JSON
   array of one object per OBX result and stores it in
   `channelMap.put('labResultPayloads', ...)`.
5. **Destinations tab → +** → destination type **JavaScript Writer**, name
   it `Post lab results to LCIIS API`. Paste the destination script from
   `LCIIS_ORU_Ingestion.xml`'s `<properties>/<script>` element (the block
   that loops over `channelMap.get('labResultPayloads')` and does an HTTP
   POST per result using `java.net.URL`/`HttpURLConnection`).
6. **Settings → Configuration Map** (top-level Mirth Administrator
   settings, not the channel): add a key `LCIIS_API_URL` with the value
   `http://<lciis-backend-host>:8000` — the destination script reads this,
   falling back to `http://localhost:8000` if unset.
7. Enable the destination queue (Destinations → the destination →
   Queueing tab → "Enabled") with a retry count so a transient LCIIS
   outage doesn't drop results — failed sends land in the queue and retry.
8. **Deploy the channel.**

## LCIIS - ADT Patient Sync

Same pattern, on a different port (`6662` suggested so it doesn't collide
with the ORU channel):

- Filter: same idea but check for `ADT` / `A01`.
- Transformer: parses PID (MRN, name, DOB, sex) and PV1 (ward/bed) into a
  single JSON object in `channelMap.put('patientPayload', ...)`.
- Destination: JavaScript Writer, one `POST /api/patients` call. Treat
  HTTP 409 (patient already exists) as success — a duplicate/re-sent ADT
  message for an already-admitted patient is expected, not an error.

Full scripts for both are in `LCIIS_ADT_PatientSync.xml`.

## Testing either channel

Once deployed, use `hl7/send_hl7.py` against whatever port you configured
— it's a plain MLLP client, so it works identically against real Mirth or
the standalone bridge:

```bash
cd hl7
python send_hl7.py samples/oru_day1_baseline.hl7 --port 6661
python send_hl7.py samples/adt_a01_admit.hl7 --port 6662
```

Check the channel's **Dashboard** tab in Mirth Administrator for
processed/errored message counts, and the LCIIS API (`GET /api/alerts`,
`GET /api/patients`) or dashboard to confirm the data landed.

## Known limitation

The ADT sync channel only listens for `A01` (admit). A real deployment
should also handle `A02` (transfer — bed changes) and `A08` (update) by
widening the filter and having `_upsert_patient` in
`backend/app/routers/lab_results.py` (or a small update in
`app/routers/patients.py`) apply bed/ward changes on repeat POSTs instead
of only on first insert.
