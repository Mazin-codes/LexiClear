import os
import json
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader

from rag.chunker import split_documents
from rag.embeddings import get_embedding_model
from rag.vector_store import create_vector_db

LEGAL_CORPUS_PATH = "legal_corpus"
METADATA_PATH = os.path.join(LEGAL_CORPUS_PATH, "metadata.json")
PERSIST_DIRECTORY = "./chroma_legal"


def load_legal_documents():
    """
    Load all legal PDFs and attach metadata.
    """

    with open(METADATA_PATH, "r") as f:
        metadata_map = json.load(f)

    documents = []

    for pdf_path in Path(LEGAL_CORPUS_PATH).rglob("*.pdf"):

        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()

        filename = pdf_path.name
        file_metadata = metadata_map.get(filename, {})

        for doc in docs:
            doc.metadata.update(file_metadata)
            doc.metadata["file_name"] = filename

        documents.extend(docs)

    return documents


def create_legal_vector_db():
    """
    Create the legal knowledge vector database.
    """

    print("Loading legal documents...")

    documents = load_legal_documents()

    print(f"Loaded {len(documents)} pages.")

    chunks = split_documents(documents)
    embeddings = get_embedding_model()

    db = create_vector_db(
        chunks=chunks,
        embeddings=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    print("Legal vector database created.")

    return db