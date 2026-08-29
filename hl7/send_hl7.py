"""Sends a sample HL7 file to the MLLP bridge (or a real Mirth Connect
TCP Listener) for testing. Simulates what the hospital LIS does.

Usage: python send_hl7.py samples/oru_day1_baseline.hl7 --host localhost --port 6661
"""

import argparse
import socket

START_BLOCK = b"\x0b"
END_BLOCK = b"\x1c"
CARRIAGE_RETURN = b"\x0d"


def send(path: str, host: str, port: int):
    message = open(path, "rb").read().replace(b"\n", b"\r")
    with socket.create_connection((host, port), timeout=10) as sock:
        sock.sendall(START_BLOCK + message + END_BLOCK + CARRIAGE_RETURN)
        ack = sock.recv(4096)
        print("ACK received:", ack.decode("utf-8", errors="replace").strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=6661)
    args = parser.parse_args()
    send(args.file, args.host, args.port)
