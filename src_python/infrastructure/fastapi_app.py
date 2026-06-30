import asyncio
import logging
from contextlib import asynccontextmanager
import secrets

from fastapi import FastAPI, Security, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials

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
    """Valida credenciales HTTP Básicas para el acceso a la documentación de Swagger/Redoc."""
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
    """Verifica que el cliente suministre una API Key válida en la cabecera 'X-API-Key'"""
    # En desarrollo se permite bypass para no forzar credenciales en pruebas manuales locales.
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
    """
    Worker en background que mantiene la consistencia caché de forma proactiva cada 60 segundos.
    Si settings.USE_REDIS es True, utiliza un Lock Distribuido en Redis para evitar que múltiples instancias
    dupliquen el scrapeo. Si es False, realiza la actualización directamente sin intentar adquirir locks de Redis.
    """
    # En desarrollo se deja en reposo para evitar ruido y trabajo en background innecesario.
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
    worker_task = None
    # Sólo crea el worker en entornos donde el proceso debe comportarse como servicio persistente.
    if settings.ENVIRONMENT != "development":
        worker_task = asyncio.create_task(proactive_cache_worker_loop())
    yield
    if worker_task is None:
        return

    # Cierra la tarea de refresh de forma explícita para no dejar trabajo pendiente al apagar Uvicorn.
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

# El prefijo `/api` y la dependencia global garantizan una política uniforme de autenticación.
app.include_router(
    router,
    prefix="/api",
    dependencies=[Security(validate_api_key)],
    tags=["API Core Components"]
)
