import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from models.user import User
from misc.utility import get_current_user
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import faiss
from services.fais import process_and_index_pdf

# Define constants and folders
DOCUMENTS_FOLDER = "documents"

# Ensure the documents folder exists
os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)

# FastAPI Router setup
router = APIRouter()

@router.post("/upload/", response_model=str)
async def document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    meeting_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    
    # Check if the file is a PDF
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Define the path to save the file
    file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = os.path.join(DOCUMENTS_FOLDER, file_name)

    # Save the file to the local storage
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Schedule the processing task in the background
    background_tasks.add_task(process_and_index_pdf, file_path, meeting_id)

    return f"File {file.filename} saved successfully as {file_path}. Processing will continue in the background."
