from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://lciis:lciis@localhost:5432/lciis"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_alert_topic_prefix: str = "lciis/bed"
    ml_model_path: str = "ml/risk_model.joblib"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
