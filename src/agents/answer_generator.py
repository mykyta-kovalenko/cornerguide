from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any
from config import LLM_MODEL
from src.models.rules import RuleChunk
from src.models.enums import Federation, AnswerType

class AnswerGeneratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    
    def generate_answer(self, 
                       original_question: str,
                       retrieved_chunks: List[RuleChunk],
                       selected_federation: Federation) -> Dict[str, Any]:
        if selected_federation == Federation.ALL:
            return self._generate_comparison_answer(original_question, retrieved_chunks)
        elif selected_federation in [Federation.IBJJF, Federation.ADCC]:
            return self._generate_federation_answer(original_question, retrieved_chunks, selected_federation)
        else:
            raise ValueError(f"Invalid federation selection: {selected_federation}")
    
    def _generate_comparison_answer(self, question: str, retrieved_chunks: List[RuleChunk]) -> Dict[str, Any]:
        ibjjf_chunks = [c for c in retrieved_chunks if c.federation == Federation.IBJJF]
        adcc_chunks = [c for c in retrieved_chunks if c.federation == Federation.ADCC]
        
        if not ibjjf_chunks and not adcc_chunks:
            return self._generate_no_context_answer("all IBJJF and ADCC")
        elif not ibjjf_chunks:
            return self._generate_federation_answer(question, retrieved_chunks, Federation.ADCC)
        elif not adcc_chunks:
            return self._generate_federation_answer(question, retrieved_chunks, Federation.IBJJF)
        
        ibjjf_context = "\n".join([chunk.content for chunk in ibjjf_chunks[:4]])
        adcc_context = "\n".join([chunk.content for chunk in adcc_chunks[:4]])
        
        system_prompt = """
        You are a BJJ rules expert. Use the provided rule context to answer the question accurately and comprehensively.
        
        GUIDELINES:
        - Base your answer primarily on the provided context
        - Interpret tables, lists, and structured data carefully
        - When you see techniques with belt level restrictions, apply that logic appropriately
        - Make reasonable inferences from the available context
        - Be specific and direct in your answers
        - If the context is incomplete but contains relevant information, provide what you can determine
        - Only say you cannot answer if the context is completely unrelated to the question
        
        Provide a comprehensive answer that fully utilizes the available context to address the question.
        """
        
        human_prompt = f"""
        Question: {question}
        
        IBJJF Rules Context:
        {ibjjf_context}
        
        ADCC Rules Context:
        {adcc_context}
        
        Provide a comprehensive comparison addressing the question.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "answer": response.content,
            "answer_type": AnswerType.COMPARISON,
            "federations_covered": [Federation.IBJJF, Federation.ADCC],
            "sources_used": len(ibjjf_chunks) + len(adcc_chunks)
        }
    
    def _generate_federation_answer(self, question: str, retrieved_chunks: List[RuleChunk], federation: Federation) -> Dict[str, Any]:
        federation_chunks = [c for c in retrieved_chunks if c.federation == federation]
        
        if not federation_chunks:
            return self._generate_no_context_answer(federation)
        
        context = "\n".join([chunk.content for chunk in federation_chunks[:5]])
        
        system_prompt = f"""
        You are a BJJ rules expert. Use the provided {federation} rule context to answer the question accurately and comprehensively.
        
        GUIDELINES:
        - Base your answer primarily on the provided {federation} context
        - Interpret tables, lists, and structured data carefully
        - When you see techniques with belt level restrictions, apply that logic appropriately
        - Make reasonable inferences from the available context
        - Be specific and direct in your answers
        - If the context is incomplete but contains relevant information, provide what you can determine
        - Only say you cannot answer if the context is completely unrelated to the question
        
        Provide a comprehensive answer that fully utilizes the available {federation} context to address the question.
        """
        
        human_prompt = f"""
        Question: {question}
        
        {federation} Rules Context:
        {context}
        
        Provide a comprehensive answer based on {federation} rules.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "answer": response.content,
            "answer_type": AnswerType.SINGLE_FEDERATION, 
            "federations_covered": [federation],
            "sources_used": len(federation_chunks)
        }
    
    def _generate_no_context_answer(self, federation_context: str) -> Dict[str, Any]:
        if federation_context == "all IBJJF and ADCC":
            answer = """
I don't know the answer to this question based on the available rule context.

**Recommended Actions:**
- **For IBJJF rules**: Check the official IBJJF website (ibjjf.com) or contact IBJJF support
- **For ADCC rules**: Visit the official ADCC website (adccsubmission.com) or contact ADCC support
- **Alternative**: Consult with experienced coaches or referees familiar with all federations

I recommend verifying any rule interpretations with official federation sources before competition.
            """.strip()
        else:
            website = "ibjjf.com" if federation_context == "IBJJF" else "adccsubmission.com"
            answer = f"""
I don't know the answer to this question based on the available {federation_context} rule context.

**Recommended Actions:**
- Check the official {federation_context} website ({website})
- Contact {federation_context} support directly
- Consult with experienced coaches or referees familiar with {federation_context} rules

I recommend verifying any rule interpretations with official {federation_context} sources before competition.
            """.strip()
        
        return {
            "answer": answer,
            "answer_type": AnswerType.NO_CONTEXT,
            "federations_covered": [],
            "sources_used": 0
        }