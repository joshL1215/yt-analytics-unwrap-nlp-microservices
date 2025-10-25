from fastapi import FastAPI
from api.routes import routes
from fastapi.middleware.cors import CORSMiddleware

# TODO: make it pre load ML models

app = FastAPI()

app.include_router(routes.router, prefix="/api")
