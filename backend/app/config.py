from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Defaults to a local SQLite file so `uvicorn app.main:app` works with
    # zero setup; docker-compose.yml overrides this to the TimescaleDB
    # Postgres instance via the DATABASE_URL environment variable.
    database_url: str = "sqlite:///./lciis.db"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_alert_topic_prefix: str = "lciis/bed"
    ml_model_path: str = "ml/risk_model.joblib"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
