import logging
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import LLM_MODEL, CONFIDENCE_THRESHOLD
from src.models.rules import RuleChunk
from src.models.enums import Federation, AnswerType

logger = logging.getLogger(__name__)

class AnswerGeneratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

    def _format_citations(self, chunks: List[RuleChunk]) -> List[Dict[str, Any]]:
        """Format chunk metadata as structured citations."""
        citations = []
        for i, chunk in enumerate(chunks):
            citation = {
                "id": i + 1,
                "federation": str(chunk.federation) if chunk.federation else "Unknown",
                "category": str(chunk.category) if chunk.category else "General",
                "source_page": chunk.source_page,
                "content_preview": chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content,
                "rerank_score": chunk.rerank_score,
                "retrieval_score": chunk.retrieval_score,
            }
            citations.append(citation)
        return citations

    def _check_confidence(self, chunks: List[RuleChunk]) -> tuple[bool, float]:
        """Check if retrieval confidence meets threshold. Returns (is_confident, avg_score)."""
        if not chunks:
            return False, 0.0

        # Use rerank scores if available, otherwise fall back to retrieval scores
        scores = []
        for chunk in chunks:
            if chunk.rerank_score is not None:
                scores.append(chunk.rerank_score)
            elif chunk.retrieval_score is not None:
                scores.append(chunk.retrieval_score)

        if not scores:
            return False, 0.0

        avg_score = sum(scores) / len(scores)
        is_confident = avg_score >= CONFIDENCE_THRESHOLD
        logger.debug("Confidence check", extra={"avg_score": avg_score, "threshold": CONFIDENCE_THRESHOLD, "is_confident": is_confident})
        return is_confident, avg_score

    def _generate_low_confidence_answer(self, question: str, avg_score: float, federation: str) -> Dict[str, Any]:
        """Generate a response when confidence is below threshold."""
        answer = f"""I'm not confident I have enough relevant information to accurately answer this question.

**Why I'm uncertain:**
The retrieved rule context may not directly address your specific question. My confidence score ({avg_score:.2f}) is below the threshold needed to provide a reliable answer.

**Recommended Actions:**
- Try rephrasing your question with more specific BJJ terminology
- Check the official {federation} rulebook directly
- Consult with an experienced referee or coach

I'd rather acknowledge uncertainty than risk giving you inaccurate rule information."""

        logger.info("Generated low-confidence answer", extra={"question": question[:100], "avg_score": avg_score})
        return {
            "answer": answer,
            "answer_type": AnswerType.LOW_CONFIDENCE,
            "federations_covered": [],
            "sources_used": 0,
            "citations": [],
            "confidence_score": avg_score,
        }

    def generate_answer(self,
                       original_question: str,
                       retrieved_chunks: List[RuleChunk],
                       selected_federation: Federation) -> Dict[str, Any]:
        # Check confidence before generating
        is_confident, avg_score = self._check_confidence(retrieved_chunks)
        if not is_confident and retrieved_chunks:
            federation_name = "IBJJF/ADCC" if selected_federation == Federation.ALL else str(selected_federation)
            return self._generate_low_confidence_answer(original_question, avg_score, federation_name)

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

        # Format contexts with source references
        ibjjf_context_parts = []
        for i, chunk in enumerate(ibjjf_chunks[:4]):
            page_ref = f" (Page {chunk.source_page})" if chunk.source_page else ""
            ibjjf_context_parts.append(f"[IBJJF-{i+1}{page_ref}]: {chunk.content}")
        ibjjf_context = "\n\n".join(ibjjf_context_parts)

        adcc_context_parts = []
        for i, chunk in enumerate(adcc_chunks[:4]):
            page_ref = f" (Page {chunk.source_page})" if chunk.source_page else ""
            adcc_context_parts.append(f"[ADCC-{i+1}{page_ref}]: {chunk.content}")
        adcc_context = "\n\n".join(adcc_context_parts)

        system_prompt = """You are a BJJ rules expert. Use the provided rule context to answer the question accurately and comprehensively.

GUIDELINES:
- Base your answer primarily on the provided context
- Interpret tables, lists, and structured data carefully
- When you see techniques with belt level restrictions, apply that logic appropriately
- Make reasonable inferences from the available context
- Be specific and direct in your answers
- IMPORTANT: When citing specific rules, reference the source tags (e.g., [IBJJF-1], [ADCC-2])
- If the context is incomplete but contains relevant information, provide what you can determine
- Only say you cannot answer if the context is completely unrelated to the question

Provide a comprehensive answer that fully utilizes the available context to address the question."""

        human_prompt = f"""Question: {question}

IBJJF Rules Context:
{ibjjf_context}

ADCC Rules Context:
{adcc_context}

Provide a comprehensive comparison addressing the question. Reference specific sources when stating rules."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        all_chunks = ibjjf_chunks[:4] + adcc_chunks[:4]
        _, avg_score = self._check_confidence(all_chunks)

        logger.info("Generated comparison answer", extra={
            "question": question[:100],
            "ibjjf_chunks": len(ibjjf_chunks),
            "adcc_chunks": len(adcc_chunks),
            "confidence_score": avg_score
        })

        return {
            "answer": response.content,
            "answer_type": AnswerType.COMPARISON,
            "federations_covered": [Federation.IBJJF, Federation.ADCC],
            "sources_used": len(ibjjf_chunks) + len(adcc_chunks),
            "citations": self._format_citations(all_chunks),
            "confidence_score": avg_score,
        }
    
    def _generate_federation_answer(self, question: str, retrieved_chunks: List[RuleChunk], federation: Federation) -> Dict[str, Any]:
        federation_chunks = [c for c in retrieved_chunks if c.federation == federation]

        if not federation_chunks:
            return self._generate_no_context_answer(federation)

        # Format context with source references
        context_parts = []
        for i, chunk in enumerate(federation_chunks[:5]):
            page_ref = f" (Page {chunk.source_page})" if chunk.source_page else ""
            context_parts.append(f"[{federation}-{i+1}{page_ref}]: {chunk.content}")
        context = "\n\n".join(context_parts)

        system_prompt = f"""You are a BJJ rules expert. Use the provided {federation} rule context to answer the question accurately and comprehensively.

GUIDELINES:
- Base your answer primarily on the provided {federation} context
- Interpret tables, lists, and structured data carefully
- When you see techniques with belt level restrictions, apply that logic appropriately
- Make reasonable inferences from the available context
- Be specific and direct in your answers
- IMPORTANT: When citing specific rules, reference the source tags (e.g., [{federation}-1], [{federation}-2])
- If the context is incomplete but contains relevant information, provide what you can determine
- Only say you cannot answer if the context is completely unrelated to the question

Provide a comprehensive answer that fully utilizes the available {federation} context to address the question."""

        human_prompt = f"""Question: {question}

{federation} Rules Context:
{context}

Provide a comprehensive answer based on {federation} rules. Reference specific sources when stating rules."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        used_chunks = federation_chunks[:5]
        _, avg_score = self._check_confidence(used_chunks)

        logger.info("Generated federation answer", extra={
            "question": question[:100],
            "federation": str(federation),
            "chunks_used": len(used_chunks),
            "confidence_score": avg_score
        })

        return {
            "answer": response.content,
            "answer_type": AnswerType.SINGLE_FEDERATION,
            "federations_covered": [federation],
            "sources_used": len(federation_chunks),
            "citations": self._format_citations(used_chunks),
            "confidence_score": avg_score,
        }
    
    def _generate_no_context_answer(self, federation_context: str) -> Dict[str, Any]:
        if federation_context == "all IBJJF and ADCC":
            answer = """I don't know the answer to this question based on the available rule context.

**Recommended Actions:**
- **For IBJJF rules**: Check the official IBJJF website (ibjjf.com) or contact IBJJF support
- **For ADCC rules**: Visit the official ADCC website (adccsubmission.com) or contact ADCC support
- **Alternative**: Consult with experienced coaches or referees familiar with all federations

I recommend verifying any rule interpretations with official federation sources before competition."""
        else:
            # Handle both string and Federation enum
            fed_str = str(federation_context)
            fed_name = fed_str.replace("Federation.", "") if "Federation." in fed_str else fed_str
            website = "ibjjf.com" if "IBJJF" in fed_name else "adccsubmission.com"
            answer = f"""I don't know the answer to this question based on the available {fed_name} rule context.

**Recommended Actions:**
- Check the official {fed_name} website ({website})
- Contact {fed_name} support directly
- Consult with experienced coaches or referees familiar with {fed_name} rules

I recommend verifying any rule interpretations with official {fed_name} sources before competition."""

        logger.info("Generated no-context answer", extra={"federation_context": str(federation_context)})
        return {
            "answer": answer,
            "answer_type": AnswerType.NO_CONTEXT,
            "federations_covered": [],
            "sources_used": 0,
            "citations": [],
            "confidence_score": 0.0,
        }