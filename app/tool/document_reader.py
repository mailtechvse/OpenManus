import asyncio
from typing import List
from app.tool.base import BaseTool
import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from app.llm import LLM



class ChromaDBDocumentSearch(BaseTool):
    name: str = "chromadb_document_search"
    description: str = """Load documents into ChromaDB, perform vector search, and retrieve relevant content.
    Use this tool when you need to search for information within a collection of documents, especially PDFs or text files.
    It supports adding documents to a ChromaDB collection and querying it based on semantic similarity."""
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "collection_name": {
                "type": "string",
                "description": "(required) The name of the ChromaDB collection to use or create.",
            },
            "document_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "(required) List of paths to the documents (PDFs or text files) to load into ChromaDB.",
            },
            "query": {
                "type": "string",
                "description": "(required) The search query to find relevant documents.",
            },
            "chunk_size": {
                "type": "integer",
                "description": "(optional) The size of text chunks when splitting documents. Default is 1000.",
                "default": 1000,
            },
            "chunk_overlap": {
                "type": "integer",
                "description": "(optional) The overlap between text chunks. Default is 0.",
                "default": 0,
            },
            "n_results": {
                "type": "integer",
                "description": "(optional) The number of search results to return. Default is 3.",
                "default": 3,
            },
        },
        "required": ["collection_name", "document_paths", "query"],
    }

    async def execute(
        self,
        collection_name: str,
        document_paths: List[str],
        query: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        n_results: int = 3,
    ) -> List[str]:
        """
        Load documents into ChromaDB, perform a vector search, and return the relevant documents.

        Returns:
            List[str]: A list of relevant documents from ChromaDB.
        """
        try:
            return await asyncio.to_thread(
                self._load_and_search_chromadb,
                collection_name, document_paths, query, chunk_size, chunk_overlap, n_results
            )
        except Exception as e:
            return {"error": str(e)}

    def _load_and_search_chromadb(
        self,
        collection_name: str,
        document_paths: List[str],
        query: str,
        chunk_size: int,
        chunk_overlap: int,
        n_results: int,
    ) -> List[str]:
        """
        Load documents, create embeddings, and search ChromaDB.
        """
        try:
            
            llm_object = LLM()
            
            
            
            # Configure ChromaDB client
            chroma_client = chromadb.PersistentClient(path="./tmp/db/")

            # Get or create collection
            # collections = [c.name for c in chroma_client.list_collections()]
            try:
                collection = chroma_client.get_collection(name=collection_name)
                print(f"Collection '{collection_name}' found.")
            except Exception as e:
                # collection to be created
                collection = chroma_client.create_collection(name=collection_name)
                print(f"Created new collection '{collection_name}'.")

            # Load documents
            documents = []
            for path in document_paths:
                if path.endswith(".pdf"):
                    loader = PyPDFLoader(path)
                elif path.endswith(".txt"):
                    loader = TextLoader(path)
                else:
                    print(f"Unsupported file type: {path}. Only PDF and TXT files are supported.")
                    continue
                documents.extend(loader.load())

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            chunks = text_splitter.split_documents(documents)

            if not chunks:
                print("No chunks to add to ChromaDB.")
                return []

            # Generate embeddings
            embedding_model = OpenAIEmbeddings(api_key = llm_object.api_key)
            chunk_texts = [chunk.page_content for chunk in chunks]
            chunk_embeddings = embedding_model.embed_documents(chunk_texts)

            # Add chunks to ChromaDB collection
            collection.add(
                ids=[str(i) for i in range(len(chunks))],
                documents=chunk_texts,
                embeddings=chunk_embeddings,
            )
            print(f"Added {len(chunks)} chunks to collection '{collection_name}'.")

            # Perform vector search
            query_embedding = embedding_model.embed_query(query)
            results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

            # Extract and return relevant documents
            relevant_documents = results["documents"][0] if results["documents"] else []
            return relevant_documents

        except Exception as e:
            print(f"Error in _load_and_search_chromadb: {e}")
            return {"error": str(e)}