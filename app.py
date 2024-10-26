import yaml
from dotenv import load_dotenv
from enum import Enum
import os
import sys
import subprocess
import threading
import time
from src.utils import loading_animation
from src.ingestion import DocumentIngestion
from src.embedding import EmbeddingService, OpenAIEmbeddingGenerator
from src.vector_store import ChromaVectorStore, VectorStoreService
from src.response_generator import ResponseGeneratorFactory
from src.generator_types import GeneratorType
from src.logger import get_logger
from src.config import Config, ConfigKeys
import questionary
from rich.console import Console
from rich.panel import Panel
from src.utils import set_startup_complete

logger = get_logger()
console = Console()


class RAGPipeline:
    def __init__(self, config_path):
        load_dotenv()
        self.config = Config(config_path)
        self._initialize_components()
        self.chat_history = []

    def _initialize_components(self):
        self.embedding_service = EmbeddingService(OpenAIEmbeddingGenerator())
        self.vector_store_service = VectorStoreService(
            ChromaVectorStore(
                self.config.get(ConfigKeys.COLLECTION_NAME),
                self.config.get(ConfigKeys.PERSIST_DIRECTORY),
            )
        )
        self.qa_generator = ResponseGeneratorFactory.create_generator(
            GeneratorType.QUESTION_ANSWER
        )
        self.summary_generator = ResponseGeneratorFactory.create_generator(
            GeneratorType.SUMMARY
        )
        self.document_ingestion = DocumentIngestion(
            self.config.get(ConfigKeys.DOCS_DIRECTORY)
        )

    def process_documents(self):
        """
        Process documents and return chunked documents
        It will load all documents, check if they are already in the vector store,
        and if not, it will split the text into chunks and return the chunked documents.
        """
        all_documents = self.document_ingestion.load_documents()

        new_documents = [
            doc
            for doc in all_documents
            if not self.vector_store_service.document_exists(doc["id"])
        ]
        chunked_documents = []
        for doc in new_documents:
            chunks = self.document_ingestion.split_text(doc["text"])
            chunked_documents.extend(
                [
                    {"id": f"{doc['id']}-{i}", "text": chunk}
                    for i, chunk in enumerate(chunks)
                ]
            )
        logger.info(f"Processed {len(chunked_documents)} new document chunks")
        return chunked_documents

    def generate_and_store_embeddings(self, chunked_documents):
        if not chunked_documents:
            logger.info("No new documents to process")
            return

        docs_to_upsert = [
            {
                "id": doc["id"],
                "text": doc["text"],
                "embedding": self.embedding_service.get_embedding(doc["text"]),
            }
            for doc in chunked_documents
        ]
        self.vector_store_service.upsert_documents(docs_to_upsert)
        logger.info(
            f"Processed and stored {len(docs_to_upsert)} new document chunks in vector database"
        )

    def generate_qa_response(self, question, chat_history, n_results=2):
        relevant_chunks = self.vector_store_service.query_documents(
            question, n_results=n_results
        )
        return self.qa_generator.generate_response(
            question=question,
            relevant_chunks=relevant_chunks,
            chat_history=chat_history,
        )

    def generate_summary(self, topic, n_results=2):
        relevant_chunks = self.vector_store_service.query_documents(
            topic, n_results=n_results
        )
        return self.summary_generator.generate_response(
            topic=topic, relevant_chunks=relevant_chunks
        )

    def run(self):
        """
        The run function is the main entry point for executing the RAG (Retrieval-Augmented Generation) pipeline.
        It manages the initialization of the pipeline, including loading documents and generating embeddings.

        Key steps in the run function:
        1. Starts a loading animation in a separate thread.
        2. Processes documents to load and chunk new data.
        3. Generates and stores embeddings for the processed documents.
        4. Invokes the main menu for user interaction.

        This function is essential for setting up the pipeline and enabling user interaction.
        """
        logger.info("Starting RAG pipeline")
        threading.Thread(target=loading_animation, daemon=True).start()

        chunked_documents = self.process_documents()
        self.generate_and_store_embeddings(chunked_documents)

        set_startup_complete(True)
        time.sleep(0.5)
        self.main_menu()

    def main_menu(self):
        """
        The main_menu function provides a user interface for interacting with the RAG pipeline.
        It allows the user to choose between three options: chatting, summarizing, or exiting the program.
        """
        console.print(Panel("Welcome to the RAG Pipeline", style="bold green"))
        while True:
            choice = questionary.select(
                "Choose an option:", choices=["Chat", "Summarize", "Exit"]
            ).ask()

            if choice == "Chat":
                self.chat_mode()
            elif choice == "Summarize":
                self.summarize_mode()
            else:
                console.print(
                    "Thank you for using the RAG pipeline. Goodbye!", style="bold green"
                )
                break

    def chat_mode(self):
        """
        The chat_mode function allows the user to engage in a conversational chat with the RAG pipeline.
        It provides a loop for continuous interaction, allowing the user to ask questions and receive answers.
        """
        console.print(Panel("Chat Mode", style="bold blue"))
        while True:
            question = questionary.text("You:").ask()
            if question.lower() == "exit":
                self.print_chat_history()
                break

            answer = self.generate_qa_response(question, self.chat_history)
            self.chat_history.append(("You", question))
            self.chat_history.append(("AI", answer.content))
            console.print(f"AI: {answer.content}", style="green")

    def summarize_mode(self):
        """
        The summarize_mode function allows the user to summarize a given topic.
        It prompts the user to enter a topic and then generates a summary of the relevant documents.
        """
        console.print(Panel("Summarize Mode", style="bold blue"))
        topic = questionary.text("Enter a topic to summarize:").ask()
        summary = self.generate_summary(topic)
        console.print(f"Summary: {summary.content}", style="green")

    def print_chat_history(self):
        console.print(Panel("Chat History", style="bold blue"))
        for role, message in self.chat_history:
            console.print(
                f"{role}: {message}", style="green" if role == "AI" else "cyan"
            )


def main():
    if sys.platform.startswith("win"):
        """
        For Windows, we use the start command to open a new command prompt window and run the script.
        """
        command = f'start cmd /K python "{__file__}"'
    elif sys.platform.startswith("darwin"):
        """
        For macOS, we use osascript to open a new terminal window and run the script.
        """
        command = (
            f'osascript -e \'tell app "Terminal" to do script "python {__file__}"\''
        )
    elif sys.platform.startswith("linux"):
        """
        For Linux, we use x-terminal-emulator to open a new terminal window and run the script.
        """
        command = f'x-terminal-emulator -e python "{__file__}"'
    else:
        raise ValueError(f"Unsupported platform: {sys.platform}")

    """
    This block checks if the script is launched from a terminal. 
    If not, it sets an environment variable and opens a new terminal window to run the script.
    """
    if os.environ.get("LAUNCHED_FROM_TERMINAL") != "1":
        os.environ["LAUNCHED_FROM_TERMINAL"] = "1"
        subprocess.call(command, shell=True)
    else:
        pipeline = RAGPipeline("config.yml")
        pipeline.run()


if __name__ == "__main__":
    main()
