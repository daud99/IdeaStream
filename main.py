from datetime import datetime

from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from core.config import settings
from core.database import init_db

from api.v1 import audio

from models.transcript import Transcript

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # Code below runs when the application shuts down

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.VERSION,
    lifespan=lifespan
)

# Include audio routes under v1 API version
app.include_router(audio.router, prefix="/v1")

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}

# Endpoint to insert a dummy document into the transcripts collection
@app.get("/insert-dummy")
async def insert_dummy():
    # Create a dummy transcript document
    dummy_transcript = Transcript(
        meeting_id="dummy_meeting_001",
        text="This is a dummy transcript for testing purposes.",
        timestamp=datetime.utcnow()
    )
    # Insert the document into the database
    await dummy_transcript.insert()
    # Return the inserted document
    return dummy_transcript

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )


