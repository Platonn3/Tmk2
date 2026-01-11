from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

import os

class DbConnection:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        current_dir = os.path.dirname(os.path.abspath(__file__))

        db_path = os.path.join(current_dir, "vector_store")

        print(f"Подключение к БД по пути: {db_path}")

        self.db = Chroma(
            embedding_function=self.embeddings,
            persist_directory=db_path
        )

    def search(self, query: str, k: int = 5, neighbor_window: int = 1) -> list[Document]:
        retriever = self.db.as_retriever(
            search_type="mmr",
            search_kwargs={'k': k, 'fetch_k': 20}
        )
        base_docs: list[Document] = retriever.invoke(query)

        if not base_docs or all("chunk_index" not in d.metadata for d in base_docs):
            return base_docs

        neighbors_by_source: dict[str, set[int]] = {}
        for doc in base_docs:
            source = doc.metadata.get("source")
            idx = doc.metadata.get("chunk_index")
            if source is None or idx is None:
                continue
            idx = int(idx)
            if source not in neighbors_by_source:
                neighbors_by_source[source] = set()
            for delta in range(-neighbor_window, neighbor_window + 1):
                neighbors_by_source[source].add(idx + delta)

        all_docs: dict[tuple[str | None, int | None], Document] = {}
        for d in base_docs:
            key = (d.metadata.get("source"), d.metadata.get("chunk_index"))
            all_docs[key] = d

        for source, indices in neighbors_by_source.items():

            where = {
                "$and": [
                    {"source": source},
                    {"chunk_index": {"$in": list(indices)}},
                ]
            }
            results = self.db.get(where=where)

            metadatas = results.get("metadatas", []) or []
            documents = results.get("documents", []) or []

            for meta, text in zip(metadatas, documents):
                key = (meta.get("source"), meta.get("chunk_index"))
                if key not in all_docs:
                    all_docs[key] = Document(page_content=text, metadata=meta)

        def sort_key(doc: Document):
            meta = doc.metadata or {}
            return (
                str(meta.get("source", "")),
                int(meta.get("page_number", 0) or 0),
                int(meta.get("chunk_index", 0) or 0),
            )

        sorted_docs = sorted(all_docs.values(), key=sort_key)
        return sorted_docs


if __name__ == "__main__":
    conn = DbConnection()
    res = conn.search("Theoretical Analyses of Hydrogen-rich Reduction in Blast Furnace", neighbor_window=2)
    print(res)
