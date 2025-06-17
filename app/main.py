from fastapi import FastAPI
from .config import lifespan
from .middleware import setup_middleware
from fastapi.staticfiles import StaticFiles
from app.routes import routers
#from .routes import index

app = FastAPI(lifespan=lifespan)

setup_middleware(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
for router in routers:
    app.include_router(router)
#app.include_router(index.router)