from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Entorno de ejecución: 'development' o 'production'
    ENVIRONMENT: str = "production"

    # Puerto HTTP del servidor ASGI
    PORT: int = 8000

    # Configuración de Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_CACHE_DB: int = 0
    REDIS_RATE_LIMIT_DB: int = 1
    USE_REDIS: bool = True  # Define si se prefiere usar Redis (True) o usar InMemory (False)
    
    # Base de Datos de Aplicación
    DATABASE_URL: str = ""
    
    # Seguridad, CORS y Autenticación
    cors_origins_raw: str = Field("*", validation_alias="CORS_ORIGINS")
    API_KEY: str = "secure_apivenezuelaearthquake_key_v1_high_performance"
    SWAGGER_USERNAME: str = "admin"
    SWAGGER_PASSWORD: str = "admin123"

    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]

    # Carga automática del archivo .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
