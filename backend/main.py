from fastapi import FastAPI

from routers.search import router as search_router
from routers.listings import router as listings_router

def include_routers(app, routers):
    for router in routers:
        app.include_router(router)

ROUTERS = [search_router, listings_router]
app = FastAPI(title="Gundam Listings API")
include_routers(app, ROUTERS)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.get("/api/hello", tags=["health"])
def hello():
    """Retained temporarily because the current Home page calls this route."""
    return {"message": "hello from FastAPI"}
