from abc import ABC, abstractmethod
from typing import List
from openai import OpenAI
import os
from dotenv import load_dotenv
from src.logger import get_logger

# Load environment variables
load_dotenv()
logger = get_logger()

class EmbeddingGenerator(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        pass

class OpenAIEmbeddingGenerator(EmbeddingGenerator):
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name
        logger.info(f"Initialized OpenAIEmbeddingGenerator with model: {model_name}")

    def generate_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(input=text, model=self.model_name)
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text of length {len(text)}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

class EmbeddingService:
    def __init__(self, embedding_generator: EmbeddingGenerator):
        self.embedding_generator = embedding_generator
        logger.info(f"Initialized EmbeddingService with {type(embedding_generator).__name__}")

    def get_embedding(self, text: str) -> List[float]:
        return self.embedding_generator.generate_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        logger.info(f"Generated embeddings for {len(texts)} texts")
        return embeddings

# Create a default embedding service using OpenAI
default_embedding_service = EmbeddingService(OpenAIEmbeddingGenerator())

def get_openai_embedding(text: str) -> List[float]:
    """
    Convenience function to get a single embedding using the default service.
    """
    return default_embedding_service.get_embedding(text)

