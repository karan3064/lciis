from hl7_parser import parse_oru_r01, to_lab_result_payloads

SAMPLE = (
    "MSH|^~\\&|LIS|CITYHOSP|LCIIS|LCIIS|20260103070000||ORU^R01|MSG00002|P|2.5.1\r"
    "PID|1||MRN-RAVI^^^CITYHOSP^MR||Kumar^Ravi||19850214|M|||Ward B^Bed 12\r"
    "PV1|1|I|WARDB^12^A||||1234^Sharma^Anita^^^Dr\r"
    "OBR|1|ORD002|LAB002|CHEM^Basic Metabolic Panel|||20260103065000\r"
    "OBX|1|NM|2160-0^Creatinine^LN||1.4|mg/dL|0.6-1.3|H|||F|||20260103070000\r"
    "OBX|2|NM|3094-0^BUN^LN||22|mg/dL|7-20|H|||F|||20260103070000\r"
)


def test_parse_patient_demographics():
    parsed = parse_oru_r01(SAMPLE)
    assert parsed.patient_id == "MRN-RAVI"
    assert parsed.patient_name == "Ravi Kumar"
    assert parsed.bed == "12"
    assert parsed.ward == "WARDB"
    assert parsed.ordering_physician == "Dr. Anita Sharma"


def test_parse_observations():
    parsed = parse_oru_r01(SAMPLE)
    assert len(parsed.observations) == 2
    creatinine = parsed.observations[0]
    assert creatinine.test_code == "2160-0"
    assert creatinine.value == 1.4
    assert creatinine.unit == "mg/dL"
    assert creatinine.ref_low == 0.6
    assert creatinine.ref_high == 1.3


def test_to_lab_result_payloads_shape():
    parsed = parse_oru_r01(SAMPLE)
    payloads = to_lab_result_payloads(parsed)
    assert len(payloads) == 2
    assert payloads[0]["patient_id"] == "MRN-RAVI"
    assert payloads[0]["collected_at"] == "2026-01-03T07:00:00"


def test_non_numeric_obx_is_skipped():
    msg = SAMPLE + "OBX|3|ST|12345-6^Comment^LN||Sample hemolyzed|||||F\r"
    parsed = parse_oru_r01(msg)
    assert len(parsed.observations) == 2  # the ST result is skipped
