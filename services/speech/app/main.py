from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="OpenSign Darija Speech")
app.include_router(router)
