from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")

    #DATABASE_URL
    database_url: str= Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")

    hugging_face_url: str = Field(..., alias="HUGGINGFACEHUB_API_TOKEN")


    # Paths
    pdf_dir: str = Field("data/pdfs", alias="PDF_DIR")
    csv_path: str = Field("data/csv/farm_production.csv", alias="CSV_PATH")
    vectorstore_dir: str = Field("data/vectorstore", alias="VECTORSTORE_DIR")

 


@lru_cache
def get_settings() -> Settings:
    return Settings()