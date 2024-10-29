import os
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

INDEX_DIRECTORY = "indices"
os.makedirs(INDEX_DIRECTORY, exist_ok=True)

# Load SentenceTransformer model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Use global variables for chunks and index
chunks = []
index = None  # Initialize index as a global variable

def process_and_index_pdf(file_path: str, meeting_id: str):
    global chunks, index  # Indicate that we are using the global variables
    
    # Load and split the PDF document into chunks
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " "]
    )
    
    # Split documents into chunks and retain original text
    document_chunks = text_splitter.split_documents(documents)

    # Store chunks globally
    chunks.extend([chunk.page_content for chunk in document_chunks])

    # Generate embeddings for each chunk
    embeddings = [model.encode(chunk.page_content).astype('float32') for chunk in document_chunks]
    embedding_matrix = np.array(embeddings)

    index_path = os.path.join(INDEX_DIRECTORY, f"{meeting_id}.faiss")
    # Load or create FAISS index
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        dimension = embedding_matrix.shape[1]
        index = faiss.IndexFlatL2(dimension)

    # Add embeddings to the FAISS index
    index.add(embedding_matrix)
    
    # Save the updated index
    faiss.write_index(index, index_path)
    print(f"Processed and indexed document: {file_path}")

def query_faiss_index(transcription, k=5):
    global chunks, index  # Indicate that we are using the global variables
    
    if index is None:
        raise Exception("FAISS index has not been initialized. Please process and index a PDF first.")
    
    # Step 1: Embed the transcription
    transcription_embedding = model.encode(transcription).astype('float32')
    
    # Step 2: Search in the FAISS index
    distances, indices = index.search(np.array([transcription_embedding]), k)  # k = number of nearest neighbors you want
    
    print('indices:', indices)
    # Step 3: Retrieve relevant chunks based on indices
    relevant_chunks = [chunks[i] for i in indices[0]]  # Assuming chunks holds the original text or context
    return relevant_chunks

def delete_faiss_index(index_path="indices/vector_index.faiss"):
    """Deletes the FAISS index file if it exists."""
    try:
        if os.path.exists(index_path):
            os.remove(index_path)
            print(f"Successfully deleted the FAISS index at {index_path}.")
        else:
            print(f"No FAISS index found at {index_path}.")
    except Exception as e:
        print(f"Error while deleting FAISS index: {str(e)}")
