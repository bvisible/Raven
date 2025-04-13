import json
import frappe
import asyncio
from typing import Dict, Any, List, Optional

from .sdk_agents import RavenAgentManager
from .handler import get_instructions, get_variables_for_instructions


async def handle_message(bot, channel_id: str, message: str, files: List[Dict] = None) -> Dict[str, Any]:
    """
    Handle a message with the SDK Agents
    
    Args:
        bot: Raven bot instance
        channel_id: Channel ID
        message: Message text
        files: List of files attached to the message
    
    Returns:
        Dict[str, Any]: Response from the agent
    """
    try:
        # Create agent manager
        agent_manager = RavenAgentManager(bot=bot)
        
        # Set up context
        frappe.flags.raven_current_bot = bot.name
        frappe.flags.raven_current_channel = channel_id
        
        # Process files if any
        file_references = []
        if files and len(files) > 0:
            for file_data in files:
                file_id = await agent_manager.upload_file_to_agent(file_data.get("file_path"))
                file_references.append({
                    "file_id": file_id,
                    "file_name": file_data.get("file_name")
                })
            
            # Add file references to the message if any
            if file_references:
                file_info = ", ".join([f"{file.get('file_name')}" for file in file_references])
                message = f"{message}\n\nI've attached these files: {file_info}"
        
        # Get dynamic instructions if needed
        instructions = None
        if bot.dynamic_instructions and bot.instruction:
            vars = get_variables_for_instructions()
            instructions = frappe.render_template(bot.instruction, vars)
            
            # If instructions are provided, use them to augment the message context
            if instructions:
                message = f"{message}\n\nContext: {instructions}"
        
        # Process the message
        response = await agent_manager.process_message(message)
        
        return {
            "text": response.get("message"),
            "full_response": response
        }
    
    except Exception as e:
        frappe.log_error(f"Error in SDK handle_message: {str(e)}", frappe.get_traceback())
        return {
            "text": f"There was an error processing your message. Please try again.\nError: {str(e)}",
            "error": True
        }


async def stream_response(bot, channel_id: str, message: str, files: List[Dict] = None) -> None:
    """
    Stream a response from the agent
    
    Args:
        bot: Raven bot instance
        channel_id: Channel ID
        message: Message text
        files: List of files attached to the message
    """
    try:
        # Publish initial thinking state
        publish_thinking_state(channel_id, bot.name)
        
        # Create agent manager
        agent_manager = RavenAgentManager(bot=bot)
        
        # Set up context
        frappe.flags.raven_current_bot = bot.name
        frappe.flags.raven_current_channel = channel_id
        
        # Process files if any
        file_references = []
        if files and len(files) > 0:
            publish_event(channel_id, bot.name, "Processing files...")
            for file_data in files:
                file_id = await agent_manager.upload_file_to_agent(file_data.get("file_path"))
                file_references.append({
                    "file_id": file_id,
                    "file_name": file_data.get("file_name")
                })
            
            # Add file references to the message if any
            if file_references:
                file_info = ", ".join([f"{file.get('file_name')}" for file in file_references])
                message = f"{message}\n\nI've attached these files: {file_info}"
        
        # Get dynamic instructions if needed
        if bot.dynamic_instructions and bot.instruction:
            vars = get_variables_for_instructions()
            instructions = frappe.render_template(bot.instruction, vars)
            
            # If instructions are provided, use them to augment the message context
            if instructions:
                message = f"{message}\n\nContext: {instructions}"
        
        # Start streaming
        publish_event(channel_id, bot.name, "Raven AI is thinking...")
        
        # Collect the full response
        full_response = ""
        
        # Process message with streaming
        async for chunk in agent_manager.process_message_stream(message):
            full_response += chunk
            
            # Publish the chunk
            frappe.publish_realtime(
                "ai_response",
                {
                    "text": chunk,
                    "channel_id": channel_id,
                    "bot": bot.name,
                },
                doctype="Raven Channel",
                docname=channel_id,
            )
        
        # Send the complete message
        bot.send_message(
            channel_id=channel_id,
            text=full_response,
            markdown=True,
        )
        
        # Clear the thinking state
        clear_thinking_state(channel_id)
    
    except Exception as e:
        frappe.log_error(f"Error in SDK stream_response: {str(e)}", frappe.get_traceback())
        
        # Send error message
        bot.send_message(
            channel_id=channel_id,
            text=f"There was an error processing your message. Please try again.\nError: {str(e)}",
        )
        
        # Clear the thinking state
        clear_thinking_state(channel_id)


def publish_thinking_state(channel_id: str, bot_name: str) -> None:
    """
    Publish the thinking state
    
    Args:
        channel_id: Channel ID
        bot_name: Bot name
    """
    frappe.publish_realtime(
        "ai_event",
        {
            "text": "Raven AI is thinking...",
            "channel_id": channel_id,
            "bot": bot_name,
        },
        doctype="Raven Channel",
        docname=channel_id,
    )


def clear_thinking_state(channel_id: str) -> None:
    """
    Clear the thinking state
    
    Args:
        channel_id: Channel ID
    """
    frappe.publish_realtime(
        "ai_event_clear",
        {
            "channel_id": channel_id,
        },
        doctype="Raven Channel",
        docname=channel_id,
        after_commit=True,
    )


def publish_event(channel_id: str, bot_name: str, text: str) -> None:
    """
    Publish an event
    
    Args:
        channel_id: Channel ID
        bot_name: Bot name
        text: Event text
    """
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