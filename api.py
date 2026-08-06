from fastapi import FastAPI, HTTPException, UploadFile
from rag.loader import load_pdf
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
from rag.language import (
    resolve_language,
    translate_document,
    translate_question_for_retrieval,
)

app = FastAPI(
    title="LexiClear+ API"
)

@app.get("/")
def home():
    return {
        "message": "LexiClear+ API Running"
    }

@app.post("/upload")
async def upload_pdf(file: UploadFile):

    if not file.filename.lower().endswith(".pdf"):
        return {
            "error": "Only PDF files are allowed"
        }

    contents = await file.read()

    with open("uploaded.pdf", "wb") as f:
        f.write(contents)

    return {
        "filename": file.filename
    }

@app.post("/analyze")
def analyze_document():

    documents = load_pdf("uploaded.pdf")

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
    language: str | None = None

@app.post("/ask")
def ask_question(request: QuestionRequest):

    try:
        language = resolve_language(request.language, request.question)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    search_question = translate_question_for_retrieval(request.question, language)

    # Build combined context from:
    # 1. Uploaded document
    # 2. Legal corpus
    context = build_context(search_question)

    answer = generate_answer(
        request.question,
        context,
        language,
    )

    return {
        "answer": answer,
        "language": language,
    }


class TranslationRequest(BaseModel):

    language: str


@app.post("/translate")
def translate_uploaded_document(request: TranslationRequest):
    """Translate every page of the uploaded legal document without changing references."""
    try:
        language = resolve_language(request.language)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    documents = load_pdf("uploaded.pdf")

    return {
        "language": language,
        "pages": translate_document(documents, language),
    }
