import sys
import os

from rag.ocr_loader import load_any_document
from rag.chunker import split_documents
from rag.embeddings import get_embedding_model
from rag.vector_store import create_vector_db
from rag.retriever import get_retriever
from rag.llm import generate_answer
from rag.explainability import explain_retrieval
from rag.risk_analyzer import analyze_risks
from rag.complexity import analyze_document_complexity
from rag.clause_classifier import classify_clauses
from rag.summary_generator import generate_document_summary


def main():
    if len(sys.argv) > 1:
        photo_path = sys.argv[1]
    else:
        photo_path = input("Enter path to photo/image file (e.g. contract_photo.jpg): ").strip()

    if not photo_path or not os.path.exists(photo_path):
        print(f"Error: File '{photo_path}' not found.")
        return

    print(f"\nProcessing photo with OCR: {photo_path}...")

    documents = load_any_document(photo_path)
    print(f"Document Pages / Images Loaded: {len(documents)}")

    print("\nGenerating Executive Summary...")
    summary = generate_document_summary(documents)

    print("\n" + "=" * 60)
    print("LexiClear+ Photo OCR Executive Summary")
    print("=" * 60)
    print(summary)

    print("\nChunking Document...")
    chunks = split_documents(documents)
    print(f"Chunks Created: {len(chunks)}")

    print("\nCreating Embeddings...")
    embeddings = get_embedding_model()

    print("\nCreating Vector Database...")
    db = create_vector_db(chunks, embeddings)

    retriever = get_retriever(db)

    print("\nLexiClear OCR Mode Ready!")

    while True:
        question = input("\nAsk Question (type exit to quit): ")

        if question.lower() == "exit":
            break

        results = retriever.invoke(question)

        # Context structure expected by llm.py generate_answer
        context = {
            "document_context": "\n\n".join([doc.page_content for doc in results]),
            "legal_context": "",
            "legal_chunks": []
        }

        answer = generate_answer(question, context)

        print("\n" + "=" * 60)
        print(answer)

        complexity = analyze_document_complexity(documents)

        print("\n" + "=" * 60)
        print("Document Complexity Report")
        print("=" * 60)
        print(f"Complexity Score : {complexity['score']}/100")
        print(f"Level            : {complexity['level']}")
        print(f"Words            : {complexity['words']}")
        print(f"Reading Time     : {complexity['reading_time']} min")
        print(f"Avg Sentence Len : {complexity['avg_sentence_length']}")
        print(f"Legal Terms      : {complexity['legal_terms']}")

        clauses = classify_clauses(documents)

        print("\n" + "=" * 60)
        print("Clause Classification Report")
        print("=" * 60)
        for category, items in clauses.items():
            if not items:
                continue
            print(f"\n{category}")
            print("-" * 30)
            for clause in items[:5]:
                print(f"• {clause[:150]}")

        print("\n" + "=" * 60)
        print("AI Legal Risk Assessment")
        print("=" * 60)
        risk_report = analyze_risks(results)
        print(risk_report)

        print("\nExplainability")
        print("-" * 30)
        explanations = explain_retrieval(results)
        for item in explanations:
            print(f"Page      : {item['page']}")
            print(f"Chunk ID  : {item['chunk']}")
            print(f"Preview   : {item['preview']}...")
            print("-" * 60)


if __name__ == "__main__":
    main()
