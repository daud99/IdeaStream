from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Form
from fastapi.responses import JSONResponse
from models.user import User
from misc.utility import hash_password, verify_password, create_access_token
from core.config import settings
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError

class OAuth2EmailRequestForm(BaseModel):
    email: EmailStr
    password: str

router = APIRouter()

@router.post("/signup/", status_code=status.HTTP_201_CREATED, response_model=str)
async def signup(user: User):
    # Check if the user already exists
    existing_user = await User.find_one(User.email == user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create a new user document
    newUser = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed_password
    )

    # Save the user to the database
    await newUser.insert()

    return JSONResponse(content={"message": "User registered successfully!"}, status_code=status.HTTP_201_CREATED)


@router.post("/login/", response_model=dict)
async def login(email: str = Form(...), password: str = Form(...)):
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/token/verify", response_model=dict)
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        return {"message": "Token is valid", "user_email": user_email}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# HELPERS
async def authenticate_user(email: str, password: str):
    user = await User.find_one(User.email == email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user