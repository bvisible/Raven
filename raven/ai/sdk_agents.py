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
        
        # Create the agent
        self.agent = Agent(
            name=self.bot.bot_name,
            instructions=self.bot.instruction,
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
        
        # Add file search tool if enabled
        if self.bot.enable_file_search:
            if self.bot.enable_local_rag:
                # Use local RAG implementation
                from .local_rag import create_local_file_search_tool
                tools.append(create_local_file_search_tool(self.bot))
            else:
                # Use OpenAI's FileSearchTool
                file_search_kwargs = {"include_search_results": True}
                
                # Add Vector Stores if specified
                if hasattr(self.bot, "vector_store_ids") and self.bot.vector_store_ids:
                    vector_store_ids = [vs.strip() for vs in self.bot.vector_store_ids.split(",")]
                    if vector_store_ids:
                        file_search_kwargs["vector_store_ids"] = vector_store_ids
                
                tools.append(FileSearchTool(**file_search_kwargs))
        
        # Add Code Interpreter tool if enabled
        if self.bot.enable_code_interpreter:
            # Code Interpreter is only supported by OpenAI's specific models
            if self.bot.model_provider == ModelProvider.OPENAI.value:
                tools.append(ComputerTool())
                
                # If specific model is required for code interpreter, check compatibility
                compatible_models = ["gpt-4o", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-4-vision-preview"]
                if getattr(self.bot, "model_name", "gpt-4o") not in compatible_models:
                    frappe.log_error(f"Code Interpreter may not work with model {self.bot.model_name}. Recommended models: {', '.join(compatible_models)}")
            else:
                frappe.log_error(f"Code Interpreter is not supported by {self.bot.model_provider}. Only available with OpenAI models.")
        
        # Add CRUD functions as tools
        from .sdk_tools import create_raven_tools
        raven_tools = create_raven_tools(self.bot)
        tools.extend(raven_tools)
        
        # Log the tools being used
        tool_names = [type(tool).__name__ for tool in tools]
        frappe.logger().debug(f"Tools for bot {self.bot.bot_name}: {tool_names}")
        
        return tools
    
    def _get_model(self) -> str:
        """
        Get the model to use for the agent
        
        Returns:
            str: Model identifier
        """
        provider = getattr(self.bot, "model_provider", ModelProvider.OPENAI.value)
        model_name = getattr(self.bot, "model_name", "gpt-4o")
        
        if provider == ModelProvider.OPENAI.value:
            return model_name
        else:
            # For local models, we need to return the model from the provider
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
        
        if provider == ModelProvider.LM_STUDIO.value:
            # Create LM Studio model provider
            if not settings.lm_studio_api_url:
                frappe.throw("LM Studio API URL not configured in Raven Settings")
            
            provider_instance = LMStudioProvider(api_base_url=settings.lm_studio_api_url)
            return provider_instance.get_model(model_name)
            
        elif provider == ModelProvider.OLLAMA.value:
            # Create Ollama model provider
            if not settings.ollama_api_url:
                frappe.throw("Ollama API URL not configured in Raven Settings")
                
            provider_instance = OllamaProvider(api_base_url=settings.ollama_api_url)
            return provider_instance.get_model(model_name)
            
        elif provider == ModelProvider.LOCALAI.value:
            # Create LocalAI model provider
            if not settings.localai_api_url:
                frappe.throw("LocalAI API URL not configured in Raven Settings")
                
            provider_instance = LocalAIProvider(api_base_url=settings.localai_api_url)
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
        
        # Create model settings
        model_settings = ModelSettings(
            temperature=temperature,
            top_p=top_p,
            truncation="auto"
        )
        
        return model_settings
    
    def get_runner(self) -> Runner:
        """
        Get a runner for the agent
        
        Returns:
            Runner: Runner for the agent
        """
        if not self.agent:
            self.create_agent()
            
        if not self.runner:
            self.runner = Runner(self.agent)
            
        return self.runner
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a message with the agent
        
        Args:
            message: Message to process
            
        Returns:
            Dict[str, Any]: Response from the agent
        """
        runner = self.get_runner()
        
        # Using the async API
        response = await runner.async_run(message)
        
        return {
            "response": response,
            "message": response.response.content
        }
    
    async def process_message_stream(self, message: str):
        """
        Process a message with the agent and stream the response
        
        Args:
            message: Message to process
            
        Yields:
            str: Chunks of the response
        """
        runner = self.get_runner()
        
        # Start the run
        run = await runner.async_create_run(message)
        
        # Stream the response
        async for chunk in run.async_stream():
            if hasattr(chunk, "delta") and chunk.delta.content:
                yield chunk.delta.content
    
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
            
            # Model-specific parameters
            model_params = self._get_model_params(model_name)
            
            # Create an OpenAI client with the LM Studio base URL
            client = AsyncOpenAI(
                api_key="lm-studio",  # LM Studio doesn't check the API key
                base_url=self.api_base_url
            )
            
            # Create a compatible ChatCompletions model
            return models.openai_chatcompletions.OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=client,
                model_kwargs=model_params
            )
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
            
            # Create a compatible ChatCompletions model
            return models.openai_chatcompletions.OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=client,
                model_kwargs=model_params
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
            
            # Create a compatible ChatCompletions model
            return models.openai_chatcompletions.OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=client,
                model_kwargs=model_params
            )
        except ImportError:
            frappe.throw("OpenAI package not available. Run 'pip install openai'")