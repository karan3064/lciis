FROM python:3.11-slim

WORKDIR /srv/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# ml/ is mounted from the repo root at compose runtime so the trained
# risk_model.joblib is available without baking it into the image.

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
