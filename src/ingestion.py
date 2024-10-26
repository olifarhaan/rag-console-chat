import os
from abc import ABC, abstractmethod
from typing import List, Dict
import docx
import PyPDF2
from src.logger import get_logger

logger = get_logger()

class DocumentHandler(ABC):
    @abstractmethod
    def read_document(self, file_path: str) -> str:
        pass

class TxtDocumentHandler(DocumentHandler):
    def read_document(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

class PdfDocumentHandler(DocumentHandler):
    def read_document(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return ' '.join(page.extract_text() for page in pdf_reader.pages)

class DocxDocumentHandler(DocumentHandler):
    def read_document(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return ' '.join(paragraph.text for paragraph in doc.paragraphs)

class DocumentIngestion:
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.handlers = {
            '.txt': TxtDocumentHandler(),
            '.pdf': PdfDocumentHandler(),
            '.docx': DocxDocumentHandler()
        }

    def load_documents(self) -> List[Dict[str, str]]:
        documents = []
        for filename in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, filename)
            _, file_extension = os.path.splitext(filename)
            
            if file_extension.lower() in self.handlers:
                handler = self.handlers[file_extension.lower()]
                content = handler.read_document(file_path)
                documents.append({"id": filename, "text": content})
            else:
                logger.warning(f"Unsupported file extension: {file_extension}")
        return documents

    @staticmethod
    def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 20) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks

    def process_documents(self) -> List[Dict[str, str]]:
        documents = self.load_documents()
        chunked_documents = []
        for doc in documents:
            chunks = self.split_text(doc["text"])
            for i, chunk in enumerate(chunks):
                chunked_documents.append({"id": f"{doc['id']}_chunk{i+1}", "text": chunk})
        return chunked_documents