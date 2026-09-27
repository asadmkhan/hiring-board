from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import applications, filters, providers

app = FastAPI(title="Hiring Board")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applications.router)
app.include_router(providers.router)
app.include_router(filters.router)


@app.get("/health")
def health():
    return {"status": "ok"}
