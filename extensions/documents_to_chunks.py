import pathlib
import re
from collections import defaultdict

from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.chunking import HybridChunker


def normalize_formulas(text: str) -> str:
    if not text:
        return ""
    broken_pattern = r"Fe\s*O\s*CO\s*53131\s*41\s*00\s*2\s*4"
    fixed_formula = "Fe2O3 + 3CO → 2Fe + 3CO2"
    text = re.sub(broken_pattern, fixed_formula, text)
    return text


class Chunk:
    def __init__(self, source_directory: str, persist_directory: str, embedding_model_name: str) -> None:
        self.SOURCE_DIRECTORY = source_directory
        self.PERSIST_DIRECTORY = persist_directory
        self.EMBEDDING_MODEL_NAME = embedding_model_name

    def _get_converter(self):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.ocr_options = RapidOcrOptions()

        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def load_documents(self) -> list[Document] | None:
        pdf_files = list(pathlib.Path(self.SOURCE_DIRECTORY).glob("*.pdf"))
        if not pdf_files:
            return None

        all_elements: list[Document] = []
        converter = self._get_converter()

        chunker = HybridChunker(
            tokenizer="sentence-transformers/all-MiniLM-L6-v2",
            max_tokens=450,
            merge_peers=True
        )

        for file_path in pdf_files:
            try:
                print(f"Processing: {file_path.name}")

                result = converter.convert(str(file_path))
                doc_obj = result.document

                chunk_iter = chunker.chunk(doc_obj)

                for i, chunk in enumerate(chunk_iter):
                    text_content = normalize_formulas(chunk.text)

                    headings_list = []
                    if chunk.meta.headings:
                        for h in chunk.meta.headings:
                            if isinstance(h, str):
                                headings_list.append(h)
                            elif hasattr(h, 'text'):
                                headings_list.append(h.text)
                            else:
                                headings_list.append(str(h))

                    headings_str = " > ".join(headings_list)

                    metadata = {
                        "source": str(file_path),
                        "filename": file_path.name,
                        "page": list(chunk.meta.doc_items)[0].prov[0].page_no if chunk.meta.doc_items else 1,
                        "headings": headings_str,
                        "chunk_index": i
                    }

                    lc_doc = Document(
                        page_content=text_content,
                        metadata=metadata
                    )
                    all_elements.append(lc_doc)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        return all_elements

    def documents_to_chunks(self) -> list[Document] | None:
        chunks = self.load_documents()
        if not chunks:
            return None

        filtered = [chunk for chunk in chunks if len(chunk.page_content) > 30]

        return filter_complex_metadata(filtered)