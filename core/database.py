# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.transcript import Transcript
from models.meeting import Meeting
from models.user import User

from core.config import settings

async def init_db():
    # Create a Motor client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Connect to the database
    database = client[settings.DB_NAME]
    # Initialize Beanie with the database and models
    await init_beanie(database, document_models=[Transcript, Meeting, User])
