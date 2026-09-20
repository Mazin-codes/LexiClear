from rag.loader import load_pdf
from rag.chunker import split_documents
from rag.embeddings import get_embedding_model
from rag.vectordb import create_vector_db, PERSIST_DIRECTORY
from rag.retriever import get_retriever
from rag.llm import generate_answer
from rag.explainability import explain_retrieval
from rag.risk_analyzer import analyze_risks
from rag.complexity import analyze_document_complexity
from rag.clause_classifier import classify_clauses
from rag.summary_generator import generate_document_summary

print("\nLoading PDF...")

documents = load_pdf("sample.pdf")
print(f"Pages Loaded: {len(documents)}")

print("\nGenerating Executive Summary...")
summary = generate_document_summary(documents)

print("\n" + "=" * 60)
print("LexiClear+ Executive Summary")
print("=" * 60)

print(summary)

print("\nChunking Document...")
chunks = split_documents(documents)
print(f"Chunks Created: {len(chunks)}")

print("\nCreating Embeddings...")
embeddings = get_embedding_model()

print("\nCreating Vector Database...")
db = create_vector_db(chunks, embeddings, PERSIST_DIRECTORY)

retriever = get_retriever(db)

print("\nLexiClear Ready!")

while True:

    question = input("\nAsk Question (type exit to quit): ")

    if question.lower() == "exit":
        break

    # Retrieve relevant documents
    results = retriever.invoke(question)

    # Generate answer using retrieved documents
    answer = generate_answer(question, results)

    # Display answer
    print("\n" + "=" * 60)
    print(answer)

    complexity = analyze_document_complexity(documents)

    print("\n" + "="*60)
    print("Document Complexity Report")
    print("="*60)

    print(
        f"Complexity Score : "
        f"{complexity['score']}/100"
    )

    print(
        f"Level            : "
        f"{complexity['level']}"
    )

    print(
        f"Words            : "
        f"{complexity['words']}"
    )

    print(
        f"Reading Time     : "
        f"{complexity['reading_time']} min"
    )

    print(
        f"Avg Sentence Len : "
        f"{complexity['avg_sentence_length']}"
    )

    print(
        f"Legal Terms      : "
        f"{complexity['legal_terms']}"
    )

    clauses = classify_clauses(documents)

    print("\n" + "="*60)
    print("Clause Classification Report")
    print("="*60)

    for category, items in clauses.items():

        if not items:
            continue

        print(f"\n{category}")
        print("-"*30)

        for clause in items[:5]:

            print(f"• {clause[:150]}")

    print("\n" + "="*60)
    print("AI Legal Risk Assessment")
    print("="*60)

    risk_report = analyze_risks(results)

    print(risk_report)

    # Explainability
    print("\nExplainability")
    print("-" * 30)

    explanations = explain_retrieval(results)

    print("\nExplainability")

    print("=" * 60)

    for item in explanations:

        print(f"Page      : {item['page']}")

        print(f"Chunk ID  : {item['chunk']}")

        print(f"Preview   : {item['preview']}...")

        print("-" * 60)
