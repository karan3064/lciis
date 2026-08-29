from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import alerts, lab_results, patients, vitals

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LCIIS API",
    description="Longitudinal Clinical Investigation Intelligence System — backend API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(lab_results.router)
app.include_router(vitals.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}
