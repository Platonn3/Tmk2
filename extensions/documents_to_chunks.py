import pathlib
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.utils import filter_complex_metadata


class Chunk:
    def __init__(self, source_directory: str, persist_directory: str, embedding_model_name: str) -> None:
        self.SOURCE_DIRECTORY = source_directory
        self.PERSIST_DIRECTORY = persist_directory
        self.EMBEDDING_MODEL_NAME = embedding_model_name
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300
        )

    def load_documents(self) -> list[Document] | None:
        pdf_files = list(pathlib.Path(self.SOURCE_DIRECTORY).glob("*.pdf"))
        if not pdf_files:
            return None
        all_elements = []
        for file_path in pdf_files:
            loader = UnstructuredPDFLoader(str(file_path), mode="elements")
            elements = loader.load()
            all_elements.extend(elements)
        allowed_categories = ["Title", "NarrativeText"]

        return [
            el for el in all_elements
            if el.metadata.get('category') in allowed_categories
        ]

    def documents_to_chunks(self) -> list[Document] | None:
        documents = self.load_documents()
        if not documents:
            return None
        chunks = self.text_splitter.split_documents(documents)

        return filter_complex_metadata([chunk for chunk in chunks if len(chunk.page_content) > 50])
