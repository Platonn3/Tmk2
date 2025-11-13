from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class DbConnection:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        self.db = Chroma(
            embedding_function=self.embeddings,
            persist_directory="vector_store"
        )

    def search(self, query: str, k: int = 5) -> list[Document]:
        retriever = self.db.as_retriever(
            search_type="mmr",
            search_kwargs={'k': k, 'fetch_k': 20}
        )
        return retriever.invoke(query)


if __name__ == "__main__":
    conn = DbConnection()
    res = conn.search("reduction of CO")
    for doc in res:
        print(doc)
