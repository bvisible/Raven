# raven/ai/migration_helper.py
"""
Migration module to switch from the Assistant API to the Agent SDK
"""
import frappe
from typing import Optional


def migrate_assistant_to_agent(bot_name: str) -> bool:
    """
    Migrate a bot from the Assistant API to the Agent SDK
    
    Args:
        bot_name: Name of the bot to migrate
        
    Returns:
        bool: True if the migration is successful
    """
    try:
        bot = frappe.get_doc("Raven Bot", bot_name)
        
        # If the bot doesn't have a model_provider, set it
        if not bot.model_provider:
            bot.model_provider = "openai" if bot.openai_assistant_id else "local"
        
        # If it's an OpenAI bot with assistant ID, migrate
        if bot.openai_assistant_id:
            # Get assistant parameters
            from .openai_client import get_open_ai_client
            client = get_open_ai_client()
            
            try:
                assistant = client.beta.assistants.retrieve(bot.openai_assistant_id)
                
                # Migrate parameters
                if not bot.model:
                    bot.model = assistant.model
                
                if not bot.instruction:
                    bot.instruction = assistant.instructions
                
                # Migrate tools
                if assistant.tools:
                    for tool in assistant.tools:
                        if tool.type == "file_search":
                            bot.enable_file_search = 1
                        elif tool.type == "code_interpreter":
                            bot.enable_code_interpreter = 1
                
                # If the bot has a vector store
                if hasattr(assistant, 'tool_resources') and assistant.tool_resources.get('file_search'):
                    vector_store_id = assistant.tool_resources['file_search']['vector_store_ids'][0]
                    bot.openai_vector_store_id = vector_store_id
                    
                    # Migration option to RAG
                    if frappe.db.get_single_value("Raven Settings", "enable_local_llm"):
                        bot.use_local_rag = 1
                        # Migrate files from vector store to local RAG
                        migrate_vector_store_to_rag(bot_name, vector_store_id)
                
            except Exception as e:
                frappe.log_error(f"Error migrating assistant {bot.openai_assistant_id}: {e}")
        
        # Save changes
        bot.save(ignore_permissions=True)
        frappe.db.commit()
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error migrating bot {bot_name}: {e}")
        return False


def migrate_vector_store_to_rag(bot_name: str, vector_store_id: str):
    """
    Migrate files from an OpenAI Vector Store to the local RAG system
    """
    try:
        from .openai_client import get_open_ai_client
        from .rag.indexer import RavenDocumentIndexer
        
        client = get_open_ai_client()
        indexer = RavenDocumentIndexer()
        
        # List files in the vector store
        files = client.beta.vector_stores.files.list(vector_store_id)
        
        for file in files:
            try:
                # Download file content
                file_content = client.files.content(file.id)
                
                # Create a temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
                    tmp_file.write(file_content.read())
                    tmp_file_path = tmp_file.name
                
                # Index in the RAG system
                import asyncio
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    indexer.index_document(tmp_file_path, bot_name, {
                        "original_file_id": file.id,
                        "migrated_from": "openai_vector_store"
                    })
                )
                
                # Delete the temporary file
                import os
                os.unlink(tmp_file_path)
                
            except Exception as e:
                frappe.log_error(f"Error migrating file {file.id}: {e}")
                
    except Exception as e:
        frappe.log_error(f"Error migrating vector store {vector_store_id}: {e}")


def migrate_all_bots():
    """
    Migrate all AI bots to the new system
    """
    bots = frappe.get_all(
        "Raven Bot",
        filters={"is_ai_bot": 1},
        fields=["name"]
    )
    
    success_count = 0
    for bot in bots:
        if migrate_assistant_to_agent(bot.name):
            success_count += 1
    
    frappe.msgprint(f"Migration completed: {success_count}/{len(bots)} bots migrated successfully")
    return success_count


def is_bot_migrated(bot_name: str) -> bool:
    """
    Check if a bot has been migrated to the new system
    """
    bot = frappe.get_doc("Raven Bot", bot_name)
    return bool(bot.model_provider)


def use_legacy_system(bot_name: str) -> bool:
    """
    Determine if the legacy system should be used for a bot
    
    Returns:
        True if the legacy system should be used
        False if the new system Agent SDK should be used
    """
    bot = frappe.get_doc("Raven Bot", bot_name)
    
    # If the bot has a model_provider, it has been migrated
    if bot.model_provider:
        return False
    
    # If the bot has an assistant ID but no provider, use the legacy system
    if bot.openai_assistant_id and not bot.model_provider:
        return True
    
    # By default, use the new system
    return False