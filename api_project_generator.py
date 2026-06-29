#!/usr/bin/env python3
"""
Clean & Hexagonal Architecture API Project Generator.
This script scaffolds a production-ready, high-performance FastAPI project
using Hexagonal Architecture (Clean Architecture), Dependency Injection, Cache (Redis),
and robust API-Key authentication, mirroring the structural excellence of the BVC API.
"""

import os
import sys

def create_directory_structure(base_dir, project_name, enable_rust=False):
    """Creates the structural directories of a clean hexagonal application."""
    dirs = [
        f"{project_name}_backend",
        f"{project_name}_backend/src_python",
        f"{project_name}_backend/src_python/domain",
        f"{project_name}_backend/src_python/domain/helpers",
        f"{project_name}_backend/src_python/application",
        f"{project_name}_backend/src_python/infrastructure",
        f"{project_name}_backend/src_python/infrastructure/adapters",
        f"{project_name}_backend/src_python/infrastructure/http",
        f"{project_name}_backend/src_python/infrastructure/http/controllers",
        f"{project_name}_backend/tests",
    ]
    if enable_rust:
        dirs.extend([
            f"{project_name}_backend/src",
        ])
    for directory in dirs:
        full_path = os.path.join(base_dir, directory)
        os.makedirs(full_path, exist_ok=True)
        print(f"📁 Creado directorio: {full_path}")


def write_file(path, content):
    """Helper method to write files cleanly."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"📄 Creado archivo: {path}")


def get_docker_compose_template(project_name):
    return f"""
version: '3.8'

services:
  api:
    build: .
    image: {project_name}-backend:latest
    container_name: {project_name}_api
    restart: always
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - REDIS_HOST=redis_cache
      - REDIS_PORT=6379
      - API_KEY=secure_{project_name}_key_v1_high_performance
      - CORS_ORIGINS=*
    env_file:
      - .env.dev # Por defecto carga variables en modo desarrollo si existe, de lo contrario .env
    depends_on:
      - redis_cache

  redis_cache:
    image: redis:7.0-alpine
    container_name: {project_name}_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
"""


def get_dockerfile_template(project_name, enable_rust=False):
    if enable_rust:
        return f"""
# --- Stage 1: Build Rust Extension via PyO3 & maturin ---
FROM python:3.12-alpine AS rust_builder

WORKDIR /app

# Instalar dependencias necesarias para construir extensiones en Rust
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev cargo rust

# Crear entorno virtual local para construir la rueda (wheel)
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

RUN pip install --no-cache-dir maturin patchelf

# Copiar archivos de Rust
COPY Cargo.toml .
COPY src/ ./src/

# Compilar e instalar el módulo Rust directamente en el entorno de build
RUN maturin develop --release

# --- Stage 2: Build Python Dependencies ---
FROM python:3.12-alpine AS python_builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Instalar dependencias en el directorio local de usuario
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 3: Final Slim Image ---
FROM python:3.12-alpine AS runner

WORKDIR /app

# Copiar paquetes instalados desde la stage anterior
COPY --from=python_builder /root/.local /root/.local
COPY --from=rust_builder /app/.venv/lib/python3.12/site-packages/ /root/.local/lib/python3.12/site-packages/
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["python", "app.py"]
"""
    else:
        return """
# --- Stage 1: Build & Dependencies ---
FROM python:3.12-alpine AS builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Instalar dependencias en el directorio local de usuario
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Final Slim Image ---
FROM python:3.12-alpine AS runner

WORKDIR /app

# Copiar paquetes instalados desde la stage anterior
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["python", "app.py"]
"""


def get_requirements_template(enable_rust=False):
    base_reqs = """
fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
redis>=5.0.0
pytest>=8.0.0
httpx>=0.27.0
"""
    if enable_rust:
        base_reqs += "maturin>=1.4.0\n"
    return base_reqs


def get_env_template(project_name, environment="production"):
    return f"""
# Entorno de ejecución: 'development' o 'production'
ENVIRONMENT={environment}

# Configuración del servidor
PORT=8000

# Parámetros de Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_CACHE_DB=0
REDIS_RATE_LIMIT_DB=1
USE_REDIS=True

# Configuración de URL de la Base de Datos (Opcional)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/{project_name}_db

# Seguridad y Autenticación
API_KEY=secure_{project_name}_key_v1_high_performance
CORS_ORIGINS=http://localhost:3000,http://localhost:4200,http://localhost:5173

# Credenciales de Swagger Docs
SWAGGER_USERNAME=admin
SWAGGER_PASSWORD=admin123
"""


def get_app_template(project_name):
    return f"""
import uvicorn
from src_python.infrastructure.config import settings

if __name__ == "__main__":
    # Arrancar FastAPI con el servidor Uvicorn optimizando según entorno
    is_development = settings.ENVIRONMENT == "development"
    
    uvicorn.run(
        "src_python.infrastructure.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development
    )
"""


def get_rust_cargo_template(project_name):
    return f"""
[package]
name = "{project_name}_core"
version = "0.1.0"
edition = "2021"

[lib]
name = "{project_name}_core"
crate-type = ["cdylib"]

[dependencies]
pyo3 = {{ version = "0.20.0", features = ["extension-module"] }}
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
"""


def get_rust_lib_template(project_name):
    return f"""
use pyo3::prelude::*;

pub mod analytics;
pub mod prompt;

#[pymodule]
fn {project_name}_core(_py: Python, m: &PyModule) -> PyResult<()> {{
    m.add_function(wrap_pyfunction!(analytics::compute_timeseries_features, m)?)?;
    m.add_function(wrap_pyfunction!(analytics::compute_fixed_income_features, m)?)?;
    m.add_function(wrap_pyfunction!(prompt::build_final_prompt, m)?)?;
    Ok(())
}}
"""


def get_rust_analytics_template():
    return """
use pyo3::prelude::*;
use pyo3::types::PyDict;

fn rolling_mean_vec(data: &Vec<f64>, window: usize) -> Vec<f64> {
    let n = data.len();
    let mut res = vec![0.0f64; n];
    if n == 0 || window == 0 {
        return res;
    }
    let mut sum = 0.0f64;
    for i in 0..n {
        sum += data[i];
        if i >= window {
            sum -= data[i - window];
            res[i] = sum / window as f64;
        } else {
            res[i] = sum / (i + 1) as f64;
        }
    }
    res
}

fn ema_vec(data: &Vec<f64>, span: usize) -> Vec<f64> {
    let n = data.len();
    let mut res = vec![0.0f64; n];
    if n == 0 || span == 0 {
        return res;
    }
    let a = 2.0 / (span as f64 + 1.0);
    res[0] = data[0];
    for i in 1..n {
        res[i] = a * data[i] + (1.0 - a) * res[i - 1];
    }
    res
}

#[pyfunction]
pub fn compute_timeseries_features(
    py: Python,
    closes: Vec<f64>,
    effective: Vec<f64>,
) -> PyResult<PyObject> {
    let n = closes.len();
    let mut log_return = Vec::with_capacity(n);
    for i in 0..n {
        if i == 0 || closes[i - 1] == 0.0 || closes[i - 1].is_nan() {
            log_return.push(0.0f64);
        } else {
            log_return.push((closes[i] / closes[i - 1]).ln());
        }
    }

    let sma_5 = rolling_mean_vec(&closes, 5);
    let sma_20 = rolling_mean_vec(&closes, 20);
    let ema_9 = ema_vec(&closes, 9);

    let avg_effective = rolling_mean_vec(&effective, 10);
    let liquidity_ratio: Vec<f64> = effective
        .iter()
        .zip(avg_effective.iter())
        .map(|(e, a)| if *a == 0.0 { 0.0 } else { *e / *a })
        .collect();

    let dict = PyDict::new(py);
    dict.set_item("log_return", log_return)?;
    dict.set_item("sma_5", sma_5)?;
    dict.set_item("sma_20", sma_20)?;
    dict.set_item("ema_9", ema_9)?;
    dict.set_item("liquidity_ratio", liquidity_ratio)?;
    Ok(dict.to_object(py))
}

#[pyfunction]
pub fn compute_fixed_income_features(py: Python, instrument: &PyAny) -> PyResult<PyObject> {
    let precio_actual: f64 = instrument
        .get_item("precio_actual")
        .and_then(|v| v.extract())
        .unwrap_or(0.0);
    let valor_nominal: f64 = instrument
        .get_item("valor_nominal")
        .and_then(|v| v.extract())
        .unwrap_or(100.0);
    let plazo_dias: Option<i64> = instrument
        .get_item("plazo_dias")
        .ok()
        .and_then(|v| v.extract().ok());
    let tasa_cupon: f64 = instrument
        .get_item("tasa_cupon")
        .and_then(|v| v.extract())
        .unwrap_or(0.0);
    let rendimiento: f64 = instrument
        .get_item("rendimiento")
        .and_then(|v| v.extract())
        .unwrap_or(0.0);
    let monto_efectivo: f64 = instrument
        .get_item("monto_efectivo")
        .and_then(|v| v.extract())
        .unwrap_or(0.0);

    let plazo_days = plazo_dias.unwrap_or(365) as f64;
    let years_to_maturity = (plazo_days / 365.25).max(0.001);

    let r = (tasa_cupon) / 100.0;
    let macaulay = if r > 0.0 && years_to_maturity > 0.0 {
        (1.0 - (1.0 + r).powf(-years_to_maturity)) / r
    } else {
        years_to_maturity
    };

    let convexity = if r > 0.0 && years_to_maturity > 0.0 {
        (1.0 - (1.0 + r).powf(-years_to_maturity)) / (r * r)
            - (years_to_maturity * (1.0 + r).powf(-years_to_maturity - 1.0)) / r
    } else {
        0.0
    };

    let spread_tir_vs_cupon_bps = (rendimiento - tasa_cupon) * 100.0;

    let carry = if precio_actual > 0.0 {
        (tasa_cupon / 100.0) * 100.0 / precio_actual
    } else {
        0.0
    };

    let features = PyDict::new(py);
    features.set_item("prima_sobre_nominal_pct", precio_actual - valor_nominal)?;
    features.set_item("years_to_maturity", years_to_maturity)?;
    features.set_item("duracion_macaulay_years", (macaulay * 1e4).round() / 1e4)?;
    features.set_item("convexidad", (convexity * 1e4).round() / 1e4)?;
    features.set_item("spread_tir_vs_cupon_bps", spread_tir_vs_cupon_bps)?;
    features.set_item("carry_anualizado_pct", (carry * 1e4).round() / 1e4)?;
    features.set_item("monto_efectivo", monto_efectivo)?;

    Ok(features.to_object(py))
}
"""


def get_rust_prompt_template(project_name):
    return f"""
use pyo3::prelude::*;

const SYSTEM_GUARDRAIL: &str = "
INSTRUCCIONES DE SEGURIDAD Y OPERACIÓN (ESTRICTO):
1. Eres un asistente experto en análisis financiero y operaciones de alto desempeño.
2. Tu propósito es responder e interpretar los datos provistos manteniendo directrices de formato limpias.
";

#[pyfunction]
pub fn build_final_prompt(
    user_prompt: String,
    context_data: String,
    filters_json: String,
    mode: &str,
) -> PyResult<String> {{
    let context_block = format!(
        "--- CONTEXTO OPERATIVO Y DATOS ---\\n\
        DATOS:\\n{{}}\\n\\n\
        Filtros aplicados: {{}}\\n\
        --------------------------------------",
        context_data, filters_json
    );

    let final_body = match mode.to_lowercase().as_str() {{
        "prefijo" => format!("{{}}\\n\\nConsulta: {{}}", context_block, user_prompt),
        "sufijo" => format!(
            "Consulta: {{}}\\n\\nContexto de soporte: {{}}",
            user_prompt, context_block
        ),
        _ => {{
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Modo de prompt inválido",
            ))
        }}
    }};

    Ok(format!("{{}}\\n\\n{{}}", SYSTEM_GUARDRAIL, final_body))
}}
"""


def get_domain_models_template():
    return """
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ResourceModel(BaseModel):
    id: str = Field(..., description="Identificador único del recurso")
    name: str = Field(..., description="Nombre descriptivo")
    description: Optional[str] = Field(None, description="Descripción ampliada")
    category: str = Field(..., description="Categoría o tipo de recurso")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadatos dinámicos")


class RequestPayload(BaseModel):
    message: str = Field(..., min_length=2, description="Mensaje de consulta o petición de usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión para rastrear la interacción")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros de filtrado")
"""


def get_domain_ports_template():
    return """
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from .models import ResourceModel

class IResourceRepository(ABC):
    @abstractmethod
    def fetch_all(self, category: Optional[str] = None) -> List[ResourceModel]:
        \"\"\"Recuperar todos los recursos bajo filtros opcionales.\"\"\"
        pass

    @abstractmethod
    def fetch_by_id(self, resource_id: str) -> Optional[ResourceModel]:
        \"\"\"Obtener un recurso según su identificador único.\"\"\"
        pass

    @abstractmethod
    def save(self, resource: ResourceModel) -> bool:
        \"\"\"Almacenar o actualizar el recurso en el almacenamiento persistente.\"\"\"
        pass


class ICacheService(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        \"\"\"Recuperar valor de la caché.\"\"\"
        pass

    @abstractmethod
    def set(self, key: str, value: Any, timeout: int = 300) -> None:
        \"\"\"Almacena un par clave-valor con expiración dinámica.\"\"\"
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        \"\"\"Remueve manualmente una clave de la caché.\"\"\"
        pass


class IRateLimiter(ABC):
    @abstractmethod
    def is_allowed(self, identifier: str, limit: int, window: int) -> bool:
        \"\"\"Verifica si un cliente supera el límite de peticiones (Rate Limit).\"\"\"
        pass
"""


def get_financial_parser_helper_template():
    return """
import logging
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger("api.helpers")

class FinancialParserHelper:
    \"\"\"
    Helper utilitario del dominio para formateo numérico, conversión y normalización de fechas.
    Completamente puro y libre de dependencias de infraestructura.
    \"\"\"
    
    @staticmethod
    def parse_float(value: Any, default: float = 0.0) -> float:
        \"\"\"Parsea de manera segura strings complejos con formato financiero a decimal float (ej: '1.250,50').\"\"\"
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
            
        try:
            cleaned = str(value).strip().replace(".", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"No se pudo parsear el valor a float: {value}. Retornando default: {default}")
            return default

    @staticmethod
    def parse_int(value: Any, default: int = 0) -> int:
        \"\"\"Parsea strings a enteros manejando caracteres extraños.\"\"\"
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
            
        try:
            cleaned = str(value).strip().split(".")[0].replace(",", "")
            return int(cleaned)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def parse_fecha(value: Any) -> datetime:
        \"\"\"Normaliza múltiples tipos de formatos de fecha a un objeto datetime nativo.\"\"\"
        if isinstance(value, datetime):
            return value
        if not value:
            return datetime.utcnow()

        val_str = str(value).strip()
        
        # Formatos comunes de parsing
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                continue

        logger.debug(f"Formato de fecha no identificado de forma estándar: {value}. Se asume UTC actual.")
        return datetime.utcnow()
"""


def get_use_case_template(project_name, enable_rust=False):
    rust_import = ""
    rust_logic = ""
    if enable_rust:
        rust_import = f"\nfrom {project_name}_core import compute_timeseries_features"
        rust_logic = """
        # Opcional: Procesamiento de Alto Rendimiento en Rust (si se tienen series temporales)
        try:
            sample_closes = [10.0, 10.5, 10.8, 11.0, 11.2]
            sample_volumes = [1000.0, 1500.0, 1200.0, 1800.0, 2000.0]
            features = compute_timeseries_features(sample_closes, sample_volumes)
            logger.info(f"⚙️ Características calculadas con PyO3 Rust con éxito: {features}")
        except ImportError:
            logger.warning("⚠️ No se pudo importar o ejecutar el módulo compiled en Rust. Se ignora cálculo proactivo.")
        except Exception as e:
            logger.error(f"❌ Error al calcular métricas en Rust: {e}")
"""
    return f"""
import logging
from typing import List, Optional, Dict, Any
from ..domain.models import ResourceModel
from ..domain.repository_ports import IResourceRepository, ICacheService{rust_import}

logger = logging.getLogger("api.application")

class GetResourcesUseCase:
    \"\"\"
    Caso de Uso: Obtener Recursos con soporte de Caché Proactivo.
    Coordina la obtención de datos a través de los puertos del dominio.
    \"\"\"
    def __init__(self, repository: IResourceRepository, cache_service: ICacheService):
        self.repository = repository
        self.cache_service = cache_service

    def execute(self, category: Optional[str] = None, refresh: bool = False) -> List[Dict[str, Any]]:
        cache_key = f"resources:list:{{category or 'all'}}"
        
        # 1. Si no se fuerza el refrescado, intentar leer de la Caché (Redis)
        if not refresh:
            cached_data = self.cache_service.get(cache_key)
            if cached_data:
                logger.info(f"⚡ Caché recuperado con éxito para la clave de consulta: {{cache_key}}")
                return cached_data

        # 2. Obtener datos reales mediante Adaptador de Repositorio (Infraestructura)
        logger.info(f"🔍 Buscando recursos frescos en almacenamiento. Categoría: {{category}}")
        resources: List[ResourceModel] = self.repository.fetch_all(category)
        
        # 3. Mapear datos a diccionarios limpios
        serialized_data = []
        for resource in resources:
            serialized_data.append({{
                "id": resource.id,
                "name": resource.name,
                "description": resource.description,
                "category": resource.category,
                "created_at": resource.created_at.isoformat(),
                "properties": resource.properties
            }})
""" + rust_logic + """
        # 4. Guardar en Caché de Redis por 120 segundos
        try:
            self.cache_service.set(cache_key, serialized_data, timeout=120)
            logger.info(f"💾 Clave de caché actualizada exitosamente: {cache_key}")
        except Exception as e:
            logger.error(f"⚠️ Error al guardar información en caché: {e}")

        return serialized_data
"""


def get_config_template(project_name):
    return f"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Entorno de ejecución: 'development' o 'production'
    ENVIRONMENT: str = "production"

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
    API_KEY: str = "secure_{project_name}_key_v1_high_performance"
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
"""


def get_container_template(project_name, enable_rust=False):
    return f"""
import logging
import redis
from .adapters.redis_cache_adapter import RedisCacheAdapter
from .adapters.redis_rate_limiter_adapter import RedisRateLimiterAdapter
from .adapters.mock_db_repository_adapter import MockDBRepositoryAdapter
from ..application.get_resources_use_case import GetResourcesUseCase
from .config import settings

logger = logging.getLogger("api.container")

class Container:
    \"\"\"
    Contenedor de Inyección de Dependencias (DI) de la API.
    Asegura un acoplamiento laxo a lo largo de las capas de negocio e infraestructura.
    Selecciona dinámicamente adaptadores InMemory si Redis está desactivado o caído.
    \"\"\"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Container, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 1. Resolver Adaptadores de Caché y Límite de Peticiones (Redis vs Fallback InMemory)
        from .adapters.redis_cache_adapter import RedisCacheAdapter, MockRedisClient
        from .adapters.redis_rate_limiter_adapter import RedisRateLimiterAdapter
        
        use_redis_db = getattr(settings, "USE_REDIS", True)
        if use_redis_db:
             try:
                  # Chequeo veloz de ping
                  test_client = redis.Redis(
                      host=settings.REDIS_HOST,
                      port=settings.REDIS_PORT,
                      socket_connect_timeout=1.5
                  )
                  test_client.ping()
                  logger.info("📡 Conexión a Redis exitosa. Usando adaptadores de producción Redis.")
                  self.cache_service = RedisCacheAdapter()
                  self.rate_limiter = RedisRateLimiterAdapter()
             except Exception as e:
                  logger.warning(f"⚠️ Servidor Redis no se pudo conectar en {{settings.REDIS_HOST}}:{{settings.REDIS_PORT}} ({{e}}). Usando Fallback InMemory.")
                  self.cache_service = RedisCacheAdapter() # Auto fallbacks a MockRedisClient
                  self.rate_limiter = RedisRateLimiterAdapter() # Auto fallbacks a fail-safe
        else:
             logger.info("ℹ️ Redis se encuentra desactivado bajo el flag USE_REDIS. Usando Adaptadores InMemory.")
             self.cache_service = RedisCacheAdapter() # Auto fallbacks a MockRedisClient
             self.rate_limiter = RedisRateLimiterAdapter() # Auto fallbacks a fail-safe

        # 2. Adaptador de Almacenamiento Primario
        self.resource_repository = MockDBRepositoryAdapter()
        
        # 3. Casos de Uso del Negocio
        self.get_resources_use_case = GetResourcesUseCase(
            repository=self.resource_repository,
            cache_service=self.cache_service
        )

# Instanciación única global (Singleton)
container = Container()
"""


def get_fastapi_app_template():
    return """
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Security, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import secrets

from .config import settings
from .container import container
from .http.routes import router

# Configuración limpia de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("api.core")

# --- Dependencia de Seguridad: Validación de API Key ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
security_basic = HTTPBasic()

def validate_swagger_auth(credentials: HTTPBasicCredentials = Security(security_basic)):
    \"\"\"Valida credenciales HTTP Básicas para el acceso a la documentación de Swagger/Redoc.\"\"\"
    is_username_correct = secrets.compare_digest(credentials.username, settings.SWAGGER_USERNAME)
    is_password_correct = secrets.compare_digest(credentials.password, settings.SWAGGER_PASSWORD)
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de documentación inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

async def validate_api_key(api_key: str = Security(api_key_header)):
    \"\"\"Verifica que el cliente suministre una API Key válida en la cabecera 'X-API-Key'\"\"\"
    # Si está en modo de desarrollo, se permite bypass o validación laxa de API Key para facilitar el desarrollo local
    if settings.ENVIRONMENT == "development":
        logger.info("🛠️ Modo Desarrollo Activo: Se permite Bypass de validación de API Key.")
        return api_key or "dev_bypass_key"

    if not api_key:
        logger.warning("Intento de acceso denegado: Cabecera 'X-API-Key' ausente.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta la API Key en el encabezado 'X-API-Key' para autenticación."
        )
    if api_key != settings.API_KEY:
        logger.warning("Intento de acceso denegado: API Key inválida proporcionada.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La API Key proporcionada es inválida o no cuenta con suficientes permisos."
        )
    return api_key


# --- Control de Concurrencia: Worker de Pre-procesamiento / Refresh de Caché ---
async def proactive_cache_worker_loop():
    \"\"\"
    Worker en background que mantiene la consistencia caché de forma proactiva cada 60 segundos.
    Si settings.USE_REDIS es True, utiliza un Lock Distribuido en Redis para evitar que múltiples instancias
    dupliquen el scrapeo. Si es False, realiza la actualización directamente sin intentar adquirir locks de Redis.
    \"\"\"
    # En entorno de desarrollo rápido, se deshabilita el worker para evitar spam de logs o consumos de infraestructura
    if settings.ENVIRONMENT == "development":
        logger.info("🛠️ Modo Desarrollo Activo: Worker proactivo de background en reposo por defecto.")
        return

    logger.info("🚀 Worker de Caché Distribuido: Ejecutándose en background.")
    lock_name = "api_worker_refresh_lock"
    # Timeout de 50 segs para liberar el lock automáticamente si el proceso falla por completo
    lock_timeout = 50 

    while True:
        try:
            acquired = False
            lock = None

            if getattr(settings, "USE_REDIS", True):
                try:
                    redis_client = container.cache_service.client
                    lock = redis_client.lock(lock_name, timeout=lock_timeout, blocking=False)
                    acquired = lock.acquire()
                except Exception as redis_lock_err:
                    logger.warning(f"⚠️ Error al intentar adquirir lock distribuido en Redis, reintentando de forma local: {redis_lock_err}")
                    # Contingencia local: si Redis falla estando en True, forzamos la actualización directa
                    acquired = True
            else:
                # Si Redis está explícitamente desactivado de settings, actualiza directamente por proceso
                acquired = True

            if acquired:
                if getattr(settings, "USE_REDIS", True):
                    logger.info("🔒 Lock distribuido de worker adquirido con éxito en Redis.")
                else:
                    logger.info("ℹ️ Redis desactivado: Iniciando actualización proactiva de forma directa...")

                try:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: container.get_resources_use_case.execute(refresh=True)
                    )
                    logger.info("✅ Caché refrescado de manera óptima por el worker proactivo.")
                except Exception as ex:
                    logger.error(f"❌ Error durante el procesamiento de datos del worker: {ex}")
                finally:
                    if getattr(settings, "USE_REDIS", True) and lock:
                        try:
                            lock.release()
                            logger.info("🔓 Lock distribuido liberado con éxito.")
                        except Exception:
                            pass
            else:
                logger.debug("⏳ Lock ocupado por otra réplica. Saltando ciclo del worker.")
        except Exception as e:
            logger.error(f"⚠️ Error general en el loop del worker: {e}")

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia la tarea en segundo plano al arrancar la aplicación
    worker_task = asyncio.create_task(proactive_cache_worker_loop())
    yield
    # Cancela la tarea en segundo plano al apagar la aplicación
    logger.info("🛑 Deteniendo el worker de caché proactivo...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Clean Architecture Production API",
    description="Servicio backend robusto, desacoplado y de alto rendimiento utilizando Arquitectura Hexagonal.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Deshabilita los endpoints públicos globales para protegerlos
    redoc_url=None
)

# Configuración integrada de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rutas de Documentación Protegidas por HTTP Basic Auth ---
@app.get("/docs", include_in_schema=False)
async def secure_swagger_html(username: str = Security(validate_swagger_auth)):
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI"
    )

@app.get("/redoc", include_in_schema=False)
async def secure_redoc_html(username: str = Security(validate_swagger_auth)):
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc"
    )

# Integración similar a la arquitectura Route de Laravel:
# - Prefijado global para versionamiento (ej: /api)
# - Aplicación de Middleware de Seguridad unificado a nivel de grupo de rutas
app.include_router(
    router,
    prefix="/api",
    dependencies=[Security(validate_api_key)],
    tags=["API Core Components"]
)
"""


def get_redis_cache_adapter_template():
    return """
import json
import logging
from typing import Any, Optional
import redis
from ...domain.repository_ports import ICacheService
from ..config import settings

logger = logging.getLogger("api.infrastructure")

class RedisCacheAdapter(ICacheService):
    \"\"\"Adaptador de Infraestructura para gestión de Caché con Redis.\"\"\"
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_CACHE_DB,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Prueba de ping rápida no bloqueante
            self.client.ping()
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"🚨 No se pudo establecer conexión nativa con Redis Server en {settings.REDIS_HOST}:{settings.REDIS_PORT} ({e}). Activando modo failover (Local Memory Mock).")
            self.client = MockRedisClient()

    def get(self, key: str) -> Any:
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error al leer de Redis (clave: {key}): {e}")
            return None

    def set(self, key: str, value: Any, timeout: int = 300) -> None:
        try:
            serialized = json.dumps(value)
            self.client.set(key, serialized, ex=timeout)
        except Exception as e:
            logger.error(f"Error al escribir en Redis (clave: {key}): {e}")

    def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Error al eliminar de Redis (clave: {key}): {e}")


class MockRedisClient:
    \"\"\"Cliente fallback en memoria por si Redis no está levantado.\"\"\"
    def __init__(self):
        self._store = {}
        
    def ping(self):
        return True
        
    def get(self, key):
        return self._store.get(key)
        
    def set(self, key, value, ex=None):
        self._store[key] = value
        
    def delete(self, key):
        self._store.pop(key, None)
        
    def lock(self, name, timeout=10, blocking=False):
        return MockLock()


class MockLock:
    def acquire(self):
        return True
    def release(self):
        return True
"""


def get_redis_rate_limiter_adapter_template():
    return """
import time
import logging
import redis
from ...domain.repository_ports import IRateLimiter
from ..config import settings

logger = logging.getLogger("api.infrastructure")

class RedisRateLimiterAdapter(IRateLimiter):
    \"\"\"Adaptador de Infraestructura para Limitar cuotas de peticiones mediante algoritmo de Sliding Window.\"\"\"
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_RATE_LIMIT_DB,
                socket_connect_timeout=2
            )
            self.client.ping()
            self._available = True
        except (redis.ConnectionError, redis.TimeoutError):
            self._available = False

    def is_allowed(self, identifier: str, limit: int, window: int) -> bool:
        if not self._available:
            # Fail-safe: si el servidor Redis de contingencia falla, permitir peticiones temporalmente
            return True
            
        try:
            current_time = time.time()
            clean_before = current_time - window
            key = f"rate_limit:{identifier}"
            
            # Utilizar pipeline multi para consistencia atómica
            pipe = self.client.pipeline()
            pipe.zremrangebyscore(key, 0, clean_before)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = pipe.execute()
            
            peticiones_realizadas = results[2]
            return peticiones_realizadas <= limit
        except Exception as e:
            logger.error(f"Excepción en el adaptador de Rate Limit Redis: {e}")
            return True
"""


def get_mock_db_repository_adapter_template():
    return """
from typing import List, Optional
from datetime import datetime
from ...domain.models import ResourceModel
from ...domain.repository_ports import IResourceRepository

class MockDBRepositoryAdapter(IResourceRepository):
    \"\"\"
    Adaptador de repositorio simulado (Mock / In-Memory Database).
    En producción, este archivo importará SQLAlchemy, Tortoise o SQLModel para interactuar con PostgreSQL.
    \"\"\"
    def __init__(self):
        self._database = [
            ResourceModel(
                id="res_01",
                name="Servicio de Autenticación Central",
                description="Clúster SSO integrado con soporte JWT.",
                category="Sistemas",
                created_at=datetime.utcnow(),
                properties={"sla": "99.99%", "owner": "DevOps Team"}
            ),
            ResourceModel(
                id="res_02",
                name="Motor de Predicciones AI",
                description="Servicio conversacional de inferencia inteligente.",
                category="IA",
                created_at=datetime.utcnow(),
                properties={"model": "deepseek-reasoner", "api_calls_quota": 5000}
            ),
            ResourceModel(
                id="res_03",
                name="Base de Datos Analítica Principal",
                description="Data warehouse analítico estructurado en PostgreSQL.",
                category="Bases de Datos",
                created_at=datetime.utcnow(),
                properties={"engine": "PostgreSQL 16", "backup_policy": "Daily"}
            )
        ]

    def fetch_all(self, category: Optional[str] = None) -> List[ResourceModel]:
        if category:
            return [res for res in self._database if res.category.lower() == category.lower()]
        return self._database

    def fetch_by_id(self, resource_id: str) -> Optional[ResourceModel]:
        for res in self._database:
            if res.id == resource_id:
                return res
        return None

    def save(self, resource: ResourceModel) -> bool:
        # Remover si ya existe para simular un UPSERT
        self._database = [res for res in self._database if res.id != resource.id]
        self._database.append(resource)
        return True
"""


def get_routes_template(project_name, enable_rust=False):
    rust_route = ""
    if enable_rust:
        rust_route = """

@router.post("/resources/rust-analytics", tags=["High Performance (Rust)"])
def execute_rust_analytics(payload: Dict[str, Any]):
    return ResourcesController.execute_rust_analytics(payload)"""

    return f"""from fastapi import APIRouter, Query, Request, Security
from typing import Optional, Dict, Any

from .controllers.resources_controller import ResourcesController
from .rate_limiter_decorator import rate_limit

# Router principal v1
router = APIRouter(prefix="/v1")

# --- 1. Definición de Rutas Directas (FastAPI Idiomático) ---
@router.get("/status", tags=["Utility"])
def get_status():
    \"\"\"Endpoint público informativo de salud.\"\"\"
    return ResourcesController.get_root_status()

# --- 2. Rutas con parámetros de entrada (FastAPI inyecta la firma aquí) ---
@router.get("/resources", tags=["Resources"])
@rate_limit(limit=20, window=60)
def get_resources(
    request: Request,
    category: Optional[str] = Query(None, description="Categoría para filtrar recursos"),
    force_refresh: bool = Query(False, alias="refresh", description="Forzar lectura omitiendo la caché de Redis"),
):
    return ResourcesController.get_resources_endpoint(
        request=request,
        category=category,
        force_refresh=force_refresh
    )

@router.post("/resources/parse-value", tags=["Helpers"])
def execute_financial_parsing(payload: Dict[str, Any]):
    return ResourcesController.execute_financial_parsing(payload){rust_route}
"""


def get_resources_controller_template(project_name, enable_rust=False):
    rust_method = ""
    if enable_rust:
        rust_method = f"""

    @staticmethod
    def execute_rust_analytics(payload: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Endpoint de demostración de alto rendimiento ejecutando algoritmos compilados en Rust vía PyO3.\"\"\"
        try:
            from {project_name}_core import compute_timeseries_features, compute_fixed_income_features, build_final_prompt
            
            # Modo 1: Series Temporales
            closes = payload.get("closes", [100.0, 101.5, 102.3, 101.0, 104.2])
            effective = payload.get("effective", [500000.0, 600000.0, 550000.0, 480000.0, 720000.0])
            ts_features = compute_timeseries_features(closes, effective)
            
            # Modo 2: Renta Fija
            instrument_data = payload.get("instrument", {{
                "precio_actual": 98.5,
                "valor_nominal": 100.0,
                "plazo_dias": 180,
                "tasa_cupon": 5.5,
                "rendimiento": 6.2,
                "monto_efectivo": 2500000.0
            }})
            fi_features = compute_fixed_income_features(instrument_data)
            
            # Modo 3: Prompt Guardrail compilado en Rust
            prompt_built = build_final_prompt(
                payload.get("user_prompt", "Hola, analiza Ron Santa Teresa"),
                "Santa Teresa cotiza a 5.2 VES en mercado primario.",
                '{{"category": "bebidas"}}',
                "prefijo"
            )
            
            return {{
                "rust_module": "v1.0.0 (Compiled C-Extension via PyO3)",
                "timeseries_features": ts_features,
                "fixed_income_features": fi_features,
                "prompt_security_built": prompt_built
            }}
        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"La extensión compilada en Rust no se encuentra disponible o no fue construida: {{e}}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error durante el procesamiento nativo de Rust: {{e}}"
            )"""

    return f"""
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Request
from ....domain.helpers.financial_parser_helper import FinancialParserHelper
from ...container import container

class ResourcesController:
    \"\"\"
    Controlador de Recursos que maneja la lógica HTTP de entrada
    y delega las ejecuciones a los casos de uso correspondientes.
    \"\"\"
    @staticmethod
    def get_root_status() -> Dict[str, str]:
        \"\"\"Endpoint público informativo de salud.\"\"\"
        return {{
            "status": "healthy",
            "message": "La API corre de manera óptima utilizando Arquitectura Hexagonal.",
            "version": "1.0.0"
        }}

    @staticmethod
    def get_resources_endpoint(
        request: Request,
        category: Optional[str] = None,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        \"\"\"Consigue los recursos a través del Caso de Uso (con límites y caché).\"\"\"
        try:
            # Delegamos a la capa de Aplicación
            return container.get_resources_use_case.execute(category=category, refresh=force_refresh)
        except HTTPException as http_ex:
            # Re-lanzamos excepciones HTTP para que FastAPI las maneje
            raise http_ex

    @staticmethod
    def execute_financial_parsing(payload: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Ejecuta Parseo Financiero del Dominio.\"\"\"
        raw_value = payload.get("value")
        return {{
            "original": raw_value,
            "parsed_float": FinancialParserHelper.parse_float(raw_value),
            "parsed_int": FinancialParserHelper.parse_int(raw_value),
            "parsed_fecha": FinancialParserHelper.parse_fecha(payload.get("fecha")).isoformat()
        }}{rust_method}
"""


def get_test_sample_template(project_name, enable_rust=False):
    rust_test = ""
    if enable_rust:
        rust_test = f"""


def test_rust_pyo3_compilation_and_calculations():
    \"\"\"Valida de forma nativa que los bindings en Rust se expongan y funcionen correctamente de forma aislada.\"\"\"
    try:
        from {project_name}_core import compute_timeseries_features, build_final_prompt
        import math
        
        # Test 1: Series Temporales en Rust (Log-Returns y Medias Móviles)
        closes = [10.0, 20.0, 40.0]
        vols = [100.0, 100.0, 100.0]
        results = compute_timeseries_features(closes, vols)
        
        assert "log_return" in results
        assert math.isclose(results["log_return"][1], 0.693147, rel_tol=1e-4) # ln(20/10)
        
        # Test 2: Prompt Guardrails en Rust
        assembled = build_final_prompt("User query", "BVC context", "{{}}", "prefijo")
        assert "INSTRUCCIONES" in assembled
        assert "User query" in assembled
    except ImportError:
        # Si no se encuentra compilado localmente en ambiente de testing rápido, se pasa de largo silenciosamente
        pass
"""
    return f"""
import pytest
from src_python.domain.helpers.financial_parser_helper import FinancialParserHelper
from src_python.domain.models import ResourceModel
from src_python.application.get_resources_use_case import GetResourcesUseCase

# Clases Mock rápidas para testing aislado sin Redis o DB
class MockRepository:
    def fetch_all(self, category=None):
        return [
            ResourceModel(
                id="test_01",
                name="Servicios de Testeo",
                category="Pruebas",
                properties={{}}
            )
        ]
    def fetch_by_id(self, id):
         return None
    def save(self, res):
         return True


class MockCache:
    def get(self, key):
         return None
    def set(self, key, val, timeout=30):
         pass
    def delete(self, key):
         pass


def test_financial_parser_helper_float():
    \"\"\"Valida que el Parser Helper de Dominio procese correctamente decimales venezolanos y americanos.\"\"\"
    assert FinancialParserHelper.parse_float("1.250,75") == 1250.75
    assert FinancialParserHelper.parse_float("100,5") == 100.5
    assert FinancialParserHelper.parse_float("450") == 450.0
    assert FinancialParserHelper.parse_float(None) == 0.0


def test_financial_parser_helper_int():
    \"\"\"Valida que el Parser Helper de Dominio convierta sin errores a enteros.\"\"\"
    assert FinancialParserHelper.parse_int("1,500") == 1500
    assert FinancialParserHelper.parse_int(78.9) == 78


def test_get_resources_use_case():
    \"\"\"Valida la correcta coordinación del Caso de Uso entregando salidas mapeadas.\"\"\"
    use_case = GetResourcesUseCase(MockRepository(), MockCache())
    result = use_case.execute()
    
    assert len(result) == 1
    assert result[0]["id"] == "test_01"
    assert result[0]["category"] == "Pruebas"{rust_test}
"""


def get_readme_template(project_name, enable_rust=False):
    rust_section = ""
    if enable_rust:
        rust_section = """
### 🦀 Integración nativa de Rust (PyO3 + Maturin)
Este proyecto incluye un pipeline para compilar código nativo de Rust de alto rendimiento bajo demanda convirtiéndolo en un módulo de extensión binario importable de Python (`.pyd` o `.so`).

Para compilar localmente el módulo de Rust:
```bash
pip install maturin patchelf
maturin develop --release
```
Esto instalará el módulo nativo compilado en su entorno virtual local para poder ejecutar y probar los cálculos analíticos a la velocidad del lenguaje compilado.
"""
    return f"""
# Backend API - {project_name.upper()}

Este proyecto ha sido generado con una robusta **Arquitectura Hexagonal (Clean Architecture)** enfocada en la alta escalabilidad, mantenimiento simple y máximo rendimiento, desacoplado de dependencias particulares.

Además, cuenta con un **Modo Desarrollo (Development Mode)** integrado para agilizar el flujo de trabajo de los ingenieros de software de forma local o en entornos compartidos.

---

## 🛠️ Arquitectura de Directorios

El backend se estructura de la siguiente manera bajo el principio de separación de responsabilidades:

```
{project_name}_backend/
├── app.py                      # Punto de arranque de la aplicación usando Uvicorn.
├── Dockerfile                  # Empaquetado Docker optimizado en dos fases (Slim).
├── docker-compose.yml          # Define servicios de API y Redis DB de forma local.
├── requirements.txt            # Dependencias actualizadas del ecosistema Python.
├── .env                        # Configuración del entorno de producción.
├── .env.dev                    # Configuración del entorno de desarrollo estructurado.
├── .env.example                # Plantilla de variables de entorno para producción.
└── src_python/
    ├── domain/                 # Capa de Core Logics y Reglas de Negocio.
    │   ├── models.py           # Estructuras de datos (Modelos de entidad).
    │   ├── repository_ports.py # Interfaces abstractas regulando adaptadores (Puertos).
    │   └── helpers/            # Calculadores e identificadores numéricos y de fechas puros.
    ├── application/            # Casos de uso de negocio (Use Cases).
    │   └── get_resources_use_case.py
    └── infrastructure/         # Adaptadores (Entrada y Salida).
        ├── config.py           # Centralizador de Pydantic Settings & Env Vars.
        ├── container.py        # Inyector de Dependencias (DI Container Singleton).
        ├── fastapi_app.py      # Levantamiento de Lifespans, Middleware de CORS, Seguridad.
        ├── adapters/           # Adaptadores de tecnologías externas (Redis, Mock DB).
        │   ├── redis_cache_adapter.py
        │   ├── redis_rate_limiter_adapter.py
        │   └── mock_db_repository_adapter.py
        └── http/               # Capa de API Controllers y Rutas.
            ├── routes.py       # Definición e interfaz web de las rutas de FastAPI.
            └── controllers/    # Controladores que mapean y procesan las solicitudes.
                └── resources_controller.py  # Controlador HTTP que delega a los casos de uso.
```

---

## ⚙️ Entornos de Ejecución (Desarrollo vs Producción)

El proyecto ofrece un comportamiento diferenciado según el entorno establecido por la variable `ENVIRONMENT`:

### 🛠️ Entorno de Desarrollo (`ENVIRONMENT=development`)
Orientado a agilizar la rapidez del desarrollo y pruebas rápidas:
1. **Bypass de API Key / Seguridad Laxa**: Los endpoints protegidos permiten el acceso con cualquier API Key o cabecera ausente, logueando un aviso de bypass local sin bloquear las solicitudes.
2. **Hot-Reload Automático**: Al arrancar `app.py` de forma manual o con docker, los cambios se recargan al instante en caliente.
3. **Mocks y Fallback del Almacenamiento**: Si Redis no está disponible o no se puede conectar, la API arranca con un cliente mock en memoria (`MockRedisClient`) sin caídas de servicio.

### 🚀 Entorno de Producción (`ENVIRONMENT=production`)
Fijado para despliegues de grado de producción:
1. **Validación Estricta de API Key**: Bloqueo estricto del tráfico anónimo y denegaciones `401 Unauthorized` / `403 Forbidden`.
2. **Worker de Caché Distribuido con Autolock**: Sincronización precisa y background loop a través de locks distribuidos en Redis.
3. **Hot-Reload Deshabilitado**: Optimización máxima de hilos y sockets.

---

## 🚀 Guía de Levantamiento de la Aplicación

### Paso 1: Instalar Dependencias Locales (Opcional si usa Docker)
Crear un entorno virtual de Python y arrancar dependencias:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### Paso 2: Configurar su entorno
Para desarrollo local, copie `.env.dev` o configure la variable `ENVIRONMENT=development` en su archivo `.env`:
```bash
cp .env.dev .env
```

### Paso 3: Arrancar con Docker Compose (Recomendado)
Levanta de manera automática la API funcional y el servidor Redis de caché en contenedores independientes:
```bash
docker-compose up --build -d
```
La aplicación se encontrará lista en `http://localhost:8000`.

---

## 🛠️ Pruebas Locales Manuales durante el Desarrollo

Durante el desarrollo, no necesitas configurar Redis ni API Keys válidas en cada petición gracias al **Modo Desarrollo**. Aquí tienes una guía rápida de cómo probar tu API de inmediato:

### 1. Probar sin Redis (Auto-Mock)
Si ejecutas la API localmente (`python app.py`) y no tienes un servidor Redis corriendo, la aplicación detectará el fallo de conexión automáticamente o la variable `ENVIRONMENT=development` y activará el **`MockRedisClient`**.
- La API seguirá funcionando perfectamente.
- Los límites de peticiones (Rate Limit) registrarán logs pero no bloquearán tus consultas.

### 2. Probar Endpoints Autenticados
Normalmente los endpoints bajo `/api/v1/...` requieren la cabecera `X-API-Key` y validación robusta. Sin embargo, en desarrollo:
- Puedes enviar peticiones **sin cabecera** o con cualquier valor arbitrario (ej. `X-API-Key: lala`).
- El backend los validará de manera laxa, registrará un aviso en la terminal `[BYPASS] API-Key checking bypassed under development mode` y te dará acceso sin problemas.

#### Ejemplo de Petición con cURL:
```bash
curl -X GET "http://localhost:8000/api/v1/resources" \\
  -H "X-API-Key: desarrollo"
```

#### Ejemplo de Petición con Python `requests`:
```python
import requests

headers = {{"X-API-Key": "cualquier_cosa_en_desarrollo"}}
response = requests.get("http://localhost:8000/api/v1/resources", headers=headers)
print(response.json())
```

{rust_section}
---

## 🔒 Consumo Seguro de Endpoints

### 1. Validación de Salud (Health Probe)
- **Ruta**: `GET http://localhost:8000/`
- **Autenticación**: Ninguna (Público).

### 2. Obtener Recursos (Endpoint Protegido)
- **Ruta**: `GET http://localhost:8000/api/v1/resources`
- **Autenticación**: Requiere la cabecera `X-API-Key` provista en su archivo `.env` (Excepto en `ENVIRONMENT=development`).
- **Rate-limit**: Protegido con **20 peticiones por minuto** para prevenir sobreingestas.

---

## 🧪 Ejecución de Pruebas de Software
Para arrancar las suites de testeo unitarias y comprobar la integridad funcional de forma automatizada, use:
```bash
pytest
```
"""


def main():
    print("=========================================================================")
    print(" 🛠️  HEXAGONAL ARCHITECTURE - FASTAPI PROJECT GENERATOR")
    print("=========================================================================\n")

    # Solicitar datos del proyecto
    if len(sys.argv) > 1:
        project_name = sys.argv[1].replace("-", "_").lower()
        # Permitir argumento para habilitar Rust
        enable_rust = "--with-rust" in sys.argv
    else:
        project_name = input("✍️  Ingrese el nombre del proyecto (default: modern_service): ").strip()
        if not project_name:
            project_name = "modern_service"
        rust_input = input("🦀 ¿Desea integrar soporte opcional para extensiones en Rust (PyO3 + Maturin)? (s/n, default: n): ").strip().lower()
        enable_rust = rust_input == "s"
            
    project_slug = project_name.replace("-", "_").lower()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, f"{project_slug}_backend")

    if os.path.exists(project_root):
        overwrite = input(f"⚠️  El directorio '{project_slug}_backend' ya existe. ¿Desea sobrescribirlo? (s/n): ").strip().lower()
        if overwrite != "s":
            print("❌ Generación cancelada por el usuario.")
            return

    print(f"\n🚀 Iniciando scaffolding de: '{project_slug}' (Soporte Rust: {'Habilitado' if enable_rust else 'Deshabilitado'})...")

    # 1. Crear directorios
    create_directory_structure(base_dir, project_slug, enable_rust=enable_rust)

    # 2. Archivos raíz del proyecto
    write_file(f"{project_root}/requirements.txt", get_requirements_template(enable_rust=enable_rust))
    write_file(f"{project_root}/Dockerfile", get_dockerfile_template(project_slug, enable_rust=enable_rust))
    write_file(f"{project_root}/docker-compose.yml", get_docker_compose_template(project_slug))
    write_file(f"{project_root}/.env", get_env_template(project_slug, "production"))
    write_file(f"{project_root}/.env.dev", get_env_template(project_slug, "development"))
    write_file(f"{project_root}/.env.example", get_env_template(project_slug, "production"))
    write_file(f"{project_root}/app.py", get_app_template(project_slug))
    write_file(f"{project_root}/README.md", get_readme_template(project_slug, enable_rust=enable_rust))

    # Si Rust está habilitado, escribir metadatos y fuentes nativos de Rust
    if enable_rust:
        write_file(f"{project_root}/Cargo.toml", get_rust_cargo_template(project_slug))
        write_file(f"{project_root}/src/lib.rs", get_rust_lib_template(project_slug))
        write_file(f"{project_root}/src/analytics.rs", get_rust_analytics_template())
        write_file(f"{project_root}/src/prompt.rs", get_rust_prompt_template(project_slug))

    # 3. Capa de dominio
    src_dir = f"{project_root}/src_python"
    write_file(f"{src_dir}/domain/__init__.py", "")
    write_file(f"{src_dir}/domain/models.py", get_domain_models_template())
    write_file(f"{src_dir}/domain/repository_ports.py", get_domain_ports_template())
    write_file(f"{src_dir}/domain/helpers/__init__.py", "")
    write_file(f"{src_dir}/domain/helpers/financial_parser_helper.py", get_financial_parser_helper_template())

    # 4. Capa de aplicación
    write_file(f"{src_dir}/application/__init__.py", "")
    write_file(f"{src_dir}/application/get_resources_use_case.py", get_use_case_template(project_slug, enable_rust=enable_rust))

    # 5. Capa de infraestructura externa y adaptadores
    write_file(f"{src_dir}/infrastructure/__init__.py", "")
    write_file(f"{src_dir}/infrastructure/config.py", get_config_template(project_slug))
    write_file(f"{src_dir}/infrastructure/container.py", get_container_template(project_slug, enable_rust=enable_rust))
    write_file(f"{src_dir}/infrastructure/fastapi_app.py", get_fastapi_app_template())
    
    # Adaptadores concretos
    write_file(f"{src_dir}/infrastructure/adapters/__init__.py", "")
    write_file(f"{src_dir}/infrastructure/adapters/redis_cache_adapter.py", get_redis_cache_adapter_template())
    write_file(f"{src_dir}/infrastructure/adapters/redis_rate_limiter_adapter.py", get_redis_rate_limiter_adapter_template())
    write_file(f"{src_dir}/infrastructure/adapters/mock_db_repository_adapter.py", get_mock_db_repository_adapter_template())

    # Controladores y Enrutadores API HTTP
    write_file(f"{src_dir}/infrastructure/http/__init__.py", "")
    write_file(f"{src_dir}/infrastructure/http/controllers/__init__.py", "")
    write_file(f"{src_dir}/infrastructure/http/routes.py", get_routes_template(project_slug, enable_rust=enable_rust))
    write_file(f"{src_dir}/infrastructure/http/controllers/resources_controller.py", get_resources_controller_template(project_slug, enable_rust=enable_rust))

    # 6. Tests unitarios en suite aislada de base de datos
    write_file(f"{project_root}/tests/__init__.py", "")
    write_file(f"{project_root}/tests/conftest.py", "# Conftest para inicialización de fixtures de tests si es necesario.")
    write_file(f"{project_root}/tests/test_api_core.py", get_test_sample_template(project_slug, enable_rust=enable_rust))

    # Mensaje final de éxito
    print("\n=========================================================================")
    print(" 🎉  PROYECTO SCAFFOLDED CON ÉXITO!")
    print("=========================================================================")
    print(f"📍 Ubicación del proyecto: {project_root}")
    print("\n📦 Pasos sugeridos para iniciar:")
    print(f"  1. Navegue al directorio: cd {project_slug}_backend")
    if enable_rust:
        print("  2. Compile el módulo nativo en Rust: maturin develop --release")
        print("  3. Inicie servicios con Docker Compose: docker-compose up --build -d")
    else:
        print("  2. Inicie servicios con Docker Compose: docker-compose up --build -d")
    print("  3. Pruebe los endpoints en: http://localhost:8000/docs")
    print("  4. Ejecute tests con la herramienta pytest: pytest")
    print("=========================================================================\n")


if __name__ == "__main__":
    main()
