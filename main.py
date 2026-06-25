from rag.loader import load_pdf
from rag.chunker import split_documents
from rag.embeddings import get_embedding_model
from rag.vectordb import create_vector_db
from rag.retriever import get_retriever
from rag.llm import generate_answer
from rag.explainability import explain_retrieval
from rag.risk_analyzer import analyze_risks

print("\nLoading PDF...")

documents = load_pdf("sample.pdf")
print(f"Pages Loaded: {len(documents)}")

print("\nChunking Document...")
chunks = split_documents(documents)
print(f"Chunks Created: {len(chunks)}")

print("\nCreating Embeddings...")
embeddings = get_embedding_model()

print("\nCreating Vector Database...")
db = create_vector_db(chunks, embeddings)

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
