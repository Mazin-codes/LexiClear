import os
from fastapi import FastAPI, UploadFile
from rag.loader import load_pdf
from rag.ocr_loader import load_any_document, IMAGE_EXTENSIONS
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
from pydantic import BaseModel
from rag.context_fusion import build_context

app = FastAPI(
    title="LexiClear+ API"
)

ALLOWED_EXTENSIONS = {".pdf"}.union(IMAGE_EXTENSIONS)

@app.get("/")
def home():
    return {
        "message": "LexiClear+ API Running"
    }

@app.post("/upload")
async def upload_pdf(file: UploadFile):

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {
            "error": f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }

    contents = await file.read()

    saved_filename = f"uploaded{ext}"
    with open(saved_filename, "wb") as f:
        f.write(contents)

    # Save target filename to track uploaded document
    with open("uploaded_target.txt", "w") as f:
        f.write(saved_filename)

    return {
        "filename": file.filename
    }

@app.post("/analyze")
def analyze_document():

    if os.path.exists("uploaded_target.txt"):
        with open("uploaded_target.txt", "r") as f:
            target_path = f.read().strip()
    elif os.path.exists("uploaded.pdf"):
        target_path = "uploaded.pdf"
    else:
        return {"error": "No document uploaded yet. Please upload a PDF or image first."}

    documents = load_any_document(target_path)

    document_type = classify_document(documents)

    set_document_type(document_type)

    print("Document Type:", document_type)

    # Build vector database once
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

    # Build combined context from:
    # 1. Uploaded document
    # 2. Legal corpus
    context = build_context(request.question)

    answer = generate_answer(
        request.question,
        context
    )

    return {
        "answer": answer
    }