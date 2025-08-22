# Raven AI System Documentation

## 📚 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [LM Studio Integration](#lm-studio-integration)
- [OpenAI Integration](#openai-integration)
- [Testing](#testing)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Overview

The Raven AI system provides a comprehensive AI integration framework for the Raven messaging platform, supporting both local LLMs (via LM Studio) and cloud providers (OpenAI). The system enables AI-powered bots with function calling capabilities, conversation history management, and seamless integration with the Frappe framework.

### Key Features
- **Multi-provider support**: LM Studio (local) and OpenAI (cloud)
- **Function calling**: AI bots can execute business functions with proper context management
- **Conversation history**: Full context preservation with intelligent truncation
- **Response formatting**: Clean message extraction with thinking process separation
- **Debug mode**: Conditional logging for development
- **Comprehensive testing**: Full test suite with modular test categories
- **Error handling**: Graceful degradation and user-friendly error messages
- **JSON serialization**: Handles dates, Decimal, and complex objects

## Architecture

```
raven/ai/
├── Core Modules
│   ├── ai.py                     # Main entry point and message processing
│   ├── agents_integration.py     # OpenAI Agents SDK integration
│   ├── functions.py              # Core business functions
│   ├── function_executor.py      # Function execution framework
│   └── response_formatter.py     # Response formatting and HTML processing
│
├── LM Studio Integration
│   └── lmstudio/
│       ├── __init__.py           # Module exports
│       ├── sdk_handler.py        # LM Studio SDK handler
│       └── test_sdk.py           # SDK-specific tests
│
├── Handlers
│   ├── local_llm_http_handler.py # HTTP handler for Ollama/LocalAI
│   ├── openai_client.py         # OpenAI client wrapper
│   └── conversation_file_handler.py # File handling for conversations
│
├── Testing
│   └── tests/
│       ├── __init__.py           # Test module exports
│       ├── base.py               # Base test class
│       ├── test_modules.py       # Module import tests
│       ├── test_lmstudio.py      # LM Studio tests
│       ├── test_openai.py        # OpenAI tests
│       ├── test_functions.py     # Function execution tests
│       ├── test_integration.py   # Integration tests
│       ├── test_actresult.py     # ActResult handling tests
│       ├── test_conversation.py  # Conversation history tests
│       └── test_runner.py        # Main test orchestrator
│
└── Documentation
    └── README.md                 # This file
```

## Components

### 1. Main AI Module (`ai.py`)

The central orchestrator that:
- Processes incoming messages from Raven channels
- Determines which handler to use (LM Studio vs OpenAI)
- Manages conversation history
- Handles bot configuration

**Key Functions:**
```python
process_message_with_agent(agent_name, message, channel_id)
# Main entry point for AI message processing
```

### 2. LM Studio Integration (`lmstudio/`)

#### SDK Handler (`sdk_handler.py`)

A simplified, production-ready handler for LM Studio:

**Features:**
- Singleton client pattern for connection reuse
- Automatic model detection
- Function calling via `act()` method
- Simple completion via `complete()` method
- Debug logging based on `bot.debug_mode`

**Key Classes:**
```python
class LMStudioClient:
    """Singleton client for LM Studio SDK connection"""
    
    def get_client(self, base_url: str = None, bot=None):
        """Get or create LM Studio client with TTL-based refresh"""

@with_frappe_context
def tool_function(**kwargs):
    """Wrapper ensuring Frappe context for tool execution"""
```

**Important Features:**
- **Context Management**: Maintains Frappe database context across async tool calls
- **Response Truncation**: Limits tool responses to 10K chars to prevent model errors
- **Channel Extraction**: Separates thinking (<|channel|>analysis) from final response
- **Custom JSON Serialization**: Handles date, datetime, Decimal objects

**Usage:**
```python
from raven.ai.lmstudio import lmstudio_sdk_handler

response = lmstudio_sdk_handler(
    bot,                    # Raven Bot document
    message,                # User message
    channel_id,             # Channel identifier
    conversation_history    # List of previous messages
    conversation_history  # List of previous messages
)
```

### 3. OpenAI Integration (`agents_integration.py`)

Integrates with OpenAI's Agents SDK for advanced capabilities:

**Features:**
- Native function calling
- Tool support (CodeInterpreter, FileSearch, WebSearch)
- Async/sync operation modes
- Error handling and retries

### 4. Function System

#### Function Executor (`function_executor.py`)

Executes Raven AI Functions with proper Frappe context:

```python
execute_raven_function(function_name, args, channel_id=None)
# Executes a function by name with context preservation
```

#### Function Registration

Functions are defined in the `Raven AI Function` DocType with:
- Function name and description
- Parameter definitions with types
- Function path (Python import path)
- Required permissions

### 5. Response Formatting (`response_formatter.py`)

Handles response formatting:
- Converts thinking tags to HTML details elements
- Processes markdown
- Handles code blocks
- Manages HTML escaping

## LM Studio Integration

### Configuration

1. **Install LM Studio SDK:**
```bash
pip install lmstudio
```

2. **Configure in Raven Settings:**
- Set `local_llm_provider` to "LM Studio"
- Set `local_llm_api_url` (e.g., "http://localhost:1234")

3. **Load a model in LM Studio:**
- Start LM Studio
- Load a model (e.g., `openai/gpt-oss-20b`)
- Start the server

### Supported Features

- **Simple Completions**: Basic text generation
- **Function Calling**: Via `act()` method with tools
- **Conversation History**: Full context preservation
- **Model Auto-detection**: Uses first loaded model if not specified

### Debug Mode

Enable debug mode on the bot to see detailed logs:
```python
bot.debug_mode = 1  # Enable debug logging
```

## OpenAI Integration

### Configuration

1. **Set API Key in Raven Settings:**
```python
settings.openai_api_key = "your-api-key"
```

2. **Enable AI Integration:**
```python
settings.enable_ai_integration = 1
```

3. **Create OpenAI Bot:**
- Set `model_provider` to "OpenAI"
- Choose model (e.g., "gpt-4o-mini")
- Configure temperature and other parameters

## Testing

### Modular Test Suite (`tests/`)

The modular test suite provides organized, category-based testing with automatic cleanup:

```bash
# Run all tests
bench --site prod.local execute raven.ai.tests.test_runner.test_all

# Run specific category
bench --site prod.local execute raven.ai.tests.test_runner.test_modules
bench --site prod.local execute raven.ai.tests.test_runner.test_lmstudio
bench --site prod.local execute raven.ai.tests.test_runner.test_openai
bench --site prod.local execute raven.ai.tests.test_runner.test_functions
bench --site prod.local execute raven.ai.tests.test_runner.test_integration
bench --site prod.local execute raven.ai.tests.test_runner.test_actresult
bench --site prod.local execute raven.ai.tests.test_runner.test_conversation
```

**Test Categories:**
- **Modules**: Import and module availability tests
- **LM Studio**: SDK connection and model detection
- **OpenAI**: API configuration and completions
- **Functions**: Function execution and schema validation
- **Integration**: Bot configurations and message pipeline
- **ActResult**: LM Studio ActResult handling and message extraction
- **Conversation**: History management and truncation

**Features:**
- **Automatic Cleanup**: Pre and post-test cleanup of test data
- **Graceful Degradation**: Tests pass with warnings if services unavailable
- **Detailed Reporting**: Per-category and overall success rates
- **No User Confusion**: Test bots use distinct names (TestBot_*)

### Manual Cleanup

If test data needs to be manually cleaned:
```bash
bench --site prod.local execute raven.ai.cleanup_test_data.clean
```

### Test Results

The test suites provide detailed feedback:

```
================================================================================
RAVEN AI UNIFIED TEST SUITE
================================================================================
Site: prod.local
User: Administrator
Time: 2025-08-17 15:30:00
================================================================================

🧹 Pre-test cleanup...
🔧 Creating test resources...
  ✓ Created bot: Test LM Studio Simple
  ✓ Created bot: Test LM Studio Functions
  ✓ Created bot: Test OpenAI Bot
✅ All test resources created successfully

🚀 Running tests...

============================================================
  Module Tests
============================================================
✅ Import Main AI module
✅ Import Functions module
✅ Import Function executor
✅ Import Response formatter
✅ Import OpenAI agents
✅ Import LM Studio package
✅ Import SDK handler

============================================================
  LM Studio Tests
============================================================
✅ LM Studio Connection
✅ LM Studio Simple Completion
✅ LM Studio History
✅ LM Studio Functions

============================================================
  OpenAI Tests
============================================================
✅ OpenAI Completion

============================================================
  Function Tests
============================================================
✅ Function: get_current_context
✅ Function Inventory

============================================================
  Integration Tests
============================================================
✅ Test Bot Creation

🧹 Cleaning up test resources...
✅ Cleaned up 3 test resources

================================================================================
TEST REPORT
================================================================================

📊 Results:
  Total:  18
  Passed: 18 ✅
  Failed: 0 ❌
  Success Rate: 100.0%

🎉 PERFECT! All tests passed!

⏱️  Test duration: 4.2 seconds

================================================================================
TEST SUITE COMPLETED
================================================================================
```

## Configuration

### Raven Settings

Key settings in `Raven Settings` DocType:

| Setting | Description | Example |
|---------|-------------|---------|
| `enable_ai_integration` | Enable AI features | `1` |
| `local_llm_provider` | Local LLM provider type | `"LM Studio"` |
| `local_llm_api_url` | LM Studio server URL | `"http://localhost:1234"` |
| `openai_api_key` | OpenAI API key | `"sk-..."` |

### Bot Configuration

Raven Bot DocType fields:

| Field | Description | Example |
|-------|-------------|---------|
| `bot_name` | Display name | `"Nora"` |
| `raven_user` | Associated Raven user | `"Administrator"` |
| `is_ai_bot` | Enable AI features | `1` |
| `model_provider` | AI provider | `"Local LLM"` or `"OpenAI"` |
| `model` | Model identifier | `"openai/gpt-oss-20b"` |
| `temperature` | Response randomness | `0.7` |
| `debug_mode` | Enable debug logging | `1` |
| `instruction` | System prompt | `"You are a helpful assistant"` |
| `bot_functions` | Linked AI functions | List of function names |

## API Reference

### Main Functions

#### `process_message_with_agent()`
```python
def process_message_with_agent(
    agent_name: str,
    message: str,
    channel_id: str
) -> dict:
    """
    Process a message with an AI agent
    
    Returns:
        {
            "success": bool,
            "response": str,
            "model": str (optional)
        }
    """
```

#### `lmstudio_sdk_handler()`
```python
def lmstudio_sdk_handler(
    bot: frappe.Document,
    message: str,
    channel_id: str,
    conversation_history: list = None
) -> dict:
    """
    Handle message with LM Studio SDK
    
    Args:
        bot: Raven Bot document
        message: User message
        channel_id: Channel identifier
        conversation_history: List of {"role": str, "content": str}
    """
```

#### `execute_raven_function()`
```python
def execute_raven_function(
    function_name: str,
    args: dict,
    channel_id: str = None
) -> Any:
    """
    Execute a Raven AI Function
    
    Args:
        function_name: Name of the function
        args: Arguments to pass
        channel_id: Optional channel context
    """
```

### Message Format

Conversation history format:
```python
[
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What's the weather?"}
]
```

## Troubleshooting

### Common Issues & Solutions

1. **LM Studio Connection Failed**
   - Ensure LM Studio is running
   - Check if a model is loaded
   - Verify the server URL (pinggy.link for remote)
   - SDK auto-reconnects with 5-minute TTL

2. **OpenAI Schema Errors**
   - Check function parameter definitions
   - Ensure 'required' array matches properties

3. **"object is not bound" Error**
   - **Cause**: Frappe context lost during async execution
   - **Fix**: Context captured and restored in tool_function wrapper
   - Function now re-establishes DB connection before execution

4. **"date is not JSON serializable" Error**
   - **Cause**: Python date/datetime objects in function results
   - **Fix**: Custom JSON serializer handles:
     - datetime/date → ISO format
     - Decimal → float
     - Complex objects → dict or string

5. **Conversation History Lost**
   - **Cause**: History not passed to model.act()
   - **Fix**: Full prompt now includes:
     - System instruction
     - Last 10 messages (truncated to 500 chars each)
     - Current message

6. **Response Shows Full Reasoning**
   - **Cause**: Channel markers not extracted
   - **Fix**: Regex extraction of `<|channel|>final<|message|>` content
   - Thinking wrapped in `<think>` tags for collapsible display

7. **Model Errors with Large Responses**
   - **Cause**: "broadcast_shapes" error with large data
   - **Fix**: Response truncation to 10K chars
   - Lists limited to first 10 items with truncation notice
   - Ensure all required fields are specified
   - Validate against OpenAI's schema requirements

3. **Function Execution Errors**
   - Verify function path is correct
   - Check parameter types match
   - Ensure proper Frappe context

### Debug Tips

1. Enable debug mode on the bot
2. Check Frappe error logs
3. Run the test suite for diagnostics
4. Use quick tests for rapid validation

## Recent Improvements (August 2025)

### Major Fixes
1. **Context Management**: Fixed "object is not bound" errors with proper Frappe context preservation
2. **Conversation History**: Full history now passed to LM Studio SDK (was only passing current message)
3. **Response Formatting**: Clean extraction of final messages from channel markers
4. **JSON Serialization**: Custom serializer for dates, Decimal, and complex objects
5. **Error Handling**: Better error messages and graceful degradation
6. **Test Suite**: Modular structure with 100% pass rate

### Performance Optimizations
- Response truncation to prevent model overload
- Singleton client pattern for connection reuse
- TTL-based client refresh (5 minutes)
- History limited to last 10 messages

### User Experience
- Thinking process in collapsible sections
- Clean message display without channel markers
- Test bots use distinct names (no more "Administrator" confusion)
- Comprehensive error messages

## Development

### Adding New Functions

1. Create function in Python module
2. Register in `Raven AI Function` DocType
3. Link to bot via `bot_functions`
4. Test with the test suite

### Contributing

1. Follow existing code patterns
2. Add tests for new features
3. Update documentation
4. Run full test suite before submitting

## File Structure

### Core Files
- **`ai.py`**: Main entry point for AI message processing
- **`agents_integration.py`**: OpenAI Agents SDK integration
- **`functions.py`**: Core business functions
- **`function_executor.py`**: Function execution framework
- **`response_formatter.py`**: Response formatting utilities

### LM Studio Integration
- **`lmstudio/sdk_handler.py`**: SDK-only handler for LM Studio
- **`lmstudio/__init__.py`**: Module exports and aliases

### Testing
- **`tests/`**: Modular test suite (100% pass rate)
  - `base.py`: Base test class with automatic cleanup
  - `test_modules.py`: Import and availability tests
  - `test_lmstudio.py`: SDK connection and model detection
  - `test_openai.py`: API configuration tests
  - `test_functions.py`: Function execution validation
  - `test_integration.py`: Full system integration
  - `test_actresult.py`: ActResult and message extraction
  - `test_conversation.py`: History management tests
  - `test_runner.py`: Orchestrator with pre/post cleanup
- **`cleanup_all_test_data.py`**: Comprehensive cleanup utility

### Documentation
- **`README.md`**: This comprehensive documentation
- **`RAVEN_AI_DOCUMENTATION.md`**: Additional technical details

## Version History

- **v4.0** (August 2025): Major fixes and improvements
  - Fixed Frappe context management for tool execution
  - Added proper conversation history support
  - Implemented response formatting with channel extraction
  - Created modular test suite with 100% pass rate
  - Added custom JSON serialization for complex types
- **v3.0**: Unified test suite with automatic lifecycle management
- **v2.5**: Enhanced testing with automatic cleanup
- **v2.0**: Simplified SDK-only handler, removed HTTP fallback
- **v1.5**: Added debug mode and improved logging
- **v1.0**: Initial multi-provider support

## License

Part of the Raven messaging platform. See main repository for license details.