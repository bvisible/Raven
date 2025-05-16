# raven/ai/file_manager.py
from typing import Dict

class FileManager:
    def __init__(self, bot_doc):
        self.bot_doc = bot_doc
        self.use_local_rag = bot_doc.use_local_rag
        self.model_provider = bot_doc.model_provider
    
    async def process_file(self, file_path: str, metadata: Dict = None):
        """Process a file according to the bot's configuration"""
        if self.use_local_rag:
            # Index locally with RAG
            from ..rag.indexer import RavenDocumentIndexer
            indexer = RavenDocumentIndexer()
            await indexer.index_document(file_path, self.bot_doc.name)
        elif self.model_provider == "openai":
            # Upload to OpenAI Vector Store (temporary, will be removed)
            await self._upload_to_openai_vector_store(file_path)
        else:
            # For other providers, use RAG by default
            from ..rag.indexer import RavenDocumentIndexer
            indexer = RavenDocumentIndexer()
            await indexer.index_document(file_path, self.bot_doc.name)
    
    async def _upload_to_openai_vector_store(self, file_path: str):
        """Upload a file to OpenAI Vector Store"""
        from .openai_client import get_client_for_bot
        
        client = get_client_for_bot(self.bot_doc.name)
        
        # Check if the bot has a vector store
        if not self.bot_doc.openai_vector_store_id:
            # Create a new vector store
            vector_store = await client.beta.vector_stores.create(
                name=f"{self.bot_doc.bot_name} - Vector Store"
            )
            self.bot_doc.openai_vector_store_id = vector_store.id
            self.bot_doc.save(ignore_permissions=True)
        
        # Upload the file
        with open(file_path, "rb") as file:
            file_response = await client.files.create(
                file=file,
                purpose="assistants"
            )
        
        # Attach the file to the vector store
        await client.beta.vector_stores.files.create(
            vector_store_id=self.bot_doc.openai_vector_store_id,
            file_id=file_response.id
        )
    
    async def retrieve_context(self, query: str):
        """Retrieve relevant context for a query"""
        if self.use_local_rag:
            from ..rag.retriever import RavenRAGRetriever
            retriever = RavenRAGRetriever(self.bot_doc.rag_settings)
            return await retriever.retrieve_context(query)
        elif self.model_provider == "openai" and self.bot_doc.openai_vector_store_id:
            # Use OpenAI Vector Store search
            from .openai_client import get_client_for_bot
            client = get_client_for_bot(self.bot_doc.name)
            
            # Note: This API might change with the Agents SDK
            results = await client.beta.vector_stores.files.search(
                vector_store_id=self.bot_doc.openai_vector_store_id,
                query=query
            )
            return results
        else:
            return []