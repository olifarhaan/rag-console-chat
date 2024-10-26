from abc import ABC, abstractmethod
from openai import OpenAI
from typing import List, Tuple
import os
from dotenv import load_dotenv
from src.logger import get_logger
from src.generator_types import GeneratorType

# Load environment variables
load_dotenv()
logger = get_logger()


class BaseResponseGenerator(ABC):
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def generate_response(
        self,
        **kwargs,
    ):
        pass

    @abstractmethod
    def get_type(self) -> GeneratorType:
        pass


class QuestionAnswerGenerator(BaseResponseGenerator):
    def generate_response(
        self,
        **kwargs,
    ):
        question = kwargs.get("question")
        relevant_chunks = kwargs.get("relevant_chunks")
        chat_history = kwargs.get("chat_history")

        context = "\n\n".join(relevant_chunks)
        chat_history_str = "\n".join(
            [f"{role}: {message}" for role, message in chat_history]
        )

        prompt = f"""
            You are an assistant for question-answering tasks. Use the following pieces of 
            retrieved context and the chat history to answer the question. If you don't know 
            the answer, say that you don't know. Use three sentences maximum and keep the answer concise.
            Context:
            {context}
            Chat History:
            {chat_history_str}
            Question:
            {question}
            """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question},
                ],
            )
            return response.choices[0].message
        except Exception as e:
            logger.error(f"Error generating QA response: {str(e)}")
            raise

    def get_type(self) -> GeneratorType:
        return GeneratorType.QUESTION_ANSWER


class SummaryGenerator(BaseResponseGenerator):
    def generate_response(
        self,
        **kwargs,
    ):
        topic = kwargs.get("topic")
        relevant_chunks = kwargs.get("relevant_chunks")

        context = "\n\n".join(relevant_chunks) if relevant_chunks else ""

        prompt = f"""
            You are an assistant for summarization of topics. Provide a concise summary 
            of the following text in three sentences or less.
            Context:
            {context}
            Topic:
            {topic}
            """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Please summarize the topic."},
                ],
            )
            return response.choices[0].message
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise

    def get_type(self) -> GeneratorType:
        return GeneratorType.SUMMARY


# Factory for creating different types of generators
class ResponseGeneratorFactory:
    @staticmethod
    def create_generator(generator_type: GeneratorType):
        if generator_type == GeneratorType.QUESTION_ANSWER:
            return QuestionAnswerGenerator()
        elif generator_type == GeneratorType.SUMMARY:
            return SummaryGenerator()
