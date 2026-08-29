from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import AlertAck, AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    active_only: bool = Query(True, description="Only return unacknowledged alerts"),
    patient_id: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Alert).order_by(Alert.triggered_at.desc())
    if active_only:
        stmt = stmt.where(Alert.acknowledged == 0)
    if patient_id:
        stmt = stmt.where(Alert.patient_id == patient_id)
    return db.execute(stmt).scalars().all()


@router.post("/{alert_id}/ack", response_model=AlertOut)
def acknowledge_alert(alert_id: int, payload: AlertAck, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = 1
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = payload.acknowledged_by
    db.commit()
    db.refresh(alert)
    return alert
