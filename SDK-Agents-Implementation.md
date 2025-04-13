# OpenAI Agents SDK Integration with RAG for Raven

## Overview
This document provides comprehensive information about the integration of the OpenAI Agents SDK into Raven, replacing the obsolete `openai.beta.assistants.create` API. The implementation maintains backward compatibility with existing CRUD functions while adding RAG (Retrieval-Augmented Generation) capabilities for both OpenAI and open source LLMs.

## Key Features
- Support for the OpenAI Agents SDK with multiple tools integration
- Multiple LLM provider support:
  - OpenAI (cloud-based)
  - LM Studio (local models)
  - Ollama (local models)
  - LocalAI (local models)
- RAG capabilities:
  - OpenAI's built-in RAG with vector stores
  - Local RAG with multiple vector store options:
    - ChromaDB
    - FAISS
    - Weaviate
- Tool integration:
  - FileSearchTool for document retrieval
  - ComputerTool for code execution and data processing
  - FunctionTool for Frappe CRUD operations
- Streaming responses for real-time message generation
- File handling for both OpenAI and local LLM implementations
- Graceful fallback when dependencies aren't available

## Implementation Files

### Core Modules
- `/raven/ai/sdk_agents.py` - Main SDK Agent management
  - `RavenAgentManager` class for managing agents
  - `LocalModelProvider` and its implementations (LM Studio, Ollama, LocalAI)
  - Dummy fallback classes for when SDK is not available
  
- `/raven/ai/sdk_tools.py` - Tools integration
  - Function tool wrappers for Frappe CRUD operations
  - CRUD function generators for DocTypes
  - Parameter schema validation
  
- `/raven/ai/local_rag.py` - Local RAG implementation
  - Base `LocalRAGProvider` class
  - Implementations for ChromaDB, FAISS, and Weaviate
  - Document processing and indexing functions
  
- `/raven/ai/sdk_handler.py` - Message handling
  - Asynchronous message handling functions
  - Streaming response handling
  - File processing and attachment handling

### Modified Files
- `/raven/ai/ai.py` - Updated AI module
  - Conditional handling based on model provider
  - Integration with existing channels and threads
  - Added SDK availability check
  
- `/raven/raven_bot/doctype/raven_bot/raven_bot.json` - Updated schema
  - Added fields for model provider, model name, RAG settings
  - Added vector store IDs for OpenAI RAG
  - Added agent settings for model parameters

- `/raven/raven_bot/doctype/raven_bot/raven_bot.py` - Updated bot implementation
  - Removed OpenAI Assistant creation methods
  - Added SDK Agent creation and management
  - Updated message handling
  
- `/raven/raven/doctype/raven_settings/raven_settings.json` - Updated schema
  - Added local LLM configuration options
  - Added API URL fields for LM Studio, Ollama, and LocalAI

- `/frontend/src/components/feature/settings/ai/bots/AIFeaturesBotForm.tsx` - Updated UI
  - Added model provider selection dropdown
  - Added model name input field
  - Added RAG configuration options
  - Added local LLM settings

## Technical Implementation Details

### SDK Agent Management

The `RavenAgentManager` class handles the creation and management of SDK Agents:

```python
class RavenAgentManager:
    """
    Agent manager for Raven using the OpenAI Agents SDK
    """
    
    def __init__(self, bot_doc):
        """Initialize the agent manager with a Raven bot"""
        self.bot = bot_doc
        self.settings = frappe.get_cached_doc("Raven Settings")
        
        # Configure model provider and API keys
        self._configure_provider()
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create an Agent instance with appropriate model and tools"""
        # Get tools based on bot configuration
        tools = self._get_tools()
        
        # Get model and model settings
        model = self._get_model()
        model_settings = self._get_model_settings()
        
        # Create the agent
        agent = Agent(
            name=self.bot.bot_name,
            instructions=self.bot.instruction,
            tools=tools,
            model=model,
            model_settings=model_settings
        )
        
        return agent
    
    async def process_message(self, message: str, files=None) -> str:
        """Process a message and return a response"""
        runner = Runner(self.agent)
        result = await runner.async_run(message)
        return result.final_output
```

### Local Model Providers

For local LLMs, custom provider classes handle the specific requirements of each platform:

```python
class LMStudioProvider(LocalModelProvider):
    """Provider for LM Studio"""
    
    def get_model(self, model_name: str) -> interface.Model:
        """Get an LM Studio model"""
        from openai import AsyncOpenAI
        
        # Create an OpenAI client with the LM Studio base URL
        client = AsyncOpenAI(
            api_key="lm-studio", # Any value, LM Studio doesn't check
            base_url=self.api_base_url
        )
        
        # Model-specific parameters
        model_params = self._get_model_params(model_name)
        
        # Create a compatible ChatCompletions model
        return models.openai_chatcompletions.OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=client,
            model_kwargs=model_params
        )
```

### Local RAG Implementation

The local RAG implementation supports multiple vector stores:

```python
class ChromaRAGProvider(LocalRAGProvider):
    """RAG provider using ChromaDB"""
    
    def _init_vector_db(self):
        """Initialize the vector database"""
        import chromadb
        from chromadb.config import Settings
        
        # Configure Chroma
        self.chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=os.path.join(self.temp_dir, "chroma_db")
        ))
        
        # Create a collection for this thread
        self.collection = self.chroma_client.create_collection(
            name=f"thread_{self.thread_id}",
            metadata={"thread_id": self.thread_id}
        )
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the vector database for relevant documents"""
        # Get embedding for the query
        query_embedding = self._get_embedding(query)
        
        # Search in Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas"]
        )
        
        return self._format_results(results)
```

### Message Streaming

Real-time message streaming is implemented for all providers:

```python
async def stream_response(agent, message: str, callback):
    """Stream a response from the agent with real-time updates"""
    runner = Runner(agent)
    run = await runner.async_create_run(message)
    
    # Stream the response in chunks
    async for chunk in run.async_stream():
        if hasattr(chunk, "delta") and chunk.delta.content:
            callback(chunk.delta.content)
```

### Graceful Degradation

The implementation includes fallback mechanisms when dependencies are not available:

```python
# Define fallback types/classes for when the SDK is not available
class DummyAgent:
    """Dummy Agent class for when the SDK is not available"""
    pass

class DummyRunner:
    """Dummy Runner class for when the SDK is not available"""
    pass

# Attempt to import the real SDK
try:
    from agents import Agent, ModelSettings, FileSearchTool, ComputerTool, FunctionTool, Runner
    from agents.models import interface, openai_chatcompletions
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    # If import fails, use dummy classes
    Agent = DummyAgent
    Runner = DummyRunner
    # ...
    AGENTS_SDK_AVAILABLE = False
```

## Dependencies

The implementation relies on the following key dependencies:

```
# OpenAI Agents SDK and RAG dependencies
openai-agents>=0.0.9
langchain>=0.3.0,<0.4.0
langchain-community>=0.3.0,<0.4.0
langchain-openai>=0.3.0,<0.4.0

# Vector database backends for RAG
chromadb>=1.0.0
faiss-cpu>=1.10.0
weaviate-client>=4.0.0

# Document processing
unstructured>=0.17.0
pdf2image>=1.16.3
pytesseract>=0.3.10
```

## UI Changes

The implementation adds the following fields to the Raven bot configuration UI:

- **Model Provider**: Select field for choosing between OpenAI, LM Studio, Ollama, and LocalAI
- **Model Name**: The name of the model to use (e.g., "gpt-4o", "llama3-8b")
- **Vector Store IDs**: Comma-separated list of OpenAI vector store IDs
- **Enable Local RAG**: Toggle for local RAG implementation
- **Local RAG Provider**: Select field for choosing vector store provider

The "Raven Settings" page includes new fields for local LLM configuration:

- **Enable Local LLM**: Main toggle for local LLM integration
- **LM Studio API URL**: URL for the LM Studio API
- **Ollama API URL**: URL for the Ollama API
- **LocalAI API URL**: URL for the LocalAI API

## Technical Architecture

```
┌─────────────────┐     ┌───────────────────────┐     ┌──────────────────┐
│  Raven Channel  │────▶│       Message         │────▶│     AI Module    │
└─────────────────┘     └───────────────────────┘     └──────────────────┘
                                                               │
                                                               ▼
                                   ┌───────────────────────────────────────────┐
                                   │                                           │
                                   ▼                                           ▼
                        ┌────────────────────┐                 ┌────────────────────┐
                        │   SDK Handler      │                 │  SDK Handler with  │
                        │   (OpenAI)         │                 │   Local LLM        │
                        └────────────────────┘                 └────────────────────┘
                                   │                                    │
                                   │                 ┌──────────────────┼──────────────────┐
                                   │                 │                  │                  │
                                   ▼                 ▼                  ▼                  ▼
                        ┌─────────────────┐ ┌─────────────────┐┌──────────────────┐┌──────────────┐
                        │  OpenAI Model   │ │  OpenAI Model   ││  LM Studio Model ││ Ollama Model │
                        └─────────────────┘ └─────────────────┘└──────────────────┘└──────────────┘
                                   │                 │                  │                  │
                                   ▼                 ▼                  ▼                  ▼
                        ┌─────────────────┐ ┌─────────────────┐┌──────────────────┐┌──────────────┐
                        │ OpenAI Tools    │ │ OpenAI RAG      ││  Local RAG       ││  Local RAG   │
                        └─────────────────┘ └─────────────────┘└──────────────────┘└──────────────┘
```

## Required Code Changes

The implementation requires updating the following code:

1. Update `raven_bot.py` to remove the OpenAI Assistant creation methods:
   - Remove `create_openai_assistant()`
   - Remove `update_openai_assistant()`
   - Remove `delete_openai_assistant()`
   - Update `on_update()` to use SDK Agent creation
   - Update `before_insert()` to use SDK Agent creation

2. Update `AIFeaturesBotForm.tsx` to add new form fields:
   - Add model provider dropdown
   - Add model name input
   - Add RAG configuration options
   - Update existing tool options

## Implementation Status

The core SDK agent implementation is complete with the following components:

- SDK integration with proper Agent creation
- Multiple model provider support
- Local RAG implementation with various backends
- Message handling with streaming support
- File handling for both OpenAI and local implementations

The remaining tasks include:

- Updating the bot DocType implementation
- Updating the React UI components
- Completing testing according to the test plan
- Creating comprehensive user documentation