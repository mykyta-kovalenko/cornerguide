from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
import cohere

from config import LLM_MODEL, TOP_K_RETRIEVAL, RERANK_TOP_K, COHERE_API_KEY
from src.models.rules import RuleChunk

class BJJQueryVariations(BaseModel):
    reformulation_1: str
    reformulation_2: str

QUERY_GENERATION_TEMPLATE = """
You are a BJJ rules expert. Generate 2 focused search queries that rephrase the original question using different BJJ terminology while maintaining the same intent.

Original query: {question}

Generate 2 reformulated queries:

reformulation_1: [rephrase using alternative BJJ terms and rule language - use federation-specific terms like "juvenile" for teenagers, "youth" for kids]
reformulation_2: [rephrase focusing on the core rule concept with different wording - include age ranges and division names]

Keep queries concise, rule-focused, and directly related to the original question intent.

{format_instructions}
"""

class RetrievalAgent:
    def __init__(self, qdrant_manager=None):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        self.qdrant_manager = qdrant_manager
        self.parser = PydanticOutputParser(pydantic_object=BJJQueryVariations)
        self.query_generation_prompt = ChatPromptTemplate.from_template(QUERY_GENERATION_TEMPLATE)
        
        if COHERE_API_KEY:
            self.cohere_client = cohere.Client(COHERE_API_KEY)
        else:
            self.cohere_client = None
    
    
    def generate_fusion_queries(self, refined_question: Dict[str, Any]) -> List[str]:
        question = refined_question["refined_question"]
        
        try:
            response = (
                self.query_generation_prompt 
                | self.llm 
                | self.parser
            ).invoke({
                "question": question, 
                "format_instructions": self.parser.get_format_instructions()
            })
            
            queries = [
                response.reformulation_1,
                response.reformulation_2,
            ]
            
            unique_queries = []
            for query in queries:
                if query and query.strip() and query not in unique_queries:
                    if len(query.split()) > 2:  # Keep more similar queries
                        unique_queries.append(query.strip())
            
            return [question] + unique_queries
        except Exception as e:
            print(f"Failed to generate query variations: {e}")
            return [question]
    
    def retrieve_chunks(self, queries: List[str], federation_filter: str = None) -> List[RuleChunk]:
        if not self.qdrant_manager or not self.qdrant_manager.vectorstore:
            print("No vectorstore available")
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
    
    def retrieve(self, refined_question: Dict[str, Any], federation_filter: str = None) -> List[RuleChunk]:
        queries = self.generate_fusion_queries(refined_question)
        raw_results = self.retrieve_chunks(queries, federation_filter)
        
        unique_results = []
        seen_content = set()
        
        raw_results.sort(key=lambda x: x.retrieval_score or 0, reverse=True)
        # Remove restrictive score filtering - let reranker do the quality assessment
        filtered_results = raw_results[:RERANK_TOP_K] if len(raw_results) > RERANK_TOP_K else raw_results
        
        for result in filtered_results:
            content_hash = hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: x.retrieval_score or 0, reverse=True)
        
        # Always apply Cohere reranking if available and we have enough results
        if self.cohere_client and len(unique_results) > 0:
            reranked_results = self._rerank_with_cohere(
                refined_question["refined_question"], 
                unique_results[:RERANK_TOP_K]
            )
            if reranked_results:  # Check if reranking was successful
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
            print(f"Reranking failed: {e}")
            return results