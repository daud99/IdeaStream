import json
from openai import OpenAI
client = OpenAI()
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import faiss


# Load SentenceTransformer model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Define the path to the PDF file
pdf_file_path = "documents/35.pdf"

# Load the PDF document
loader = PyMuPDFLoader(pdf_file_path)
documents = loader.load()

# Use RecursiveCharacterTextSplitter with custom separators
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", " "]
)

# Split text into logical chunks
chunks = text_splitter.split_documents(documents)

# Perform embedding on each chunk
embeddings = [model.encode(chunk.page_content) for chunk in chunks]

# Initialize FAISS index
dimension = len(embeddings[0])
index = faiss.IndexFlatL2(dimension)  # Using L2 distance for similarity

# Convert embeddings list to a numpy array and add to the FAISS index
embedding_matrix = np.array(embeddings).astype('float32')
index.add(embedding_matrix)

# Save the index (optional)
faiss.write_index(index, "vector_index.faiss")

print(f"Stored {len(embeddings)} embeddings in the vector database.")