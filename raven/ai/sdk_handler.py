import json
import frappe
import asyncio
from typing import Dict, Any, List, Optional, Union

from .sdk_agents import RavenAgentManager, AGENTS_SDK_AVAILABLE
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
        # Check if the SDK is available
        if not AGENTS_SDK_AVAILABLE:
            return {
                "text": "OpenAI Agents SDK is not installed. Please run 'pip install openai-agents' on the server.",
                "error": True
            }
        
        # Set current channel ID in frappe local context for RAG filtering
        if channel_id:
            frappe.local.current_channel_id = channel_id
            frappe.log_error("SDK Channel Context", f"Set current channel_id: {channel_id}")
        
        # Log debug info about bot functions
        frappe.log_error("SDK Functions Debug", f"Handle message for bot: {bot.name}")
        if hasattr(bot, "bot_functions"):
            frappe.log_error("SDK Functions Debug", f"Bot has {len(bot.bot_functions)} bot_functions")
            for i, func in enumerate(bot.bot_functions):
                frappe.log_error("SDK Functions Debug", f"Bot function {i+1}: {func.function}")
        else:
            frappe.log_error("SDK Functions Debug", "Bot does not have bot_functions attribute")
        
        # Verify OpenAI API key if using OpenAI
        if hasattr(bot, "model_provider") and bot.model_provider == "OpenAI":
            settings = frappe.get_cached_doc("Raven Settings")
            api_key = settings.get_password("openai_api_key")
            if not api_key:
                return {
                    "text": "OpenAI API key is not configured in Raven Settings. Please add your API key in Settings.",
                    "error": True
                }
        
        # Create agent manager
        try:
            agent_manager = RavenAgentManager(bot=bot)
        except Exception as e:
            error_message = str(e)
            frappe.log_error("SDK Functions Debug", f"Error initializing agent: {error_message}")
            return {
                "text": f"Error initializing agent: {error_message}",
                "error": True
            }
        
        # Set up context
        frappe.flags.raven_current_bot = bot.name
        frappe.flags.raven_current_channel = channel_id
        
        # Process files if any
        file_references = []
        if files and len(files) > 0:
            frappe.log_error("SDK File Processing", f"Processing {len(files)} files")
            
            # Use the unified RAG system to process files
            from .rag import process_file_upload
            for file_data in files:
                frappe.log_error("SDK File Processing", f"Processing file: {file_data}")
                
                # Process file upload through RAG system
                file_id = await process_file_upload(bot, file_data.get("file_path"), {
                    "filename": file_data.get("file_name"),
                    "channel_id": channel_id
                })
                
                frappe.log_error("SDK File Processing", f"File ID from RAG: {file_id}")
                
                # Also process directly to handle thread context properly
                try:
                    # Import here to avoid circular imports
                    from .rag import process_uploaded_file_immediately
                    import os
                    
                    # Try to process file immediately as well to ensure it's in the recent files list
                    file_path = file_data.get("file_path")
                    if file_path and os.path.exists(file_path):
                        frappe.log_error("SDK Handler", f"Processing file directly during upload: {file_data.get('file_name')}")
                        process_uploaded_file_immediately(
                            file_path=file_path,
                            filename=file_data.get("file_name"),
                            file_id=file_id,
                            channel_id=channel_id
                        )
                        frappe.log_error("SDK File Processing", f"Direct file processing completed")
                    else:
                        frappe.log_error("SDK File Processing", f"File path not found: {file_path}")
                except Exception as e:
                    frappe.log_error("SDK Handler", f"Error in direct file processing: {str(e)}")
                
                # Add to file references list
                file_references.append({
                    "file_id": file_id,
                    "file_name": file_data.get("file_name")
                })
                
                frappe.log_error("SDK File Processing", f"Added file reference: {file_references[-1]}")
            
            # Add file references to the message if any with enhanced context
            if file_references:
                file_info = ", ".join([f"{file.get('file_name')}" for file in file_references])
                
                frappe.log_error("SDK File Processing", f"Modifying message with file context: {file_info}")
                
                # Add more specific instruction about the files in the message
                message = f"{message}\n\nIMPORTANT: I've just attached these files to examine: {file_info}.\n\n" + \
                          f"Please focus ONLY on these specific files when responding. " + \
                          f"If asked about content, totals, or data in these files, use the file_search tool."
                
                frappe.log_error("SDK File Processing", f"Final message with file context: {message}")
        
        # Get dynamic instructions if needed
        instructions = None
        if bot.dynamic_instructions and bot.instruction:
            vars = get_variables_for_instructions()
            instructions = frappe.render_template(bot.instruction, vars)
            
            # If instructions are provided, use them to augment the message context
            if instructions:
                message = f"{message}\n\nContext: {instructions}"
        
        # Get conversation history
        conversation_history = get_channel_conversation(channel_id)
        
        # Process the message with conversation history
        frappe.log_error("SDK Functions Debug", f"Processing message with conversation history: {len(conversation_history) if conversation_history else 0} messages")
        frappe.log_error("SDK Pre-Process", f"Channel ID before process_message: {getattr(frappe.local, 'current_channel_id', 'NOT SET')}")
        
        response = await agent_manager.process_message(message, conversation_history)
        
        frappe.log_error("SDK Post-Process", f"Channel ID after process_message: {getattr(frappe.local, 'current_channel_id', 'NOT SET')}")
        
        # Ensure response is not None before accessing
        if response is None:
            frappe.log_error("SDK Clean Error", "Received None response from agent_manager.process_message")
            return {
                "text": "Sorry, I encountered an error processing your message.",
                "full_response": {}
            }
        
        # Clean the response text - remove <think> tags
        response_text = response.get("message", "")
        if response_text:
            # Remove <think>...</think> content including nested tags
            import re
            response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
            response_text = response_text.strip()
        
        return {
            "text": response_text,
            "full_response": response
        }
    
    except Exception as e:
        error_message = str(e)
        error_type = type(e).__name__
        
        # Use minimal error info to avoid character length errors
        short_message = error_message[:50] + "..." if len(error_message) > 50 else error_message
        frappe.log_error("SDK Functions Debug", error_message)
        
        # Format a user-friendly error message
        user_message = "There was an error processing your message."
        
        # Add debug mode info to error message if enabled
        debug_mode = getattr(bot, "debug_mode", False)
        
        # Handle specific OpenAI errors - check for common error patterns
        if any(err in error_message.lower() for err in ["insufficient_quota", "exceeded your current quota", "billing details"]):
            user_message = "OpenAI API quota exceeded. Please check your OpenAI account billing details or try using a different model provider."
        elif "model_not_found" in error_message.lower():
            user_message = "Model not found. Please check that the model name is correct and available in your OpenAI account."
        elif any(err in error_message.lower() for err in ["api_key", "invalid", "incorrect", "authentication"]):
            user_message = "Invalid OpenAI API key. Please check your API key in Raven Settings."
        elif "failed to initialize rag" in error_message.lower():
            if "local embeddings" in error_message.lower() or "sentence-transformers" in error_message.lower() or "sentence_transformers" in error_message.lower():
                user_message = "Failed to initialize local embeddings. Please run: pip install sentence-transformers"
            else:
                user_message = "Failed to initialize RAG system. File search has been disabled."
        elif "vector_store_ids" in error_message.lower():
            user_message = "Vector store IDs are not configured correctly. Please check your bot configuration."
        elif "computer tool" in error_message.lower() or "code interpreter" in error_message.lower():
            user_message = "Code Interpreter is currently not supported with the SDK Agents implementation. Please disable it in your bot configuration."
        elif "function_calling" in error_message.lower() or "function" in error_message.lower():
            user_message = "There was an error with function calling. Please check your bot functions configuration."
            # Add more detailed error message for debug mode
            if debug_mode:
                user_message += f"\n\nDetailed error: {error_message}"
        elif "parameter_schema" in error_message.lower() or "schema" in error_message.lower():
            user_message = "There was an error with function parameter schema. Please check your function definitions."
            # Add more detailed error message for debug mode
            if debug_mode:
                user_message += f"\n\nDetailed error: {error_message}"
        elif "bot_functions" in error_message.lower():
            user_message = "There was an error setting up bot functions. Please check your bot configuration."
            # Add more detailed error message for debug mode
            if debug_mode:
                user_message += f"\n\nDetailed error: {error_message}"
        else:
            # Include a summarized version of the original error for other cases
            if debug_mode:
                user_message += f"\nError: {error_type} - {short_message}"
            else:
                user_message += f"\nError: {error_type}"
                
        return {
            "text": user_message,
            "error": True
        }


async def stream_response(bot, channel_id: str, message: str, files: List[Dict] = None) -> None:
    """
    Handle a message through the Agents SDK and send a single response
    
    Args:
        bot: Raven bot instance
        channel_id: Channel ID
        message: Message text
        files: List of files attached to the message
    """
    try:
        # Publish initial thinking state
        publish_thinking_state(channel_id, bot.name)
        
        # Check if the SDK is available
        if not AGENTS_SDK_AVAILABLE:
            bot.send_message(
                channel_id=channel_id,
                text="OpenAI Agents SDK is not installed. Please run 'pip install openai-agents' on the server.",
            )
            clear_thinking_state(channel_id)
            return
        
        # Verify OpenAI API key if using OpenAI
        if hasattr(bot, "model_provider") and bot.model_provider == "OpenAI":
            settings = frappe.get_cached_doc("Raven Settings")
            api_key = settings.get_password("openai_api_key")
            if not api_key:
                bot.send_message(
                    channel_id=channel_id,
                    text="OpenAI API key is not configured in Raven Settings. Please add your API key in Settings.",
                )
                clear_thinking_state(channel_id)
                return
        
        # Create agent manager
        try:
            agent_manager = RavenAgentManager(bot=bot)
        except Exception as e:
            error_message = str(e)
            bot.send_message(
                channel_id=channel_id,
                text=f"Error initializing agent: {error_message}",
            )
            clear_thinking_state(channel_id)
            return
        
        # Set up context
        frappe.flags.raven_current_bot = bot.name
        frappe.flags.raven_current_channel = channel_id
        
        # Process files if any
        file_references = []
        if files and len(files) > 0:
            publish_event(channel_id, bot.name, "Processing files...")
            # Use the unified RAG system to process files
            from .rag import process_file_upload
            for file_data in files:
                # Process file upload through RAG system
                file_id = await process_file_upload(bot, file_data.get("file_path"), {
                    "filename": file_data.get("file_name"),
                    "channel_id": channel_id
                })
                
                # Also process directly to handle thread context properly
                try:
                    # Import here to avoid circular imports
                    from .rag import process_uploaded_file_immediately
                    import os
                    
                    # Try to process file immediately as well to ensure it's in the recent files list
                    file_path = file_data.get("file_path")
                    if file_path and os.path.exists(file_path):
                        frappe.log_error("SDK Handler", f"Processing file directly during upload: {file_data.get('file_name')}")
                        process_uploaded_file_immediately(
                            file_path=file_path,
                            filename=file_data.get("file_name"),
                            file_id=file_id,
                            channel_id=channel_id
                        )
                except Exception as e:
                    frappe.log_error("SDK Handler", f"Error in direct file processing: {str(e)}")
                
                # Add to file references list
                file_references.append({
                    "file_id": file_id,
                    "file_name": file_data.get("file_name")
                })
            
            # Add file references to the message if any with enhanced context
            if file_references:
                file_info = ", ".join([f"{file.get('file_name')}" for file in file_references])
                
                # Add more specific instruction about the files in the message
                message = f"{message}\n\nIMPORTANT: I've just attached these files to examine: {file_info}.\n\n" + \
                          f"Please focus ONLY on these specific files when responding. " + \
                          f"If asked about content, totals, or data in these files, use the file_search tool."
        
        # Get dynamic instructions if needed
        if bot.dynamic_instructions and bot.instruction:
            vars = get_variables_for_instructions()
            instructions = frappe.render_template(bot.instruction, vars)
            
            # If instructions are provided, use them to augment the message context
            if instructions:
                message = f"{message}\n\nContext: {instructions}"
        
        # Publish thinking state
        publish_event(channel_id, bot.name, "Raven AI is thinking...")
        
        # Check for previous conversation history in this channel
        conversation_history = get_channel_conversation(channel_id)
        
        # Process message with NO streaming, for a simpler implementation
        frappe.log_error("SDK Clean", f"Processing message for channel: {channel_id}")
        response = await agent_manager.process_message(message, conversation_history)
        
        # Get the message to send - ensure response is not None before accessing
        if response is None:
            frappe.log_error("SDK Clean Error", "Received None response from agent_manager.process_message")
            response_text = "Sorry, I encountered an error processing your message."
        else:
            response_text = response.get('message', '')
        
        # Clean the response text - remove <think> tags
        if response_text:
            # Remove <think>...</think> content including nested tags
            import re
            response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
            response_text = response_text.strip()
        
        # Log message preparation but DO NOT SEND
        frappe.log_error("SDK Clean", f"Preparing message to return to caller, length: {len(response_text)}")
        
        # IMPORTANT: DO NOT SEND THE MESSAGE HERE
        # The caller of this function will handle sending the message
        # This avoids the duplicate message problem
        
        # Clear the thinking state
        clear_thinking_state(channel_id)
        
        # Add special debug log to track whether we're returning a response
        frappe.log_error("SDK Clean", f"Returning response to caller. Response length: {len(response_text) if response_text else 0}")
        
        # Return the response so the caller can send the message
        return response_text
    
    except Exception as e:
        error_message = str(e)
        error_type = type(e).__name__
        
        # Use minimal error info to avoid character length errors
        frappe.log_error("SDK Clean Error", f"{error_type}: {error_message}")
        
        # Format a user-friendly error message
        user_message = "There was an error processing your message."
        
        # Add debug mode info to error message if enabled
        debug_mode = getattr(bot, "debug_mode", False)
        
        # Handle specific OpenAI errors - check for common error patterns
        if any(err in error_message.lower() for err in ["insufficient_quota", "exceeded your current quota", "billing details"]):
            user_message = "OpenAI API quota exceeded. Please check your OpenAI account billing details or try using a different model provider."
        elif "model_not_found" in error_message.lower():
            user_message = "Model not found. Please check that the model name is correct and available in your OpenAI account."
        elif any(err in error_message.lower() for err in ["api_key", "invalid", "incorrect", "authentication"]):
            user_message = "Invalid OpenAI API key. Please check your API key in Raven Settings."
        
        # For debug mode, include more details
        if debug_mode:
            user_message += f"\n\nError details: {error_message}"
        
        # IMPORTANT: DO NOT SEND THE MESSAGE HERE
        # The caller of this function will handle sending the message
        # This avoids the duplicate message problem
        
        # Clear the thinking state
        clear_thinking_state(channel_id)
        
        # Add special debug log to track error handling path
        frappe.log_error("SDK Clean", f"Returning error message to caller. Error message length: {len(user_message) if user_message else 0}")
        
        # Return the error message so the caller can send it
        return user_message


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


def get_channel_conversation(channel_id: str) -> Optional[List[Dict[str, str]]]:
    """
    Get the conversation history for a channel
    
    Args:
        channel_id: Channel ID
        
    Returns:
        List: Conversation history in the format expected by the SDK
    """
    try:
        # Use the more comprehensive get_messages function from chat_stream.py
        from raven.api.chat_stream import get_messages
        
        # Get messages from the channel, with a limit (adjust if needed)
        # This will be from newest to oldest
        result = get_messages(channel_id=channel_id, limit=25)
        
        if not result or not result.get("messages"):
            return None
            
        # Messages are in reverse chronological order, so we need to reverse them
        messages = list(reversed(result.get("messages", [])))
        
        # Format messages for the SDK
        conversation = []
        for msg in messages:
            # Get the message content - use 'content' field if available, otherwise fallback to 'text'
            content = msg.get("content")
            if not content and msg.get("text"):
                from bs4 import BeautifulSoup
                # Extract plain text from HTML if needed
                soup = BeautifulSoup(msg.get("text"), "html.parser")
                content = soup.get_text()
                
            # Skip empty messages
            if not content:
                continue
                
            if msg.get("is_bot_message"):
                conversation.append({
                    "role": "assistant", 
                    "content": content
                })
            else:
                conversation.append({
                    "role": "user", 
                    "content": content
                })
        
        return conversation if conversation else None
        
    except Exception as e:
        frappe.log_error("Memory Retrieval Error", f"Error getting channel conversation: {str(e)}")
        # Fall back to simpler implementation if there's an error
        return None


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