import os
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from rag.ocr_loader import load_photo_ocr, load_any_document, IMAGE_EXTENSIONS
from rag.summary_generator import generate_document_summary
from rag.retriever import get_retriever
from rag.complexity import analyze_document_complexity
from rag.llm import generate_answer
from rag.clause_classifier import classify_clauses
from rag.risk_analyzer import analyze_risks
from rag.vectordb import create_document_vector_db
from rag.vector_store import load_vector_db
from rag.embeddings import get_embedding_model
from rag.document_classifier import classify_document
from rag.session import set_document_type
from rag.context_fusion import build_context

app = FastAPI(
    title="LexiClear+ Photo & OCR API"
)

UPLOADED_FILE = "uploaded_document"


@app.get("/")
def home():
    return {
        "message": "LexiClear+ Photo & OCR API Running"
    }


@app.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    allowed = IMAGE_EXTENSIONS.union({".pdf"})

    if ext not in allowed:
        return {
            "error": f"Invalid file type '{ext}'. Allowed types: {', '.join(sorted(allowed))}"
        }

    contents = await file.read()

    saved_filename = f"{UPLOADED_FILE}{ext}"
    with open(saved_filename, "wb") as f:
        f.write(contents)

    # Save tracking file with actual filename
    with open("uploaded_target.txt", "w") as f:
        f.write(saved_filename)

    return {
        "filename": file.filename,
        "saved_as": saved_filename,
        "message": "Photo uploaded and ready for OCR analysis"
    }


@app.post("/analyze")
def analyze_document():
    if os.path.exists("uploaded_target.txt"):
        with open("uploaded_target.txt", "r") as f:
            target_path = f.read().strip()
    else:
        target_path = "uploaded.pdf"

    if not os.path.exists(target_path):
        return {"error": f"No uploaded document found at '{target_path}'. Please upload a photo or PDF first."}

    documents = load_any_document(target_path)

    document_type = classify_document(documents)

    set_document_type(document_type)

    print("Photo Document Type:", document_type)

    # Build vector database
    create_document_vector_db(
        documents,
        document_type
    )

    summary = generate_document_summary(documents)

    complexity = analyze_document_complexity(documents)

    clauses = classify_clauses(documents)

    risks = analyze_risks(documents)

    return {
        "document_type": document_type,
        "summary": summary,
        "complexity": complexity,
        "clauses": clauses,
        "risks": risks
    }


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_question(request: QuestionRequest):
    context = build_context(request.question)

    answer = generate_answer(
        request.question,
        context
    )

    return {
        "answer": answer
    }
