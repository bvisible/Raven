# raven/ai/agent_handler.py
import json
import frappe
from typing import Dict, Any
import sys
import os

# Add the agents SDK to Python path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
agents_path = os.path.join(base_dir, 'openai-agents-python-0.0.14', 'src')
if agents_path not in sys.path:
    sys.path.insert(0, agents_path)

from agents import StreamEvent
from agents.exceptions import AgentsException
from .agent_manager import RavenAgentManager
from .openai_client import get_open_ai_client


async def process_message_with_agent(
    message: str,
    bot,
    channel_id: str,
    ai_thread_id: str = None,
    context: Dict = None
):
    """Process a message using the new agent system"""
    
    manager = RavenAgentManager()
    
    # Context variables
    run_context = context or {}
    run_context["channel_id"] = channel_id
    run_context["thread_id"] = ai_thread_id
    run_context["bot"] = bot
    run_context["docs_updated"] = []
    
    # Publish a starting event
    publish_ai_event("Raven AI is processing...", channel_id, bot.name)
    
    try:
        # Create or retrieve the agent
        agent = manager.create_agent_from_bot(bot)
        
        # Handle attached documentation if RAG is enabled
        if bot.use_local_rag and bot.enable_file_search:
            from .rag.retriever import RavenRAGRetriever
            retriever = RavenRAGRetriever(bot.rag_settings or {})
            relevant_docs = await retriever.retrieve_context(message, bot.name)
            
            if relevant_docs:
                context_text = "\n\n".join([doc["text"] for doc in relevant_docs[:3]])
                message = f"Context from documents:\n{context_text}\n\nUser query: {message}"
        
        # Stream the response
        async for event in manager.stream_response(
            agent_name=bot.name,
            message=message,
            context=run_context
        ):
            handle_stream_event(event, channel_id, bot, run_context)
            
    except Exception as e:
        frappe.log_error(f"Error in agent processing: {e}")
        error_message = str(e) if bot.debug_mode else "An error occurred while processing your request."
        bot.send_message(
            channel_id=channel_id,
            text=error_message,
            markdown=True
        )
    finally:
        # Clean up the AI event
        frappe.publish_realtime(
            "ai_event_clear",
            {"channel_id": channel_id},
            doctype="Raven Channel",
            docname=channel_id,
            after_commit=True
        )


def handle_stream_event(event: StreamEvent, channel_id: str, bot, context: Dict):
    """Handle agent stream events"""
    
    if event.type == "error":
        # Handle errors
        error_text = event.message if hasattr(event, 'message') else str(event)
        if bot.debug_mode:
            bot.send_message(
                channel_id=channel_id,
                text=f"Error: {error_text}",
                markdown=True
            )
        else:
            publish_ai_event("An error occurred", channel_id, bot.name)
    
    elif event.type == "message":
        # Normal text message
        if event.content:
            bot.send_message(
                channel_id=channel_id,
                text=event.content,
                markdown=True,
                link_doctype=get_link_doctype(context),
                link_document=get_link_document(context)
            )
    
    elif event.type == "tool_use":
        # Tool usage
        publish_ai_event(f"Using tool: {event.tool_name}", channel_id, bot.name)
        
        # If the tool updates documents, add it to the context
        if event.tool_name in ["create_document", "update_document", "delete_document"]:
            if event.result and isinstance(event.result, dict):
                context["docs_updated"].append({
                    "doctype": event.result.get("doctype"),
                    "document_id": event.result.get("name")
                })
    
    elif event.type == "status":
        # Status message
        publish_ai_event(event.message, channel_id, bot.name)


def publish_ai_event(text: str, channel_id: str, bot_name: str):
    """Publish an AI event in real time"""
    frappe.publish_realtime(
        "ai_event",
        {
            "text": text,
            "channel_id": channel_id,
            "bot": bot_name,
        },
        doctype="Raven Channel",
        docname=channel_id,
    )


def get_link_doctype(context: Dict) -> str:
    """Get the link doctype if only one document was updated"""
    docs_updated = context.get("docs_updated", [])
    if len(docs_updated) == 1:
        return docs_updated[0]["doctype"]
    return None


def get_link_document(context: Dict) -> str:
    """Get the document ID if only one document was updated"""
    docs_updated = context.get("docs_updated", [])
    if len(docs_updated) == 1:
        return docs_updated[0]["document_id"]
    return None


def get_variables_for_instructions():
    """Get variables for dynamic instructions"""
    # Existing function to keep
    import frappe
    from frappe.utils import get_fullname
    
    return {
        "user": frappe.session.user,
        "full_name": get_fullname(frappe.session.user),
        "role": frappe.get_roles(frappe.session.user),
        "company": frappe.defaults.get_user_default("Company"),
        "date": frappe.utils.nowdate(),
        "time": frappe.utils.nowtime(),
        "datetime": frappe.utils.now_datetime(),
        "year": frappe.utils.nowdate()[:4],
        "month": frappe.utils.nowdate()[5:7],
        "day": frappe.utils.nowdate()[8:10],
    }