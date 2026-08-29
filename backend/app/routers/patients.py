from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient
from app.schemas import PatientCreate, PatientOut

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post("", response_model=PatientOut)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    existing = db.get(Patient, payload.id)
    if existing:
        raise HTTPException(status_code=409, detail="Patient already exists")
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return db.execute(select(Patient)).scalars().all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
