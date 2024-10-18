from fastapi import FastAPI
import uvicorn
from core.config import settings
from api.v1 import audio

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.VERSION
)

# Include audio routes under v1 API version
app.include_router(audio.router, prefix="/v1")

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
