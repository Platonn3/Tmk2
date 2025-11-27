import pathlib
import re
from collections import defaultdict

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.utils import filter_complex_metadata

import docling


def normalize_formulas(text: str) -> str:
    broken_pattern = r"Fe\s*O\s*CO\s*53131\s*41\s*00\s*2\s*4"
    fixed_formula = "Fe2O3 + 3CO → 2Fe + 3CO2"
    text = re.sub(broken_pattern, fixed_formula, text)

    return text


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
        all_elements: list[Document] = []
        for file_path in pdf_files:
            loader = UnstructuredPDFLoader(
                str(file_path),
                mode="elements",
            )
            elements: list[Document] = loader.load()


            for el in elements:
                el.page_content = normalize_formulas(el.page_content)

            all_elements.extend(elements)

        return all_elements

    def documents_to_chunks(self) -> list[Document] | None:
        documents = self.load_documents()
        if not documents:
            return None

        merged_documents: list[Document] = []
        skip_next = False
        for i, doc in enumerate(documents):
            if skip_next:
                skip_next = False
                continue

            category = doc.metadata.get("category")
            if category == "Title" and i + 1 < len(documents):
                next_doc = documents[i + 1]
                combined_text = f"{doc.page_content.strip()}\n\n{next_doc.page_content.strip()}"

                new_metadata = dict(next_doc.metadata)
                new_metadata["title"] = doc.page_content.strip()

                merged_documents.append(
                    Document(page_content=combined_text, metadata=new_metadata)
                )
                skip_next = True
            else:
                merged_documents.append(doc)

        chunks = self.text_splitter.split_documents(merged_documents)

        chunks_by_source: dict[str, list[Document]] = defaultdict(list)
        for chunk in chunks:
            source = chunk.metadata.get("source", "unknown")
            chunks_by_source[source].append(chunk)

        numbered_chunks: list[Document] = []
        for source, source_chunks in chunks_by_source.items():
            for idx, chunk in enumerate(source_chunks):
                chunk.metadata["chunk_index"] = idx
                chunk.metadata["source"] = source
                numbered_chunks.append(chunk)


        filtered = [chunk for chunk in numbered_chunks if len(chunk.page_content) > 50]

        return filter_complex_metadata(filtered)
