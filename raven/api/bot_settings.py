# raven/api/bot_settings.py
import frappe
from typing import List, Dict
import httpx

@frappe.whitelist()
def get_available_models_for_bot(bot_name: str):
    """Obtain the models available for a bot according to its provider"""
    bot_doc = frappe.get_doc("Raven Bot", bot_name)
    settings = frappe.get_doc("Raven Settings")
    
    if bot_doc.model_provider == "openai":
        return ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"]
    elif bot_doc.model_provider == "local":
        # Return models according to the local provider configured
        provider = settings.local_llm_provider
        if provider == "Ollama":
            # Call API Ollama to list models
            try:
                response = httpx.get(f"{settings.local_llm_api_url.replace('/v1', '')}/api/tags")
                return [m["name"] for m in response.json()["models"]]
            except Exception as e:
                frappe.log_error(f"Error fetching Ollama models: {e}")
                return ["default", "llama3", "mistral", "codellama"]
        else:
            # For LM Studio and LocalAI, return suggestions
            return ["default", "llama3", "mistral", "codellama", "mixtral", "deepseek"]

@frappe.whitelist()
def test_bot_connection(bot_name: str):
    """Test the connection for a specific bot"""
    from ..ai.agent_manager import RavenAgentManager
    
    bot_doc = frappe.get_doc("Raven Bot", bot_name)
    manager = RavenAgentManager()
    
    try:
        client = manager._get_client_for_bot(bot_doc)
        # Simple test of connection
        response = client.chat.completions.create(
            model="gpt-3.5-turbo" if bot_doc.model_provider == "openai" else "default",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        return {"status": "success", "provider": bot_doc.model_provider}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def upload_file_to_bot(bot_name: str, file_path: str):
    """Upload a file to the bot's file system (RAG or Vector Store)"""
    from ..ai.file_manager import FileManager
    
    bot_doc = frappe.get_doc("Raven Bot", bot_name)
    file_manager = FileManager(bot_doc)
    
    try:
        # Asynchronous process
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(file_manager.process_file(file_path))
        
        return {"status": "success", "message": "File uploaded successfully"}
    except Exception as e:
        frappe.log_error(f"Error uploading file: {e}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def search_bot_documents(bot_name: str, query: str):
    """Search in the bot's documents using RAG"""
    from ..ai.rag.retriever import RavenRAGRetriever
    
    bot_doc = frappe.get_doc("Raven Bot", bot_name)
    
    if not bot_doc.use_local_rag:
        return {"error": "RAG is not enabled for this bot"}
    
    try:
        retriever = RavenRAGRetriever(bot_doc.rag_settings or {})
        
        # Asynchronous search
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(retriever.retrieve_context(query, bot_name))
        
        return {"status": "success", "results": results}
    except Exception as e:
        frappe.log_error(f"Error searching documents: {e}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_bot_rag_statistics(bot_name: str):
    """Get RAG statistics for a bot"""
    # Count embeddings
    embedding_count = frappe.db.count(
        "Raven Document Embedding",
        filters={"bot_name": bot_name}
    )
    
    # Get unique files
    files = frappe.db.get_all(
        "Raven Document Embedding",
        filters={"bot_name": bot_name},
        fields=["file_path"],
        distinct=True
    )
    
    # Calculate total size of chunks
    total_size = frappe.db.sql("""
        SELECT SUM(LENGTH(chunk_text)) 
        FROM `tabRaven Document Embedding`
        WHERE bot_name = %s
    """, bot_name)[0][0] or 0
    
    return {
        "embedding_count": embedding_count,
        "file_count": len(files),
        "total_text_size": total_size,
        "files": [f["file_path"] for f in files]
    }

@frappe.whitelist()
def clear_bot_embeddings(bot_name: str):
    """Delete all embeddings for a bot"""
    if not frappe.has_permission("Raven Bot", "delete"):
        frappe.throw("Permission denied")
    
    frappe.db.delete(
        "Raven Document Embedding",
        {"bot_name": bot_name}
    )
    frappe.db.commit()
    
    return {"status": "success", "message": "All embeddings cleared"}