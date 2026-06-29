import functools
from fastapi import Request, HTTPException, status
from ..container import container

def rate_limit(limit: int, window: int = 60):
    """
    Decorador para aplicar límites de peticiones (Rate Limiting) en endpoints de FastAPI.
    Extrae la dirección IP del cliente o el identificador personalizado y consulta el adaptador de Rate Limit.
    Compatible con funciones asíncronas y asíncronas decoradas de FastAPI.
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Buscar el objeto Request de FastAPI en los argumentos posicionales o de palabra clave
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                # Si el endpoint no recibe el Request, no podemos identificar el IP de forma segura.
                # Permitimos continuar o arrojamos advertencia según las sugerencias de arquitectura.
                return await func(*args, **kwargs)
            
            # Obtener IP del cliente de forma segura
            client_ip = request.client.host if request.client else "unknown_ip"
            
            # Definir un identificador de rate limit único basado en la función decorada y el IP
            identifier = f"{func.__name__}:{client_ip}"
            
            # Consultar con el limitador inyectado en el contenedor
            allowed = container.rate_limiter.is_allowed(identifier, limit=limit, window=window)
            
            if not allowed:
                 raise HTTPException(
                     status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                     detail=f"Has excedido el límite de {limit} peticiones por {window} segundos."
                 )
            
            return await func(*args, **kwargs)
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Versión sincrónica si se requiere en endpoints síncronos
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                return func(*args, **kwargs)
                
            client_ip = request.client.host if request.client else "unknown_ip"
            identifier = f"{func.__name__}:{client_ip}"
            
            allowed = container.rate_limiter.is_allowed(identifier, limit=limit, window=window)
            
            if not allowed:
                 raise HTTPException(
                     status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                     detail=f"Has excedido el límite de {limit} peticiones por {window} segundos."
                 )
                 
            return func(*args, **kwargs)

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
