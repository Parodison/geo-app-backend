import redis
from decouple import config
from pathlib import Path
from celery import Celery

class Env:
    database_url = config('DATABASE_URL')
    secret_key = config('SECRET_KEY')
    base_url = config('BASE_URL')
    redis_host = config('REDIS_HOST')
    redis_port = int(config('REDIS_PORT'))
    google_maps_api_key = config('GOOGLE_MAPS_API_KEY')
    google_places_url = config('GOOGLE_PLACES_URL')
    google_maps_api_url = config('GOOGLE_MAPS_API_URL')

env = Env()

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_DIR = Path("media")

REDIS_INSTANCE = redis.Redis(host=env.redis_host, port=env.redis_port, db=0, decode_responses=True)

celery_app = Celery(
    "geo_app",
    broker=f"redis://{env.redis_host}:{env.redis_port}/0",
    backend=f"redis://{env.redis_host}:{env.redis_port}/0",
)

import works.tasks