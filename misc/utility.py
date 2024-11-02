from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from passlib.context import CryptContext
from core.config import settings
from jose import jwt, JWTError
from models.user import User
from fastapi.security import OAuth2PasswordBearer
from typing import List  # Import List

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception
    

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = await User.find_one(User.email == email)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return user


async def get_participants(self) -> List[User]:
    """Fetch all participants with their full user details."""
    participants = []
    for participant_id in self.participants:
        # Retrieve each user by their ID instead of using fetch()
        user = await User.get(participant_id)
        if user:
            participants.append({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            })
    return participants
