from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.issues import router as issues_router
from app.api.auth import router as auth_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A RESTful API for managing issues",
)

# enable cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(issues_router)
app.include_router(auth_router)



@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": f"{settings.APP_NAME} is running", "version": settings.APP_VERSION}
