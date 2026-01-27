"""Deterministic retrieval agent for semantic search and reranking.

This module handles vector similarity search and Cohere reranking.
Query expansion (LLM-based) has been moved to QueryExpansionAgent to
maintain the principle that retrieval should be deterministic.

Reference: "Precise Zero-Shot Dense Retrieval" (Gao et al., 2021) for reranking patterns
"""
import logging
from typing import List, Optional

import cohere

from config import TOP_K_RETRIEVAL, RERANK_TOP_K, COHERE_API_KEY
from src.models.rules import RuleChunk

logger = logging.getLogger(__name__)


class RetrievalAgent:
    """Deterministic retrieval agent for semantic search and reranking.

    This agent does NOT call LLMs. Query expansion should happen before
    calling this agent's retrieve method.
    """

    def __init__(self, qdrant_manager=None):
        self.qdrant_manager = qdrant_manager

        if COHERE_API_KEY:
            self.cohere_client = cohere.Client(COHERE_API_KEY)
        else:
            self.cohere_client = None
    
    def retrieve_chunks(self, queries: List[str], federation_filter: str = None) -> List[RuleChunk]:
        if not self.qdrant_manager or not self.qdrant_manager.vectorstore:
            logger.error("No vectorstore available for retrieval")
            return []
        
        all_results = []
        # Get sufficient results per query to ensure good coverage for reranking
        results_per_query = 7
        
        for query in queries:
            # Get semantic search results only
            semantic_results = self.qdrant_manager.search_similar(
                query=query,
                federation_filter=federation_filter,
                limit=results_per_query
            )
            
            # Convert to RuleChunk objects
            for result in semantic_results:
                rule_chunk = RuleChunk(
                    content=result["content"],
                    federation=result["federation"],
                    category=result["category"],
                    belt_level=result.get("belt_level"),
                    technique=result.get("technique"),
                    source_page=result["metadata"].get("source_page"),
                    retrieval_score=result["score"],
                    query_used=query
                )
                all_results.append(rule_chunk)
        
        return all_results
    
    def retrieve(self, queries: List[str], federation_filter: Optional[str] = None) -> List[RuleChunk]:
        """Retrieve and rerank chunks for the given queries.

        Args:
            queries: List of search queries (typically from QueryExpansionAgent)
            federation_filter: Optional federation to filter results by

        Returns:
            List of RuleChunk objects, reranked if Cohere is available
        """
        if not queries:
            logger.warning("No queries provided for retrieval")
            return []

        raw_results = self.retrieve_chunks(queries, federation_filter)

        # Deduplicate results
        unique_results = []
        seen_content = set()

        raw_results.sort(key=lambda x: x.retrieval_score or 0, reverse=True)
        filtered_results = raw_results[:RERANK_TOP_K] if len(raw_results) > RERANK_TOP_K else raw_results

        for result in filtered_results:
            content_hash = hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)

        unique_results.sort(key=lambda x: x.retrieval_score or 0, reverse=True)

        logger.info("Retrieved chunks", extra={
            "num_queries": len(queries),
            "raw_results": len(raw_results),
            "unique_results": len(unique_results),
            "federation_filter": federation_filter
        })

        # Apply Cohere reranking if available
        if self.cohere_client and len(unique_results) > 0:
            # Use the first query (original question) for reranking
            reranked_results = self._rerank_with_cohere(
                queries[0],
                unique_results[:RERANK_TOP_K]
            )
            if reranked_results:
                return reranked_results[:TOP_K_RETRIEVAL]

        return unique_results[:TOP_K_RETRIEVAL]
    
    def _rerank_with_cohere(self, query: str, results: List[RuleChunk]) -> List[RuleChunk]:
        """Rerank results using Cohere reranker."""
        try:
            documents = [result.content for result in results]
            
            response = self.cohere_client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=documents,
                top_n=len(documents)
            )
            
            reranked_results = []
            for result in response.results:
                original_chunk = results[result.index]
                # Create new chunk with rerank score
                updated_chunk = original_chunk.model_copy(update={"rerank_score": result.relevance_score})
                reranked_results.append(updated_chunk)
            
            return reranked_results
        except Exception as e:
            logger.warning("Cohere reranking failed, using original results", extra={"error": str(e)})
            return results