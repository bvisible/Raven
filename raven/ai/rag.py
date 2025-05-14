"""
Unified RAG (Retrieval-Augmented Generation) System for Raven

This module provides a unified interface for document retrieval and processing,
supporting both OpenAI's built-in RAG (with vector stores) and local implementations.
"""

from typing import Any, Dict, List, Optional, Union
import frappe
import json
import os
import time
import hashlib
from datetime import datetime, timedelta
import threading

# Global lock for thread safety
_recent_uploads_lock = threading.RLock()

# Attempt to import the OpenAI Agents SDK
try:
    from agents import FileSearchTool, FunctionTool
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False
    frappe.log_error("RAG", "OpenAI Agents SDK not installed. Run 'pip install openai-agents'")

# Initialize global cache for recent file uploads
if not hasattr(frappe, 'recent_file_uploads'):
    frappe.recent_file_uploads = {}

# Redis key for storing persistent file upload information
REDIS_RECENT_FILES_KEY = "raven:recent_file_uploads"

def _get_recent_files_from_redis():
    """Get recent files data from Redis"""
    try:
        redis_client = frappe.cache()
        data = redis_client.get_value(REDIS_RECENT_FILES_KEY)
        if data:
            return json.loads(data)
        return {}
    except Exception as e:
        frappe.log_error("RAG Redis", f"Error getting recent files from Redis: {str(e)}")
        return {}

def _save_recent_files_to_redis(data):
    """Save recent files data to Redis"""
    try:
        redis_client = frappe.cache()
        redis_client.set_value(REDIS_RECENT_FILES_KEY, json.dumps(data), expires_in_sec=86400*7) # 7 days
        frappe.log_error("RAG Redis", f"Saved {len(data)} file records to Redis")
        return True
    except Exception as e:
        frappe.log_error("RAG Redis", f"Error saving recent files to Redis: {str(e)}")
        return False

# Load recent files from Redis on module initialization
try:
    redis_data = _get_recent_files_from_redis()
    if redis_data:
        frappe.recent_file_uploads.update(redis_data)
        frappe.log_error("RAG Redis", f"Loaded {len(redis_data)} file records from Redis")
except Exception as e:
    frappe.log_error("RAG Redis", f"Error loading Redis data on init: {str(e)}")

class OpenAIRAGProvider:
    """
    RAG provider using OpenAI's built-in vector stores
    
    This implementation uses OpenAI's FileSearchTool and vector stores for
    document retrieval.
    """
    
    def __init__(self, bot_config: Dict[str, Any]):
        """
        Initialize the OpenAI RAG provider
        
        Args:
            bot_config: Bot configuration
        """
        self.bot_config = bot_config
        self.vector_store_ids = None
        self.file_search_tool = None
        self.file_search_enabled = True
    
    def initialize(self) -> bool:
        """
        Initialize the provider
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if not AGENTS_SDK_AVAILABLE:
            frappe.log_error("RAG", "OpenAI Agents SDK not available")
            return False
        
        # Get vector store IDs from bot configuration
        vector_store_ids_str = self.bot_config.get("vector_store_ids")
        
        # If no vector store IDs are provided, create one automatically
        if not vector_store_ids_str or not vector_store_ids_str.strip():
            frappe.log_error("RAG", "No vector store IDs provided, attempting to create one automatically")
            try:
                # First check if we have OpenAI API key configured
                settings = frappe.get_cached_doc("Raven Settings")
                api_key = settings.get_password("openai_api_key")
                
                if not api_key:
                    frappe.log_error("RAG", "Cannot create vector store: OpenAI API key is not configured")
                    return False
                
                # Create a vector store automatically
                frappe.log_error("RAG", "Creating vector store with valid API key")
                new_vs_id = self._create_vector_store()
                
                if new_vs_id:
                    # Update the vector_store_ids in bot's configuration
                    self.vector_store_ids = [new_vs_id]
                    frappe.log_error("RAG", f"Successfully created vector store ID: {new_vs_id}")
                    
                    # Save the vector store ID back to the bot document if possible
                    try:
                        bot_name = self.bot_config.get("bot_name")
                        if bot_name:
                            bot_doc = frappe.get_doc("Raven Bot", bot_name)
                            bot_doc.vector_store_ids = new_vs_id
                            bot_doc.save(ignore_permissions=True)
                    except Exception as e:
                        # Log but continue
                        frappe.log_error("RAG", f"Failed to update bot document: {str(e)}")
                else:
                    # Use a temporary ID
                    import uuid
                    temp_id = f"temp-{str(uuid.uuid4())[:8]}"
                    self.vector_store_ids = [temp_id]
                    self.file_search_enabled = False
                    return True
            except Exception as e:
                error_msg = str(e)
                frappe.log_error("RAG", f"Error creating vector store: {error_msg}")
                return False
        else:
            # Parse vector store IDs from comma-separated string
            self.vector_store_ids = [vs.strip() for vs in vector_store_ids_str.split(",") if vs.strip()]
            if not self.vector_store_ids:
                frappe.log_error("RAG", "Empty vector store IDs list for OpenAI RAG")
                return False
        
        # Create the FileSearchTool
        try:
            self.file_search_tool = FileSearchTool(
                vector_store_ids=self.vector_store_ids,
                include_search_results=True,
                max_num_results=5
            )
            frappe.log_error("RAG", f"Created FileSearchTool with vector_store_ids: {self.vector_store_ids}")
            return True
        except Exception as e:
            frappe.log_error("RAG", f"Error creating FileSearchTool: {str(e)}")
            return False
            
    def _create_vector_store(self) -> str:
        """
        Create a new vector store in OpenAI
        
        Returns:
            str: Vector store ID, or empty string if failed
        """
        try:
            # Import the OpenAI SDK
            from openai import OpenAI
            
            # Get OpenAI API key
            settings = frappe.get_cached_doc("Raven Settings")
            api_key = settings.get_password("openai_api_key")
            
            if not api_key:
                return ""
            
            # Create OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Generate a unique name for the vector store
            import datetime
            import uuid
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            vs_name = f"raven-vs-{timestamp}-{unique_id}"
            
            # Try to create vector store using the SDK method
            try:
                if hasattr(client, 'beta') and hasattr(client.beta, 'vector_stores'):
                    response = client.beta.vector_stores.create(name=vs_name)
                    vector_store_id = response.id
                    return vector_store_id
                else:
                    raise AttributeError("Beta SDK methods not available")
            except Exception as e:
                # Fall back to REST API approach
                import requests
                
                # Define potential API endpoints
                api_endpoints = [
                    "https://api.openai.com/v1/vector_stores",
                    "https://api.openai.com/v1/beta/vector_stores"
                ]
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                data = {"name": vs_name}
                
                # Try each endpoint
                for endpoint in api_endpoints:
                    try:
                        response = requests.post(endpoint, headers=headers, json=data)
                        
                        if response.status_code in [200, 201, 202]:
                            json_resp = response.json()
                            
                            # Extract ID using various possible formats
                            vector_store_id = None
                            
                            if "id" in json_resp:
                                vector_store_id = json_resp["id"]
                            elif "data" in json_resp and "id" in json_resp["data"]:
                                vector_store_id = json_resp["data"]["id"]
                            elif "object" in json_resp and json_resp.get("object") == "vector_store":
                                vector_store_id = json_resp.get("id")
                                
                            if vector_store_id:
                                return vector_store_id
                    except Exception:
                        continue
                
                return ""
                
        except Exception as e:
            frappe.log_error("RAG", f"Unexpected error creating vector store: {str(e)}")
            return ""
    
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a file and upload it to OpenAI
        
        Args:
            file_path: Path to the file
            metadata: Additional metadata for the document
            
        Returns:
            str: File ID
        """
        try:
            from openai import OpenAI
            
            # Get the filename for better logging
            filename = os.path.basename(file_path)
            frappe.log_error("RAG", f"Processing file: {filename}")
            
            # Get OpenAI API key
            settings = frappe.get_cached_doc("Raven Settings")
            client = OpenAI(
                api_key=settings.get_password("openai_api_key")
            )
            
            # Ensure we have a vector store ID
            if not self.vector_store_ids or len(self.vector_store_ids) == 0:
                if not self.initialize():
                    return ""
            
            # Upload file
            with open(file_path, "rb") as file:
                response = client.files.create(
                    file=file,
                    purpose="assistants"
                )
            
            file_id = response.id
            frappe.log_error("RAG", f"Uploaded file '{filename}' to OpenAI with ID: {file_id}")
            
            # Track this file upload globally with enhanced metadata
            with _recent_uploads_lock:
                if not hasattr(frappe, 'recent_file_uploads'):
                    frappe.recent_file_uploads = {}
                
                current_time = time.time()
                
                # Extract more metadata from the file for better filtering
                file_metadata = {
                    'filename': filename, 
                    'upload_time': current_time,
                    'indexed': False,
                    'vector_stores': self.vector_store_ids,
                    'file_id': file_id,
                    'file_type': os.path.splitext(filename)[1].lower() if filename else '',
                    'channel_id': metadata.get('channel_id') if metadata else None,
                    'is_most_recent': True  # Mark this as the most recent upload
                }
                
                # Mark all other files as not most recent
                for existing_file_id in frappe.recent_file_uploads:
                    if existing_file_id != file_id:
                        frappe.recent_file_uploads[existing_file_id]['is_most_recent'] = False
                
                # Store the enhanced metadata
                frappe.recent_file_uploads[file_id] = file_metadata
                
                # Log the tracked file
                frappe.log_error("RAG", f"Tracking file upload: {json.dumps(file_metadata)}")
            
            # Add file to vector store(s)
            success_count = 0
            for vector_store_id in self.vector_store_ids:
                try:
                    # Utiliser directement le SDK OpenAI pour ajouter le fichier au vector store
                    # Cela est plus fiable que de faire des appels API directs
                    
                    # Log que nous essayons d'ajouter le fichier
                    frappe.log_error("RAG", f"Adding file {file_id} to vector store {vector_store_id}")
                    
                    # Créer une batch de fichiers dans le vector store
                    batch_response = client.vector_stores.file_batches.create(
                        vector_store_id=vector_store_id,
                        file_ids=[file_id]
                    )
                    
                    # Log le résultat
                    frappe.log_error("RAG", f"Added file to vector store: batch ID {batch_response.id}, status: {batch_response.status}")
                    
                    # Si nous arrivons ici, considérons que c'est un succès
                    frappe.log_error("RAG", f"Added file '{filename}' to vector store {vector_store_id}")
                    # Mark that this file should be searchable
                    with _recent_uploads_lock:
                        if file_id in frappe.recent_file_uploads:
                            frappe.recent_file_uploads[file_id]['indexed'] = True
                    success_count += 1
                except Exception as e:
                    frappe.log_error("RAG", f"Error adding file to vector store: {str(e)}")
            
            return file_id
        except Exception as e:
            frappe.log_error("RAG", f"Error uploading file to OpenAI: {str(e)}")
            return ""
    
    def get_tool(self) -> Any:
        """
        Get a tool for file search compatible with OpenAI Agents SDK
        
        Returns:
            Any: FunctionTool that can be used for file search
        """
        # Check if file search has been disabled
        if not self.file_search_enabled:
            frappe.log_error("RAG", "File search is disabled")
            return None
            
        # Initialize if needed
        if not self.initialize():
            return None
        
        # IMPORTANT: FileSearchTool is a hosted tool not supported with ChatCompletions API
        # Instead, create a FunctionTool with similar functionality
        
        # Define async handler for file search
        async def on_invoke_file_search(ctx, args_json: str) -> str:
            frappe.log_error("RAG", f"File search invoked with args: {args_json}")
            
            try:
                # Parse arguments
                args = json.loads(args_json)
                query = args.get("query", "")
                max_results = args.get("max_results", 5)
                
                # Get OpenAI client
                from openai import OpenAI
                settings = frappe.get_cached_doc("Raven Settings")
                client = OpenAI(api_key=settings.get_password("openai_api_key"))
                
                # Search the files
                if not self.vector_store_ids:
                    return json.dumps({
                        "error": "No vector store IDs configured."
                    })
                
                # Use the Files API directly
                try:
                    # Utiliser search au lieu de batched_search qui n'existe pas dans l'API actuelle
                    # Get recent file uploads to prioritize
                    recent_files = []
                    most_recent_file_id = None
                    most_recent_openai_file_id = None
                    most_recent_time = 0
                    most_recent_filename = None
                    
                    # First try to load from Redis to get the most up-to-date data
                    redis_data = _get_recent_files_from_redis()
                    if redis_data:
                        frappe.log_error("RAG", f"Loaded {len(redis_data)} file records from Redis")
                        # Update the in-memory cache with Redis data
                        frappe.recent_file_uploads.update(redis_data)
                    
                    with _recent_uploads_lock:
                        # Find the most recently uploaded file
                        if hasattr(frappe, 'recent_file_uploads'):
                            # Log the in-memory data for debugging
                            frappe.log_error("RAG", f"In-memory recent files before search: {json.dumps(list(frappe.recent_file_uploads.keys()))}")
                            
                            # Prioritize files marked as most recent
                            for file_id, info in frappe.recent_file_uploads.items():
                                if info.get('is_most_recent', False):
                                    most_recent_file_id = file_id
                                    most_recent_openai_file_id = info.get('openai_file_id')
                                    most_recent_time = info.get('upload_time', 0)
                                    most_recent_filename = info.get('filename', '')
                                    frappe.log_error("RAG", f"Found most recent file (is_most_recent=True): {most_recent_filename}")
                                    # Break immediately if we find a file marked as most recent
                                    break
                            
                            # Fallback to time-based sorting if no file is explicitly marked
                            if not most_recent_file_id:
                                for file_id, info in frappe.recent_file_uploads.items():
                                    upload_time = info.get('upload_time', 0)
                                    if upload_time > most_recent_time:
                                        most_recent_time = upload_time
                                        most_recent_file_id = file_id
                                        most_recent_openai_file_id = info.get('openai_file_id')
                                        most_recent_filename = info.get('filename', '')
                            
                            # Collect all files for logging
                            for file_id, info in frappe.recent_file_uploads.items():
                                recent_files.append({
                                    'file_id': file_id,
                                    'openai_file_id': info.get('openai_file_id', ''),
                                    'filename': info.get('filename', ''),
                                    'upload_time': info.get('upload_time', 0),
                                    'is_most_recent': info.get('is_most_recent', False)
                                })
                    
                    # Log recent file information
                    frappe.log_error("RAG", f"Recent files: {json.dumps(recent_files)}")
                    frappe.log_error("RAG", f"Most recent file: ID={most_recent_file_id}, OpenAI ID={most_recent_openai_file_id}, Name={most_recent_filename}")
                    
                    # Add metadata filter if we have a recent file
                    metadata_filters = {}
                    filter_applied = False
                    
                    # First try to filter by OpenAI file ID if available
                    if most_recent_openai_file_id:
                        metadata_filters = {"file_id": {"type": "equals", "value": most_recent_openai_file_id}}
                        filter_applied = True
                        frappe.log_error("RAG", f"Using OpenAI file ID filter: {most_recent_openai_file_id}")
                    # Fall back to Frappe file ID if needed
                    elif most_recent_file_id:
                        metadata_filters = {"file_id": {"type": "equals", "value": most_recent_file_id}}
                        filter_applied = True
                        frappe.log_error("RAG", f"Using Frappe file ID filter: {most_recent_file_id}")
                    
                    # Enhance query with relevant file context
                    enhanced_query = query
                    
                    # Add strong file context if we have a most recent file
                    if most_recent_filename:
                        # Add very explicit instructions to focus on the specific file
                        enhanced_query = f"SEARCH ONLY IN {most_recent_filename}: {query}"
                        frappe.log_error("RAG", f"Enhanced query with specific file focus: {enhanced_query}")
                    # Fall back to general file context if we have any files but no specific one identified
                    elif recent_files:
                        # Add general filename context to the query
                        filenames = [f['filename'] for f in sorted(recent_files, key=lambda x: x['upload_time'], reverse=True)]
                        if filenames:
                            first_filename = filenames[0]
                            enhanced_query = f"Using the file {first_filename}, {query}"
                            frappe.log_error("RAG", f"Enhanced query with general filename: {enhanced_query}")
                    
                    # Determine search strategy based on filter availability
                    search_strategy = "both_filter_and_query" # one of: filter_only, query_only, both_filter_and_query, then_no_filter
                    frappe.log_error("RAG", f"Search strategy: {search_strategy}, filter applied: {filter_applied}")
                    
                    # Try the search with different approaches for maximum reliability
                    if search_strategy == "both_filter_and_query":
                        # Try up to 3 different approaches to get the best results
                        results_with_filter = []
                        results_without_filter = []
                        
                        # First attempt: with metadata filter
                        try:
                            # If we have a most recent file but processing might still be in progress
                            # we might need to retry the search with a small delay
                            max_retry_count = 3  # Maximum number of retries
                            retry_count = 0
                            retry_delay = 2  # Seconds between retries
                            has_results = False
                            
                            while retry_count < max_retry_count and not has_results:
                                # On retry, check Redis again to get latest file info
                                if retry_count > 0:
                                    frappe.log_error("RAG", f"Retry {retry_count} for file search")
                                    # Small delay to allow processing to complete
                                    import time
                                    time.sleep(retry_delay)
                                    # Reload from Redis on retry
                                    retry_redis_data = _get_recent_files_from_redis()
                                    if retry_redis_data:
                                        frappe.recent_file_uploads.update(retry_redis_data)
                                        # Try to find most recent file again
                                        for file_id, info in frappe.recent_file_uploads.items():
                                            if info.get('is_most_recent', False):
                                                most_recent_file_id = file_id
                                                most_recent_openai_file_id = info.get('openai_file_id')
                                                most_recent_filename = info.get('filename', '')
                                                frappe.log_error("RAG", f"Retry found most recent file: {most_recent_filename}")
                                                # Update filter if we have an OpenAI file ID
                                                if most_recent_openai_file_id:
                                                    metadata_filters = {"file_id": {"type": "equals", "value": most_recent_openai_file_id}}
                                                    filter_applied = True
                                                    frappe.log_error("RAG", f"Updated filter on retry: {most_recent_openai_file_id}")
                                
                                # Try with filter first if we have one
                                if filter_applied:
                                    try:
                                        force_query = f"SEARCH ONLY IN FILE {most_recent_filename}: {query}" if most_recent_filename else enhanced_query
                                        filter_response = client.vector_stores.search(
                                            vector_store_id=self.vector_store_ids[0],
                                            query=force_query,
                                            max_num_results=max_results,
                                            metadata_filter=metadata_filters
                                        )
                                        frappe.log_error("RAG", f"Search with filter (attempt {retry_count+1}): {force_query}")
                                        
                                        # Check if we got results
                                        if filter_response and hasattr(filter_response, 'data') and len(filter_response.data) > 0:
                                            response = filter_response
                                            frappe.log_error("RAG", f"Using filter-based results with {len(filter_response.data)} items")
                                            has_results = True
                                            break
                                    except Exception as filter_error:
                                        frappe.log_error("RAG", f"Filter search error: {str(filter_error)}")
                                
                                # If no results with filter or no filter available, try without filter
                                if not has_results:
                                    try:
                                        # Force query with very explicit file focus
                                        force_query = f"FOCUS EXCLUSIVELY ON {most_recent_filename}: {query}" if most_recent_filename else enhanced_query
                                        no_filter_response = client.vector_stores.search(
                                            vector_store_id=self.vector_store_ids[0],
                                            query=force_query,
                                            max_num_results=max_results
                                        )
                                        
                                        frappe.log_error("RAG", f"Search without filter (attempt {retry_count+1}): {force_query}")
                                        
                                        if no_filter_response and hasattr(no_filter_response, 'data') and len(no_filter_response.data) > 0:
                                            response = no_filter_response
                                            frappe.log_error("RAG", f"Got {len(no_filter_response.data)} results without filter")
                                            has_results = True
                                            break
                                    except Exception as no_filter_error:
                                        frappe.log_error("RAG", f"No-filter search error: {str(no_filter_error)}")
                                
                                retry_count += 1
                            
                            # If we still have no results after all retries, try a final simple search
                            if not has_results:
                                frappe.log_error("RAG", "No results after retries, using simple query")
                                # Try one more search with very simple terms
                                simple_response = client.vector_stores.search(
                                    vector_store_id=self.vector_store_ids[0],
                                    query="find total amount",
                                    max_num_results=max_results
                                )
                                
                                response = simple_response
                                if hasattr(simple_response, 'data'):
                                    frappe.log_error("RAG", f"Using simple query results with {len(simple_response.data)} items")
                                    
                        except Exception as e:
                            frappe.log_error("RAG", f"Error with enhanced search strategy: {str(e)}")
                            # Final fallback: simple query without enhancements
                            try:
                                response = client.vector_stores.search(
                                    vector_store_id=self.vector_store_ids[0],
                                    query=query,  # Use original query without enhancements
                                    max_num_results=max_results
                                )
                                frappe.log_error("RAG", f"Using fallback query: {query}")
                            except Exception as final_error:
                                frappe.log_error("RAG", f"Final fallback search failed: {str(final_error)}")
                                # Create empty response structure to avoid errors
                                response = None
                    else:
                        # Default search with metadata filter if available
                        try:
                            if filter_applied:
                                response = client.vector_stores.search(
                                    vector_store_id=self.vector_store_ids[0],
                                    query=enhanced_query,
                                    max_num_results=max_results,
                                    metadata_filter=metadata_filters
                                )
                                frappe.log_error("RAG", f"Search with metadata filter: {enhanced_query}")
                            else:
                                response = client.vector_stores.search(
                                    vector_store_id=self.vector_store_ids[0],
                                    query=enhanced_query,
                                    max_num_results=max_results
                                )
                                frappe.log_error("RAG", f"Search without filter: {enhanced_query}")
                        except Exception as e:
                            frappe.log_error("RAG", f"Error with search: {str(e)}, falling back to basic search")
                            # Fall back to regular search if metadata filter fails
                            response = client.vector_stores.search(
                                vector_store_id=self.vector_store_ids[0],
                                query=query,  # Use original query without enhancements
                                max_num_results=max_results
                            )
                    
                    # Format results according to the new response format
                    results = []
                    if response and hasattr(response, 'data'):
                        frappe.log_error("RAG", f"Found {len(response.data)} results from vector store")
                        for item in response.data:
                            # Process the data returned by the API
                            text_content = ""
                            if hasattr(item, 'content') and item.content:
                                for content_item in item.content:
                                    if hasattr(content_item, 'text'):
                                        text_content += content_item.text + " "
                            
                            # Get file metadata if available
                            file_id = item.file_id if hasattr(item, 'file_id') else None
                            filename = item.filename if hasattr(item, 'filename') else None
                            
                            # Try to get filename from our tracked uploads if not available in response
                            if file_id and not filename and hasattr(frappe, 'recent_file_uploads'):
                                if file_id in frappe.recent_file_uploads:
                                    filename = frappe.recent_file_uploads[file_id].get('filename', None)
                            
                            # Create a formatted result
                            results.append({
                                "text": text_content.strip(),
                                "file_id": file_id,
                                "filename": filename,
                                "score": item.score if hasattr(item, 'score') else None
                            })
                    
                    # Enhanced response with detailed guidance for the LLM
                    response = {
                        "results": results,
                        "query": query,
                        "enhanced_query": enhanced_query,
                        "file_context": most_recent_filename if most_recent_filename else "unknown",
                        "analysis": f"Here are the key pieces of information found in the document '{most_recent_filename if most_recent_filename else 'unknown'}':",
                        "usage_instructions": f"""
CRITICAL INSTRUCTIONS FOR USING SEARCH RESULTS:

This is file search data from the file: {most_recent_filename if most_recent_filename else 'unknown'}

When responding to the user:
1. ONLY use information from this specific file - do not reference other files
2. Extract and cite specific data points exactly as they appear in the text - especially for numbers, amounts, dates, and totals
3. When mentioning totals or financial amounts, include the exact currency symbol and formatting from the document (e.g., "CHF 1'234.56")
4. Format your answer to clearly state you are getting information specifically from this file: {most_recent_filename if most_recent_filename else 'unknown'}
5. Be precise and avoid generalizing or summarizing when exact data is available
6. For questions about totals or amounts, always mention the specific total you found (e.g., "According to the invoice, the total is...")

The user's question is about THIS file that was just uploaded, not older files. Focus exclusively on the information in these search results.
"""
                    }
                    
                    # Add information about the most recent file
                    if most_recent_filename:
                        response["primary_source"] = most_recent_filename
                        response["source_file"] = most_recent_filename
                        response["is_recent_upload"] = True
                    
                    # Add additional context for financial documents if detected
                    if any("invoice" in result.get("text", "").lower() for result in results) or \
                       any("facture" in result.get("text", "").lower() for result in results) or \
                       "invoice" in query.lower() or "facture" in query.lower() or "total" in query.lower():
                        response["document_type"] = "invoice"
                        response["document_context"] = f"""This appears to be an invoice. When answering questions about totals, 
be sure to extract the exact amount with currency symbol from the document. 
Search for phrases like "Total:", "Montant total:", "Total Amount:", etc."""
                    
                    # Add additional analysis if results contain certain patterns
                    if results:
                        # Look for patterns like currency amounts, numbers with symbols, dates
                        import re
                        money_pattern = re.compile(r'(\$|€|£|¥)?\s*\d+[,\.]\d+')
                        percentage_pattern = re.compile(r'\d+(\.\d+)?%')
                        date_pattern = re.compile(r'\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}')
                        
                        amounts = []
                        dates = []
                        percentages = []
                        
                        for result in results:
                            text = result.get("text", "")
                            # Find amounts
                            money_matches = money_pattern.findall(text)
                            if money_matches:
                                amounts.extend(money_matches)
                            
                            # Find percentages
                            pct_matches = percentage_pattern.findall(text)
                            if pct_matches:
                                percentages.extend(pct_matches)
                                
                            # Find dates
                            date_matches = date_pattern.findall(text)
                            if date_matches:
                                dates.extend(date_matches)
                        
                        # Add enhanced analysis based on patterns found
                        if amounts:
                            response["amount_info"] = f"Found monetary values: {', '.join(amounts[:5])}"
                        if dates:
                            response["date_info"] = f"Found dates: {', '.join(dates[:5])}"
                        if percentages:
                            response["percentage_info"] = f"Found percentages: {', '.join(percentages[:5])}"
                    
                    return json.dumps(response)
                except Exception as e:
                    frappe.log_error("RAG", f"Vector store search error: {str(e)}")
                    # Fallback to older files search API if newer one fails
                    try:
                        # Use files search endpoint as fallback
                        file_ids = []
                        for file_info in frappe.recent_file_uploads.values():
                            if file_info.get('indexed') and file_info.get('vector_stores'):
                                if any(vs_id in self.vector_store_ids for vs_id in file_info.get('vector_stores', [])):
                                    if 'file_id' in file_info:
                                        file_ids.append(file_info['file_id'])
                        
                        # If we have file IDs, search them
                        if file_ids:
                            frappe.log_error("RAG", f"Searching in files: {file_ids}")
                            results = []
                            for file_id in file_ids:
                                try:
                                    file_result = client.files.retrieve(file_id=file_id)
                                    results.append({
                                        "file_id": file_id,
                                        "filename": file_result.filename,
                                        "purpose": file_result.purpose
                                    })
                                except Exception:
                                    continue
                            
                            return json.dumps({
                                "results": results,
                                "query": query,
                                "note": "Limited search results available"
                            })
                    except Exception as fallback_error:
                        frappe.log_error("RAG", f"Fallback search error: {str(fallback_error)}")
                    
                    return json.dumps({
                        "error": f"Error searching vector store: {str(e)}",
                        "results": []
                    })
            except Exception as e:
                frappe.log_error("RAG", f"Error in file search function: {str(e)}")
                return json.dumps({
                    "error": str(e),
                    "results": []
                })
        
        # Create FunctionTool for file search with enhanced description and guidance
        function_tool = FunctionTool(
            name="file_search",
            description="""Search for information in uploaded files and documents.
You MUST use this tool whenever a user asks about:
1. Documents, files, or PDFs that have been uploaded
2. Specifics like totals, amounts, dates, names, or details from documents
3. Information that might be contained in uploaded files
4. Information about an invoice, receipt, contract, or any document
5. When questions start with "what is in...", "can you tell me about...", "extract from..."
6. Questions about data, figures, text, or content from any file

VERY IMPORTANT INSTRUCTIONS:
- When a user uploads a file and then asks a question about it, you MUST search within that specific file
- ALWAYS prioritize the most recently uploaded files in your responses
- When extracting information like totals or amounts from a file, be specific about which file and where the information was found
- For questions like "what is the total in this invoice?", make sure to search and respond with data from the most recently uploaded file
""",
            params_json_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query - should be related to what the user is asking about the document. For questions about totals, numbers, or specific data, use explicit terms like 'total amount', 'invoice total', 'date', etc. ALWAYS include specific details like document type (e.g., 'invoice', 'receipt', 'contract') and be very explicit about what information you're looking for (e.g., 'find the total amount in the invoice', 'extract the invoice number')."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            on_invoke_tool=on_invoke_file_search
        )
        
        frappe.log_error("RAG", "Created FunctionTool for file search as replacement for FileSearchTool")
        return function_tool


def create_rag_provider(bot) -> Optional[Any]:
    """
    Create a RAG provider for a Raven bot, supporting both OpenAI and local providers
    
    Args:
        bot: Raven bot document
        
    Returns:
        Optional[Any]: RAG provider instance or None if not available
    """
    try:
        # Create bot configuration dict
        bot_config = {
            "bot_name": bot.name,
            "model_provider": bot.model_provider,
            "enable_file_search": bot.enable_file_search,
            "vector_store_ids": getattr(bot, "vector_store_ids", None),
            "enable_local_rag": getattr(bot, "enable_local_rag", False),
            "local_rag_provider": getattr(bot, "local_rag_provider", "Chroma"),
            "use_local_embeddings": getattr(bot, "use_local_embeddings", False),
            "embeddings_model": getattr(bot, "embeddings_model", "all-MiniLM-L6-v2")
        }
        
        # Log configuration for debugging
        frappe.log_error("RAG", f"Creating RAG provider with config: {json.dumps(bot_config)}")
        
        # Check if RAG is enabled
        if not bot_config.get("enable_file_search"):
            frappe.log_error("RAG", f"File search is disabled for bot {bot.name}")
            return None
        
        # Check if local RAG should be used
        provider = None
        if bot_config.get("enable_local_rag"):
            frappe.log_error("RAG", f"Using local RAG provider: {bot_config.get('local_rag_provider')}")
            try:
                # Import local RAG provider
                from .local_rag import LocalRAGProvider
                
                # Create local provider based on config
                provider = LocalRAGProvider.create(
                    bot_config.get("local_rag_provider", "Chroma"), 
                    bot_config
                )
                frappe.log_error("RAG", f"Created local RAG provider of type: {bot_config.get('local_rag_provider')}")
            except ImportError as e:
                frappe.log_error("RAG", f"Error importing local RAG: {str(e)}")
                frappe.log_error("RAG", "Falling back to OpenAI RAG provider")
                # Fall back to OpenAI RAG provider
                provider = OpenAIRAGProvider(bot_config)
        else:
            # Use OpenAI provider
            frappe.log_error("RAG", "Using OpenAI RAG provider")
            provider = OpenAIRAGProvider(bot_config)
        
        # Initialize the provider
        result = provider.initialize()
        
        if not result:
            frappe.log_error("RAG", "Provider initialization failed")
            return None
            
        return provider
    except Exception as e:
        error_msg = str(e)
        frappe.log_error("RAG", f"Error creating RAG provider: {error_msg}")
        frappe.throw(f"Failed to initialize RAG: {error_msg}. File search has been disabled.")
        return None


async def process_file_upload(bot, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Process a file upload for a bot, using either local RAG or OpenAI
    
    Args:
        bot: Raven bot document
        file_path: Path to the file
        metadata: Additional metadata for the document
        
    Returns:
        str: File ID or reference
    """
    try:
        # Check if bot has local RAG enabled
        use_local_rag = getattr(bot, "enable_local_rag", False)
        frappe.log_error("RAG", f"Processing file upload with enable_local_rag={use_local_rag}")
        
        if use_local_rag:
            frappe.log_error("RAG", f"Using local RAG for file: {os.path.basename(file_path)}")
            try:
                # Create RAG provider
                provider = create_rag_provider(bot)
                if not provider:
                    frappe.log_error("RAG", "Local provider creation failed, falling back to OpenAI")
                    # Fall back to OpenAI provider
                    openai_provider = OpenAIRAGProvider({
                        "bot_name": bot.name,
                        "model_provider": bot.model_provider,
                        "enable_file_search": bot.enable_file_search,
                        "vector_store_ids": getattr(bot, "vector_store_ids", None)
                    })
                    openai_provider.initialize()
                    file_id = openai_provider.process_file(file_path, metadata)
                    frappe.log_error("RAG", f"Processed file with OpenAI fallback, ID: {file_id}")
                    return file_id
                
                # Process with local provider
                file_id = provider.process_file(file_path, metadata)
                frappe.log_error("RAG", f"Processed file with local RAG, ID: {file_id}")
                
                # For local RAG we should also log the file processing in our memory store
                filename = os.path.basename(file_path)
                frappe.log_error("RAG", f"Adding '{filename}' to recent file uploads with local RAG")
                
                # Store in memory and redis
                with _recent_uploads_lock:
                    if not hasattr(frappe, 'recent_file_uploads'):
                        frappe.recent_file_uploads = {}
                        
                    current_time = time.time()
                    frappe.recent_file_uploads[file_id] = {
                        'filename': filename,
                        'upload_time': current_time,
                        'indexed': True,
                        'vector_stores': ['local'],
                        'file_id': file_id,
                        'local_rag': True,
                        'is_most_recent': True
                    }
                    
                    # Mark other files as not most recent
                    for existing_id in frappe.recent_file_uploads:
                        if existing_id != file_id:
                            frappe.recent_file_uploads[existing_id]['is_most_recent'] = False
                
                # Save to Redis
                try:
                    _save_recent_files_to_redis(frappe.recent_file_uploads)
                    frappe.log_error("RAG", f"Saved file record to Redis: {file_id}")
                except Exception as redis_err:
                    frappe.log_error("RAG", f"Redis error: {str(redis_err)}")
                
                return file_id
                
            except Exception as local_err:
                frappe.log_error("RAG", f"Error with local RAG: {str(local_err)}")
                frappe.log_error("RAG", "Falling back to OpenAI RAG")
                # Continue with OpenAI as fallback
                pass
        
        # If not using local RAG or local RAG failed, use OpenAI provider
        frappe.log_error("RAG", f"Using OpenAI RAG for file: {os.path.basename(file_path)}")
        
        # Create RAG provider
        provider = create_rag_provider(bot)
        if not provider:
            return ""
        
        # Process file with OpenAI
        file_id = provider.process_file(file_path, metadata)
        frappe.log_error("RAG", f"Added file '{os.path.basename(file_path)}' to vector store {provider.vector_store_ids}")
        return file_id
    except Exception as e:
        frappe.log_error("RAG", f"Error processing file upload: {str(e)}")
        return ""


def get_file_search_tool(bot) -> Optional[Any]:
    """
    Get a file search tool for a bot (either local RAG tool or OpenAI FileSearchTool)
    
    Args:
        bot: Raven bot document
        
    Returns:
        Optional[Any]: File search tool object
    """
    try:
        # Check if local RAG is enabled
        use_local_rag = getattr(bot, "enable_local_rag", False)
        frappe.log_error("RAG", f"Getting file search tool with enable_local_rag={use_local_rag}")
        
        if use_local_rag:
            frappe.log_error("RAG", "Using local file search tool")
            try:
                # Import from local_rag module
                from .local_rag import create_local_file_search_tool
                
                # Create local search tool
                tool = create_local_file_search_tool(bot)
                frappe.log_error("RAG", "Created local file search tool")
                return tool
            except ImportError as e:
                frappe.log_error("RAG", f"Error importing local_rag module: {str(e)}")
                frappe.log_error("RAG", "Falling back to OpenAI file search tool")
                # Fall back to OpenAI provider if local import fails
            except Exception as e:
                frappe.log_error("RAG", f"Error creating local file search tool: {str(e)}")
                frappe.log_error("RAG", "Falling back to OpenAI file search tool")
                # Fall back to OpenAI provider if local tool creation fails
        
        # If not using local RAG or it failed, use OpenAI provider
        frappe.log_error("RAG", "Using OpenAI file search tool")
        provider = create_rag_provider(bot)
        if not provider:
            return None
        
        # Get tool from OpenAI provider
        tool = provider.get_tool()
        return tool
    except Exception as e:
        frappe.log_error("RAG", f"Error getting file search tool: {str(e)}")
        return None


def preprocess_pdf_for_upload(input_path: str, output_path: str = None) -> str:
    """
    Preprocess a PDF file to make it more compatible with OpenAI's file upload
    
    Args:
        input_path: Path to the original PDF file
        output_path: Path where the processed PDF should be saved (if None, uses a temp file)
    
    Returns:
        str: Path to the processed PDF file
    """
    try:
        import os
        from tempfile import mktemp
        
        # Use PyPDF2 if installed, otherwise try to use pdf2image and PIL
        try:
            frappe.log_error("PDF Process", f"Attempting to process PDF: {input_path}")
            
            try:
                # Try PyPDF2 approach first
                from PyPDF2 import PdfReader, PdfWriter
                
                if not output_path:
                    output_path = mktemp() + '.pdf'
                
                reader = PdfReader(input_path)
                writer = PdfWriter()
                
                # Process each page
                for page in reader.pages:
                    # Add page without compression to avoid compatibility issues
                    writer.add_page(page)
                
                # Write the processed PDF to a new file
                with open(output_path, 'wb') as out_file:
                    writer.write(out_file)
                
                frappe.log_error("PDF Process", f"Successfully processed PDF with PyPDF2: {output_path}")
                return output_path
                
            except ImportError:
                # Fall back to pdf2image and PIL approach
                frappe.log_error("PDF Process", "PyPDF2 not found, trying pdf2image approach")
                from pdf2image import convert_from_path
                from PIL import Image
                
                if not output_path:
                    output_path = mktemp() + '.pdf'
                    
                # Convert PDF to images
                images = convert_from_path(input_path)
                
                # Save the first image as PDF (simple approach for single page)
                if len(images) > 0:
                    images[0].save(output_path, 'PDF', resolution=150.0, save_all=True, append_images=images[1:])
                    frappe.log_error("PDF Process", f"Successfully converted PDF to images and back: {output_path}")
                    return output_path
                else:
                    frappe.log_error("PDF Process", "No pages found in PDF, returning original")
                    return input_path
                    
        except Exception as e:
            frappe.log_error("PDF Process", f"Error processing PDF with libraries: {str(e)}")
            
            # Last resort: try to use system commands if available
            try:
                if not output_path:
                    output_path = mktemp() + '.pdf'
                
                # Try using ghostscript (available on many systems)
                import subprocess
                subprocess.run([
                    'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                    '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
                    f'-sOutputFile={output_path}', input_path
                ], check=True)
                
                frappe.log_error("PDF Process", f"Successfully processed PDF with ghostscript: {output_path}")
                return output_path
                
            except Exception as cmd_error:
                frappe.log_error("PDF Process", f"System command failed: {str(cmd_error)}")
                return input_path
                
    except Exception as outer_error:
        frappe.log_error("PDF Process", f"Error in PDF preprocessing: {str(outer_error)}")
        return input_path

def process_uploaded_file_immediately(file_path: str, filename: str, file_id: str, channel_id: str = None) -> bool:
    """
    Directly process an uploaded file for immediate RAG without going through the async flow
    This is critical for files that are uploaded in threads where the normal flow might not process them
    
    Args:
        file_path: Path to the file on disk
        filename: Original filename
        file_id: Unique file ID to reference
        channel_id: Channel context where this file was uploaded
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        frappe.log_error("RAG Direct", f"Processing file directly: {filename}, ID: {file_id}")
        
        # Initialize tracking data structure if needed
        with _recent_uploads_lock:
            if not hasattr(frappe, 'recent_file_uploads'):
                frappe.recent_file_uploads = {}
            
            # Track the file with full metadata regardless of whether vector processing succeeds
            current_time = time.time()
            file_metadata = {
                'filename': filename, 
                'upload_time': current_time,
                'indexed': True,  # Mark as already indexed to avoid double processing
                'vector_stores': [],  # Will be populated if vector store processing succeeds
                'file_id': file_id,
                'file_type': os.path.splitext(filename)[1].lower() if filename else '',
                'channel_id': channel_id,
                'is_most_recent': True,  # Mark this as the most recent file
                'direct_processed': True  # Flag that this was processed through direct path
            }
            
            # Mark all other files as not most recent
            for existing_file_id in frappe.recent_file_uploads:
                if existing_file_id != file_id:
                    frappe.recent_file_uploads[existing_file_id]['is_most_recent'] = False
            
            # Store metadata immediately
            frappe.recent_file_uploads[file_id] = file_metadata
            
            # Save to Redis for persistence between requests
            _save_recent_files_to_redis(frappe.recent_file_uploads)
            
            # Log the tracking info
            frappe.log_error("RAG Direct", f"Tracking file in memory and Redis: {json.dumps(file_metadata)}")
        
        # Find a bot with RAG capability
        bots = frappe.get_all("Raven Bot", 
                              filters={"enable_file_search": 1}, 
                              fields=["name", "vector_store_ids", "enable_local_rag"])
        
        if not bots:
            frappe.log_error("RAG Direct", "No bots with file search enabled found")
            return True  # Still return success since we've tracked the file
        
        # Look for a bot with local RAG enabled first
        local_rag_bot = None
        openai_rag_bot = None
        
        for bot_record in bots:
            # Check if the bot has local RAG enabled
            if bot_record.get("enable_local_rag"):
                local_rag_bot = frappe.get_doc("Raven Bot", bot_record.name)
                frappe.log_error("RAG Direct", f"Found local RAG bot: {local_rag_bot.name}")
                break
            # Keep track of an OpenAI RAG bot as fallback
            elif bot_record.get("vector_store_ids"):
                openai_rag_bot = frappe.get_doc("Raven Bot", bot_record.name)
        
        # Try to process with local RAG first
        if local_rag_bot:
            frappe.log_error("RAG Direct", f"Using local RAG for file: {filename}")
            try:
                # Import local RAG module
                from .local_rag import LocalRAGProvider
                
                # Create local provider
                provider_type = local_rag_bot.local_rag_provider
                config = {
                    "bot_name": local_rag_bot.name,
                    "model_provider": local_rag_bot.model_provider,
                    "enable_file_search": local_rag_bot.enable_file_search,
                    "enable_local_rag": local_rag_bot.enable_local_rag,
                    "local_rag_provider": local_rag_bot.local_rag_provider,
                    "use_local_embeddings": getattr(local_rag_bot, "use_local_embeddings", True),
                    "embeddings_model": getattr(local_rag_bot, "embeddings_model", "all-MiniLM-L6-v2")
                }
                
                frappe.log_error("RAG Direct", f"Creating local provider: {provider_type}")
                local_provider = LocalRAGProvider.create(provider_type, config)
                
                # Initialize provider
                init_result = local_provider.initialize()
                if not init_result:
                    frappe.log_error("RAG Direct", "Failed to initialize local provider")
                    raise ValueError("Local provider initialization failed")
                
                # Process the file with local provider
                frappe.log_error("RAG Direct", f"Processing file with local provider: {filename}")
                local_doc_id = local_provider.process_file(file_path, {
                    "channel_id": channel_id,
                    "file_id": file_id,
                    "source": "direct_upload"
                })
                
                frappe.log_error("RAG Direct", f"Added file '{filename}' to local RAG with ID: {local_doc_id}")
                
                # Update metadata with local processing info
                with _recent_uploads_lock:
                    if file_id in frappe.recent_file_uploads:
                        frappe.recent_file_uploads[file_id]['local_rag'] = True
                        frappe.recent_file_uploads[file_id]['local_doc_id'] = local_doc_id
                        frappe.recent_file_uploads[file_id]['vector_stores'].append('local')
                        # Save to Redis
                        _save_recent_files_to_redis(frappe.recent_file_uploads)
                
                return True
                
            except Exception as local_err:
                frappe.log_error("RAG Direct", f"Error using local RAG: {str(local_err)}")
                frappe.log_error("RAG Direct", "Falling back to OpenAI RAG")
                # Continue with OpenAI as fallback
        
        # If no local RAG bot found or local processing failed, try OpenAI
        if not openai_rag_bot:
            # If no standard OpenAI bot found, try finding one with SQL
            try:
                bot_records = frappe.db.sql("""
                    SELECT name, vector_store_ids FROM `tabRaven Bot` 
                    WHERE enable_file_search = 1 
                    AND vector_store_ids IS NOT NULL
                    AND vector_store_ids != ''
                    LIMIT 1
                """, as_dict=True)
                
                if bot_records and len(bot_records) > 0 and bot_records[0].get("vector_store_ids"):
                    openai_rag_bot = frappe.get_doc("Raven Bot", bot_records[0].get("name"))
            except Exception as sql_err:
                frappe.log_error("RAG Direct", f"SQL error finding OpenAI bot: {str(sql_err)}")
        
        # If we still don't have a bot, return
        if not openai_rag_bot:
            frappe.log_error("RAG Direct", "No suitable bot found for processing file")
            return True  # Still return success since we've tracked the file
        
        # Process with OpenAI
        frappe.log_error("RAG Direct", f"Using OpenAI RAG for file: {filename}")
        try:
            # Create OpenAI client
            from openai import OpenAI
            settings = frappe.get_cached_doc("Raven Settings")
            api_key = settings.get_password("openai_api_key")
            
            if not api_key:
                frappe.log_error("RAG Direct", "OpenAI API key not configured")
                return True  # Still return success since we've tracked the file
            
            client = OpenAI(api_key=api_key)
            
            # Preprocess PDF files if needed to increase compatibility with OpenAI
            processed_file_path = file_path
            is_pdf = file_path.lower().endswith('.pdf')
            is_using_processed = False
            
            if is_pdf:
                frappe.log_error("RAG Direct", f"Preprocessing PDF file: {file_path}")
                processed_file_path = preprocess_pdf_for_upload(file_path)
                is_using_processed = (processed_file_path != file_path)
                frappe.log_error("RAG Direct", f"Using {'processed' if is_using_processed else 'original'} PDF file: {processed_file_path}")
            
            # Try to upload the file to OpenAI (with retry logic for PDF files)
            max_upload_retries = 3
            upload_retry = 0
            upload_success = False
            
            while upload_retry < max_upload_retries and not upload_success:
                try:
                    frappe.log_error("RAG Direct", f"Uploading file to OpenAI (attempt {upload_retry+1}): {processed_file_path}")
                    with open(processed_file_path, "rb") as file:
                        response = client.files.create(
                            file=file,
                            purpose="assistants"
                        )
                    upload_success = True
                except Exception as upload_error:
                    upload_retry += 1
                    error_message = str(upload_error)
                    frappe.log_error("RAG Direct", f"Upload error (attempt {upload_retry}): {error_message}")
                    
                    # If using the processed file failed, try with the original one
                    if is_using_processed and "Invalid file format" in error_message:
                        frappe.log_error("RAG Direct", "Processed PDF failed, trying original file")
                        processed_file_path = file_path
                        is_using_processed = False
                    
                    # If we've reached the max retries, raise the exception
                    if upload_retry >= max_upload_retries:
                        raise Exception(f"Failed to upload after {max_upload_retries} attempts: {error_message}")
            
            # If we got here, the upload succeeded
            if not upload_success:
                raise Exception("Upload failed for unknown reasons")
            
            openai_file_id = response.id
            frappe.log_error("RAG Direct", f"File uploaded to OpenAI with ID: {openai_file_id}")
            
            # Get vector store IDs from the bot
            vector_store_ids = [vs_id.strip() for vs_id in openai_rag_bot.vector_store_ids.split(",") if vs_id.strip()]
            
            if not vector_store_ids:
                frappe.log_error("RAG Direct", "No valid vector store IDs found in bot configuration")
                return True  # Still return success since we've tracked the file
            
            # Update file metadata with the OpenAI file ID for future reference
            with _recent_uploads_lock:
                if file_id in frappe.recent_file_uploads:
                    frappe.recent_file_uploads[file_id]['openai_file_id'] = openai_file_id
                    # Persist to Redis immediately to ensure it's available for next request
                    _save_recent_files_to_redis(frappe.recent_file_uploads)
                    frappe.log_error("RAG Direct", f"Updated OpenAI file ID in Redis: {file_id} -> {openai_file_id}")
            
            # Add file to vector stores
            for vector_store_id in vector_store_ids:
                # Log that we're attempting to add the file
                frappe.log_error("RAG Direct", f"Adding file {openai_file_id} to vector store {vector_store_id}")
                
                # Add the file batch
                batch_response = client.vector_stores.file_batches.create(
                    vector_store_id=vector_store_id,
                    file_ids=[openai_file_id]
                )
                
                # Log the result
                frappe.log_error("RAG Direct", f"Added file to vector store: batch ID {batch_response.id}, status: {batch_response.status}")
                
                # Update the file metadata with vector store ID
                with _recent_uploads_lock:
                    if file_id in frappe.recent_file_uploads:
                        if 'vector_stores' not in frappe.recent_file_uploads[file_id]:
                            frappe.recent_file_uploads[file_id]['vector_stores'] = []
                        frappe.recent_file_uploads[file_id]['vector_stores'].append(vector_store_id)
                        # Persist to Redis immediately with vector store information
                        _save_recent_files_to_redis(frappe.recent_file_uploads)
                        frappe.log_error("RAG Direct", f"Updated vector stores in Redis: {file_id} -> {vector_store_id}")
            
            return True
            
        except Exception as openai_err:
            frappe.log_error("RAG Direct", f"Error processing file with OpenAI: {str(openai_err)}")
            # Still return True since we've tracked the file in memory
            return True
            
    except Exception as e:
        frappe.log_error("RAG Direct", f"Error in direct file processing: {str(e)}")
        return False


def get_recent_uploads() -> Dict[str, float]:
    """
    Get a list of recently uploaded files
    
    Returns:
        Dict[str, float]: Dictionary mapping filenames to upload times
    """
    result = {}
    with _recent_uploads_lock:
        if hasattr(frappe, 'recent_file_uploads'):
            for file_id, info in frappe.recent_file_uploads.items():
                filename = info.get('filename', '')
                if filename:
                    result[filename] = info.get('upload_time', 0)
    return result