from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from conf.settings import MEDIA_DIR
from users.routes import router as users_router
from vehicles.routes import router as vehicles_router
from works.routes import router as works_router

app = FastAPI()

app.include_router(users_router, prefix="/api/users")
app.include_router(vehicles_router, prefix="/api/vehicles")
app.include_router(works_router, prefix="/api/works")

MEDIA_DIR.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")