import shutil

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from extensions.documents_to_chunks import Chunk
import os


def load_documents_to_db() -> None:
    if os.path.exists("vector_store"):
        print("Removing existing vector_store...")
        shutil.rmtree("vector_store")

    print("Loading and chunking documents...")
    chunks = Chunk(
        "/Users/platonkurbatov/Desktop/TMK2/data_sources",
        "vector_store",
        "sentence-transformers/all-MiniLM-L6-v2"
    ).documents_to_chunks()

    if not chunks:
        print("No chunks were created. Exiting.")
        return

    print(f"Loaded {len(chunks)} chunks. Initializing embeddings...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

    print("Building Chroma vector store (this may take some time)...")
    _ = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="vector_store"
    )

    print("Vector store has been successfully created and persisted to 'vector_store'.")

load_documents_to_db()
