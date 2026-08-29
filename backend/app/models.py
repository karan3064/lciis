from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)  # hospital MRN
    name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    sex = Column(String, nullable=True)
    bed = Column(String, nullable=True)
    ward = Column(String, nullable=True)
    admitted_at = Column(DateTime, default=datetime.utcnow)

    lab_results = relationship("LabResult", back_populates="patient")
    vital_readings = relationship("VitalReading", back_populates="patient")
    alerts = relationship("Alert", back_populates="patient")


class LabResult(Base):
    """Time-series row. In TimescaleDB this table is converted to a hypertable
    on `collected_at` (see db/init.sql)."""

    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    test_code = Column(String, nullable=False, index=True)  # LOINC code
    test_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    ref_low = Column(Float, nullable=True)
    ref_high = Column(Float, nullable=True)
    ordering_physician = Column(String, nullable=True)
    collected_at = Column(DateTime, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="lab_results")


class VitalReading(Base):
    """Streamed from the bedside Vitals Node (SpO2, HR, temperature)."""

    __tablename__ = "vital_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    metric = Column(String, nullable=False)  # spo2 | heart_rate | temperature
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    recorded_at = Column(DateTime, nullable=False, index=True)

    patient = relationship("Patient", back_populates="vital_readings")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    severity = Column(String, nullable=False)  # yellow | amber | red
    source = Column(String, nullable=False)  # rule_engine | ml_engine
    rule_name = Column(String, nullable=True)
    risk_score = Column(Float, nullable=True)
    test_codes = Column(String, nullable=True)  # comma-separated contributing tests
    message = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged = Column(Integer, default=0)  # 0/1 boolean (portable)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="alerts")
