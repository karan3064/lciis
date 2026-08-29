"""Parses HL7 v2.x ORU^R01 messages into the JSON payload LCIIS's
/api/lab-result endpoint expects.

This mirrors the transform Mirth Connect's JavaScript Transformer performs
in production (see mirth/transformer.js for the equivalent Mirth-side
code) and doubles as a standalone ingestion bridge for environments where
Mirth Connect isn't installed (e.g. this dev/demo environment) — see
mllp_bridge.py, which uses this module to run a real MLLP listener without
requiring Mirth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def _split_segments(message: str) -> list[list[str]]:
    # HL7 segments are separated by \r (or \r\n / \n in relaxed sources);
    # fields within a segment by |.
    raw = message.replace("\r\n", "\r").replace("\n", "\r")
    segments = [seg for seg in raw.split("\r") if seg.strip()]
    return [seg.split("|") for seg in segments]


def _parse_hl7_timestamp(ts: str) -> datetime:
    """HL7 TS fields are YYYYMMDDHHMMSS[.ffff][+/-ZZZZ], with any suffix
    after the seconds optional. Right-pad missing components with zeros."""
    ts = ts.strip().split(".")[0]
    for sep in ("+", "-"):
        if len(ts) > 8 and sep in ts[8:]:
            ts = ts[: 8 + ts[8:].index(sep)]
    digits = (ts + "00000000000000")[:14]
    return datetime.strptime(digits, "%Y%m%d%H%M%S")


@dataclass
class ParsedObservation:
    test_code: str
    test_name: str
    value: float
    unit: str | None
    ref_low: float | None
    ref_high: float | None
    observed_at: datetime


@dataclass
class ParsedOruMessage:
    patient_id: str
    patient_name: str
    bed: str | None
    ward: str | None
    ordering_physician: str | None
    observations: list[ParsedObservation] = field(default_factory=list)


def _parse_reference_range(raw: str) -> tuple[float | None, float | None]:
    if not raw or "-" not in raw:
        return None, None
    low, _, high = raw.partition("-")
    try:
        return float(low), float(high)
    except ValueError:
        return None, None


def parse_oru_r01(message: str) -> ParsedOruMessage:
    """Parses the segments LCIIS cares about: PID (patient demographics),
    PV1 (bed/ward/physician), and OBX (one row per lab result)."""
    segments = _split_segments(message)

    patient_id = ""
    patient_name = ""
    bed = None
    ward = None
    physician = None
    observations: list[ParsedObservation] = []
    default_collected_at = datetime.utcnow()

    for fields in segments:
        seg_id = fields[0]

        if seg_id == "PID":
            # PID-3 patient identifier list (MRN^^^facility^MR), PID-5 name (Last^First)
            id_field = fields[3] if len(fields) > 3 else ""
            patient_id = id_field.split("^")[0]
            name_field = fields[5] if len(fields) > 5 else ""
            name_parts = name_field.split("^")
            last, first = (name_parts + ["", ""])[:2]
            patient_name = f"{first} {last}".strip() or patient_id
            location = fields[11] if len(fields) > 11 else ""
            if "^" in location:
                ward_part, bed_part = (location.split("^") + [""])[:2]
                ward, bed = ward_part or None, bed_part or None

        elif seg_id == "PV1":
            # PV1-3 assigned patient location (ward^bed^room), PV1-7 attending doctor
            location = fields[3] if len(fields) > 3 else ""
            if "^" in location:
                parts = location.split("^")
                ward = parts[0] or ward
                bed = parts[1] or bed
            doctor = fields[7] if len(fields) > 7 else ""
            if doctor:
                doc_parts = doctor.split("^")
                physician = f"Dr. {doc_parts[2] if len(doc_parts) > 2 else ''} " \
                             f"{doc_parts[1] if len(doc_parts) > 1 else ''}".strip()

        elif seg_id == "OBR":
            observed_str = fields[7] if len(fields) > 7 else ""
            if observed_str:
                default_collected_at = _parse_hl7_timestamp(observed_str)

        elif seg_id == "OBX":
            # OBX-3 test code^name^coding-system, OBX-5 value, OBX-6 unit,
            # OBX-7 reference range, OBX-14 observation datetime
            code_field = fields[3] if len(fields) > 3 else ""
            code_parts = code_field.split("^")
            test_code = code_parts[0] if code_parts else ""
            test_name = code_parts[1] if len(code_parts) > 1 else test_code

            value_str = fields[5] if len(fields) > 5 else ""
            unit = fields[6] if len(fields) > 6 else None
            ref_range = fields[7] if len(fields) > 7 else ""
            ref_low, ref_high = _parse_reference_range(ref_range)

            observed_at = default_collected_at
            if len(fields) > 14 and fields[14]:
                observed_at = _parse_hl7_timestamp(fields[14])

            try:
                value = float(value_str)
            except ValueError:
                continue  # skip non-numeric results (e.g. free-text OBX)

            observations.append(
                ParsedObservation(
                    test_code=test_code,
                    test_name=test_name,
                    value=value,
                    unit=unit or None,
                    ref_low=ref_low,
                    ref_high=ref_high,
                    observed_at=observed_at,
                )
            )

    return ParsedOruMessage(
        patient_id=patient_id,
        patient_name=patient_name,
        bed=bed,
        ward=ward,
        ordering_physician=physician,
        observations=observations,
    )


def to_lab_result_payloads(parsed: ParsedOruMessage) -> list[dict]:
    """One LCIIS /api/lab-result JSON payload per OBX observation."""
    return [
        {
            "patient_id": parsed.patient_id,
            "patient_name": parsed.patient_name,
            "bed": parsed.bed,
            "ward": parsed.ward,
            "test_code": obs.test_code,
            "test_name": obs.test_name,
            "value": obs.value,
            "unit": obs.unit,
            "ref_low": obs.ref_low,
            "ref_high": obs.ref_high,
            "ordering_physician": parsed.ordering_physician,
            "collected_at": obs.observed_at.isoformat(),
        }
        for obs in parsed.observations
    ]
