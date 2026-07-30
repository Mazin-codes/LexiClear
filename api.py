from fastapi import FastAPI, UploadFile
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

@app.post("/ask")
def ask_question(request: QuestionRequest):

    embeddings = get_embedding_model()

    vector_db = load_vector_db(
        embeddings=embeddings,
        persist_directory="./chroma_docs"
    )

    retriever = get_retriever(vector_db)

    context = build_context(request.question)

    answer = generate_answer(
        request.question,
        context
    )

    # DEBUG
    for i, doc in enumerate(docs):
        print(f"\n===== CHUNK {i} =====")
        print(doc.page_content[:500])

    answer = generate_answer(
        request.question,
        docs
    )

    return {
        "answer": answer
    }