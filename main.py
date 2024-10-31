from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.config import settings
from core.database import init_db

from api.v1 import audio, meeting, user, file

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:3001","http://192.168.1.6:3001","https://9f8e-58-65-217-21.ngrok-free.app","http://9f8e-58-65-217-21.ngrok-free.app", "https://brainstormsession.netlify.app/", "http://brainstormsession.netlify.app/"],  # Add your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include audio routes under v1 API version
app.include_router(audio.router, prefix="/ws")
app.include_router(meeting.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(file.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )


