# raven/ai/agent_manager.py
from agents import Agent, Runner
from typing import Dict, Any
import frappe
from openai import OpenAI

class RavenAgentManager:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    def create_agent_from_bot(self, bot_doc) -> Agent:
        """Create an agent with the bot's specific provider"""
        
        # Get the client for this bot
        client = self._get_client_for_bot(bot_doc)
        
        # RAG configuration if enabled
        rag_config = None
        if bot_doc.use_local_rag:
            rag_config = self._setup_rag_config(bot_doc)
        
        # Determine the model
        if bot_doc.model_provider == "local" and bot_doc.local_model_override:
            model = bot_doc.local_model_override
        else:
            model = bot_doc.model or "gpt-4"
        
        # Create the agent
        agent = Agent(
            name=bot_doc.bot_name,
            instructions=bot_doc.instruction,
            model=model,
            model_settings=self._get_model_settings(bot_doc),
            tools=self._convert_tools(bot_doc),
            output_guardrails=self._setup_guardrails(bot_doc),
        )
        
        # Add RAG configuration to context if necessary
        if rag_config:
            agent.metadata = {"rag_config": rag_config}
        
        self.agents[bot_doc.name] = agent
        return agent
    
    def _get_client_for_bot(self, bot_doc) -> OpenAI:
        """Get the OpenAI client for a specific bot"""
        settings = frappe.get_doc("Raven Settings")
        
        if bot_doc.model_provider == "openai":
            if not settings.enable_openai_services:
                frappe.throw("OpenAI services are not enabled in settings")
                
            return OpenAI(
                api_key=settings.get_password("openai_api_key"),
                organization=settings.openai_organisation_id
            )
        
        elif bot_doc.model_provider == "local":
            if not settings.enable_local_llm:
                frappe.throw("Local LLM is not enabled in settings")
                
            # Use the provider configured in settings
            provider = settings.local_llm_provider
            api_url = settings.local_llm_api_url
            
            if not api_url:
                frappe.throw(f"Local LLM API URL not configured for provider: {provider}")
            
            # Create an OpenAI-compatible client for the local provider
            return OpenAI(
                api_key="sk-111222333",  # Dummy key for local providers
                base_url=api_url
            )
        
        else:
            frappe.throw(f"Unknown provider: {bot_doc.model_provider}")
    
    def _setup_rag_config(self, bot_doc):
        """Set up RAG for a bot"""
        rag_settings = bot_doc.rag_settings or {}
        
        return {
            "enabled": True,
            "similarity_threshold": rag_settings.get("similarity_threshold", 0.7),
            "max_results": rag_settings.get("max_results", 5),
            "chunk_size": rag_settings.get("chunk_size", 1000)
        }
    
    def _get_model_settings(self, bot_doc):
        """Get model settings"""
        from agents import ModelSettings
        
        # Base configuration
        settings = ModelSettings()
        
        # Specific configuration for reasoning models
        if bot_doc.model and bot_doc.model.startswith("o") and bot_doc.reasoning_effort:
            settings.extra = {"reasoning_effort": bot_doc.reasoning_effort}
        
        return settings
    
    def _convert_tools(self, bot_doc):
        """Convert bot tools to Agent SDK tools"""
        from ..functions import get_tool_for_function
        
        tools = []
        
        # Convert bot functions to tools
        for bot_function in bot_doc.bot_functions or []:
            tool = get_tool_for_function(bot_function)
            if tool:
                tools.append(tool)
        
        # Add file search tool if enabled
        if bot_doc.enable_file_search:
            from agents.tools import file_search
            tools.append(file_search)
        
        # Add code interpreter if enabled (only for OpenAI)
        if bot_doc.enable_code_interpreter and bot_doc.model_provider == "openai":
            from agents.tools import code_interpreter
            tools.append(code_interpreter)
        
        return tools
    
    def _setup_guardrails(self, bot_doc):
        """Set up guardrails for the bot"""
        guardrails = []
        
        # Add guardrails based on bot configuration
        if not bot_doc.allow_bot_to_write_documents:
            from agents import OutputGuardrail
            
            def prevent_document_writes(context, result):
                # Verify that the result doesn't contain write operations
                return True
            
            guardrails.append(OutputGuardrail(
                name="prevent_document_writes",
                check_function=prevent_document_writes
            ))
        
        return guardrails
    
    async def process_message(self, bot_name: str, message: str, 
                            channel_id: str, context: Dict = None):
        """Process a message with the correct provider and RAG if necessary"""
        agent = self.agents.get(bot_name)
        if not agent:
            bot_doc = frappe.get_doc("Raven Bot", bot_name)
            agent = self.create_agent_from_bot(bot_doc)
        
        # RAG context if enabled
        run_context = context or {}
        if agent.metadata and agent.metadata.get("rag_config"):
            from ..rag.retriever import RavenRAGRetriever
            retriever = RavenRAGRetriever(agent.metadata["rag_config"])
            relevant_docs = await retriever.retrieve_context(message)
            run_context["rag_context"] = relevant_docs
        
        # Execute
        result = await Runner.run(
            agent, 
            input=message,
            context=run_context
        )
        
        return result
    
    async def stream_response(self, agent_name: str, message: str, context: Dict = None):
        """Stream the agent's response"""
        agent = self.agents.get(agent_name)
        if not agent:
            bot_doc = frappe.get_doc("Raven Bot", agent_name)
            agent = self.create_agent_from_bot(bot_doc)
        
        # Context with RAG if necessary
        run_context = context or {}
        if agent.metadata and agent.metadata.get("rag_config"):
            from ..rag.retriever import RavenRAGRetriever
            retriever = RavenRAGRetriever(agent.metadata["rag_config"])
            relevant_docs = await retriever.retrieve_context(message, agent_name)
            run_context["rag_context"] = relevant_docs
        
        # Use the SDK's streaming API
        async for event in await Runner.stream(
            agent,
            input=message,
            context=run_context
        ):
            yield event
    
    def get_client_for_bot(self, bot_name: str) -> OpenAI:
        """Get the OpenAI client for a bot by its name"""
        bot_doc = frappe.get_doc("Raven Bot", bot_name)
        return self._get_client_for_bot(bot_doc)