from abc import ABC, abstractmethod
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger()

# Load environment variables
load_dotenv()


class VectorStore(ABC):
    @abstractmethod
    def upsert(
        self, ids: List[str], documents: List[str], embeddings: List[List[float]]
    ):
        pass

    @abstractmethod
    def query(self, query_texts: List[str], n_results: int = 2) -> Dict[str, Any]:
        pass

    @abstractmethod
    def document_exists(self, id: str) -> bool:
        pass


class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name: str, persist_directory: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = collection_name

        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-small"
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=openai_ef
        )
        logger.info(f"Initialized ChromaVectorStore with collection: {collection_name}")

    def upsert(
        self, ids: List[str], documents: List[str], embeddings: List[List[float]]
    ):
        try:
            self.collection.upsert(ids=ids, documents=documents, embeddings=embeddings)
            logger.info(f"Upserted {len(ids)} documents to ChromaVectorStore")
        except Exception as e:
            logger.error(f"Error upserting to ChromaVectorStore: {str(e)}")
            raise

    def query(self, query_texts: List[str], n_results: int = 2) -> Dict[str, Any]:
        try:
            results = self.collection.query(
                query_texts=query_texts, n_results=n_results
            )
            logger.info(f"Queried ChromaVectorStore with {len(query_texts)} texts")
            return results
        except Exception as e:
            logger.error(f"Error querying ChromaVectorStore: {str(e)}")
            raise

    def document_exists(self, id: str) -> bool:
        try:
            result = self.collection.get(ids=[id + "-0"])
            exists = len(result["ids"]) > 0
            logger.info(f"Document {id} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking if document exists: {str(e)}")
            return False


class VectorStoreService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        logger.info(
            f"Initialized VectorStoreService with {type(vector_store).__name__}"
        )

    def upsert_documents(self, documents: List[Dict[str, Any]]):
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        embeddings = [doc["embedding"] for doc in documents]
        self.vector_store.upsert(ids, texts, embeddings)

    def query_documents(self, query: str, n_results: int = 2) -> List[str]:
        results = self.vector_store.query([query], n_results)
        return [doc for sublist in results["documents"] for doc in sublist]

    def document_exists(self, id: str) -> bool:
        return self.vector_store.document_exists(id)
