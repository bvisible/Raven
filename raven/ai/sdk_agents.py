from typing import Any, Dict, List, Optional, Union, AsyncGenerator
import frappe
import json
import os
from enum import Enum

# Define fallback types/classes for when the SDK is not available
class DummyAgent:
    """Dummy Agent class for when the SDK is not available"""
    pass

class DummyModelSettings:
    """Dummy ModelSettings class for when the SDK is not available"""
    pass

class DummyFileSearchTool:
    """Dummy FileSearchTool class for when the SDK is not available"""
    pass

class DummyComputerTool:
    """Dummy ComputerTool class for when the SDK is not available"""
    pass

class DummyFunctionTool:
    """Dummy FunctionTool class for when the SDK is not available"""
    pass

class DummyRunner:
    """Dummy Runner class for when the SDK is not available"""
    pass

# Define dummy module namespace
class DummyInterface:
    """Dummy interface module for when the SDK is not available"""
    class Model:
        """Dummy Model class for when the SDK is not available"""
        pass

class DummyOpenAIChatCompletions:
    """Dummy openai_chatcompletions module for when the SDK is not available"""
    class OpenAIChatCompletionsModel:
        """Dummy OpenAIChatCompletionsModel class for when the SDK is not available"""
        pass

# Attempt to import the real SDK
try:
    from agents import Agent, ModelSettings, FileSearchTool, ComputerTool, FunctionTool, Runner
    from agents.models import interface, openai_chatcompletions
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    # If import fails, use dummy classes
    Agent = DummyAgent
    ModelSettings = DummyModelSettings
    FileSearchTool = DummyFileSearchTool
    ComputerTool = DummyComputerTool
    FunctionTool = DummyFunctionTool
    Runner = DummyRunner
    interface = DummyInterface
    openai_chatcompletions = DummyOpenAIChatCompletions
    AGENTS_SDK_AVAILABLE = False
    frappe.log_error("OpenAI Agents SDK not installed. Run 'pip install openai-agents'")


class ModelProvider(str, Enum):
    """Supported model providers"""
    OPENAI = "OpenAI"
    LM_STUDIO = "LM Studio"
    OLLAMA = "Ollama" 
    LOCALAI = "LocalAI"
    LOCAL_LLM = "LocalLLM"  # Generic local LLM provider, determined from settings


class RavenAgentManager:
    """Manager for Raven Agents using the OpenAI Agents SDK"""
    
    def __init__(self, bot_name: str = None, bot=None):
        """
        Initialize the agent manager
        
        Args:
            bot_name: Name of the bot
            bot: Bot document instance
        """
        if not AGENTS_SDK_AVAILABLE:
            frappe.throw("OpenAI Agents SDK not available. Run 'pip install openai-agents'")
            
        self.bot = bot or frappe.get_doc("Raven Bot", bot_name)
        self.agent = None
        self.runner = None
    
    def create_agent(self) -> Agent:
        """
        Create an Agent instance
        
        Returns:
            Agent: The created agent
        """
        # Get tools based on bot configuration
        tools = self._get_tools()
        
        # Get model and model settings
        model = self._get_model()
        model_settings = self._get_model_settings()
        
        # Get original instructions
        instructions = self.bot.instruction
        
        # If file search is enabled, add specific instructions about using the tool
        if hasattr(self.bot, "enable_file_search") and self.bot.enable_file_search:
            file_search_instructions = """
When users ask about documents or files that have been uploaded, you MUST use the file_search tool to find relevant information.
CRITICAL GUIDELINES:
1. If a user asks about content in a file, ALWAYS use the file_search tool first before responding
2. If a user asks about specific information like totals, amounts, dates, or details from a document, ALWAYS use file_search
3. For questions like "what is the total of this invoice?" or "what's in this document?", use file_search immediately
4. NEVER tell users you cannot access PDF contents - you have the file_search tool for this purpose
5. If a file has been uploaded and the user refers to it, use file_search to examine its contents
6. When responding about document contents, cite the information you found using the file_search tool

EXTREMELY IMPORTANT:
- ALWAYS prioritize the most recently uploaded file in your responses
- When a user uploads a file and then asks a question about it, you MUST use file_search on that specific file
- For questions about totals, amounts, or specific data in a document, be extremely explicit in your file_search query (e.g., "find the total amount in euros in the invoice")
- When extracting information from files, ALWAYS specify which file you're referring to
- ONLY include information from the specific file the user has asked about, not from other files

Remember: You have access to document contents through the file_search tool. You MUST use it when users ask about uploaded files.
"""
            # Combine instructions
            if instructions:
                instructions = f"{instructions}\n\n{file_search_instructions}"
            else:
                instructions = file_search_instructions
                
            frappe.log_error("SDK Functions Debug", "Added file search instructions to agent")
        
        # Create the agent
        self.agent = Agent(
            name=self.bot.bot_name,
            instructions=instructions,
            tools=tools,
            model=model,
            model_settings=model_settings
        )
        
        return self.agent
    
    def _get_tools(self) -> List[Any]:
        """
        Get the configured tools for the agent
        
        Returns:
            List[Any]: List of tools for the agent
        """
        tools = []
        
        # Add detailed logging for debugging
        frappe.log_error("SDK Functions Debug", f"Getting tools for bot: {self.bot.name}, bot_name: {self.bot.bot_name}")
        
        # Log bot_functions attribute existence and content
        if hasattr(self.bot, "bot_functions"):
            frappe.log_error("SDK Functions Debug", f"Bot has {len(self.bot.bot_functions)} bot_functions")
            for i, func in enumerate(self.bot.bot_functions):
                frappe.log_error("SDK Functions Debug", f"Bot function {i+1}: {func.function}")
        else:
            frappe.log_error("SDK Functions Debug", "Bot does not have bot_functions attribute")
        
        # Add file search tool if enabled
        if self.bot.enable_file_search:
            try:
                # Use the unified RAG architecture
                frappe.log_error("SDK Functions Debug", "Attempting to add RAG search tool using unified architecture")
                from .rag import get_file_search_tool
                
                frappe.log_error("RAG Debug", f"Calling get_file_search_tool for bot: {self.bot.name}")
                
                # Verify bot attributes for RAG
                frappe.log_error("RAG Debug", f"Bot file search settings: enable_file_search={self.bot.enable_file_search}, enable_local_rag={getattr(self.bot, 'enable_local_rag', 'N/A')}")
                frappe.log_error("RAG Debug", f"Bot local RAG provider: {getattr(self.bot, 'local_rag_provider', 'N/A')}")
                frappe.log_error("RAG Debug", f"Bot use local embeddings: {getattr(self.bot, 'use_local_embeddings', 'N/A')}")
                frappe.log_error("RAG Debug", f"Bot embeddings model: {getattr(self.bot, 'embeddings_model', 'N/A')}")
                
                # Get the appropriate file search tool
                file_search_tool = get_file_search_tool(self.bot)
                
                if file_search_tool:
                    tools.append(file_search_tool)
                    frappe.log_error("SDK Functions Debug", f"RAG search tool added successfully for bot {self.bot.bot_name}")
                    frappe.log_error("RAG Debug", f"Search tool type: {type(file_search_tool).__name__}")
                else:
                    frappe.log_error("SDK Functions Debug", f"Failed to create RAG search tool for bot {self.bot.bot_name}")
                    frappe.log_error("RAG Debug", f"get_file_search_tool returned None")
                    # Log the error but don't try to save the bot itself
                    # This avoids TimestampMismatchError when multiple processes 
                    # try to save the document at the same time
                    frappe.log_error("RAG", f"Will use bot without file search due to initialization error")
                    
                    # Propagate the error with a short message
                    raise ValueError("Failed to initialize RAG. File search has been disabled for this bot.")
                    
            except Exception as e:
                # Format error message
                error_type = type(e).__name__
                error_msg = str(e)
                frappe.log_error("RAG Debug", f"Exception in file search tool setup: {error_type}: {error_msg}")
                frappe.log_error("SDK Functions Debug", e)
                
                # Log the error but don't try to save the bot itself
                # This avoids TimestampMismatchError when multiple processes 
                # try to save the document at the same time
                frappe.log_error("RAG", f"Will use bot without file search due to initialization error: {error_type}")
                
                # Propagate the error with a short message
                raise ValueError(f"Failed to initialize RAG: {error_type}: {error_msg}. File search has been disabled.")
        
        # Add Code Interpreter tool if enabled
        if self.bot.enable_code_interpreter:
            # Code Interpreter support has changed in the latest SDK and is not currently supported
            frappe.log_error("SDK Functions Debug", "Code Interpreter not supported in SDK implementation")
            
            # Log the error but don't try to save the bot itself
            frappe.log_error("SDK Functions Debug", "Will use bot without code interpreter due to SDK limitations")
            # Raise ValueError with a short message to inform the user
            raise ValueError("Code Interpreter is not supported and has been disabled.")
        
        # Add CRUD functions as tools
        frappe.log_error("SDK Functions Debug", "Attempting to add bot functions as tools")
        from .sdk_tools import create_raven_tools
        try:
            raven_tools = create_raven_tools(self.bot)
            frappe.log_error("SDK Functions Debug", f"Created {len(raven_tools)} Raven tools for bot {self.bot.bot_name}")
            tools.extend(raven_tools)
        except Exception as e:
            frappe.log_error("SDK Functions Debug", f"Error creating Raven tools: {str(e)}")
        
        # Log the tools being used
        tool_names = [getattr(tool, 'name', type(tool).__name__) for tool in tools]
        frappe.log_error("SDK Functions Debug", f"Final tools for bot {self.bot.bot_name}: {tool_names}")
        
        return tools
    
    def _get_model(self) -> str:
        """
        Get the model to use for the agent
        
        Returns:
            str: Model identifier or Model object
        """
        provider = getattr(self.bot, "model_provider", ModelProvider.OPENAI.value)
        model_name = getattr(self.bot, "model_name", "gpt-3.5-turbo")
        
        if provider == ModelProvider.OPENAI.value:
            # For OpenAI, we need to create a model with a properly configured client
            from agents.models import openai_chatcompletions
            from openai import AsyncOpenAI
            
            # Get OpenAI API key from settings
            try:
                settings = frappe.get_cached_doc("Raven Settings")
                
                if not settings.enable_ai_integration:
                    raise ValueError("AI Integration is not enabled in Raven Settings")
                
                if not settings.enable_openai_services:
                    raise ValueError("OpenAI services are not enabled in Raven Settings")
                
                api_key = settings.get_password("openai_api_key")
                
                if not api_key:
                    raise ValueError("OpenAI API key is not configured in Raven Settings")
                
                # Create client with API key
                client = AsyncOpenAI(api_key=api_key)
                
                # Create and return model
                return openai_chatcompletions.OpenAIChatCompletionsModel(
                    model=model_name,
                    openai_client=client
                )
            except Exception as e:
                error_msg = str(e)
                if "API key" in error_msg:
                    frappe.log_error(f"OpenAI API key error: {error_msg}")
                    raise ValueError("OpenAI API key is not configured correctly in Raven Settings. Please check your settings.")
                else:
                    frappe.log_error(f"Error creating OpenAI model: {error_msg}")
                    raise ValueError(f"Could not initialize OpenAI model: {error_msg}")
        elif provider == ModelProvider.LOCAL_LLM.value:
            # For the generic Local LLM option, get the actual provider from settings
            settings = frappe.get_cached_doc("Raven Settings")
            
            if not settings.enable_ai_integration:
                frappe.throw("AI Integration is not enabled in Raven Settings")
            
            if not settings.enable_local_llm:
                frappe.throw("Local LLM is not enabled in Raven Settings")
            
            actual_provider = settings.get("local_llm_provider")
            
            if not actual_provider:
                frappe.throw("Local LLM provider not configured in Raven Settings")
                
            # Map the provider name to the enum value
            if actual_provider == "LM Studio":
                provider = ModelProvider.LM_STUDIO.value
            elif actual_provider == "Ollama":
                provider = ModelProvider.OLLAMA.value
            elif actual_provider == "LocalAI":
                provider = ModelProvider.LOCALAI.value
            else:
                # If provider is not recognized, log a warning but try to use it anyway
                frappe.log_error(f"Unknown local LLM provider in settings: {actual_provider}. Will attempt to use as direct value.")
                
            # Log the provider for debugging
            frappe.log_error("LLM Debug", f"Using local LLM provider from settings: {actual_provider}")
            
            # Get the local model with the determined provider
            return self._get_local_model(provider, model_name)
        else:
            # For specific local model providers, use them directly
            return self._get_local_model(provider, model_name)
    
    def _get_local_model(self, provider: str, model_name: str) -> interface.Model:
        """
        Get a local model from the specified provider
        
        Args:
            provider: Provider name
            model_name: Model name
            
        Returns:
            interface.Model: Model interface
        """
        # Get the settings
        settings = frappe.get_doc("Raven Settings")
        
        # Verify AI integration and local LLM is enabled
        if not settings.enable_ai_integration:
            frappe.throw("AI Integration is not enabled in Raven Settings")
        
        if not settings.enable_local_llm:
            frappe.throw("Local LLM is not enabled in Raven Settings")
        
        # Verify that local_llm_api_url is configured
        if not settings.local_llm_api_url:
            frappe.throw(f"Local LLM API URL not configured in Raven Settings for provider: {provider}")
        
        # Create appropriate provider instance based on the specified provider
        provider_class = None
        if provider == ModelProvider.LM_STUDIO.value:
            provider_class = LMStudioProvider
        elif provider == ModelProvider.OLLAMA.value:
            provider_class = OllamaProvider
        elif provider == ModelProvider.LOCALAI.value:
            provider_class = LocalAIProvider
        elif provider == ModelProvider.LOCAL_LLM.value:
            # This should never happen as the LOCAL_LLM is mapped to a specific provider above,
            # but we handle it just in case
            frappe.log_error("LLM Debug", "Unmapped LOCAL_LLM value reached provider selection")
            provider_class = LMStudioProvider  # Default to LM Studio as fallback
        else:
            frappe.throw(f"Unsupported model provider: {provider}")
            
        # Create and return the model
        provider_instance = provider_class(api_base_url=settings.local_llm_api_url)
        return provider_instance.get_model(model_name)
        
        # Default to OpenAI model if provider not supported yet
        return model_name
    
    def _get_model_settings(self) -> ModelSettings:
        """
        Get model settings from bot configuration
        
        Returns:
            ModelSettings: Model settings
        """
        # Parse agent settings from bot configuration
        agent_settings = {}
        if hasattr(self.bot, "agent_settings") and self.bot.agent_settings:
            try:
                agent_settings = json.loads(self.bot.agent_settings)
            except json.JSONDecodeError:
                frappe.log_error(f"Invalid agent settings JSON: {self.bot.agent_settings}")
        
        # Extract known model settings
        temperature = agent_settings.get("temperature", 0.7)
        top_p = agent_settings.get("top_p", 1.0)
        max_tokens = agent_settings.get("max_tokens", None)
        
        # Check if we're using a Computer Tool (code interpreter)
        # This requires truncation="auto" for compatibility
        uses_code_interpreter = hasattr(self.bot, "enable_code_interpreter") and self.bot.enable_code_interpreter
        
        # Set model settings parameters
        settings_kwargs = {
            "temperature": temperature,
            "top_p": top_p
        }
        
        # Add truncation setting if needed
        if uses_code_interpreter or agent_settings.get("truncation"):
            settings_kwargs["truncation"] = agent_settings.get("truncation", "auto")
        
        # Add max_tokens if specified
        if max_tokens:
            settings_kwargs["max_tokens"] = max_tokens
        
        # If file search is enabled, set tool_choice to auto so the model uses tools appropriately
        if hasattr(self.bot, "enable_file_search") and self.bot.enable_file_search:
            settings_kwargs["tool_choice"] = "auto"
            frappe.log_error("SDK Functions Debug", "Setting tool_choice=auto to encourage tool usage")
            
        # Create model settings
        model_settings = ModelSettings(**settings_kwargs)
        
        return model_settings
    
    def get_runner(self) -> Runner:
        """
        Get a runner for the agent
        
        Returns:
            Runner: Runner for the agent
        """
        if not self.agent:
            self.create_agent()
            
        # In the latest SDK version, Runner is used as a class with static methods
        # We don't need to instantiate it
        return Runner
    
    async def process_message(self, message: str, conversation_history=None) -> Dict[str, Any]:
        """
        Process a message with the agent
        
        Args:
            message: Message to process
            conversation_history: Optional list of previous messages in the conversation
            
        Returns:
            Dict[str, Any]: Response from the agent
        """
        # Get provider information for the bot
        provider = getattr(self.bot, "model_provider", ModelProvider.OPENAI.value)
        settings = frappe.get_cached_doc("Raven Settings")
        
        # Check if we should use direct API calls for local providers
        using_local_llm = False
        actual_provider = provider
        
        if provider == ModelProvider.LOCAL_LLM.value:
            # Get the actual provider from settings
            actual_provider = settings.get("local_llm_provider")
            if actual_provider == "LM Studio":
                using_local_llm = True
                frappe.log_error("LLM Debug", "Using direct API for LM Studio")
            elif actual_provider == "Ollama":
                using_local_llm = True
                frappe.log_error("LLM Debug", "Using direct API for Ollama")
            elif actual_provider == "LocalAI":
                using_local_llm = True
                frappe.log_error("LLM Debug", "Using direct API for LocalAI")
        elif provider in [ModelProvider.LM_STUDIO.value, ModelProvider.OLLAMA.value, ModelProvider.LOCALAI.value]:
            using_local_llm = True
            frappe.log_error("LLM Debug", f"Using direct API for {provider}")
        
        # If using a local LLM, use direct API calls instead of the SDK Agent
        if using_local_llm:
            frappe.log_error("LLM Debug", "Using direct API path for local LLM")
            return await self._process_message_direct_api(
                message, 
                conversation_history, 
                provider=actual_provider
            )
        
        # For cloud providers like OpenAI, use the SDK Agent as before
        # Get the agent and runner class
        if not self.agent:
            self.create_agent()
        
        # Determine the input based on conversation history
        if conversation_history:
            # If we have history, use it with the new message appended
            # Add the new user message
            conversation_history.append({"role": "user", "content": message})
            input_data = conversation_history
        else:
            # Otherwise just use the message directly
            input_data = message
        
        try:
            # Using the static run method from Runner class
            frappe.log_error("SDK Debug", f"Running agent with input of type: {type(input_data)}")
            response = await Runner.run(self.agent, input_data)
            
            # Log the response type for debugging
            frappe.log_error("SDK Debug", f"Runner.run returned response of type: {type(response)}")
            if response is not None:
                frappe.log_error("SDK Debug", f"Response attributes: {dir(response)}")
            
            # Verify that response exists and has the expected attributes
            if response is None:
                frappe.log_error("SDK Clean Error", "Runner.run returned None")
                return {
                    "response": {},
                    "message": "Sorry, I encountered an error processing your message."
                }
            
            # Safely access the final_output attribute
            message = getattr(response, 'final_output', None)
            if message is None:
                message = "I received your message, but had trouble formulating a response."
                frappe.log_error("SDK Clean Error", "Response has no final_output attribute")
            
            return {
                "response": response,
                "message": message
            }
        except Exception as e:
            # Log the error
            error_message = str(e)
            frappe.log_error("SDK Clean Error", error_message)
            
            # Return a fallback response
            return {
                "response": {},
                "message": f"Sorry, I encountered an error: {error_message}"
            }
            
    async def _process_message_direct_api(self, message: str, conversation_history=None, provider="LM Studio") -> Dict[str, Any]:
        """
        Process a message with direct API calls to local LLM provider
        This method bypasses the SDK Agent for better compatibility with local LLMs
        
        Args:
            message: Message to process
            conversation_history: Optional list of previous messages in the conversation
            provider: The local LLM provider to use
            
        Returns:
            Dict[str, Any]: Response from the LLM
        """
        try:
            # Get settings for the local LLM
            settings = frappe.get_cached_doc("Raven Settings")
            
            # Verify AI integration and local LLM is enabled
            if not settings.enable_ai_integration:
                yield "AI Integration is not enabled in Raven Settings"
                return
            
            if not settings.enable_local_llm:
                yield "Local LLM is not enabled in Raven Settings"
                return
            
            if not settings.local_llm_api_url:
                frappe.throw("Local LLM API URL not configured in Raven Settings")
                
            # Get model name from the bot
            model_name = getattr(self.bot, "model_name", "")
            if not model_name:
                # Use a reasonable default based on provider
                if provider == "LM Studio":
                    model_name = "openhermes"
                elif provider == "Ollama":
                    model_name = "llama2"
                elif provider == "LocalAI":
                    model_name = "gpt4all"
                else:
                    model_name = "unknown"  # Will be caught in error handling
                    
                frappe.log_error("LLM Debug", f"No model name specified, using default: {model_name}")
            
            # Import OpenAI client library for direct API calls
            from openai import AsyncOpenAI
            
            # Create a client instance with the local LLM API URL
            api_key = "sk-no-key-required"  # Most local providers don't check the API key
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.local_llm_api_url
            )
            
            # Log the client initialization
            frappe.log_error("LLM Debug", f"Created AsyncOpenAI client with base URL: {settings.local_llm_api_url}")
            
            # Prepare the messages list for the chat completion API
            messages = []
            
            # System message (instructions) - Add tool instructions
            system_instructions = ""
            if hasattr(self.bot, "instruction") and self.bot.instruction:
                system_instructions = self.bot.instruction
            
            # Add file search instructions if file search is enabled
            file_search_enabled = hasattr(self.bot, "enable_file_search") and self.bot.enable_file_search
            if file_search_enabled:
                file_search_instructions = """
CRITICAL INSTRUCTION - YOU MUST FOLLOW THIS EXACTLY:

You have the ability to access and search files like PDFs that are uploaded. 
To do this, you MUST use the file_search tool for ANY questions about files.

MANDATORY FILE TOOL USAGE RULES:
- When users ask about "total," "amount," "content," or anything in a document → ALWAYS use file_search
- When a file was just uploaded → AUTOMATICALLY use file_search WITHOUT asking permission
- For questions like "what does this document say" or "what's the total" → IMMEDIATELY use file_search
- NEVER respond with "I cannot access files" or "I don't have capability" - YOU CAN AND MUST USE file_search
- You MUST use file_search even if you think it might not work - it WILL work

IMMEDIATE ACTION REQUIRED:
For THIS conversation specifically, a file has been uploaded. You MUST use the file_search tool BEFORE responding to any questions about this file.

USE THIS FORMAT for your file_search query:
{"query": "extract total amount, invoice number, and other important information from invoice"}

If a user asks about an invoice total or any document content, you MUST use file_search BEFORE responding.
"""
                # Add to system instructions
                if system_instructions:
                    system_instructions = f"{system_instructions}\n\n{file_search_instructions}"
                else:
                    system_instructions = file_search_instructions
            
            # Add general tool usage instructions
            has_tools = file_search_enabled or (hasattr(self.bot, "bot_functions") and self.bot.bot_functions)
            if has_tools:
                tools_instruction = """
You have access to the following tools. You should use these tools when appropriate to respond to user queries.
When you need to use a tool:
1. Identify which tool is best suited for the task
2. Call the tool with appropriate parameters
3. Wait for the result, and incorporate it into your response

Always use tools for specific queries that require retrieving or manipulating data.
"""
                # Combine instructions
                if system_instructions:
                    system_instructions = f"{system_instructions}\n\n{tools_instruction}"
                else:
                    system_instructions = tools_instruction
            
            # Add system instructions if available
            if system_instructions:
                messages.append({
                    "role": "system",
                    "content": system_instructions
                })
            
            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history)
                
                # Check if the last message is already the current user message
                if conversation_history[-1].get("role") != "user" or conversation_history[-1].get("content") != message:
                    # Add the current message if it's not already in the history
                    messages.append({
                        "role": "user",
                        "content": message
                    })
            else:
                # Just add the current message if no history
                messages.append({
                    "role": "user",
                    "content": message
                })
            
            # Prepare the model parameters based on provider and model
            model_params = self._get_direct_api_model_params(provider, model_name)
            
            # Get tools configuration for the bot
            tools = []
            raven_tools = []
            
            # First, check if file search is enabled and add the file search tool
            if hasattr(self.bot, "enable_file_search") and self.bot.enable_file_search:
                # Import the file search tool function
                frappe.log_error("Tools Debug", f"Bot has file search enabled, trying to add file search tool")
                try:
                    from .rag import get_file_search_tool
                    file_search_tool = get_file_search_tool(self.bot)
                    
                    if file_search_tool:
                        frappe.log_error("Tools Debug", f"Adding file search tool: {file_search_tool.name if hasattr(file_search_tool, 'name') else 'unknown'}")
                        
                        # Add to the list of tools
                        raven_tools.append(file_search_tool)
                        
                        # Convert to OpenAI tool format
                        try:
                            # Get parameter schema from the tool
                            parameter_schema = None
                            if hasattr(file_search_tool, 'parameter_schema'):
                                parameter_schema = file_search_tool.parameter_schema
                            elif hasattr(file_search_tool, 'params_json_schema'):
                                parameter_schema = file_search_tool.params_json_schema
                            else:
                                frappe.log_error("Tools Debug", "File search tool missing parameter schema")
                                # Use a default schema as fallback
                                parameter_schema = {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The search query to find information in documents"
                                        },
                                        "max_results": {
                                            "type": "integer",
                                            "description": "Maximum number of results",
                                            "default": 5
                                        }
                                    },
                                    "required": ["query"]
                                }
                            
                            # Create tool definition
                            tools.append({
                                "type": "function",
                                "function": {
                                    "name": "file_search",
                                    "description": "Search for information in uploaded files, documents, and PDFs. Use this tool whenever a user asks about the content of a document or file that has been uploaded.",
                                    "parameters": parameter_schema
                                }
                            })
                            frappe.log_error("Tools Debug", "Successfully added file_search tool definition")
                        except Exception as e:
                            frappe.log_error("Tools Debug", f"Error converting file search tool: {str(e)}")
                except Exception as e:
                    frappe.log_error("Tools Debug", f"Error adding file search tool: {str(e)}")
            
            # Add normal bot functions
            if hasattr(self.bot, "bot_functions") and self.bot.bot_functions:
                from .sdk_tools import create_raven_tools
                # Get tools from SDK tools
                function_tools = create_raven_tools(self.bot)
                
                # Add to our list of tools
                if function_tools:
                    raven_tools.extend(function_tools)
                    frappe.log_error("Tools Debug", f"Found {len(function_tools)} function tools for bot {self.bot.name}")
                    
                    # Convert FunctionTool objects to OpenAI tool format
                    for tool in function_tools:
                        try:
                            # Skip if missing required attributes
                            if not hasattr(tool, 'name') or not hasattr(tool, 'description'):
                                frappe.log_error("Tools Debug", f"Tool missing name or description: {str(tool)}")
                                continue
                                
                            # Get the parameter schema - check both possible attribute names
                            parameter_schema = None
                            if hasattr(tool, 'parameter_schema'):
                                parameter_schema = tool.parameter_schema
                            elif hasattr(tool, 'params_json_schema'):
                                parameter_schema = tool.params_json_schema
                            else:
                                frappe.log_error("Tools Debug", f"Tool missing parameter schema: {str(tool)}")
                                # Continue anyway with empty schema
                                parameter_schema = {"type": "object", "properties": {}}
                                
                            # Create tool definition in OpenAI format
                            tool_def = {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": parameter_schema
                                }
                            }
                            tools.append(tool_def)
                            frappe.log_error("Tools Debug", f"Added tool: {tool.name}")
                        except Exception as e:
                            frappe.log_error("Tools Debug", f"Error adding tool {getattr(tool, 'name', 'unknown')}: {str(e)}")
                
                if tools:
                    frappe.log_error("LLM Debug", f"Using {len(tools)} tools with the API request")
                    model_params["tools"] = tools
                    
                    # Determine if we should force tool usage
                    should_force_file_search = False
                    
                    # If the user is asking about files, we want to force file_search
                    file_related_keywords = [
                        'file', 'pdf', 'document', 'facture', 'invoice', 'total', 'amount', 
                        'contenu', 'content', 'que dit', 'what does', 'in this', 'dans ce', 
                        'uploaded', 'téléchargé'
                    ]
                    
                    # Check if any of the keywords are in the message (case insensitive)
                    message_lower = message.lower()
                    for keyword in file_related_keywords:
                        if keyword.lower() in message_lower:
                            should_force_file_search = True
                            frappe.log_error("Tools Debug", f"Forcing file_search tool due to keyword: {keyword}")
                            break
                    
                    # If file search is enabled and keywords matched, force the tool
                    if file_search_enabled and should_force_file_search:
                        # Find the file_search tool to force its use
                        file_search_tool = next((t for t in tools if t.get("function", {}).get("name") == "file_search"), None)
                        if file_search_tool:
                            model_params["tool_choice"] = {
                                "type": "function",
                                "function": {"name": "file_search"}
                            }
                            frappe.log_error("Tools Debug", "Set tool_choice to force file_search")
                        else:
                            model_params["tool_choice"] = "auto"
                    else:
                        model_params["tool_choice"] = "auto"
            
            # Log the request for debugging
            frappe.log_error("LLM Debug", f"Sending chat completion request to {provider} with model {model_name}")
            frappe.log_error("LLM Debug", f"Message count: {len(messages)}")
            frappe.log_error("LLM Debug", f"Using parameters: {model_params}")
            
            # Make the API request with appropriate parameters
            completion = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                **model_params
            )
            
            # Log the response type for debugging
            if completion:
                frappe.log_error("LLM Debug", f"Received completion response with {len(completion.choices)} choices")
            else:
                frappe.log_error("LLM Debug", "Received empty completion response")
                
            # Check if the model used a tool
            tool_calls = None
            tool_results = {}
            
            if completion.choices and completion.choices[0].message and completion.choices[0].message.tool_calls:
                frappe.log_error("Tools Debug", f"Model used {len(completion.choices[0].message.tool_calls)} tool(s)")
                tool_calls = completion.choices[0].message.tool_calls
                
                # Process each tool call
                for tool_call in tool_calls:
                    try:
                        # Extract tool call info
                        tool_id = tool_call.id
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                        
                        frappe.log_error("Tools Debug", f"Processing tool call: {tool_name} with args: {tool_args}")
                        
                        # Special handling for file_search tool
                        if tool_name == "file_search":
                            # Check if we have a file_search tool in our raven_tools
                            file_search_tool = next((tool for tool in raven_tools if getattr(tool, 'name', '') == "file_search"), None)
                            
                            if file_search_tool:
                                frappe.log_error("Tools Debug", f"Found file_search tool, calling it with args: {tool_args}")
                                matching_tool = file_search_tool
                            else:
                                # If we don't have the tool in our list but it was requested, create one
                                frappe.log_error("Tools Debug", "file_search tool called but not in tools list, creating on-demand")
                                try:
                                    from .rag import get_file_search_tool
                                    file_search_tool = get_file_search_tool(self.bot)
                                    if file_search_tool:
                                        matching_tool = file_search_tool
                                        frappe.log_error("Tools Debug", "Created file_search tool on-demand")
                                    else:
                                        frappe.log_error("Tools Debug", "Failed to create file_search tool on-demand")
                                        matching_tool = None
                                except Exception as fs_error:
                                    frappe.log_error("Tools Debug", f"Error creating file_search tool: {str(fs_error)}")
                                    matching_tool = None
                        else:
                            # For other tools, find the matching tool in our list
                            matching_tool = next((tool for tool in raven_tools if getattr(tool, 'name', '') == tool_name), None)
                        
                        if matching_tool:
                            # Call the tool with the provided arguments
                            if hasattr(matching_tool, "on_invoke_tool") and callable(matching_tool.on_invoke_tool):
                                # Create a dummy context
                                ctx = {"agent_id": self.bot.name}
                                
                                # Call the tool - ensure tool_args is a valid JSON string
                                # Sometimes the model gives malformed JSON
                                try:
                                    # Parse JSON to validate it
                                    json.loads(tool_args)
                                    # If valid, use as is
                                    result = await matching_tool.on_invoke_tool(ctx, tool_args)
                                except (json.JSONDecodeError, ValueError):
                                    # If invalid JSON, try to fix common issues
                                    frappe.log_error("Tools Debug", f"Invalid JSON in tool args: {tool_args}")
                                    # Try to clean up the JSON - often models add extra quotes
                                    cleaned_args = tool_args.replace('\\"', '"').replace('"{', '{').replace('}"', '}')
                                    try:
                                        # Validate the cleaned JSON
                                        json.loads(cleaned_args)
                                        # If valid now, use the cleaned version
                                        result = await matching_tool.on_invoke_tool(ctx, cleaned_args)
                                    except (json.JSONDecodeError, ValueError):
                                        # Give up and return an error
                                        frappe.log_error("Tools Debug", f"Failed to fix JSON: {tool_args}")
                                        result = json.dumps({"error": "Invalid arguments format. Expected valid JSON."})
                                except Exception as tool_error:
                                    # Handle any other errors during tool execution
                                    frappe.log_error("Tools Debug", f"Error executing tool: {str(tool_error)}")
                                    result = json.dumps({"error": f"Error executing tool: {str(tool_error)}"})
                                
                                # Store the result
                                tool_results[tool_id] = {
                                    "tool_call_id": tool_id,
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": result
                                }
                                
                                # Log the full result for debugging
                                try:
                                    frappe.log_error("Tools Debug", f"Tool {tool_name} result (full): {result}")
                                    # Also log first few characters for quick review
                                    frappe.log_error("Tools Debug", f"Tool {tool_name} result (summary): {result[:100]}{'...' if len(result) > 100 else ''}")
                                    
                                    # Check if the result is valid JSON - if not, try to make it valid
                                    if result:
                                        try:
                                            json.loads(result)
                                        except (json.JSONDecodeError, ValueError):
                                            frappe.log_error("Tools Debug", f"Result from {tool_name} is not valid JSON, attempting to fix")
                                            # Common issue: function may have returned plain string or object instead of JSON
                                            if not result.startswith('{') and not result.startswith('['):
                                                # Wrap in JSON
                                                fixed_result = json.dumps({"result": result})
                                                frappe.log_error("Tools Debug", f"Fixed result: {fixed_result}")
                                                result = fixed_result
                                except Exception as log_error:
                                    frappe.log_error("Tools Debug", f"Error logging tool result: {str(log_error)}")
                            else:
                                frappe.log_error("Tools Debug", f"Tool {tool_name} does not have an on_invoke_tool method")
                                tool_results[tool_id] = {
                                    "tool_call_id": tool_id,
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": f"Error: Tool {tool_name} does not have an implementation"
                                }
                        else:
                            frappe.log_error("Tools Debug", f"Tool {tool_name} not found")
                            tool_results[tool_id] = {
                                "tool_call_id": tool_id,
                                "role": "tool",
                                "name": tool_name,
                                "content": f"Error: Tool {tool_name} not found"
                            }
                    except Exception as e:
                        frappe.log_error("Tools Debug", f"Error processing tool call: {str(e)}")
                        # Create error result
                        tool_results[tool_id] = {
                            "tool_call_id": tool_id,
                            "role": "tool",
                            "name": tool_name if 'tool_name' in locals() else "unknown",
                            "content": f"Error: {str(e)}"
                        }
                
                # If there were tool calls, make a follow-up request with the tool results
                if tool_results:
                    frappe.log_error("Tools Debug", f"Making follow-up request with {len(tool_results)} tool results")
                    
                    # Copy the original messages
                    follow_up_messages = list(messages)
                    
                    # Add the assistant message with tool calls
                    follow_up_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in tool_calls
                        ]
                    })
                    
                    # Add each tool result as a message
                    for tool_id, result in tool_results.items():
                        follow_up_messages.append({
                            "role": "tool",
                            "tool_call_id": result["tool_call_id"],
                            "name": result["name"],
                            "content": result["content"]
                        })
                    
                    frappe.log_error("Tools Debug", f"Follow-up messages: {len(follow_up_messages)}")
                    
                    # Make the follow-up request without tool params
                    follow_up_params = {k: v for k, v in model_params.items() if k not in ['tools', 'tool_choice']}
                    
                    completion = await client.chat.completions.create(
                        model=model_name,
                        messages=follow_up_messages,
                        **follow_up_params
                    )
                    
                    frappe.log_error("Tools Debug", "Follow-up request completed")
            
            # Extract the final response content
            response_text = ""
            if completion and completion.choices and len(completion.choices) > 0:
                if completion.choices[0].message and completion.choices[0].message.content:
                    response_text = completion.choices[0].message.content
            
            # Return the response in the expected format
            return {
                "response": completion,
                "message": response_text
            }
            
        except Exception as e:
            # Detailed error logging
            error_message = str(e)
            error_type = type(e).__name__
            frappe.log_error("LLM Direct API Error", f"{error_type}: {error_message}")
            
            # Provide a helpful error message based on the error
            if "Connection refused" in error_message:
                user_message = f"Could not connect to the local LLM at {settings.local_llm_api_url}. Please ensure the LLM service is running."
            elif "Timeout" in error_type or "timeout" in error_message.lower():
                user_message = "The request to the local LLM timed out. The model may be processing a large request or experiencing issues."
            elif "404" in error_message:
                user_message = f"The API endpoint at {settings.local_llm_api_url} was not found. Please check your Local LLM API URL in Raven Settings."
            elif "model_not_found" in error_message.lower() or "model not found" in error_message.lower():
                user_message = f"The model '{model_name}' was not found. Please check that you have the correct model loaded in your local LLM."
            else:
                user_message = f"Error communicating with the local LLM: {error_type}. Please check the server logs for details."
            
            # Return error in the expected format
            return {
                "response": {},
                "message": user_message,
                "error": True
            }
    
    def _get_direct_api_model_params(self, provider: str, model_name: str) -> dict:
        """
        Get model parameters for direct API requests based on provider and model
        
        Args:
            provider: The local LLM provider
            model_name: The model name
            
        Returns:
            dict: Model parameters for the API request
        """
        # Common parameters for all providers
        common_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048,
            "stream": False
        }
        
        # Parse agent settings from bot configuration for temperature
        if hasattr(self.bot, "agent_settings") and self.bot.agent_settings:
            try:
                agent_settings = json.loads(self.bot.agent_settings)
                if "temperature" in agent_settings:
                    common_params["temperature"] = float(agent_settings["temperature"])
                if "top_p" in agent_settings:
                    common_params["top_p"] = float(agent_settings["top_p"])
                if "max_tokens" in agent_settings:
                    common_params["max_tokens"] = int(agent_settings["max_tokens"])
            except (json.JSONDecodeError, ValueError) as e:
                frappe.log_error(f"Invalid agent settings JSON: {str(e)}")
        
        # Provider-specific parameters
        if provider == "LM Studio":
            if "llama" in model_name.lower():
                return {
                    **common_params,
                    "stop": ["<|im_end|>"],
                    "repeat_penalty": 1.1
                }
            elif "mistral" in model_name.lower():
                return {
                    **common_params,
                    "stop": ["<|im_end|>"],
                    "repeat_penalty": 1.2
                }
            elif "openhermes" in model_name.lower():
                return {
                    **common_params,
                    "repeat_penalty": 1.1
                }
            
            # Default parameters for LM Studio
            return common_params
            
        elif provider == "Ollama":
            # Ollama-specific params
            return common_params
            
        elif provider == "LocalAI":
            # LocalAI-specific params
            return common_params
            
        # Default parameters for unknown provider
        return common_params
    
    async def process_message_stream(self, message: str, conversation_history=None):
        """
        Process a message with the agent and stream the response
        
        Args:
            message: Message to process
            conversation_history: Optional list of previous messages in the conversation
            
        Yields:
            str: Chunks of the response
        """
        # Get provider information for the bot
        provider = getattr(self.bot, "model_provider", ModelProvider.OPENAI.value)
        settings = frappe.get_cached_doc("Raven Settings")
        
        # Check if we should use direct API calls for local providers
        using_local_llm = False
        actual_provider = provider
        
        if provider == ModelProvider.LOCAL_LLM.value:
            # Get the actual provider from settings
            actual_provider = settings.get("local_llm_provider")
            if actual_provider in ["LM Studio", "Ollama", "LocalAI"]:
                using_local_llm = True
                frappe.log_error("LLM Debug", f"Using direct API streaming for {actual_provider}")
            
        elif provider in [ModelProvider.LM_STUDIO.value, ModelProvider.OLLAMA.value, ModelProvider.LOCALAI.value]:
            using_local_llm = True
            frappe.log_error("LLM Debug", f"Using direct API streaming for {provider}")
        
        # If using a local LLM, use direct API calls instead of the SDK Agent
        if using_local_llm:
            frappe.log_error("LLM Debug", "Using direct API streaming path for local LLM")
            async for chunk in self._process_message_stream_direct_api(message, conversation_history, provider=actual_provider):
                yield chunk
            return
            
        # For cloud providers like OpenAI, use the SDK Agent as before
        # Get the agent
        if not self.agent:
            self.create_agent()
            
        try:
            # Determine the input based on conversation history
            if conversation_history:
                # If we have history, use it with the new message appended
                # Add the new user message
                conversation_history.append({"role": "user", "content": message})
                input_data = conversation_history
            else:
                # Otherwise just use the message directly
                input_data = message
                
            # Run the agent with the appropriate input
            try:
                result = Runner.run_streamed(self.agent, input=input_data)
                
                # Verify that result is not None
                if result is None:
                    frappe.log_error("SDK Clean Error", "Runner.run_streamed returned None")
                    yield "Sorry, I encountered an error processing your message."
                    return
                
                # Stream events
                event_count = 0
                content_received = False
                log_threshold = 1000  # Only log once we've hit a high threshold without content
                
                async for event in result.stream_events():
                    event_count += 1
                    
                    # Process raw_response_event type efficiently
                    if hasattr(event, "type") and event.type == "raw_response_event":
                        # Safely access nested attributes with None checks
                        data = getattr(event, "data", None)
                        if data is not None:
                            delta = getattr(data, "delta", None)
                            if delta is not None:
                                content = getattr(delta, "content", None)
                                if content:
                                    content_received = True
                                    yield content
                
                # If no content was received but we have results, use final_output
                if event_count > 0 and not content_received:
                    # No need to log every time, this is an expected case with some models
                    # Only log when events exceed the threshold without content
                    if event_count > log_threshold:
                        frappe.log_error("SDK Agents",f"High event count ({event_count}) without content in stream_events")
                        
                    # Access final_output attribute safely
                    if hasattr(result, "final_output"):
                        final_output = result.final_output
                        if final_output is not None:
                            yield final_output
                        else:
                            yield "I received your message, but had trouble generating a response."
                    else:
                        yield "I received your message, but couldn't generate a response."
            
            except Exception as e:
                # Process exception more efficiently
                error_message = str(e)
                error_lower = error_message.lower()
                
                # Check for common error cases
                if "429" in error_message or "quota" in error_lower or "exceeded" in error_lower:
                    frappe.log_error("OpenAI quota exceeded", error_message)
                    raise ValueError("OpenAI API quota exceeded. Please check your OpenAI account billing details.")
                
                elif "authentication" in error_lower or "api key" in error_lower or "invalid" in error_lower:
                    frappe.log_error("OpenAI Authentication Error", error_message)
                    raise ValueError("OpenAI API authentication failed. Please check your API key in Raven Settings.")
                
                # For other errors, log concisely and try to get final result
                frappe.log_error("SDK Streaming Error", error_message)
                
                # Try to recover with final_output if available
                try:
                    if result is not None and hasattr(result, "final_output"):
                        final_output = result.final_output
                        if final_output is not None:
                            yield final_output
                        else:
                            yield "Sorry, there was an error processing your request. The response had no content."
                    else:
                        yield "Sorry, there was an error processing your request. No valid response was received."
                except Exception as inner_e:
                    # Log the inner exception with a short message
                    frappe.log_error("SDK Inner Error", str(inner_e))
                    yield "Sorry, there was an error processing your request. The system encountered an unexpected condition."
        
        except Exception as e:
            # Process exception more efficiently
            error_message = str(e)
            error_lower = error_message.lower()
            error_type = type(e).__name__
            
            # Handle common known error cases with specific messages
            if "429" in error_message or "quota" in error_lower or "exceeded" in error_lower:
                frappe.log_error("OpenAI quota exceeded", error_message)
                raise ValueError("OpenAI API quota exceeded. Please check your OpenAI account billing details.")
            
            elif "authentication" in error_lower or "api key" in error_lower:
                frappe.log_error("OpenAI Authentication Error", error_message)
                raise ValueError("OpenAI API authentication failed. Please check your API key in Raven Settings.")
            
            elif "model_not_found" in error_lower or "does not exist" in error_lower:
                frappe.log_error("Model Not Found", error_message)
                raise ValueError("The specified model was not found. Please check that the model name is correct and available.")
            
            # For all other errors, log concisely with error type
            frappe.log_error("SDK Agents", error_message)
            
            # Re-raise with a clean error message
            raise ValueError(f"Error processing message: {error_type}")
            
    async def _process_message_stream_direct_api(self, message: str, conversation_history=None, provider="LM Studio"):
        """
        Process a message with direct API calls to local LLM provider with streaming
        This method bypasses the SDK Agent for better compatibility with local LLMs
        
        Args:
            message: Message to process
            conversation_history: Optional list of previous messages in the conversation
            provider: The local LLM provider to use
            
        Yields:
            str: Chunks of the response
        """
        try:
            # Get settings for the local LLM
            settings = frappe.get_cached_doc("Raven Settings")
            
            # Verify AI integration and local LLM is enabled
            if not settings.enable_ai_integration:
                yield "AI Integration is not enabled in Raven Settings"
                return
            
            if not settings.enable_local_llm:
                yield "Local LLM is not enabled in Raven Settings"
                return
            
            if not settings.local_llm_api_url:
                yield "Local LLM API URL not configured in Raven Settings"
                return
                
            # Get model name from the bot
            model_name = getattr(self.bot, "model_name", "")
            if not model_name:
                # Use a reasonable default based on provider
                if provider == "LM Studio":
                    model_name = "openhermes"
                elif provider == "Ollama":
                    model_name = "llama2"
                elif provider == "LocalAI":
                    model_name = "gpt4all"
                else:
                    model_name = "unknown"  # Will be caught in error handling
                    
                frappe.log_error("LLM Debug", f"No model name specified, using default: {model_name}")
            
            # Import OpenAI client library for direct API calls
            from openai import AsyncOpenAI
            
            # Create a client instance with the local LLM API URL
            api_key = "sk-no-key-required"  # Most local providers don't check the API key
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.local_llm_api_url
            )
            
            # Log the client initialization for streaming
            frappe.log_error("LLM Debug", f"Created AsyncOpenAI streaming client with base URL: {settings.local_llm_api_url}")
            
            # Prepare the messages list for the chat completion API
            messages = []
            
            # System message (instructions)
            if hasattr(self.bot, "instruction") and self.bot.instruction:
                messages.append({
                    "role": "system",
                    "content": self.bot.instruction
                })
            
            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history)
                
                # Check if the last message is already the current user message
                if conversation_history[-1].get("role") != "user" or conversation_history[-1].get("content") != message:
                    # Add the current message if it's not already in the history
                    messages.append({
                        "role": "user",
                        "content": message
                    })
            else:
                # Just add the current message if no history
                messages.append({
                    "role": "user",
                    "content": message
                })
            
            # Prepare the model parameters based on provider and model
            model_params = self._get_direct_api_model_params(provider, model_name)
            # Make sure streaming is enabled
            model_params["stream"] = True
            
            # Log the request for debugging
            frappe.log_error("LLM Debug", f"Sending streaming chat completion request to {provider} with model {model_name}")
            frappe.log_error("LLM Debug", f"Streaming message count: {len(messages)}")
            
            # Make the API request with streaming
            stream = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                **model_params
            )
            
            # Stream the response chunks
            content_received = False
            async for chunk in stream:
                try:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        content_received = True
                        yield content
                except Exception as chunk_error:
                    frappe.log_error("LLM Streaming Chunk Error", f"Error processing chunk: {str(chunk_error)}")
            
            # Check if we received any content
            if not content_received:
                yield "I received your message, but didn't receive any response content from the local LLM."
            
        except Exception as e:
            # Detailed error logging
            error_message = str(e)
            error_type = type(e).__name__
            frappe.log_error("LLM Direct API Streaming Error", f"{error_type}: {error_message}")
            
            # Provide a helpful error message based on the error
            if "Connection refused" in error_message:
                user_message = f"Could not connect to the local LLM at {settings.local_llm_api_url}. Please ensure the LLM service is running."
            elif "Timeout" in error_type or "timeout" in error_message.lower():
                user_message = "The request to the local LLM timed out. The model may be processing a large request or experiencing issues."
            elif "404" in error_message:
                user_message = f"The API endpoint at {settings.local_llm_api_url} was not found. Please check your Local LLM API URL in Raven Settings."
            elif "model_not_found" in error_message.lower() or "model not found" in error_message.lower():
                user_message = f"The model '{model_name}' was not found. Please check that you have the correct model loaded in your local LLM."
            else:
                user_message = f"Error communicating with the local LLM: {error_type}. Please check the server logs for details."
            
            # Return error message
            yield user_message
    
    async def upload_file_to_agent(self, file_path: str) -> str:
        """
        Upload a file to the agent
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: File ID
        """
        if not os.path.exists(file_path):
            frappe.throw(f"File not found: {file_path}")
        
        # If using OpenAI, use their file upload API
        if self.bot.model_provider == ModelProvider.OPENAI.value:
            try:
                from openai import OpenAI
                
                client = OpenAI(
                    api_key=frappe.get_doc("Raven Settings").openai_api_key
                )
                
                with open(file_path, "rb") as file:
                    response = client.files.create(
                        file=file,
                        purpose="assistants"
                    )
                
                return response.id
            except ImportError:
                frappe.throw("OpenAI package not available. Run 'pip install openai'")
            except Exception as e:
                frappe.throw(f"Error uploading file to OpenAI: {e}")
        
        # For local models, handle file content directly through RAG
        else:
            if not self.bot.enable_local_rag:
                frappe.throw("Local RAG must be enabled to use files with local models")
            
            # Process file for local RAG (just return the file path for now)
            # The actual file processing will be handled by the local RAG provider
            return file_path


# This class will be implemented in Phase 5
class LocalModelProvider:
    """Base class for local model providers"""
    
    def __init__(self, api_base_url: str):
        """
        Initialize the provider
        
        Args:
            api_base_url: Base URL for the API
        """
        self.api_base_url = api_base_url
    
    def get_model(self, model_name: str) -> interface.Model:
        """
        Get a model from this provider
        
        Args:
            model_name: Name of the model
            
        Returns:
            interface.Model: Model interface
        """
        raise NotImplementedError("Subclasses must implement this method")


class LMStudioProvider(LocalModelProvider):
    """Provider for LM Studio"""
    
    def get_model(self, model_name: str) -> interface.Model:
        """
        Get an LM Studio model
        
        Args:
            model_name: Model name
            
        Returns:
            interface.Model: Model interface
        """
        try:
            from openai import AsyncOpenAI
            # Import the models module from the agents SDK explicitly
            from agents.models import openai_chatcompletions
            
            # Model-specific parameters
            model_params = self._get_model_params(model_name)
            
            # Log the configuration for debugging
            frappe.log_error("LLM Debug", f"Initializing LM Studio with base URL: {self.api_base_url}")
            frappe.log_error("LLM Debug", f"Using model: {model_name} with parameters: {model_params}")
            
            # Create an OpenAI client with the LM Studio base URL
            client = AsyncOpenAI(
                api_key="lm-studio",  # LM Studio doesn't check the API key
                base_url=self.api_base_url
            )
            
            # We can't easily test the async client here, so we'll just log it
            frappe.log_error("LLM Debug", "LM Studio client created, connection will be tested on first use.")
            
            # Create a compatible ChatCompletions model (model_params will be passed in the chat completion request)
            # We store the model_params in a variable to be used later in the request 
            # because OpenAIChatCompletionsModel doesn't accept model_kwargs parameter
            self.model_params = model_params
            
            # Create a model instance with only the parameters it accepts
            model = openai_chatcompletions.OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=client
            )
            
            frappe.log_error("LLM Debug", f"Successfully created LM Studio model instance: {type(model)}")
            return model
        except ImportError:
            frappe.throw("OpenAI package not available. Run 'pip install openai'")
    
    def _get_model_params(self, model_name: str) -> dict:
        """
        Get model-specific parameters
        
        Args:
            model_name: Model name
            
        Returns:
            dict: Model parameters
        """
        # Common parameters for all models
        common_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048
        }
        
        # Model-specific parameters
        if "llama" in model_name.lower():
            return {
                **common_params,
                "stop": ["<|im_end|>"],
                "repeat_penalty": 1.1
            }
        elif "mistral" in model_name.lower():
            return {
                **common_params,
                "stop": ["<|im_end|>"],
                "repeat_penalty": 1.2
            }
        elif "gemma" in model_name.lower():
            return {
                **common_params,
                "repeat_penalty": 1.1
            }
        
        # Default parameters
        return common_params


class OllamaProvider(LocalModelProvider):
    """Provider for Ollama"""
    
    def get_model(self, model_name: str) -> interface.Model:
        """
        Get an Ollama model
        
        Args:
            model_name: Model name
            
        Returns:
            interface.Model: Model interface
        """
        try:
            from openai import AsyncOpenAI
            # Import the models module from the agents SDK explicitly
            from agents.models import openai_chatcompletions
            
            # Model-specific parameters
            model_params = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }
            
            # Create an OpenAI client with the Ollama base URL
            client = AsyncOpenAI(
                api_key="ollama",  # Ollama doesn't check the API key
                base_url=self.api_base_url
            )
            
            # Create a compatible ChatCompletions model (model_params will be passed in the chat completion request)
            # We store the model_params in a variable to be used later in the request 
            # because OpenAIChatCompletionsModel doesn't accept model_kwargs parameter
            self.model_params = model_params
            
            # Create a model instance with only the parameters it accepts
            return openai_chatcompletions.OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=client
            )
        except ImportError:
            frappe.throw("OpenAI package not available. Run 'pip install openai'")


class LocalAIProvider(LocalModelProvider):
    """Provider for LocalAI"""
    
    def get_model(self, model_name: str) -> interface.Model:
        """
        Get a LocalAI model
        
        Args:
            model_name: Model name
            
        Returns:
            interface.Model: Model interface
        """
        try:
            from openai import AsyncOpenAI
            # Import the models module from the agents SDK explicitly
            from agents.models import openai_chatcompletions
            
            # Model-specific parameters
            model_params = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }
            
            # Create an OpenAI client with the LocalAI base URL
            client = AsyncOpenAI(
                api_key="localai",  # LocalAI doesn't check the API key
                base_url=self.api_base_url
            )
            
            # Create a compatible ChatCompletions model (model_params will be passed in the chat completion request)
            # We store the model_params in a variable to be used later in the request 
            # because OpenAIChatCompletionsModel doesn't accept model_kwargs parameter
            self.model_params = model_params
            
            # Create a model instance with only the parameters it accepts
            return openai_chatcompletions.OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=client
            )
        except ImportError:
            frappe.throw("OpenAI package not available. Run 'pip install openai'")