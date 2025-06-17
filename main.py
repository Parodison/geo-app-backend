import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from conf.middleware import LoginMiddleware
from geolocation.geo_manager import GeolocationManager
from conf.settings import MEDIA_DIR
from users.routes import router as users_router
from vehicles.routes import router as vehicles_router
from works.routes import router as works_router
from geolocation.routes import router as locations_router
from places.routes import router as places_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    geo_manager = GeolocationManager()
    location_listener = asyncio.create_task(geo_manager.locations_listener())
    
    yield
    location_listener.cancel()
    
    

app = FastAPI(lifespan=lifespan)
#uvicorn main:app --host 0.0.0.0 --port 8000 --reload
#celery -A conf.settings.celery_app worker --loglevel=info -P threads
#Iniciar ubuntu para que inicie redis porque de lo contrario no inicia la app


app.include_router(users_router, prefix="/api/users")
app.include_router(vehicles_router, prefix="/api/vehicles")
app.include_router(works_router, prefix="/api/works")
app.include_router(locations_router, prefix="/api/locations")
app.include_router(places_router, prefix="/api/places")

MEDIA_DIR.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.add_middleware(LoginMiddleware)