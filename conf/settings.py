from decouple import config

class Env:
    database_url = config('DATABASE_URL')
    secret_key = config('SECRET_KEY')

env = Env()