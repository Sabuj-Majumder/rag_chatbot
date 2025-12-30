import os
import shutil
import base64
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
import pytesseract
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from processor import DocumentProcessor

# Load .env
load_dotenv()

# --- CONFIG ---
UPLOAD_DIR = "storage/uploads"
DB_DIR = "storage/chroma_db"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

app = FastAPI(title="Groq RAG API with Bonus Features")

# --- INITIALIZATION ---
processor = DocumentProcessor()

# 1. Embeddings (Local & Free)
print("Loading embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Vector Store (Multi-document support is native here)
vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

# 3. LLM (Groq)
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise ValueError("GROQ_API_KEY not found in .env")

llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile", 
    api_key=groq_key
)

# --- HELPER: File Type Icons ---
def get_file_icon(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    icons = {
        ".pdf": "📕",
        ".docx": "📝",
        ".txt": "📄",
        ".csv": "📊",
        ".db": "🗄️",
        ".sqlite": "🗄️",
        ".png": "🖼️",
        ".jpg": "🖼️",
        ".jpeg": "🖼️"
    }
    return icons.get(ext, "📁")

# --- MODELS ---
class QueryRequest(BaseModel):
    question: str
    image_base64: Optional[str] = None # For "What is in this image?"

class SourceInfo(BaseModel):
    filename: str
    file_type_icon: str
    page_content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]

# --- ENDPOINTS ---

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    BONUS: Returns file_id and handles all formats.
    """
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process & Ingest
    chunks = processor.process_file(file_path, file.content_type, file.filename)
    if not chunks:
        raise HTTPException(status_code=400, detail="Unsupported file or no text found.")

    vector_db.add_documents(chunks)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "message": f"Successfully indexed {len(chunks)} chunks.",
        "icon": get_file_icon(file.filename)
    }

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    BONUS: Handles Image Inputs (Multimodal-like via OCR) + Multi-doc Querying
    """
    full_query = request.question

    # 1. OCR Handling (Simulating Vision)
    if request.image_base64:
        try:
            image_bytes = base64.b64decode(request.image_base64)
            img = Image.open(BytesIO(image_bytes))
            # Extract text from the uploaded query image
            img_text = pytesseract.image_to_string(img)
            full_query += f"\n\n[CONTEXT FROM USER IMAGE]: {img_text}"
        except Exception as e:
            print(f"OCR Error: {e}")

    # 2. Vector Search (Retrieves from ALL uploaded docs)
    retriever = vector_db.as_retriever(search_kwargs={"k": 4})
    docs = retriever.invoke(full_query)

    context_text = "\n\n".join([d.page_content for d in docs])

    # 3. LLM Generation
    prompt_template = """
    You are a smart assistant. Use the context below to answer the user's question.
    If the context contains tables, format them nicely.
    
    Context:
    {context}
    
    Question: 
    {question}
    
    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = prompt | llm
    response = chain.invoke({"context": context_text, "question": full_query})

    # 4. Construct Response with Icons/Metadata
    sources_data = []
    seen_sources = set()
    
    for doc in docs:
        src = doc.metadata.get("source", "unknown")
        if src not in seen_sources:
            seen_sources.add(src)
            sources_data.append(SourceInfo(
                filename=src,
                file_type_icon=get_file_icon(src),
                page_content=doc.page_content[:200] + "..."
            ))

    return {
        "answer": response.content,
        "sources": sources_data
    }