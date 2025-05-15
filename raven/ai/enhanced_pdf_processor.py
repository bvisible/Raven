"""
Processeur PDF amélioré utilisant PyMuPDF4LLM
pour une meilleure extraction de texte des PDFs
"""

import frappe
import os
import json
from typing import Dict, Any, List, Optional

# Essayer d'importer PyMuPDF4LLM
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False
    frappe.log_error("RAG PDF", "PyMuPDF4LLM not available. Install with: pip install pymupdf4llm")

class EnhancedPDFProcessor:
    """
    Processeur PDF amélioré qui utilise PyMuPDF4LLM si disponible,
    sinon revient à la méthode standard
    """
    
    def __init__(self):
        self.use_pymupdf4llm = PYMUPDF4LLM_AVAILABLE
        
    def process_pdf(self, file_path: str, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Traite un fichier PDF et retourne des chunks de texte
        
        Args:
            file_path: Chemin vers le fichier PDF
            chunk_size: Taille des chunks (nombre de caractères)
            
        Returns:
            List[Dict[str, Any]]: Liste de documents avec contenu et métadonnées
        """
        if self.use_pymupdf4llm:
            return self._process_with_pymupdf4llm(file_path, chunk_size)
        else:
            return self._process_with_standard_method(file_path, chunk_size)
            
    def _process_with_pymupdf4llm(self, file_path: str, chunk_size: int) -> List[Dict[str, Any]]:
        """
        Utilise PyMuPDF4LLM pour une extraction avancée
        """
        try:
            frappe.log_error("RAG PDF", f"Processing PDF with PyMuPDF4LLM: {file_path}")
            
            # Extraire le texte en Markdown avec des chunks par page
            pages_data = pymupdf4llm.to_markdown(
                file_path,
                page_chunks=True,  # Obtenir des chunks par page
                write_images=False  # Pour l'instant, pas d'extraction d'images
            )
            
            documents = []
            
            for page_num, page_data in enumerate(pages_data):
                # page_data est un dictionnaire avec 'metadata' et 'text'
                page_text = page_data.get('text', '')
                page_metadata = page_data.get('metadata', {})
                
                # Diviser le texte de la page en chunks plus petits si nécessaire
                chunks = self._split_text_into_chunks(page_text, chunk_size)
                
                for chunk_num, chunk_text in enumerate(chunks):
                    doc = {
                        'content': chunk_text,
                        'metadata': {
                            'page': page_num + 1,
                            'chunk': chunk_num + 1,
                            'source': 'pymupdf4llm',
                            'file_path': file_path,
                            'file_name': os.path.basename(file_path),
                            **page_metadata  # Ajouter les métadonnées de la page
                        }
                    }
                    documents.append(doc)
            
            frappe.log_error("RAG PDF", f"Extracted {len(documents)} chunks from PDF")
            return documents
            
        except Exception as e:
            frappe.log_error("RAG PDF", f"Error with PyMuPDF4LLM: {str(e)}")
            # Fallback à la méthode standard
            return self._process_with_standard_method(file_path, chunk_size)
            
    def _process_with_standard_method(self, file_path: str, chunk_size: int) -> List[Dict[str, Any]]:
        """
        Utilise la méthode standard (PyPDFLoader de langchain)
        """
        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            frappe.log_error("RAG PDF", f"Processing PDF with standard method: {file_path}")
            
            # Charger le PDF
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            
            # Créer un text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=200,
                length_function=len
            )
            
            documents = []
            for page_num, page in enumerate(pages):
                # Diviser la page en chunks
                chunks = text_splitter.split_documents([page])
                
                for chunk_num, chunk in enumerate(chunks):
                    doc = {
                        'content': chunk.page_content,
                        'metadata': {
                            'page': page_num + 1,
                            'chunk': chunk_num + 1,
                            'source': 'pypdfloader',
                            'file_path': file_path,
                            'file_name': os.path.basename(file_path),
                            **chunk.metadata
                        }
                    }
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            frappe.log_error("RAG PDF", f"Error with standard method: {str(e)}")
            raise
            
    def _split_text_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """
        Divise un texte en chunks de taille maximale
        """
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        current_chunk = ""
        sentences = text.split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk + ".")
                current_chunk = sentence
                
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

# Fonction utilitaire pour intégrer dans le système existant
def enhance_pdf_processing():
    """
    Monkey patch pour améliorer le traitement des PDFs dans local_rag.py
    """
    if not PYMUPDF4LLM_AVAILABLE:
        frappe.log_error("RAG PDF", "PyMuPDF4LLM not available, PDF processing not enhanced")
        return
        
    try:
        from . import local_rag
        
        # Sauvegarder la méthode originale
        original_process_file = local_rag.ChromaRAGProvider.process_file
        
        # Créer le processeur amélioré
        enhanced_processor = EnhancedPDFProcessor()
        
        def enhanced_process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
            """Méthode améliorée qui utilise PyMuPDF4LLM pour les PDFs"""
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf' and enhanced_processor.use_pymupdf4llm:
                frappe.log_error("RAG PDF", f"Using enhanced PDF processor for: {file_path}")
                
                try:
                    # Utiliser le processeur amélioré
                    documents = enhanced_processor.process_pdf(file_path)
                    
                    # Ajouter les métadonnées supplémentaires
                    if metadata:
                        for doc in documents:
                            doc['metadata'].update(metadata)
                    
                    # Ajouter les documents au vector store
                    if hasattr(self, 'vector_store') and self.vector_store:
                        # Convertir en format compatible avec langchain
                        from langchain.schema import Document
                        langchain_docs = []
                        for doc in documents:
                            langchain_doc = Document(
                                page_content=doc['content'],
                                metadata=doc['metadata']
                            )
                            langchain_docs.append(langchain_doc)
                        
                        # Ajouter au vector store
                        self.vector_store.add_documents(langchain_docs)
                        
                        # Génerer un ID unique
                        import uuid
                        doc_id = str(uuid.uuid4())
                        
                        frappe.log_error("RAG PDF", f"Enhanced PDF processing completed with ID: {doc_id}")
                        return doc_id
                    else:
                        raise ValueError("Vector store not initialized")
                        
                except Exception as e:
                    frappe.log_error("RAG PDF", f"Enhanced processing failed, falling back: {str(e)}")
                    # Fallback à la méthode originale
                    return original_process_file(self, file_path, metadata)
            
            # Pour tous les autres fichiers, utiliser la méthode originale
            return original_process_file(self, file_path, metadata)
        
        # Remplacer la méthode dans toutes les classes de provider
        local_rag.ChromaRAGProvider.process_file = enhanced_process_file
        if hasattr(local_rag, 'FAISSRAGProvider'):
            local_rag.FAISSRAGProvider.process_file = enhanced_process_file
        if hasattr(local_rag, 'WeaviateRAGProvider'):
            local_rag.WeaviateRAGProvider.process_file = enhanced_process_file
            
        frappe.log_error("RAG PDF", "PDF processing enhancement installed successfully")
        
    except Exception as e:
        frappe.log_error("RAG PDF", f"Failed to enhance PDF processing: {str(e)}")