import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from conf.settings import env
from starlette.middleware.base import BaseHTTPMiddleware

no_login_paths = ['/api/users/login']

ALGORITHM = "HS256"

class LoginMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in no_login_paths:
            return await call_next(request)
        
        
        try:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                access_token = authorization.split(" ")[1]
                payload = jwt.decode(access_token, env.secret_key, algorithms=[ALGORITHM])
                request.state.user = payload
                return await call_next(request)
            else:
                return JSONResponse(status_code=401, content={"error": "No se encontró el token de acceso"})
            
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"error": "Token de acceso expirado"})
        
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"error": "Token de acceso inválido"})
        
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})
        
