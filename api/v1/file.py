import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from models.user import User
from misc.utility import get_current_user
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import faiss

# Define constants and folders
DOCUMENTS_FOLDER = "documents"
INDEX_PATH = "vector_index.faiss"

# Ensure the documents folder exists
os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)

# Load SentenceTransformer model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# FastAPI Router setup
router = APIRouter()

def process_and_index_pdf(file_path: str):
    # Load and split the PDF document into chunks
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " "]
    )
    chunks = text_splitter.split_documents(documents)

    # Generate embeddings for each chunk
    embeddings = [model.encode(chunk.page_content) for chunk in chunks]
    embedding_matrix = np.array(embeddings).astype('float32')

    # Load or create FAISS index
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
    else:
        dimension = embedding_matrix.shape[1]
        index = faiss.IndexFlatL2(dimension)

    # Add embeddings to the FAISS index
    index.add(embedding_matrix)
    
    # Save the updated index
    faiss.write_index(index, INDEX_PATH)
    print(f"Processed and indexed document: {file_path}")

@router.post("/upload/", response_model=str)
async def document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
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
    background_tasks.add_task(process_and_index_pdf, file_path)

    return f"File {file.filename} saved successfully as {file_path}. Processing will continue in the background."
