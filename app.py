import uvicorn
from src_python.infrastructure.config import settings
from src_python.infrastructure.fastapi_app import app

if __name__ == "__main__":
    # El entrypoint raíz expone `app` para runners ASGI y usa `PORT` para evitar puertos hardcodeados.
    is_development = settings.ENVIRONMENT == "development"
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=is_development
    )
