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
    
    def get_tool(self) -> Any:
        """
        Get the tool to use with the OpenAI Agents SDK
        
        Returns:
            Any: Tool object compatible with the OpenAI Agents SDK
        """
        # Create a function tool for local file search
        return create_local_file_search_tool(None)
    
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
            frappe.log_error("RAG Debug", f"Starting ChromaRAGProvider initialization with config: {self.config}")
            
            from langchain_community.vectorstores import Chroma
            frappe.log_error("RAG Debug", f"Successfully imported Chroma from langchain_community")
            
            # Check if local embeddings model should be used (from config)
            use_local_embeddings = self.config.get("use_local_embeddings", False)
            frappe.log_error("RAG Debug", f"Use local embeddings: {use_local_embeddings}")
            
            if use_local_embeddings:
                # Try to use local embeddings models (HuggingFace)
                try:
                    frappe.log_error("RAG Debug", f"Attempting to import HuggingFaceEmbeddings")
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    
                    # Use a small, efficient model like all-MiniLM-L6-v2
                    model_name = self.config.get("embeddings_model", "all-MiniLM-L6-v2")
                    frappe.log_error("RAG Debug", f"Creating HuggingFaceEmbeddings with model: {model_name}")
                    
                    # Try importing sentence_transformers directly to check it's available
                    try:
                        import sentence_transformers
                        frappe.log_error("RAG Debug", f"sentence_transformers version: {sentence_transformers.__version__}")
                    except ImportError:
                        frappe.log_error("RAG Debug", f"sentence_transformers not found, may cause HuggingFaceEmbeddings to fail")
                    
                    self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
                    frappe.log_error("RAG", f"Successfully created local HuggingFace embeddings model: {model_name}")
                except ImportError as e:
                    frappe.log_error("RAG Debug", f"ImportError with HuggingFaceEmbeddings: {str(e)}")
                    frappe.log_error("RAG", f"Error loading HuggingFace embeddings: {str(e)}. Install with: pip install sentence-transformers")
                    frappe.throw("Local embeddings not available. Install with: pip install sentence-transformers")
                except Exception as e:
                    frappe.log_error("RAG Debug", f"Exception creating HuggingFaceEmbeddings: {type(e).__name__}: {str(e)}")
                    frappe.throw(f"Error creating local embeddings: {type(e).__name__}: {str(e)}")
            else:
                # Use OpenAI embeddings (default)
                frappe.log_error("RAG Debug", f"Attempting to use OpenAI embeddings")
                from langchain_openai import OpenAIEmbeddings
                
                # Get OpenAI API key from settings
                settings = frappe.get_cached_doc("Raven Settings")
                api_key = settings.get_password("openai_api_key")
                if not api_key:
                    frappe.log_error("RAG Debug", f"OpenAI API key not found in settings")
                    frappe.throw("OpenAI API key is not configured in Raven Settings. Either add an API key or use local embeddings.")
                
                # Set up embedding model with API key
                frappe.log_error("RAG Debug", f"Creating OpenAIEmbeddings with API key")
                self.embedding_model = OpenAIEmbeddings(openai_api_key=api_key)
                frappe.log_error("RAG Debug", f"Successfully created OpenAI embeddings model")
            
            # Set up Chroma DB
            persist_directory = self.config.get("persist_directory")
            frappe.log_error("RAG Debug", f"Persist directory from config: {persist_directory}")
            
            if not persist_directory:
                # Create a directory in site's private files
                site_path = frappe.get_site_path()
                persist_directory = os.path.join(site_path, "private", "chroma_db")
                frappe.log_error("RAG Debug", f"Using default persist directory: {persist_directory}")
                
                try:
                    frappe.log_error("RAG Debug", f"Creating directory: {persist_directory}")
                    os.makedirs(persist_directory, exist_ok=True)
                    frappe.log_error("RAG Debug", f"Directory created successfully")
                except Exception as e:
                    frappe.log_error("RAG Debug", f"Error creating directory: {type(e).__name__}: {str(e)}")
                    frappe.throw(f"Failed to create Chroma DB directory: {str(e)}")
            
            # Initialize Chroma
            frappe.log_error("RAG Debug", f"Initializing Chroma with persist_directory: {persist_directory}")
            try:
                self.vector_store = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embedding_model
                )
                frappe.log_error("RAG Debug", f"Chroma initialized successfully")
                return True
            except Exception as e:
                frappe.log_error("RAG Debug", f"Error initializing Chroma: {type(e).__name__}: {str(e)}")
                frappe.throw(f"Failed to initialize Chroma: {type(e).__name__}: {str(e)}")
            
        except ImportError as e:
            frappe.log_error(f"Error initializing ChromaDB: {e}")
            frappe.throw("ChromaDB not available. Run 'pip install chromadb langchain-community langchain-openai'")
            
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a file and add it to the vector store
        
        Args:
            file_path: Path to the file
            metadata: Additional metadata for the document
            
        Returns:
            str: Document ID or reference
        """
        try:
            frappe.log_error("RAG Debug", f"Processing file: {file_path}")
            
            # Ensure the vector store is initialized
            if not hasattr(self, "vector_store") or not self.vector_store:
                self.initialize()
                
            # Process the file based on its type
            from langchain_community.document_loaders import (
                PyPDFLoader, 
                TextLoader, 
                CSVLoader, 
                UnstructuredExcelLoader,
                UnstructuredPowerPointLoader,
                UnstructuredWordDocumentLoader
            )
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            # Get file info for metadata
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            import datetime
            current_time = datetime.datetime.now().isoformat()
            
            # Enhance metadata with file information
            if not metadata:
                metadata = {}
            
            file_metadata = {
                "file_name": file_name,
                "file_size": file_size,
                "file_extension": file_extension,
                "processed_at": current_time,
                "source": "raven_upload"
            }
            
            # Merge with provided metadata
            enhanced_metadata = {**file_metadata, **(metadata or {})}
            frappe.log_error("RAG Debug", f"Enhanced metadata: {enhanced_metadata}")
            
            # Initialize text splitter for chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Determine file type and use appropriate loader
            if file_extension == '.pdf':
                frappe.log_error("RAG Debug", f"Loading PDF file: {file_path}")
                
                # Use UnstructuredPDFLoader for better text extraction with OCR fallback
                try:
                    # First try with PyPDFLoader which is faster
                    loader = PyPDFLoader(file_path)
                    pages = loader.load_and_split()
                    frappe.log_error("RAG Debug", f"Loaded {len(pages)} pages from PDF using PyPDFLoader")
                    
                    # Check if we got meaningful content
                    is_content_meaningful = False
                    for page in pages:
                        content = page.page_content.strip()
                        # Check if content is meaningful (not just spaces or very short)
                        if len(content) > 100:
                            is_content_meaningful = True
                            break
                    
                    # If content is not meaningful, try UnstructuredPDFLoader
                    if not is_content_meaningful:
                        frappe.log_error("RAG Debug", "PDF content seems insufficient, trying UnstructuredPDFLoader")
                        from langchain_community.document_loaders import UnstructuredPDFLoader
                        loader = UnstructuredPDFLoader(file_path, mode="elements")
                        raw_pages = loader.load()
                        frappe.log_error("RAG Debug", f"Loaded {len(raw_pages)} elements from PDF using UnstructuredPDFLoader")
                        pages = raw_pages
                    
                except Exception as e:
                    frappe.log_error("RAG Debug", f"Error with primary PDF loader: {str(e)}, trying fallback")
                    # Fallback to UnstructuredPDFLoader
                    from langchain_community.document_loaders import UnstructuredPDFLoader
                    loader = UnstructuredPDFLoader(file_path, mode="elements")
                    pages = loader.load()
                    frappe.log_error("RAG Debug", f"Loaded {len(pages)} elements from PDF using fallback UnstructuredPDFLoader")
                
                # Process the pages into documents with metadata
                documents = []
                
                # Custom splitter for PDFs that preserves more context
                pdf_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                
                # Process each page
                page_number = 1
                for i, page in enumerate(pages):
                    # Check if this is from UnstructuredPDFLoader which has a different structure
                    if hasattr(page, 'metadata') and 'page' in page.metadata:
                        page_number = page.metadata['page']
                    else:
                        # Use the index+1 as page number if not available in metadata
                        page_number = i+1
                    
                    # Add enhanced metadata including page number
                    page_metadata = {**enhanced_metadata, "page": page_number}
                    
                    # Update the page's metadata
                    if hasattr(page, 'metadata'):
                        page.metadata.update(page_metadata)
                    else:
                        # Create metadata if it doesn't exist
                        page.metadata = page_metadata
                    
                    # Split the page into chunks
                    chunks = pdf_splitter.split_documents([page])
                    for j, chunk in enumerate(chunks):
                        # Add chunk number to metadata
                        chunk.metadata["chunk"] = j+1
                        documents.append(chunk)
                
                frappe.log_error("RAG Debug", f"Created {len(documents)} chunks from PDF")
                
            elif file_extension == '.txt':
                frappe.log_error("RAG Debug", f"Loading text file: {file_path}")
                loader = TextLoader(file_path)
                raw_documents = loader.load()
                # Add metadata
                for doc in raw_documents:
                    doc.metadata.update(enhanced_metadata)
                # Split documents
                documents = text_splitter.split_documents(raw_documents)
                frappe.log_error("RAG Debug", f"Created {len(documents)} chunks from text file")
                
            elif file_extension == '.csv':
                frappe.log_error("RAG Debug", f"Loading CSV file: {file_path}")
                loader = CSVLoader(file_path)
                raw_documents = loader.load()
                # Add metadata
                for doc in raw_documents:
                    doc.metadata.update(enhanced_metadata)
                # Split documents
                documents = text_splitter.split_documents(raw_documents)
                frappe.log_error("RAG Debug", f"Created {len(documents)} chunks from CSV")
                
            elif file_extension in ['.xlsx', '.xls']:
                frappe.log_error("RAG Debug", f"Loading Excel file: {file_path}")
                loader = UnstructuredExcelLoader(file_path)
                raw_documents = loader.load()
                # Add metadata
                for doc in raw_documents:
                    doc.metadata.update(enhanced_metadata)
                # Split documents
                documents = text_splitter.split_documents(raw_documents)
                frappe.log_error("RAG Debug", f"Created {len(documents)} chunks from Excel")
                
            elif file_extension in ['.pptx', '.ppt']:
                frappe.log_error("RAG Debug", f"Loading PowerPoint file: {file_path}")
                loader = UnstructuredPowerPointLoader(file_path)
                raw_documents = loader.load()
                # Add metadata
                for doc in raw_documents:
                    doc.metadata.update(enhanced_metadata)
                # Split documents
                documents = text_splitter.split_documents(raw_documents)
                frappe.log_error("RAG Debug", f"Created {len(documents)} chunks from PowerPoint")
                
            elif file_extension in ['.docx', '.doc']:
                frappe.log_error("RAG Debug", f"Loading Word file: {file_path}")
                loader = UnstructuredWordDocumentLoader(file_path)
                raw_documents = loader.load()
                # Add metadata
                for doc in raw_documents:
                    doc.metadata.update(enhanced_metadata)
                # Split documents
                documents = text_splitter.split_documents(raw_documents)
                frappe.log_error("RAG Debug", f"Created {len(documents)} chunks from Word")
                
            else:
                frappe.log_error("RAG Debug", f"Unsupported file type: {file_extension}")
                return f"Unsupported file type: {file_extension}"
                
            # Log total chunks
            frappe.log_error("RAG Debug", f"Total chunks to add: {len(documents)}")
            
            # Process in batches for better performance
            batch_size = 32  # Optimal batch size for Chroma
            total_documents = len(documents)
            
            for i in range(0, total_documents, batch_size):
                end_idx = min(i + batch_size, total_documents)
                batch = documents[i:end_idx]
                frappe.log_error("RAG Debug", f"Adding batch {i//batch_size + 1}/{(total_documents-1)//batch_size + 1} with {len(batch)} documents")
                
                # Add documents to vector store
                self.vector_store.add_documents(batch)
            
            frappe.log_error("RAG Debug", f"Successfully added all documents to vector store")
            
            # Generate a unique ID for reference
            import uuid
            doc_id = str(uuid.uuid4())
            
            # Store reference in metadata for future retrieval
            frappe.log_error("RAG Debug", f"Processed file with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error processing file: {type(e).__name__}: {str(e)}")
            frappe.log_error("RAG Debug", f"Error details: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing file: {str(e)}")
    
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
        try:
            frappe.log_error("RAG Debug", f"Searching for: '{query}', k={k}")
            
            if not self.vector_store:
                frappe.log_error("RAG Debug", "Vector store not initialized, initializing now")
                self.initialize()
            
            # Identify key concepts from the query
            keywords = self._extract_keywords(query)
            frappe.log_error("RAG Debug", f"Extracted keywords: {keywords}")
            
            # Multi-strategy search for better results
            all_results = []
            
            # Strategy 1: Direct vector similarity search
            frappe.log_error("RAG Debug", "Strategy 1: Direct vector similarity search")
            try:
                direct_results = self.vector_store.similarity_search_with_relevance_scores(
                    query, 
                    k=k
                )
                frappe.log_error("RAG Debug", f"Direct search found {len(direct_results)} results")
                all_results.extend(direct_results)
            except Exception as e:
                frappe.log_error("RAG Debug", f"Direct search failed: {str(e)}")
            
            # Strategy 2: MMR search (Maximum Marginal Relevance) for diversity
            # This helps find more diverse results that might contain the answer
            frappe.log_error("RAG Debug", "Strategy 2: MMR search for diversity")
            try:
                if hasattr(self.vector_store, "max_marginal_relevance_search"):
                    mmr_results = self.vector_store.max_marginal_relevance_search(
                        query,
                        k=k,
                        fetch_k=k*3,  # Fetch more then filter down
                        lambda_mult=0.5  # Balance between relevance and diversity
                    )
                    # Convert to same format as similarity_search_with_relevance_scores
                    mmr_formatted = [(doc, 0.5) for doc in mmr_results]  # Assign a default score
                    all_results.extend(mmr_formatted)
                    frappe.log_error("RAG Debug", f"MMR search found {len(mmr_results)} results")
            except Exception as e:
                frappe.log_error("RAG Debug", f"MMR search failed: {str(e)}")
            
            # Strategy 3: Use LLM enhancer if available, otherwise use statistical detection
            try:
                from .rag_llm_enhanced import LLMQueryEnhancer, IntentClassifier
                
                try:
                    # Use intent classification to detect financial content
                    intent_classifier = IntentClassifier()
                    intent_scores = intent_classifier.classify_intent(query)
                    
                    frappe.log_error("RAG Debug", f"Intent scores: {intent_scores}")
                    
                    # Check if financial intent is strong
                    is_financial = intent_scores.get('financial_information', 0) > 0.3
                    
                    if is_financial:
                        frappe.log_error("RAG Debug", "Strategy 3: Targeted financial content search via intent")
                        try:
                            # Use LLM-enhanced financial terms
                            enhancer = LLMQueryEnhancer()
                            financial_terms = enhancer.enhance_query("financial information, amounts, costs, prices, totals")
                            
                            financial_results = self.vector_store.similarity_search_with_relevance_scores(
                                financial_terms, 
                                k=k
                            )
                            frappe.log_error("RAG Debug", f"Financial term search found {len(financial_results)} results")
                            all_results.extend(financial_results)
                        except Exception as e:
                            frappe.log_error("RAG Debug", f"Financial term search failed: {str(e)}")
                            
                except Exception as e:
                    frappe.log_error("RAG Debug", f"Intent classification failed: {str(e)}")
                    # Fall back to simple detection
                    raise ImportError("Intent classification failed")
                
            except (ImportError, Exception) as e:
                frappe.log_error("RAG Debug", f"Using simplified financial detection: {str(e)}")
                
                # Simplified financial detection using statistics and universal patterns
                query_lower = query.lower()
                
                # Check for universal financial symbols
                financial_symbols = ["$", "€", "¥", "£", "%"]
                is_financial = any(symbol in query_lower for symbol in financial_symbols)
                
                # Check for digits (strong indicator of financial content)
                if not is_financial:
                    import re
                    is_financial = bool(re.search(r'\d', query_lower))
                
                # Use purely statistical approach for detecting financial content
                # This is completely language-agnostic and doesn't rely on specific terms
                if not is_financial:
                    # Check for longer words usually present in financial discussions
                    # Instead of hardcoding terms, look for statistical patterns in the query
                    words = query_lower.split()
                    if words:
                        # Financial queries often have longer words and higher concentration of digits
                        avg_word_len = sum(len(word) for word in words) / len(words)
                        digit_chars = sum(1 for c in query_lower if c.isdigit())
                        digit_ratio = digit_chars / len(query_lower) if len(query_lower) > 0 else 0
                        
                        # High digit ratio or long average word length could indicate financial content
                        is_financial = (digit_ratio > 0.05) or (avg_word_len > 6)
                        
                        if is_financial:
                            frappe.log_error("RAG Debug", f"Statistical financial detection: digit_ratio={digit_ratio}, avg_word_len={avg_word_len}")
                
                if is_financial:
                    frappe.log_error("RAG Debug", "Strategy 3: Targeted financial content search")
                    try:
                        # Create financial terms on-the-fly using query context
                        # Instead of hardcoded terms, create a search pattern based on query characteristics
                        
                        # Universal financial symbols as a base
                        basic_financial_terms = "$ € % ¥ £"
                        
                        # Add number-related terms if query has numbers
                        if re.search(r'\d', query_lower):
                            basic_financial_terms += " value amount total sum number"
                        
                        # Add general payment terms (these appear in most languages)
                        financial_results = self.vector_store.similarity_search_with_relevance_scores(
                            basic_financial_terms, 
                            k=k
                        )
                        frappe.log_error("RAG Debug", f"Financial term search found {len(financial_results)} results")
                        all_results.extend(financial_results)
                    except Exception as e:
                        frappe.log_error("RAG Debug", f"Financial term search failed: {str(e)}")
            
            # Deduplicate results by document content
            seen_content = set()
            unique_results = []
            
            for doc, score in all_results:
                # Use a hash of the content to detect duplicates
                content_hash = hash(doc.page_content)
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append((doc, score))
            
            frappe.log_error("RAG Debug", f"Deduplicated to {len(unique_results)} unique results")
            
            # Sort by relevance score (highest first)
            unique_results.sort(key=lambda x: x[1], reverse=True)
            
            # Limit to requested number
            filtered_results = unique_results[:k]
            
            # Format and enhance results
            formatted_results = []
            for doc, score in filtered_results:
                # Format the content for better readability
                content = doc.page_content.strip()
                
                # Include source information
                source_info = ""
                if "file_name" in doc.metadata:
                    source_info = f"Source: {doc.metadata['file_name']}"
                    if "page" in doc.metadata:
                        source_info += f", Page {doc.metadata['page']}"
                
                # Add the formatted results
                formatted_results.append({
                    "content": content,
                    "metadata": doc.metadata,
                    "score": score,
                    "source": source_info,
                    "keywords": self._extract_keywords(content)  # Extract keywords from content too
                })
            
            # If we find nothing even after trying multiple strategies, try more general search
            if not formatted_results:
                frappe.log_error("RAG Debug", "No results found with specific queries, trying general document search")
                try:
                    # Try to use LLM enhancer for fallback query if available
                    fallback_query = None
                    try:
                        from .rag_llm_enhanced import LLMQueryEnhancer
                        enhancer = LLMQueryEnhancer()
                        fallback_query = enhancer.enhance_query("general document content key information important data")
                        frappe.log_error("RAG Debug", f"Using LLM-enhanced fallback query: {fallback_query}")
                    except Exception:
                        # If LLM enhancement fails, use language-agnostic search vectors
                        pass
                    
                    if not fallback_query:
                        # Use language-agnostic universal symbols and patterns
                        # These should work across languages without specific terms
                        # We rely on vector similarity to find relevant content
                        fallback_query = "* ? ! . , : ; () {} [] <> 1 2 3 $ € % & @ #"
                    
                    # Try a very general search to retrieve any document content
                    general_results = self.vector_store.similarity_search(
                        fallback_query, 
                        k=k
                    )
                    for doc in general_results:
                        source_info = ""
                        if "file_name" in doc.metadata:
                            source_info = f"Source: {doc.metadata['file_name']}"
                            if "page" in doc.metadata:
                                source_info += f", Page {doc.metadata['page']}"
                        
                        formatted_results.append({
                            "content": doc.page_content.strip(),
                            "metadata": doc.metadata,
                            "score": 0.5,  # Default score
                            "source": source_info,
                            "fallback": True  # Mark as fallback result
                        })
                    frappe.log_error("RAG Debug", f"General search found {len(general_results)} results")
                except Exception as e:
                    frappe.log_error("RAG Debug", f"General search failed: {str(e)}")
            
            frappe.log_error("RAG Debug", f"Returning {len(formatted_results)} final results")
            return formatted_results
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error in search: {type(e).__name__}: {str(e)}")
            frappe.log_error("RAG Debug", f"Error details: {str(e)}", exc_info=True)
            # Return empty list on error to not break the flow
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from text, useful for debugging and result enhancement
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List[str]: Extracted keywords
        """
        # Language-agnostic approach - no hardcoded stopwords

        # Convert to lowercase and split
        words = text.lower().split()
        
        # Create a frequency counter for this specific text
        word_freq = {}
        for word in words:
            if word in word_freq:
                word_freq[word] += 1
            else:
                word_freq[word] = 1
        
        # Calculate average and standard deviation of word frequencies
        if not word_freq:
            return []
            
        total_freq = sum(word_freq.values())
        avg_freq = total_freq / len(word_freq)
        
        # Identify potential stopwords based on statistical analysis
        # Words that appear with very high frequency relative to others are likely stopwords
        # Words that are very short are likely stopwords or not meaningful
        potential_stopwords = set()
        for word, freq in word_freq.items():
            if len(word) <= 2:  # Very short words are likely not meaningful
                potential_stopwords.add(word)
            elif freq > 2 * avg_freq and len(word) <= 3:  # High frequency short words
                potential_stopwords.add(word)
        
        # Filter out potential stopwords and short words
        keywords = [word for word in words if len(word) > 2 and word not in potential_stopwords]
        
        # Return unique keywords with higher frequency first
        unique_keywords = list(set(keywords))
        unique_keywords.sort(key=lambda x: word_freq.get(x, 0), reverse=True)
        
        return unique_keywords[:10]  # Limit to 10 keywords


class FAISSRAGProvider(LocalRAGProvider):
    """RAG provider using FAISS"""
    
    def initialize(self):
        """Initialize the vector store and embedding model"""
        try:
            from langchain_community.vectorstores import FAISS
            
            # Check if local embeddings model should be used (from config)
            use_local_embeddings = self.config.get("use_local_embeddings", False)
            
            if use_local_embeddings:
                # Try to use local embeddings models (HuggingFace)
                try:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    
                    # Use a small, efficient model like all-MiniLM-L6-v2
                    model_name = self.config.get("embeddings_model", "all-MiniLM-L6-v2")
                    self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
                    frappe.log_error("RAG", f"Using local HuggingFace embeddings model: {model_name}")
                except ImportError:
                    frappe.log_error("RAG", "Error loading HuggingFace embeddings. Install with: pip install sentence-transformers")
                    frappe.throw("Local embeddings not available. Install with: pip install sentence-transformers")
            else:
                # Use OpenAI embeddings (default)
                from langchain_openai import OpenAIEmbeddings
                
                # Get OpenAI API key from settings
                settings = frappe.get_cached_doc("Raven Settings")
                api_key = settings.get_password("openai_api_key")
                if not api_key:
                    frappe.throw("OpenAI API key is not configured in Raven Settings. Either add an API key or use local embeddings.")
                
                # Set up embedding model with API key
                self.embedding_model = OpenAIEmbeddings(openai_api_key=api_key)
            
            # FAISS doesn't need an initial setup like Chroma
            # It's created when documents are added
            self.vector_store = None
            return True
            
        except ImportError as e:
            frappe.log_error(f"Error initializing FAISS: {e}")
            frappe.throw("FAISS not available. Run 'pip install faiss-cpu langchain-community langchain-openai'")
            
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a file and add it to the vector store
        
        Args:
            file_path: Path to the file
            metadata: Additional metadata for the document
            
        Returns:
            str: Document ID or reference
        """
        try:
            frappe.log_error("RAG Debug", f"Processing file with FAISS: {file_path}")
            
            # Process the file based on its type
            from langchain_community.document_loaders import (
                PyPDFLoader, 
                TextLoader, 
                CSVLoader, 
                UnstructuredExcelLoader,
                UnstructuredPowerPointLoader,
                UnstructuredWordDocumentLoader
            )
            
            # Determine file type and use appropriate loader
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                frappe.log_error("RAG Debug", f"Loading PDF file: {file_path}")
                loader = PyPDFLoader(file_path)
            elif file_extension == '.txt':
                frappe.log_error("RAG Debug", f"Loading text file: {file_path}")
                loader = TextLoader(file_path)
            elif file_extension == '.csv':
                frappe.log_error("RAG Debug", f"Loading CSV file: {file_path}")
                loader = CSVLoader(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                frappe.log_error("RAG Debug", f"Loading Excel file: {file_path}")
                loader = UnstructuredExcelLoader(file_path)
            elif file_extension in ['.pptx', '.ppt']:
                frappe.log_error("RAG Debug", f"Loading PowerPoint file: {file_path}")
                loader = UnstructuredPowerPointLoader(file_path)
            elif file_extension in ['.docx', '.doc']:
                frappe.log_error("RAG Debug", f"Loading Word file: {file_path}")
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                frappe.log_error("RAG Debug", f"Unsupported file type: {file_extension}")
                return f"Unsupported file type: {file_extension}"
                
            # Load the document
            documents = loader.load()
            frappe.log_error("RAG Debug", f"Loaded {len(documents)} documents from file")
            
            # Add metadata if provided
            if metadata:
                for doc in documents:
                    if not hasattr(doc, 'metadata'):
                        doc.metadata = {}
                    doc.metadata.update(metadata)
            
            # For FAISS, we need special handling as it's created when documents are added
            from langchain_community.vectorstores import FAISS
            
            if not self.embedding_model:
                self.initialize()
                
            # Create vector store if it doesn't exist
            if not self.vector_store:
                frappe.log_error("RAG Debug", f"Creating new FAISS vector store")
                self.vector_store = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embedding_model
                )
            else:
                # Add documents to existing vector store
                frappe.log_error("RAG Debug", f"Adding to existing FAISS vector store")
                self.vector_store.add_documents(documents)
                
            # Save the vector store to disk if persist_directory is provided
            persist_directory = self.config.get("persist_directory")
            if persist_directory:
                os.makedirs(persist_directory, exist_ok=True)
                self.vector_store.save_local(persist_directory)
                frappe.log_error("RAG Debug", f"Saved FAISS index to {persist_directory}")
            
            # Generate a unique ID for reference
            import uuid
            doc_id = str(uuid.uuid4())
            
            frappe.log_error("RAG Debug", f"Processed file with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error processing file with FAISS: {type(e).__name__}: {str(e)}")
            raise ValueError(f"Error processing file: {str(e)}")
    
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
            import weaviate
            
            # Check if local embeddings model should be used (from config)
            use_local_embeddings = self.config.get("use_local_embeddings", False)
            
            if use_local_embeddings:
                # Try to use local embeddings models (HuggingFace)
                try:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    
                    # Use a small, efficient model like all-MiniLM-L6-v2
                    model_name = self.config.get("embeddings_model", "all-MiniLM-L6-v2")
                    self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
                    frappe.log_error("RAG", f"Using local HuggingFace embeddings model: {model_name}")
                except ImportError:
                    frappe.log_error("RAG", "Error loading HuggingFace embeddings. Install with: pip install sentence-transformers")
                    frappe.throw("Local embeddings not available. Install with: pip install sentence-transformers")
            else:
                # Use OpenAI embeddings (default)
                from langchain_openai import OpenAIEmbeddings
                
                # Get OpenAI API key from settings
                settings = frappe.get_cached_doc("Raven Settings")
                api_key = settings.get_password("openai_api_key")
                if not api_key:
                    frappe.throw("OpenAI API key is not configured in Raven Settings. Either add an API key or use local embeddings.")
                
                # Set up embedding model with API key
                self.embedding_model = OpenAIEmbeddings(openai_api_key=api_key)
            
            # Get Weaviate connection info from config
            url = self.config.get("url", "http://localhost:8080")
            
            # Set up Weaviate client
            if "api_key" in self.config:
                auth_config = weaviate.AuthApiKey(api_key=self.config["api_key"])
                self.client = weaviate.Client(
                    connection_params=weaviate.ConnectionParams.from_url(url=url),
                    auth_client_secret=auth_config
                )
            else:
                self.client = weaviate.Client(
                    connection_params=weaviate.ConnectionParams.from_url(url=url)
                )
            
            # Get or create class name
            self.class_name = self.config.get("class_name", "RavenDocument")
            
            # Initialize the vector store
            self.vector_store = Weaviate(
                client=self.client,
                index_name=self.class_name,
                text_key="content",
                embedding=self.embedding_model
            )
            return True
            
        except ImportError as e:
            frappe.log_error(f"Error initializing Weaviate: {e}")
            frappe.throw("Weaviate not available. Run 'pip install weaviate-client langchain-community langchain-openai'")
        except Exception as e:
            frappe.log_error(f"Error connecting to Weaviate: {e}")
            frappe.throw(f"Error connecting to Weaviate: {e}")
    
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a file and add it to the vector store
        
        Args:
            file_path: Path to the file
            metadata: Additional metadata for the document
            
        Returns:
            str: Document ID or reference
        """
        try:
            frappe.log_error("RAG Debug", f"Processing file with Weaviate: {file_path}")
            
            # Ensure the vector store is initialized
            if not hasattr(self, "vector_store") or not self.vector_store:
                self.initialize()
                
            # Process the file based on its type
            from langchain_community.document_loaders import (
                PyPDFLoader, 
                TextLoader, 
                CSVLoader, 
                UnstructuredExcelLoader,
                UnstructuredPowerPointLoader,
                UnstructuredWordDocumentLoader
            )
            
            # Determine file type and use appropriate loader
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                frappe.log_error("RAG Debug", f"Loading PDF file: {file_path}")
                loader = PyPDFLoader(file_path)
            elif file_extension == '.txt':
                frappe.log_error("RAG Debug", f"Loading text file: {file_path}")
                loader = TextLoader(file_path)
            elif file_extension == '.csv':
                frappe.log_error("RAG Debug", f"Loading CSV file: {file_path}")
                loader = CSVLoader(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                frappe.log_error("RAG Debug", f"Loading Excel file: {file_path}")
                loader = UnstructuredExcelLoader(file_path)
            elif file_extension in ['.pptx', '.ppt']:
                frappe.log_error("RAG Debug", f"Loading PowerPoint file: {file_path}")
                loader = UnstructuredPowerPointLoader(file_path)
            elif file_extension in ['.docx', '.doc']:
                frappe.log_error("RAG Debug", f"Loading Word file: {file_path}")
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                frappe.log_error("RAG Debug", f"Unsupported file type: {file_extension}")
                return f"Unsupported file type: {file_extension}"
                
            # Load the document
            documents = loader.load()
            frappe.log_error("RAG Debug", f"Loaded {len(documents)} documents from file")
            
            # Add metadata if provided
            if metadata:
                for doc in documents:
                    if not hasattr(doc, 'metadata'):
                        doc.metadata = {}
                    doc.metadata.update(metadata)
            
            # Add documents to Weaviate
            self.vector_store.add_documents(documents)
            frappe.log_error("RAG Debug", f"Added documents to Weaviate vector store")
            
            # Generate a unique ID for reference
            import uuid
            doc_id = str(uuid.uuid4())
            
            frappe.log_error("RAG Debug", f"Processed file with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error processing file with Weaviate: {type(e).__name__}: {str(e)}")
            raise ValueError(f"Error processing file: {str(e)}")
    
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
    # Log tool creation attempt
    frappe.log_error("RAG Debug", f"Creating local file search tool for bot: {bot.name if bot else 'None'}")
    
    # Define async handler for the tool invocation
    async def on_invoke_tool(ctx, args_json: str) -> str:
        frappe.log_error("RAG Debug", f"File search tool invoked with args: {args_json}")
        
        try:
            # Parse arguments from JSON
            args_dict = json.loads(args_json)
            
            # Extract parameters
            original_query = args_dict.get("query", "")
            max_results = args_dict.get("max_results", 5)
            
            # Process the query to make it more effective for RAG
            enhanced_query = _enhance_search_query(original_query, ctx)
            frappe.log_error("RAG Debug", f"Original query: '{original_query}', Enhanced query: '{enhanced_query}'")
            
            # Call the search function with enhanced query
            result = local_file_search(enhanced_query, max_results)
            
            # Enhance result with original query for LLM context
            if result.get("success", False):
                result["original_query"] = original_query
                result["enhanced_query"] = enhanced_query
                # Add guide for the LLM
                result["guide_for_llm"] = (
                    "Important: Do not say 'I can't access the PDF'. You have access to the content through the search results. "
                    "Use the information from the returned chunks to answer the user's question. "
                    "Reference the source document when appropriate."
                )
            
            # Return result as JSON string
            return json.dumps(result)
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error in file search on_invoke_tool: {str(e)}")
            return json.dumps({"error": str(e)})
    
    # Create a function tool for local file search
    tool = FunctionTool(
        name="file_search",
        description="Search for information in uploaded files and documents. Use this tool when the user asks about PDFs, documents, or uploaded files.",
        params_json_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query - if the user is asking about a PDF or document, formulate a query to extract relevant content."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        },
        on_invoke_tool=on_invoke_tool
    )
    
    frappe.log_error("RAG Debug", f"Successfully created file search tool")
    return tool

def _enhance_search_query(query: str, ctx) -> str:
    """
    Enhance the search query to be more effective for retrieving document content
    
    Args:
        query: The original user query
        ctx: The conversation context from the agent
    
    Returns:
        str: An enhanced version of the query
    """
    frappe.log_error("RAG Debug", f"Enhancing query with legacy method: '{query}'")
    
    # Check if we can use the LLM enhancer
    try:
        from .rag_llm_enhanced import LLMQueryEnhancer
        
        # Get bot configuration from context if available
        bot_config = None
        if ctx and hasattr(ctx, 'bot'):
            bot_config = ctx.bot
        
        enhancer = LLMQueryEnhancer(bot_config)
        enhanced_query = enhancer.enhance_query(query)
        frappe.log_error("RAG Debug", f"Using LLM enhancer: '{enhanced_query}'")
        return enhanced_query
    except (ImportError, Exception) as e:
        frappe.log_error("RAG Debug", f"LLM enhancer unavailable, falling back to basic enhancement: {str(e)}")
        pass
    
    # If LLM enhancement fails, use a very basic fallback that is language-agnostic
    # This approach avoids hardcoding language-specific terms
    
    # Simple statistical keyword extraction
    words = query.lower().split()
    
    # Filter out very short words (likely articles, prepositions in most languages)
    keywords = [word for word in words if len(word) > 2]
    
    if not keywords:
        # If no meaningful keywords found, return original query
        return query
    
    # Prioritize longer words as they tend to carry more meaning
    keywords.sort(key=len, reverse=True)
    
    # For very short queries, use the original to preserve context
    if len(query) < 10:
        return query
        
    # Join the top keywords
    enhanced_query = " ".join(keywords[:5])  # Limit to 5 most meaningful words
    
    # Add context terms for documents if the query mentions files
    doc_indicators = ["pdf", "doc", "xlsx", "file"]
    for indicator in doc_indicators:
        if indicator in query.lower():
            enhanced_query += " document content information"
            break
    
    # Add numerical indicators if they exist in the query (often financial)
    import re
    if re.search(r'\d', query):
        enhanced_query += " amount total sum"
    
    frappe.log_error("RAG Debug", f"Basic enhanced query: '{enhanced_query}'")
    return enhanced_query


def local_file_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search for information in files
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        Dict[str, Any]: Search results
    """
    frappe.log_error("RAG Debug", f"File search called with query: '{query}', max_results: {max_results}")
    
    # Get current bot from context
    bot_name = frappe.flags.get("raven_current_bot")
    if not bot_name:
        frappe.log_error("RAG Debug", "No bot context found in frappe.flags")
        return {
            "success": False,
            "error": "No bot context found"
        }
    
    frappe.log_error("RAG Debug", f"Got bot name from context: {bot_name}")
    
    try:
        bot = frappe.get_doc("Raven Bot", bot_name)
        frappe.log_error("RAG Debug", f"Retrieved bot document: {bot.name}")
        
        # Get the RAG provider from bot settings
        provider_type = bot.local_rag_provider
        frappe.log_error("RAG Debug", f"Using provider type: {provider_type}")
        
        # Create proper config from bot settings
        config = {
            "model_provider": bot.model_provider,
            "enable_file_search": bot.enable_file_search,
            "enable_local_rag": bot.enable_local_rag,
            "local_rag_provider": bot.local_rag_provider,
            "use_local_embeddings": getattr(bot, "use_local_embeddings", True),
            "embeddings_model": getattr(bot, "embeddings_model", "all-MiniLM-L6-v2")
        }
        
        # Log the config for debugging
        frappe.log_error("RAG Debug", f"Creating provider for search with config: {config}")
        
        # Create provider
        try:
            provider = LocalRAGProvider.create(provider_type, config)
            frappe.log_error("RAG Debug", f"Created provider of type: {type(provider).__name__}")
            
            # Initialize provider
            init_result = provider.initialize()
            frappe.log_error("RAG Debug", f"Provider initialization result: {init_result}")
            
            # Search
            results = provider.search(query, k=max_results)
            frappe.log_error("RAG Debug", f"Search returned {len(results)} results")
            
            # If no results found, return clear message
            if not results:
                frappe.log_error("RAG Debug", "No results found for query")
                return {
                    "success": True,
                    "results": [],
                    "message": "No relevant information found in the available documents."
                }
            
            # Format results for better LLM consumption
            formatted_results = []
            
            for i, result in enumerate(results, 1):
                content = result.get("content", "").strip()
                source_info = result.get("source", "")
                score = result.get("score", 0)
                
                formatted_result = {
                    "content": content,
                    "source": source_info,
                    "relevance_score": f"{score:.2f}"
                }
                
                # Add metadata selectively (don't include everything)
                meta = result.get("metadata", {})
                if meta:
                    important_meta = {}
                    for key in ["file_name", "page", "chunk", "file_extension"]:
                        if key in meta:
                            important_meta[key] = meta[key]
                    
                    if important_meta:
                        formatted_result["metadata"] = important_meta
                
                formatted_results.append(formatted_result)
            
            frappe.log_error("RAG Debug", f"Returning {len(formatted_results)} formatted results")
            
            # Create a meaningful response
            return {
                "success": True,
                "results": formatted_results,
                "message": f"Found {len(formatted_results)} relevant document sections. Review these to answer the query."
            }
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error in search process: {type(e).__name__}: {str(e)}")
            frappe.log_error("RAG Debug", f"Error details: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error searching documents: {str(e)}",
                "error_type": type(e).__name__
            }
            
    except Exception as e:
        frappe.log_error("RAG Debug", f"Error in local_file_search setup: {type(e).__name__}: {str(e)}")
        frappe.log_error("RAG Debug", f"Error details: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Error in file search: {str(e)}",
            "error_type": type(e).__name__
        }