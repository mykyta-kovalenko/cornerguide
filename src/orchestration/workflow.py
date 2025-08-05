from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END

from src.agents.retrieval_agent import RetrievalAgent
from src.agents.answer_generator import AnswerGeneratorAgent
from src.agents.medical_research_agent import MedicalResearchAgent
from src.models.rules import RuleChunk
from src.models.enums import Federation

class BJJQueryState(TypedDict):
    original_question: str
    selected_federation: Federation
    federation_routing: Dict[str, Any]
    retrieved_chunks: List[RuleChunk]
    final_answer: Dict[str, Any]
    medical_research: Dict[str, Any]
    error: str

class BJJRuleWorkflow:
    def __init__(self, qdrant_manager=None):
        self.retrieval_agent = RetrievalAgent(qdrant_manager)
        self.answer_generator = AnswerGeneratorAgent()
        self.medical_research_agent = MedicalResearchAgent()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(BJJQueryState)
        
        workflow.add_node("route_federation", self._route_federation_node)
        workflow.add_node("retrieve_chunks", self._retrieve_chunks_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        workflow.add_node("research_medical", self._research_medical_node)
        
        workflow.set_entry_point("route_federation")
        workflow.add_edge("route_federation", "retrieve_chunks")
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
    
    def _retrieve_chunks_node(self, state: BJJQueryState) -> BJJQueryState:
        try:
            federation_filter = None if state["selected_federation"] == Federation.ALL else state["selected_federation"]
            question_dict = {"refined_question": state["original_question"]}
            
            retrieved_chunks = self.retrieval_agent.retrieve(
                question_dict,
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
            print(f"Medical research failed: {str(e)}")
            state["medical_research"] = {}
            return state
    
    def process_query(self, question: str, selected_federation: Federation = Federation.ALL) -> Dict[str, Any]:
        initial_state = BJJQueryState(
            original_question=question,
            selected_federation=selected_federation,
            federation_routing={},
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
                "retrieved_chunks": final_state.get("retrieved_chunks", []),
                "medical_research": final_state.get("medical_research", {})
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "answer": "I encountered an error processing your question. Please try again or contact support."
            }