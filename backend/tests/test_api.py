from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ingest_lab_result_creates_patient_and_no_alert(db_session):
    client = TestClient(app)
    resp = client.post(
        "/api/lab-result",
        json={
            "patient_id": "MRN001",
            "patient_name": "Ravi Kumar",
            "bed": "12",
            "test_code": "2160-0",
            "test_name": "Creatinine",
            "value": 1.0,
            "unit": "mg/dL",
            "collected_at": datetime.utcnow().isoformat(),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["alerts_triggered"] == []

    patients = client.get("/api/patients").json()
    assert len(patients) == 1
    assert patients[0]["id"] == "MRN001"


def test_ingest_creatinine_rising_triggers_amber_alert(db_session):
    client = TestClient(app)
    base = datetime.utcnow() - timedelta(days=4)
    values = [1.0, 1.2, 1.4]
    for i, v in enumerate(values):
        client.post(
            "/api/lab-result",
            json={
                "patient_id": "MRN002",
                "patient_name": "Test Patient",
                "bed": "5",
                "test_code": "2160-0",
                "test_name": "Creatinine",
                "value": v,
                "unit": "mg/dL",
                "collected_at": (base + timedelta(days=2 * i)).isoformat(),
            },
        )

    alerts = client.get("/api/alerts", params={"patient_id": "MRN002"}).json()
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "amber"
    assert alerts[0]["source"] == "rule_engine"


def test_acknowledge_alert(db_session):
    client = TestClient(app)
    base = datetime.utcnow() - timedelta(days=2)
    for i, v in enumerate([2.5, 3.1]):
        client.post(
            "/api/lab-result",
            json={
                "patient_id": "MRN003",
                "test_code": "2524-7",
                "test_name": "Lactate",
                "value": v,
                "unit": "mmol/L",
                "collected_at": (base + timedelta(days=i)).isoformat(),
            },
        )
    alerts = client.get("/api/alerts", params={"patient_id": "MRN003"}).json()
    assert len(alerts) == 1
    alert_id = alerts[0]["id"]

    resp = client.post(f"/api/alerts/{alert_id}/ack", json={"acknowledged_by": "nurse_1"})
    assert resp.status_code == 200
    assert resp.json()["acknowledged"] == 1

    active = client.get("/api/alerts", params={"patient_id": "MRN003", "active_only": True}).json()
    assert active == []


def test_trend_endpoint_returns_series(db_session):
    client = TestClient(app)
    for v in [1.0, 1.1]:
        client.post(
            "/api/lab-result",
            json={
                "patient_id": "MRN004",
                "test_code": "2160-0",
                "test_name": "Creatinine",
                "value": v,
                "unit": "mg/dL",
                "collected_at": datetime.utcnow().isoformat(),
            },
        )
    trend = client.get("/api/patients/MRN004/trend").json()
    assert len(trend) == 1
    assert trend[0]["test_code"] == "2160-0"
    assert len(trend[0]["points"]) == 2
