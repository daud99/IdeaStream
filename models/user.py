# models.py
from beanie import Document
from datetime import datetime
from pydantic import EmailStr, Field

class User(Document):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    date_joined: datetime = Field(default_factory=datetime.now)

    class Settings:
        collection = "users"

    class Config:
        json_schema_extra = {
            "example": {
                "email": "johndoe@example.com",
                "first_name": "John",
                "last_name":  "Doe",
                "password": "hashed_password_here",
                "date_joined": "2024-10-21T15:30:00Z",
            }
        }
