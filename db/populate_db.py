import os
import hashlib
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

print("Loading Embedding Model...")
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)


def add_single_document_to_db(file_path: str, persist_directory: str = "vector_store") -> None:
    print(f"Processing file: {file_path}")

    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return

    if not docs:
        print("Document is empty.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)

    print(f"Generated {len(chunks)} chunks.")

    filename = os.path.basename(file_path)
    ids = [f"{filename}_{i}" for i in range(len(chunks))]

    for chunk in chunks:
        chunk.metadata["source_filename"] = filename

    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_function
    )

    try:
        db.add_documents(documents=chunks, ids=ids)
        print(f"Successfully added {len(chunks)} chunks to DB from {filename}")
        os.remove("../data_sources/scraped_article.pdf")
    except Exception as e:
        print(f"Error writing to Vector DB: {e}")