import os
import re
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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
from rag.language import (
    resolve_language,
    translate_document,
    translate_question_for_retrieval,
    translate_answer,
)
from rag.obligation_extractor import extract_obligations
from rag.rights_extractor import extract_rights
from fastapi.responses import FileResponse
import uuid
from rag.tts import generate_speech

app = FastAPI(
    title="LexiClear+ API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".pdf"}.union(IMAGE_EXTENSIONS)

@app.get("/")
def home():
    return {
        "message": "LexiClear+ API Running"
    }

@app.get("/document")
def get_document():
    """Serve the last uploaded document so PDF.js can render it in the browser."""
    if os.path.exists("uploaded_target.txt"):
        with open("uploaded_target.txt", "r") as f:
            target_path = f.read().strip()
    elif os.path.exists("uploaded.pdf"):
        target_path = "uploaded.pdf"
    else:
        raise HTTPException(status_code=404, detail="No document uploaded yet.")

    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"File not found: {target_path}")

    media_type = "application/pdf"
    ext = os.path.splitext(target_path)[1].lower()
    if ext in {".jpg", ".jpeg"}:
        media_type = "image/jpeg"
    elif ext == ".png":
        media_type = "image/png"

    return FileResponse(target_path, media_type=media_type)

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

    obligations = extract_obligations(documents)

    rights = extract_rights(documents)

    return {
    "document_type": document_type,
    "summary": summary,
    "complexity": complexity,
    "clauses": clauses,
    "risks": risks,
    "obligations": obligations,
    "rights": rights
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

    # Translate non-English question into English for retrieval
    search_question = translate_question_for_retrieval(
        request.question,
        language
    )

    # Retrieve document + legal context
    context = build_context(search_question)

    # Generate ONE authoritative answer in English
    english_answer = generate_answer(
    search_question,
    context,
)

    # Translate only if needed
    final_answer = translate_answer(
        english_answer,
        language
    )

    return {
        "answer": final_answer,
        "language": language,
    }


class TranslationRequest(BaseModel):
    language: str

class TranslateTextRequest(BaseModel):
    text: str
    target_language: str

@app.post("/translate")
def translate_text(request: TranslateTextRequest):
    try:
        lang = resolve_language(request.target_language)
        translated = translate_answer(request.text, lang)
        return {
            "translated_text": translated,
            "language": lang
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {error}"
        ) from error

class SpeechRequest(BaseModel):
    text: str
    language: str


def clean_text_for_tts(text: str) -> str:
    """Clean markdown and special symbols so TTS models generate clean audio."""
    if not text:
        return ""
    cleaned = re.sub(r'[*#_`~|\-]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

@app.post("/speak")
def speak(request: SpeechRequest):

    # Validate and normalize language
    try:
        language = resolve_language(request.language)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error

    # Validate text
    raw_text = clean_text_for_tts(request.text)
    if not raw_text:
        raise HTTPException(
            status_code=422,
            detail="Text cannot be empty."
        )

    try:

        output_path = generate_speech(
            text=raw_text,
            language=language,
            output_path="answer.wav",
        )

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="lexiclear_answer.wav",
        )

    except Exception as error:

        print("\n========== TTS ERROR ==========")
        print(error)
        print("===============================\n")

        raise HTTPException(
            status_code=500,
            detail=f"Speech generation failed: {error}"
        ) from error