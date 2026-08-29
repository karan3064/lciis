from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VitalReading
from app.schemas import VitalReadingIn

router = APIRouter(prefix="/api", tags=["vitals"])


@router.post("/vitals", status_code=201)
def ingest_vital(payload: VitalReadingIn, db: Session = Depends(get_db)):
    """Ingests a single SpO2 / heart-rate / temperature reading streamed
    from a Bedside Vitals Node over MQTT -> a small bridge subscriber that
    forwards to this endpoint (see hl7/README.md)."""
    reading = VitalReading(**payload.model_dump())
    db.add(reading)
    db.commit()
    return {"status": "ok", "id": reading.id}
