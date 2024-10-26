from typing import List
from src.vector_store import VectorStoreService, default_vector_store_service
from src.logger import get_logger

logger = get_logger()

class VectorStoreRetriever:
    def __init__(self, vector_store_service: VectorStoreService):
        self.vector_store_service = vector_store_service
        logger.info("Initialized VectorStoreRetriever")

    def retrieve(self, query: str, n_results: int = 2) -> List[str]:
        try:
            relevant_chunks = self.vector_store_service.query_documents(query, n_results)
            logger.info(f"Retrieved {len(relevant_chunks)} chunks for query: {query}")
            return relevant_chunks
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise

# Create a default retriever
default_retriever = VectorStoreRetriever(default_vector_store_service)

def query_documents(query: str, n_results: int = 2) -> List[str]:
    """
    Convenience function to query documents using the default retriever.
    """
    return default_retriever.retrieve(query, n_results)

