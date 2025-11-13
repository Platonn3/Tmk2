import shutil

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from extensions.documents_to_chunks import Chunk
import os


def load_documents_to_db() -> None:
    if os.path.exists("vector_store"):
        shutil.rmtree("vector_store")

    chunks = Chunk(
        "/Users/platonkurbatov/Desktop/TMK2/data_sources",
        "vector_store",
        "sentence-transformers/all-MiniLM-L6-v2"
    ).documents_to_chunks()

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

    _ = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="vector_store"
    )

load_documents_to_db()
