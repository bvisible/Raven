# raven/ai/rag/retriever.py
import frappe
import json
import numpy as np
from typing import List, Dict, Optional
from sklearn.metrics.pairwise import cosine_similarity

class RavenRAGRetriever:
    """Context retrieval manager for the RAG system"""
    
    def __init__(self, rag_config: Dict):
        self.config = rag_config
        self.similarity_threshold = rag_config.get("similarity_threshold", 0.7)
        self.max_results = rag_config.get("max_results", 5)
    
    async def retrieve_context(self, query: str, bot_name: str = None) -> List[Dict]:
        """Retrieve relevant context for a query"""
        # Generate embedding for the query
        query_embedding = await self._generate_query_embedding(query, bot_name)
        
        # Retrieve all embeddings for the bot
        embeddings_data = self._get_all_embeddings(bot_name)
        
        if not embeddings_data:
            return []
        
        # Calculate similarities
        similarities = self._calculate_similarities(query_embedding, embeddings_data)
        
        # Filter and sort results
        relevant_docs = self._filter_and_sort_results(similarities, embeddings_data)
        
        return relevant_docs[:self.max_results]
    
    async def _generate_query_embedding(self, query: str, bot_name: str) -> List[float]:
        """Generate embedding for a query"""
        from ..agent_manager import RavenAgentManager
        
        manager = RavenAgentManager()
        client = manager.get_client_for_bot(bot_name)
        
        try:
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            frappe.log_error(f"Error generating query embedding: {e}")
            # Return a random vector in case of error
            return np.random.rand(1536).tolist()
    
    def _get_all_embeddings(self, bot_name: str) -> List[Dict]:
        """Retrieve all embeddings for a bot"""
        embeddings = frappe.get_all(
            "Raven Document Embedding",
            filters={"bot_name": bot_name},
            fields=[
                "name", 
                "chunk_id", 
                "chunk_text", 
                "embedding", 
                "file_path", 
                "metadata",
                "created_at"
            ]
        )
        
        # Decode JSON embeddings
        for emb in embeddings:
            try:
                emb["embedding_vector"] = json.loads(emb["embedding"])
                emb["metadata"] = json.loads(emb.get("metadata", "{}"))
            except Exception as e:
                frappe.log_error(f"Error decoding embedding: {e}")
                emb["embedding_vector"] = None
        
        # Filter invalid embeddings
        return [emb for emb in embeddings if emb.get("embedding_vector")]
    
    def _calculate_similarities(self, query_embedding: List[float], 
                              embeddings_data: List[Dict]) -> List[float]:
        """Calculate cosine similarities between query and documents"""
        try:
            # Convert to numpy arrays
            query_vec = np.array(query_embedding).reshape(1, -1)
            doc_vectors = np.array([emb["embedding_vector"] for emb in embeddings_data])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vec, doc_vectors)[0]
            
            return similarities.tolist()
        except Exception as e:
            frappe.log_error(f"Error calculating similarities: {e}")
            # Return random similarities in case of error
            return [np.random.random() for _ in embeddings_data]
    
    def _filter_and_sort_results(self, similarities: List[float], 
                                embeddings_data: List[Dict]) -> List[Dict]:
        """Filter and sort results by relevance"""
        results = []
        
        for i, similarity in enumerate(similarities):
            if similarity >= self.similarity_threshold:
                result = {
                    "chunk_id": embeddings_data[i]["chunk_id"],
                    "text": embeddings_data[i]["chunk_text"],
                    "file_path": embeddings_data[i]["file_path"],
                    "similarity": similarity,
                    "metadata": embeddings_data[i].get("metadata", {})
                }
                results.append(result)
        
        # Sort by descending similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results
    
    async def hybrid_search(self, query: str, bot_name: str, 
                           keyword_weight: float = 0.3) -> List[Dict]:
        """Hybrid search combining semantic similarity and keywords"""
        # Semantic search
        semantic_results = await self.retrieve_context(query, bot_name)
        
        # Keyword search
        keyword_results = self._keyword_search(query, bot_name)
        
        # Combine results
        combined_results = self._combine_results(
            semantic_results, 
            keyword_results, 
            keyword_weight
        )
        
        return combined_results[:self.max_results]
    
    def _keyword_search(self, query: str, bot_name: str) -> List[Dict]:
        """Keyword search in chunks"""
        keywords = query.lower().split()
        
        embeddings = frappe.get_all(
            "Raven Document Embedding",
            filters={"bot_name": bot_name},
            fields=["chunk_id", "chunk_text", "file_path", "metadata"]
        )
        
        results = []
        for emb in embeddings:
            text_lower = emb["chunk_text"].lower()
            score = sum(1 for keyword in keywords if keyword in text_lower)
            
            if score > 0:
                results.append({
                    "chunk_id": emb["chunk_id"],
                    "text": emb["chunk_text"],
                    "file_path": emb["file_path"],
                    "keyword_score": score / len(keywords),
                    "metadata": json.loads(emb.get("metadata", "{}"))
                })
        
        # Sort by keyword score
        results.sort(key=lambda x: x["keyword_score"], reverse=True)
        
        return results
    
    def _combine_results(self, semantic_results: List[Dict], 
                        keyword_results: List[Dict], 
                        keyword_weight: float) -> List[Dict]:
        """Combine semantic and keyword results"""
        combined = {}
        
        # Add semantic results
        for result in semantic_results:
            chunk_id = result["chunk_id"]
            combined[chunk_id] = result
            combined[chunk_id]["final_score"] = result["similarity"] * (1 - keyword_weight)
        
        # Add or update with keyword results
        for result in keyword_results:
            chunk_id = result["chunk_id"]
            if chunk_id in combined:
                combined[chunk_id]["final_score"] += result["keyword_score"] * keyword_weight
            else:
                result["similarity"] = 0
                result["final_score"] = result["keyword_score"] * keyword_weight
                combined[chunk_id] = result
        
        # Convert to list and sort
        final_results = list(combined.values())
        final_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return final_results