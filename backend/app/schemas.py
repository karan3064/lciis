from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    id: str
    name: str
    date_of_birth: Optional[datetime] = None
    sex: Optional[str] = None
    bed: Optional[str] = None
    ward: Optional[str] = None


class PatientOut(PatientCreate):
    admitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabResultIn(BaseModel):
    """Shape of the JSON payload Mirth Connect POSTs to /api/lab-result
    after parsing an HL7 ORU^R01 message's OBX segments."""

    patient_id: str = Field(..., description="Hospital MRN")
    patient_name: Optional[str] = None
    bed: Optional[str] = None
    ward: Optional[str] = None
    test_code: str = Field(..., description="LOINC code")
    test_name: str
    value: float
    unit: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    ordering_physician: Optional[str] = None
    collected_at: datetime


class LabResultOut(BaseModel):
    id: int
    patient_id: str
    test_code: str
    test_name: str
    value: float
    unit: Optional[str]
    ref_low: Optional[float]
    ref_high: Optional[float]
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VitalReadingIn(BaseModel):
    patient_id: str
    metric: str
    value: float
    unit: Optional[str] = None
    recorded_at: datetime


class AlertOut(BaseModel):
    id: int
    patient_id: str
    severity: str
    source: str
    rule_name: Optional[str]
    risk_score: Optional[float]
    test_codes: Optional[str]
    message: str
    explanation: Optional[str]
    triggered_at: datetime
    acknowledged: int
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class AlertAck(BaseModel):
    acknowledged_by: str


class IngestResult(BaseModel):
    lab_result_id: int
    alerts_triggered: list[AlertOut]


class TrendPoint(BaseModel):
    collected_at: datetime
    value: float


class TrendSeries(BaseModel):
    test_code: str
    test_name: str
    unit: Optional[str]
    points: list[TrendPoint]
