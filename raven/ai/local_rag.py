from typing import Any, Dict, List, Optional, Union
import frappe
import json
import os
import tempfile
from abc import ABC, abstractmethod

# Define fallback types/classes for when the SDK is not available
class DummyFunctionTool:
    """Dummy FunctionTool class for when the SDK is not available"""
    def __init__(self, function=None, name=None, description=None, parameter_schema=None):
        self.function = function
        self.name = name
        self.description = description
        self.parameter_schema = parameter_schema

# Attempt to import the real SDK
try:
    from agents import FunctionTool
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    # If import fails, use dummy class
    FunctionTool = DummyFunctionTool
    AGENTS_SDK_AVAILABLE = False
    frappe.log_error("OpenAI Agents SDK not installed. Run 'pip install openai-agents'")


class LocalRAGProvider(ABC):
    """Base class for local RAG providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.vector_store = None
        self.embedding_model = None
        
    @abstractmethod
    def initialize(self):
        """Initialize the vector store and embedding model"""
        pass
        
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents to add
        """
        pass
        
    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector store
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        pass
    
    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> 'LocalRAGProvider':
        """
        Create a LocalRAGProvider instance
        
        Args:
            provider_type: Provider type
            config: Provider configuration
            
        Returns:
            LocalRAGProvider: Provider instance
        """
        if provider_type == "Chroma":
            return ChromaRAGProvider(config)
        elif provider_type == "FAISS":
            return FAISSRAGProvider(config)
        elif provider_type == "Weaviate":
            return WeaviateRAGProvider(config)
        else:
            frappe.throw(f"Unsupported RAG provider: {provider_type}")


class ChromaRAGProvider(LocalRAGProvider):
    """RAG provider using ChromaDB"""
    
    def initialize(self):
        """Initialize the vector store and embedding model"""
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_openai import OpenAIEmbeddings
            
            # Set up embedding model
            # This can be customized based on settings
            self.embedding_model = OpenAIEmbeddings()
            
            # Set up Chroma DB
            persist_directory = self.config.get("persist_directory")
            if not persist_directory:
                # Create a directory in site's private files
                site_path = frappe.get_site_path()
                persist_directory = os.path.join(site_path, "private", "chroma_db")
                os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize Chroma
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding_model
            )
            
        except ImportError as e:
            frappe.log_error(f"Error initializing ChromaDB: {e}")
            frappe.throw("ChromaDB not available. Run 'pip install chromadb langchain-community langchain-openai'")
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents to add
        """
        if not self.vector_store:
            self.initialize()
        
        # Extract texts and metadata from documents
        texts = [doc.get("content", "") for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        # Add documents to the vector store
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector store
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        if not self.vector_store:
            self.initialize()
        
        # Search the vector store
        results = self.vector_store.similarity_search_with_relevance_scores(query, k=k)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })
        
        return formatted_results


class FAISSRAGProvider(LocalRAGProvider):
    """RAG provider using FAISS"""
    
    def initialize(self):
        """Initialize the vector store and embedding model"""
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_openai import OpenAIEmbeddings
            
            # Set up embedding model
            # This can be customized based on settings
            self.embedding_model = OpenAIEmbeddings()
            
            # FAISS doesn't need an initial setup like Chroma
            # It's created when documents are added
            self.vector_store = None
            
        except ImportError as e:
            frappe.log_error(f"Error initializing FAISS: {e}")
            frappe.throw("FAISS not available. Run 'pip install faiss-cpu langchain-community langchain-openai'")
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents to add
        """
        try:
            from langchain_community.vectorstores import FAISS
            
            if not self.embedding_model:
                self.initialize()
            
            # Extract texts and metadata from documents
            texts = [doc.get("content", "") for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # If the vector store doesn't exist yet, create it
            if not self.vector_store:
                self.vector_store = FAISS.from_texts(
                    texts=texts,
                    embedding=self.embedding_model,
                    metadatas=metadatas
                )
            # Otherwise, add to the existing vector store
            else:
                self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas
                )
                
            # Save the vector store to disk
            persist_directory = self.config.get("persist_directory")
            if persist_directory:
                os.makedirs(persist_directory, exist_ok=True)
                self.vector_store.save_local(persist_directory)
                
        except Exception as e:
            frappe.log_error(f"Error adding documents to FAISS: {e}")
            frappe.throw(f"Error adding documents to FAISS: {e}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector store
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        if not self.vector_store:
            # Try to load from disk
            persist_directory = self.config.get("persist_directory")
            if persist_directory and os.path.exists(persist_directory):
                try:
                    from langchain_community.vectorstores import FAISS
                    
                    if not self.embedding_model:
                        self.initialize()
                        
                    self.vector_store = FAISS.load_local(
                        folder_path=persist_directory,
                        embeddings=self.embedding_model
                    )
                except Exception as e:
                    frappe.log_error(f"Error loading FAISS from disk: {e}")
                    return []
            else:
                return []
        
        # Search the vector store
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)  # Convert numpy float to Python float
            })
        
        return formatted_results


class WeaviateRAGProvider(LocalRAGProvider):
    """RAG provider using Weaviate"""
    
    def initialize(self):
        """Initialize the vector store and embedding model"""
        try:
            from langchain_community.vectorstores import Weaviate
            from langchain_openai import OpenAIEmbeddings
            import weaviate
            
            # Set up embedding model
            self.embedding_model = OpenAIEmbeddings()
            
            # Get Weaviate connection info from config
            url = self.config.get("url", "http://localhost:8080")
            
            # Set up Weaviate client
            if "api_key" in self.config:
                auth_config = weaviate.AuthApiKey(api_key=self.config["api_key"])
                self.client = weaviate.Client(url=url, auth_client_secret=auth_config)
            else:
                self.client = weaviate.Client(url=url)
            
            # Get or create class name
            self.class_name = self.config.get("class_name", "RavenDocument")
            
            # Initialize the vector store
            self.vector_store = Weaviate(
                client=self.client,
                index_name=self.class_name,
                text_key="content",
                embedding=self.embedding_model
            )
            
        except ImportError as e:
            frappe.log_error(f"Error initializing Weaviate: {e}")
            frappe.throw("Weaviate not available. Run 'pip install weaviate-client langchain-community langchain-openai'")
        except Exception as e:
            frappe.log_error(f"Error connecting to Weaviate: {e}")
            frappe.throw(f"Error connecting to Weaviate: {e}")
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents to add
        """
        if not hasattr(self, "vector_store") or not self.vector_store:
            self.initialize()
        
        try:
            # Extract texts and metadata from documents
            texts = [doc.get("content", "") for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # Add documents to Weaviate
            self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas
            )
            
        except Exception as e:
            frappe.log_error(f"Error adding documents to Weaviate: {e}")
            frappe.throw(f"Error adding documents to Weaviate: {e}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector store
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        if not hasattr(self, "vector_store") or not self.vector_store:
            try:
                self.initialize()
            except Exception as e:
                frappe.log_error(f"Error initializing Weaviate for search: {e}")
                return []
        
        try:
            # Search Weaviate
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            return formatted_results
            
        except Exception as e:
            frappe.log_error(f"Error searching Weaviate: {e}")
            return []


def create_local_file_search_tool(bot) -> FunctionTool:
    """
    Create a FunctionTool for local file search
    
    Args:
        bot: Raven bot document
        
    Returns:
        FunctionTool: Function tool for file search
    """
    # Create a function tool for local file search
    tool = FunctionTool(
        function=local_file_search,
        name="file_search",
        description="Search for information in files and documents",
        parameter_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    )
    
    return tool


def local_file_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search for information in files
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        Dict[str, Any]: Search results
    """
    # Get current bot from context
    bot_name = frappe.flags.get("raven_current_bot")
    if not bot_name:
        return {
            "success": False,
            "error": "No bot context found"
        }
    
    bot = frappe.get_doc("Raven Bot", bot_name)
    
    # Get the RAG provider from bot settings
    provider_type = bot.local_rag_provider
    
    # Create provider
    config = {}  # This would come from settings
    provider = LocalRAGProvider.create(provider_type, config)
    
    # Search
    results = provider.search(query, k=max_results)
    
    return {
        "success": True,
        "results": results
    }