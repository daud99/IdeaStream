import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from models.meeting import Meeting
from models.user import User
from misc.utility import get_current_user
from fastapi import APIRouter, Depends

# Define the directory where documents will be saved
DOCUMENTS_FOLDER = "documents"

# Ensure the folder exists
os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)

router = APIRouter()

# Endpoint to insert a new meeting
@router.post("/upload/", response_model=str)
async def document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
     # Check if the file is a PDF
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    # Define the file path to save the document
    file_path = os.path.join(DOCUMENTS_FOLDER, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")

    # Save the file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return f"File {file.filename} saved successfully as {file_path}"
