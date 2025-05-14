"""
Enhanced RAG implementation using LLM for query understanding and SetFit for intent classification.
This approach avoids hardcoded terms and patterns, making it language-agnostic by design.
"""

import frappe
import json
import os
from typing import Any, Dict, List, Optional, Union
from .openai_client import get_open_ai_client
from .local_rag import LocalRAGProvider, ChromaRAGProvider

# Try to import SetFit for zero-shot text classification
try:
    from setfit import SetFitModel
    from huggingface_hub import hf_hub_download
    from sentence_transformers import SentenceTransformer
    SETFIT_AVAILABLE = True
except ImportError:
    SETFIT_AVAILABLE = False
    frappe.log_error("RAG", "SetFit or sentence-transformers not available. Install with: pip install setfit")


class LLMQueryEnhancer:
    """
    Uses the configured LLM directly to enhance queries instead of hardcoded patterns.
    This makes the approach language-agnostic by leveraging the LLM's understanding.
    Works with any LLM provider (OpenAI, local models, etc.) configured in the bot.
    """
    
    def __init__(self, bot_config=None):
        """
        Initialize the LLM query enhancer
        
        Args:
            bot_config: Bot configuration containing model provider information
        """
        self.bot_config = bot_config
        self.client = None
        self.model_provider = bot_config.get("model_provider") if bot_config else None
        
        try:
            # Initialize the appropriate client based on the model provider
            if self.model_provider == "OpenAI":
                # Use OpenAI client
                self.client = get_open_ai_client()
                frappe.log_error("RAG Debug", "LLMQueryEnhancer initialized with OpenAI client")
            else:
                # For local models, we'll use a different approach
                # Import local model providers
                from .sdk_agents import RavenAgentManager
                self.agent_manager = RavenAgentManager(bot=self.bot_config)
                frappe.log_error("RAG Debug", f"LLMQueryEnhancer initialized with {self.model_provider} provider")
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error initializing LLMQueryEnhancer: {str(e)}")
            self.client = None
    
    def enhance_query(self, query: str) -> str:
        """
        Use the LLM to enhance the query by extracting key concepts
        
        Args:
            query: The original user query
            
        Returns:
            str: An enhanced version of the query
        """
        # Create the prompt for query enhancement
        prompt = f"""
You are a search query optimizer for a RAG (Retrieval Augmented Generation) system.
Your task is to analyze the user's query and extract or generate the most relevant search terms
that will improve document retrieval, without assuming any specific language.

Original Query: "{query}"

Instructions:
1. Identify the key concepts and main information needs from the query
2. Extract important keywords and entities that should be searched for
3. Remove language-specific terms that might not be in the document text
4. If the query appears to be about a document or file, include terms like "document", "content", "information"
5. If the query appears to be about financial information, include terms like "price", "amount", "total", "payment"
6. Respond ONLY with the enhanced search terms, not with explanations

Enhanced Search Terms:
"""
        
        try:
            if self.model_provider == "OpenAI" and self.client:
                # Use OpenAI client for enhancement
                frappe.log_error("RAG Debug", f"Enhancing query with OpenAI: '{query}'")
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a search query optimization assistant that extracts key concepts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,  # Lower temperature for more deterministic results
                    max_tokens=100
                )
                
                enhanced_query = response.choices[0].message.content.strip()
                frappe.log_error("RAG Debug", f"OpenAI enhanced query: '{enhanced_query}'")
                
                return enhanced_query
                
            elif hasattr(self, 'agent_manager'):
                # Use local model for enhancement
                frappe.log_error("RAG Debug", f"Enhancing query with {self.model_provider}: '{query}'")
                
                try:
                    # Use the RavenAgentManager to process the query
                    import asyncio
                    
                    # Create a simple synchronous wrapper for the async function
                    def sync_process_message(message):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(
                                self.agent_manager.process_message(message)
                            )
                            return result
                        finally:
                            loop.close()
                    
                    # Process the query
                    result = sync_process_message(prompt)
                    if result and "message" in result:
                        enhanced_query = result["message"].strip()
                        frappe.log_error("RAG Debug", f"Local model enhanced query: '{enhanced_query}'")
                        return enhanced_query
                    else:
                        frappe.log_error("RAG Debug", f"Local model returned no result")
                        return query
                        
                except Exception as e:
                    frappe.log_error("RAG Debug", f"Error using local model for query enhancement: {str(e)}")
                    return query
            else:
                frappe.log_error("RAG Debug", "No LLM provider available, returning original query")
                return query
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error in LLM query enhancement: {str(e)}")
            return query  # Return original query if enhancement fails


class IntentClassifier:
    """
    Uses SetFit for zero-shot intent classification, avoiding hardcoded patterns.
    """
    
    def __init__(self):
        """Initialize the intent classifier"""
        self.model = None
        self.embedding_model = None
        
        if not SETFIT_AVAILABLE:
            frappe.log_error("RAG Debug", "SetFit not available, intent classification disabled")
            return
        
        try:
            # Load a small multilingual embedding model
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Define document intents with examples (for zero-shot classification)
            self.intents = {
                "document_request": [
                    "What does this document say?",
                    "Can you summarize this PDF?",
                    "Tell me about this file",
                    "What's in this document?",
                    "Read this document for me",
                    "Extract information from this PDF",
                    "Analyze this file",
                    "What is the content of this document?",
                    "Give me details from this file",
                    "Can you explain what this document contains?"
                ],
                "financial_information": [
                    "What is the total amount?",
                    "How much does it cost?",
                    "What's the price?",
                    "Find the invoice total",
                    "What was the payment amount?",
                    "How much was charged?",
                    "What's the bill total?",
                    "Find the cost in the document",
                    "What is the expense amount?",
                    "How much was paid?"
                ],
                "general_query": [
                    "What time is the meeting?",
                    "Who wrote this?",
                    "When was this created?",
                    "Where is the conference?",
                    "What is the address?",
                    "Who is the customer?",
                    "What is the deadline?",
                    "How do I contact them?",
                    "What should I do next?",
                    "Is this correct?"
                ]
            }
            
            frappe.log_error("RAG Debug", "IntentClassifier initialized with embedding model")
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error initializing IntentClassifier: {str(e)}")
            self.embedding_model = None
    
    def classify_intent(self, query: str) -> Dict[str, float]:
        """
        Classify the intent of the query using embedding similarity
        
        Args:
            query: User query
            
        Returns:
            Dict[str, float]: Intent scores
        """
        if not self.embedding_model:
            frappe.log_error("RAG Debug", "No embedding model available")
            # Default to conservative classification
            return {"document_request": 0.3, "financial_information": 0.3, "general_query": 0.4}
        
        try:
            # Encode the query
            query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
            
            # Get scores for each intent
            intent_scores = {}
            
            for intent, examples in self.intents.items():
                # Encode all examples
                example_embeddings = self.embedding_model.encode(examples, convert_to_tensor=True)
                
                # Calculate similarities
                import torch.nn.functional as F
                similarities = F.cosine_similarity(query_embedding.unsqueeze(0), example_embeddings, dim=1)
                
                # Use max similarity as the score for this intent
                intent_scores[intent] = float(similarities.max().item())
            
            # Normalize scores
            total = sum(intent_scores.values())
            if total > 0:
                for intent in intent_scores:
                    intent_scores[intent] /= total
            
            frappe.log_error("RAG Debug", f"Intent classification for '{query}': {intent_scores}")
            return intent_scores
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error in intent classification: {str(e)}")
            # Return default scores
            return {"document_request": 0.3, "financial_information": 0.3, "general_query": 0.4}


class LLMEnhancedRAGProvider(ChromaRAGProvider):
    """
    Enhanced RAG provider that uses LLM for query understanding and SetFit for intent classification.
    This approach avoids hardcoded terms and patterns, making it language-agnostic.
    Works with any configured LLM provider (OpenAI, Ollama, LM Studio, etc.)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the enhanced RAG provider
        
        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.llm_enhancer = LLMQueryEnhancer(config)
        self.intent_classifier = IntentClassifier()
        frappe.log_error("RAG Debug", f"LLMEnhancedRAGProvider initialized with {config.get('model_provider', 'unknown')} provider")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector store with enhanced query understanding
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        try:
            frappe.log_error("RAG Debug", f"Searching for: '{query}', k={k}")
            
            if not self.vector_store:
                frappe.log_error("RAG Debug", "Vector store not initialized, initializing now")
                self.initialize()
            
            # Step 1: Classify the intent of the query
            intent_scores = self.intent_classifier.classify_intent(query)
            frappe.log_error("RAG Debug", f"Intent scores: {intent_scores}")
            
            # Step 2: Use LLM to enhance the query - language-agnostic approach
            enhanced_query = self.llm_enhancer.enhance_query(query)
            frappe.log_error("RAG Debug", f"LLM enhanced query: '{enhanced_query}'")
            
            # Multi-strategy search for better results
            all_results = []
            
            # Strategy 1: Direct vector similarity search with the original query
            frappe.log_error("RAG Debug", "Strategy 1: Direct vector similarity search")
            try:
                direct_results = self.vector_store.similarity_search_with_relevance_scores(
                    query, 
                    k=k
                )
                frappe.log_error("RAG Debug", f"Direct search found {len(direct_results)} results")
                all_results.extend(direct_results)
            except Exception as e:
                frappe.log_error("RAG Debug", f"Direct search failed: {str(e)}")
            
            # Strategy 2: Search with LLM-enhanced query for better semantic matching
            frappe.log_error("RAG Debug", "Strategy 2: Enhanced query search")
            try:
                enhanced_results = self.vector_store.similarity_search_with_relevance_scores(
                    enhanced_query, 
                    k=k
                )
                frappe.log_error("RAG Debug", f"Enhanced search found {len(enhanced_results)} results")
                all_results.extend(enhanced_results)
            except Exception as e:
                frappe.log_error("RAG Debug", f"Enhanced search failed: {str(e)}")
            
            # Strategy 3: MMR search for diversity if appropriate
            frappe.log_error("RAG Debug", "Strategy 3: MMR search for diversity")
            try:
                if hasattr(self.vector_store, "max_marginal_relevance_search"):
                    mmr_results = self.vector_store.max_marginal_relevance_search(
                        query,
                        k=k,
                        fetch_k=k*3,  # Fetch more then filter down
                        lambda_mult=0.5  # Balance between relevance and diversity
                    )
                    # Convert to same format as similarity_search_with_relevance_scores
                    mmr_formatted = [(doc, 0.5) for doc in mmr_results]  # Assign a default score
                    all_results.extend(mmr_formatted)
                    frappe.log_error("RAG Debug", f"MMR search found {len(mmr_results)} results")
            except Exception as e:
                frappe.log_error("RAG Debug", f"MMR search failed: {str(e)}")
            
            # Deduplicate results by document content
            seen_content = set()
            unique_results = []
            
            for doc, score in all_results:
                # Use a hash of the content to detect duplicates
                content_hash = hash(doc.page_content)
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append((doc, score))
            
            frappe.log_error("RAG Debug", f"Deduplicated to {len(unique_results)} unique results")
            
            # Sort by relevance score (highest first)
            unique_results.sort(key=lambda x: x[1], reverse=True)
            
            # Limit to requested number
            filtered_results = unique_results[:k]
            
            # Format and enhance results
            formatted_results = []
            for doc, score in filtered_results:
                # Format the content for better readability
                content = doc.page_content.strip()
                
                # Include source information
                source_info = ""
                if "file_name" in doc.metadata:
                    source_info = f"Source: {doc.metadata['file_name']}"
                    if "page" in doc.metadata:
                        source_info += f", Page {doc.metadata['page']}"
                
                # Add the formatted results
                formatted_results.append({
                    "content": content,
                    "metadata": doc.metadata,
                    "score": score,
                    "source": source_info
                })
            
            # If we find nothing even after trying multiple strategies, try more general search
            if not formatted_results:
                frappe.log_error("RAG Debug", "No results found with specific queries, trying general document search")
                try:
                    # Try a very general search to retrieve any document content
                    general_results = self.vector_store.similarity_search(
                        "important information document data", 
                        k=k
                    )
                    for doc in general_results:
                        source_info = ""
                        if "file_name" in doc.metadata:
                            source_info = f"Source: {doc.metadata['file_name']}"
                            if "page" in doc.metadata:
                                source_info += f", Page {doc.metadata['page']}"
                        
                        formatted_results.append({
                            "content": doc.page_content.strip(),
                            "metadata": doc.metadata,
                            "score": 0.5,  # Default score
                            "source": source_info,
                            "fallback": True  # Mark as fallback result
                        })
                    frappe.log_error("RAG Debug", f"General search found {len(general_results)} results")
                except Exception as e:
                    frappe.log_error("RAG Debug", f"General search failed: {str(e)}")
            
            frappe.log_error("RAG Debug", f"Returning {len(formatted_results)} final results")
            return formatted_results
            
        except Exception as e:
            frappe.log_error("RAG Debug", f"Error in search: {type(e).__name__}: {str(e)}")
            frappe.log_error("RAG Debug", f"Error details: {str(e)}", exc_info=True)
            # Return empty list on error to not break the flow
            return []


# Update provider registry to include our new LLM-enhanced provider
def register_llm_enhanced_provider():
    """Register the LLM-enhanced RAG provider in the LocalRAGProvider registry"""
    try:
        # Add the LLM-enhanced provider class to the LocalRAGProvider.create method
        original_create = LocalRAGProvider.create
        
        def enhanced_create(cls, provider_type: str, config: Dict[str, Any]) -> 'LocalRAGProvider':
            """Enhanced create method that includes the LLM-enhanced provider"""
            if provider_type == "LLMEnhanced":
                return LLMEnhancedRAGProvider(config)
            else:
                return original_create(provider_type, config)
        
        # Replace the class method
        LocalRAGProvider.create = classmethod(enhanced_create)
        frappe.log_error("RAG Debug", "Registered LLMEnhancedRAGProvider")
        return True
    except Exception as e:
        frappe.log_error("RAG Debug", f"Error registering LLMEnhancedRAGProvider: {str(e)}")
        return False


# Run registration at module import time
register_llm_enhanced_provider()