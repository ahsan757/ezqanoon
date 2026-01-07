from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.chat import router as chat_router
from app.db.database import engine
from fastapi.middleware.cors import CORSMiddleware
from app.db.models import Base
from app.config.settings import settings

print("🚀 Starting EzQanoon Statute Bot...")
print("📦 Loading FastAPI application...")

app = FastAPI(title="EzQanoon Statute Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables (for simple setups; for production, prefer migrations)
Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/config")
async def get_config():
    return {"apiUrl": settings.API_URL}

app.include_router(chat_router)

print("✅ FastAPI app initialized successfully!")
print("🌐 API available at /api/ask")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8007, reload=True)
