# raven/ai/rag/indexer.py
import frappe
import json
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
import os

class RavenDocumentIndexer:
    """Document indexing manager for the RAG system"""
    
    def __init__(self):
        self.chunk_size = 1000  # Default chunk size
        self.overlap = 200  # Overlap between chunks
    
    async def index_document(self, file_path: str, bot_name: str, metadata: Dict = None):
        """Index a document for the RAG system"""
        if not os.path.exists(file_path):
            frappe.throw(f"File not found: {file_path}")
        
        # Read file content
        content = self._read_file(file_path)
        
        # Split content into chunks
        chunks = self._chunk_content(content, bot_name)
        
        # Generate embeddings for each chunk
        embeddings = await self._generate_embeddings(chunks)
        
        # Store in database
        await self._store_embeddings(
            chunks=chunks,
            embeddings=embeddings,
            file_path=file_path,
            bot_name=bot_name,
            metadata=metadata
        )
    
    def _read_file(self, file_path: str) -> str:
        """Read file content"""
        # Determine file type and use the right reader
        if file_path.endswith('.pdf'):
            return self._read_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self._read_docx(file_path)
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Try to read as text by default
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                frappe.throw(f"Unable to read file: {e}")
    
    def _read_pdf(self, file_path: str) -> str:
        """Read a PDF file"""
        try:
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            
            return text
        except ImportError:
            frappe.throw("PyPDF2 is required to read PDF files. Please install it: pip install PyPDF2")
    
    def _read_docx(self, file_path: str) -> str:
        """Read a DOCX file"""
        try:
            import docx
            
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            
            return '\n'.join(text)
        except ImportError:
            frappe.throw("python-docx is required to read DOCX files. Please install it: pip install python-docx")
    
    def _chunk_content(self, content: str, bot_name: str) -> List[Dict]:
        """Split content into chunks with metadata"""
        chunks = []
        bot_doc = frappe.get_doc("Raven Bot", bot_name)
        
        # Get chunk size from bot's RAG settings
        rag_settings = bot_doc.rag_settings or {}
        chunk_size = rag_settings.get("chunk_size", self.chunk_size)
        
        # Split text
        words = content.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 pour l'espace
            
            if current_size >= chunk_size:
                chunk_text = ' '.join(current_chunk)
                
                # Generate a unique ID for the chunk
                chunk_id = hashlib.md5(chunk_text.encode()).hexdigest()
                
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "bot_name": bot_name,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Start next chunk with overlap
                overlap_words = int(self.overlap / 5)  # Approximation des mots
                current_chunk = current_chunk[-overlap_words:]
                current_size = sum(len(word) + 1 for word in current_chunk)
        
        # Add the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = hashlib.md5(chunk_text.encode()).hexdigest()
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "bot_name": bot_name,
                "timestamp": datetime.now().isoformat()
            })
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[Dict]) -> List[List[float]]:
        """Generate embeddings for chunks"""
        from ..agent_manager import RavenAgentManager
        
        # Get the appropriate client for this bot
        if not chunks:
            return []
        
        bot_name = chunks[0]["bot_name"]
        manager = RavenAgentManager()
        client = manager.get_client_for_bot(bot_name)
        
        embeddings = []
        for chunk in chunks:
            try:
                # Use the client's embeddings API
                response = await client.embeddings.create(
                    model="text-embedding-ada-002",  # Modèle par défaut
                    input=chunk["text"]
                )
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                frappe.log_error(f"Error generating embedding: {e}")
                # Use an empty vector in case of error
                embeddings.append([0.0] * 1536)  # Dimension par défaut
        
        return embeddings
    
    async def _store_embeddings(self, chunks: List[Dict], embeddings: List[List[float]], 
                               file_path: str, bot_name: str, metadata: Dict = None):
        """Store embeddings in the database"""
        for chunk, embedding in zip(chunks, embeddings):
            # Create a new RavenDocumentEmbedding document
            doc = frappe.new_doc("Raven Document Embedding")
            doc.bot_name = bot_name
            doc.chunk_id = chunk["id"]
            doc.chunk_text = chunk["text"]
            doc.file_path = file_path
            doc.embedding = json.dumps(embedding)
            doc.metadata = json.dumps(metadata or {})
            doc.created_at = chunk["timestamp"]
            
            # Save
            doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
    
    async def delete_embeddings_for_file(self, file_path: str, bot_name: str):
        """Delete all embeddings associated with a file"""
        frappe.db.delete(
            "Raven Document Embedding",
            {
                "file_path": file_path,
                "bot_name": bot_name
            }
        )
        frappe.db.commit()