"""LangGraph workflow for BJJ rules question answering.

This workflow orchestrates:
1. Federation routing - determine which ruleset(s) to query
2. Query expansion - generate multiple search queries (LLM step)
3. Retrieval - deterministic semantic search + reranking
4. Answer generation - synthesize answer with citations
5. Medical research - optional injury safety info

Reference: LangGraph documentation (https://langchain-ai.github.io/langgraph/)
"""
import logging
from typing import Dict, Any, List, TypedDict

from langgraph.graph import StateGraph, END

from src.agents.query_expansion_agent import QueryExpansionAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.answer_generator import AnswerGeneratorAgent
from src.agents.medical_research_agent import MedicalResearchAgent
from src.models.rules import RuleChunk
from src.models.enums import Federation

logger = logging.getLogger(__name__)


class BJJQueryState(TypedDict):
    original_question: str
    selected_federation: Federation
    federation_routing: Dict[str, Any]
    expanded_queries: List[str]
    retrieved_chunks: List[RuleChunk]
    final_answer: Dict[str, Any]
    medical_research: Dict[str, Any]
    error: str

class BJJRuleWorkflow:
    def __init__(self, qdrant_manager=None):
        self.query_expansion_agent = QueryExpansionAgent()
        self.retrieval_agent = RetrievalAgent(qdrant_manager)
        self.answer_generator = AnswerGeneratorAgent()
        self.medical_research_agent = MedicalResearchAgent()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(BJJQueryState)

        workflow.add_node("route_federation", self._route_federation_node)
        workflow.add_node("expand_queries", self._expand_queries_node)
        workflow.add_node("retrieve_chunks", self._retrieve_chunks_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        workflow.add_node("research_medical", self._research_medical_node)

        workflow.set_entry_point("route_federation")
        workflow.add_edge("route_federation", "expand_queries")
        workflow.add_edge("expand_queries", "retrieve_chunks")
        workflow.add_edge("retrieve_chunks", "generate_answer")
        workflow.add_conditional_edges(
            "generate_answer",
            self._should_research_medical,
            {"research": "research_medical", "end": END}
        )
        workflow.add_edge("research_medical", END)

        return workflow.compile()
    
    def _should_research_medical(self, state: BJJQueryState) -> str:
        if not state["final_answer"] or state.get("error"):
            return "end"
        
        question_lower = state["original_question"].lower()
        dangerous_keywords = ["heel hook", "leg lock", "neck crank", "spine", "knee", "ankle", "submission"]
        
        return "research" if any(keyword in question_lower for keyword in dangerous_keywords) else "end"
    
    def _route_federation_node(self, state: BJJQueryState) -> BJJQueryState:
        try:
            if state["selected_federation"] not in [Federation.IBJJF, Federation.ADCC, Federation.ALL]:
                state["selected_federation"] = Federation.ALL

            state["federation_routing"] = {
                "selected": state["selected_federation"],
                "routing_reason": f"Processing for {state['selected_federation']}"
            }
            return state
        except Exception as e:
            state["error"] = f"Federation routing failed: {str(e)}"
            return state

    def _expand_queries_node(self, state: BJJQueryState) -> BJJQueryState:
        """Expand the original question into multiple search queries using LLM."""
        try:
            expanded_queries = self.query_expansion_agent.expand_query(
                state["original_question"]
            )
            state["expanded_queries"] = expanded_queries
            logger.debug("Query expansion complete", extra={
                "original": state["original_question"][:100],
                "num_queries": len(expanded_queries)
            })
            return state
        except Exception as e:
            # Fallback to original question if expansion fails
            logger.warning("Query expansion failed, using original question", extra={"error": str(e)})
            state["expanded_queries"] = [state["original_question"]]
            return state

    def _retrieve_chunks_node(self, state: BJJQueryState) -> BJJQueryState:
        """Retrieve chunks using expanded queries (deterministic operation)."""
        try:
            federation_filter = None if state["selected_federation"] == Federation.ALL else state["selected_federation"]

            retrieved_chunks = self.retrieval_agent.retrieve(
                state["expanded_queries"],
                federation_filter
            )

            state["retrieved_chunks"] = retrieved_chunks
            return state
        except Exception as e:
            state["error"] = f"Chunk retrieval failed: {str(e)}"
            return state
    
    def _generate_answer_node(self, state: BJJQueryState) -> BJJQueryState:
        try:
            final_answer = self.answer_generator.generate_answer(
                state["original_question"],
                state["retrieved_chunks"],
                state["selected_federation"]
            )
            
            state["final_answer"] = final_answer
            return state
        except Exception as e:
            state["error"] = f"Answer generation failed: {str(e)}"
            return state
    
    def _research_medical_node(self, state: BJJQueryState) -> BJJQueryState:
        try:
            medical_research = self.medical_research_agent.process_medical_research(
                state["original_question"],
                state["final_answer"]["answer"],
                state["retrieved_chunks"]
            )
            
            state["medical_research"] = medical_research or {}
            return state
        except Exception as e:
            logger.warning("Medical research failed", extra={"error": str(e)})
            state["medical_research"] = {}
            return state
    
    def process_query(self, question: str, selected_federation: Federation = Federation.ALL) -> Dict[str, Any]:
        initial_state = BJJQueryState(
            original_question=question,
            selected_federation=selected_federation,
            federation_routing={},
            expanded_queries=[],
            retrieved_chunks=[],
            final_answer={},
            medical_research={},
            error=""
        )
        
        try:
            final_state = self.workflow.invoke(initial_state)
            
            if final_state.get("error"):
                return {
                    "success": False,
                    "error": final_state["error"],
                    "answer": "I encountered an error processing your question. Please try again or contact support."
                }
            
            return {
                "success": True,
                "answer": final_state["final_answer"]["answer"],
                "answer_type": final_state["final_answer"]["answer_type"],
                "federations_covered": final_state["final_answer"]["federations_covered"],
                "sources_used": final_state["final_answer"]["sources_used"],
                "citations": final_state["final_answer"].get("citations", []),
                "confidence_score": final_state["final_answer"].get("confidence_score", 0.0),
                "retrieved_chunks": final_state.get("retrieved_chunks", []),
                "medical_research": final_state.get("medical_research", {})
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "answer": "I encountered an error processing your question. Please try again or contact support."
            }