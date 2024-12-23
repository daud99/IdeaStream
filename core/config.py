import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "IdeaStream"
    VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "192.168.1.6")
    PORT: int = int(os.getenv("PORT", 8000))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    MONGODB_URL: str = os.getenv("MONGODB_URL", f"mongodb+srv://umarmukhtar4455:{os.getenv('MONGODB_PASSWORD')}@cluster0.e2q1w.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DB_NAME: str = os.getenv("DB_NAME", "test")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
settings = Settings()
