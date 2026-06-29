import uvicorn
from src_python.infrastructure.config import settings
from src_python.infrastructure.fastapi_app import app

if __name__ == "__main__":
    # Arrancar FastAPI con el servidor Uvicorn optimizando según entorno
    is_development = settings.ENVIRONMENT == "development"
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development
    )
