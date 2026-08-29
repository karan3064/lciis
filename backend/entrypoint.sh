#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import time
import sqlalchemy
from app.config import settings

for _ in range(30):
    try:
        sqlalchemy.create_engine(settings.database_url).connect().close()
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit('Database never became available')
"

echo "Creating tables..."
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

if [ "$RUN_TIMESCALE_INIT" = "1" ]; then
    echo "Applying TimescaleDB hypertables / continuous aggregates..."
    python -c "
import sqlalchemy
from app.config import settings

with open('app/db/init.sql') as f:
    sql = f.read()

engine = sqlalchemy.create_engine(settings.database_url)
with engine.connect() as conn:
    for statement in sql.split(';'):
        statement = statement.strip()
        if statement:
            conn.execute(sqlalchemy.text(statement))
    conn.commit()
"
fi

if [ ! -f ml/risk_model.joblib ]; then
    echo "Training ML risk model (first run)..."
    python ml/train_model.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
