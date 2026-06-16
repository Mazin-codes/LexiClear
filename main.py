from rag.loader import load_pdf
from rag.chunker import split_documents
from rag.embeddings import get_embedding_model
from rag.vectordb import create_vector_db
from rag.retriever import get_retriever
from rag.llm import generate_answer

print("\nLoading PDF...")

documents = load_pdf("sample.pdf")

print(f"Pages Loaded: {len(documents)}")

print("\nChunking Document...")

chunks = split_documents(documents)

print(f"Chunks Created: {len(chunks)}")

print("\nCreating Embeddings...")

embeddings = get_embedding_model()

print("\nCreating Vector Database...")

db = create_vector_db(
    chunks,
    embeddings
)

retriever = get_retriever(db)

print("\nLexiClear Ready!")

while True:

    question = input("\nAsk Question (type exit to quit): ")

    if question.lower() == "exit":
        break

    results = retriever.invoke(question)

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    answer = generate_answer(
        context,
        question
    )

    print("\n" + "="*60)
    print(answer)
    print("="*60)