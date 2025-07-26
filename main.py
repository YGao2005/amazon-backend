import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.ingredients import router as ingredients_router
from app.api.recipes import router as recipes_router
from app.api.users import router as users_router
from app.api.expiration import router as expiration_router

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
    )

    # Set up CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For development; restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(ingredients_router, prefix=f"{settings.API_PREFIX}/ingredients")
    application.include_router(recipes_router, prefix=f"{settings.API_PREFIX}/recipes")
    application.include_router(users_router, prefix=f"{settings.API_PREFIX}/users")
    application.include_router(expiration_router, prefix=f"{settings.API_PREFIX}/expiration")

    return application

app = create_application()

@app.get("/")
async def root():
    return {"message": "Welcome to Smart Recipe App API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)