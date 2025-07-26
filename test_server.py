#!/usr/bin/env python3
"""
Simple test server for user preferences API
This bypasses Firebase dependency issues by only loading the users API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.users import router as users_router

app = FastAPI(title="Smart Recipe App - User Preferences API Test", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only the users router for testing
app.include_router(users_router, prefix="/api", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Smart Recipe App - User Preferences API Test Server"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "api": "user preferences"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)