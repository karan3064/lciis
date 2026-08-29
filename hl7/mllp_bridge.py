"""A minimal MLLP (Minimum Lower Layer Protocol) listener that plays the
same role as the Mirth Connect TCP Listener + JS Transformer + HTTP Sender
channel described in the architecture doc (section 3.1): it accepts HL7
v2.x ORU^R01 messages over TCP/MLLP from the hospital LIS, parses them,
and POSTs the resulting JSON payloads to the LCIIS FastAPI backend.

Run this when Mirth Connect isn't installed (e.g. local dev, this demo
environment); swap it for a real Mirth channel in a production hospital
deployment by importing mirth/channel_notes.md's configuration instead —
the wire contract (the JSON body it POSTs) is identical either way.

MLLP framing: <VT> message <FS><CR>  (0x0B ... 0x1C 0x0D)
"""

from __future__ import annotations

import argparse
import logging
import socketserver

import httpx

from hl7_parser import parse_oru_r01, to_lab_result_payloads

logger = logging.getLogger("lciis.mllp_bridge")

START_BLOCK = b"\x0b"
END_BLOCK = b"\x1c"
CARRIAGE_RETURN = b"\x0d"


def build_ack(message: str) -> str:
    """Minimal MSA|AA acknowledgment so the sending LIS considers the
    message delivered."""
    return "MSH|^~\\&|LCIIS|LCIIS|LIS|CITYHOSP|||ACK|1|P|2.5.1\rMSA|AA|1\r"


class MLLPHandler(socketserver.BaseRequestHandler):
    api_base_url = "http://localhost:8000"

    def handle(self):
        buffer = b""
        while True:
            chunk = self.request.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while START_BLOCK in buffer and END_BLOCK in buffer:
                start = buffer.index(START_BLOCK)
                end = buffer.index(END_BLOCK)
                raw_message = buffer[start + 1 : end].decode("utf-8", errors="replace")
                buffer = buffer[end + 2 :]  # skip <FS><CR>
                self._process_message(raw_message)
                ack = build_ack(raw_message)
                self.request.sendall(START_BLOCK + ack.encode("utf-8") + END_BLOCK + CARRIAGE_RETURN)

    def _process_message(self, raw_message: str):
        try:
            parsed = parse_oru_r01(raw_message)
            payloads = to_lab_result_payloads(parsed)
        except Exception:
            logger.exception("Failed to parse inbound HL7 message")
            return

        for payload in payloads:
            try:
                resp = httpx.post(f"{self.api_base_url}/api/lab-result", json=payload, timeout=10)
                resp.raise_for_status()
                logger.info(
                    "Ingested %s for patient %s -> %s alert(s)",
                    payload["test_code"],
                    payload["patient_id"],
                    len(resp.json().get("alerts_triggered", [])),
                )
            except Exception:
                logger.exception("Failed to POST lab result to LCIIS API — will not retry "
                                  "(a real Mirth channel would queue and retry here)")


def main():
    parser = argparse.ArgumentParser(description="LCIIS MLLP-to-REST bridge")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=6661)
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    MLLPHandler.api_base_url = args.api_url

    with socketserver.ThreadingTCPServer((args.host, args.port), MLLPHandler) as server:
        logger.info("LCIIS MLLP bridge listening on %s:%s -> %s", args.host, args.port, args.api_url)
        server.serve_forever()


if __name__ == "__main__":
    main()
