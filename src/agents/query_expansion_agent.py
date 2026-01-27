"""Query expansion agent for generating search query variations.

This agent uses an LLM to generate multiple query reformulations for
improved retrieval coverage. This follows the principle that retrieval
should be deterministic - the LLM call happens here, before retrieval.

Reference: "Query Expansion by Prompting Large Language Models" (Jagerman et al., 2023)
"""
import logging
from typing import List, Dict, Any

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import LLM_MODEL

logger = logging.getLogger(__name__)


class BJJQueryVariations(BaseModel):
    """Structured output for query reformulations."""
    reformulation_1: str
    reformulation_2: str


QUERY_GENERATION_TEMPLATE = """You are a BJJ rules expert. Generate 2 focused search queries that rephrase the original question using different BJJ terminology while maintaining the same intent.

Original query: {question}

Generate 2 reformulated queries:

reformulation_1: [rephrase using alternative BJJ terms and rule language - use federation-specific terms like "juvenile" for teenagers, "youth" for kids]
reformulation_2: [rephrase focusing on the core rule concept with different wording - include age ranges and division names]

Keep queries concise, rule-focused, and directly related to the original question intent.

{format_instructions}"""


class QueryExpansionAgent:
    """Agent responsible for expanding user queries into multiple search variations.

    This separation ensures the retrieval layer remains deterministic and testable,
    while query expansion can leverage LLM capabilities for better coverage.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=BJJQueryVariations)
        self.prompt = ChatPromptTemplate.from_template(QUERY_GENERATION_TEMPLATE)

    def expand_query(self, question: str) -> List[str]:
        """Generate multiple query variations from a single question.

        Args:
            question: The original user question

        Returns:
            List of queries including original + LLM-generated variations
        """
        try:
            response = (
                self.prompt
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

            # Filter and deduplicate
            unique_queries = []
            for query in queries:
                if query and query.strip() and query not in unique_queries:
                    if len(query.split()) > 2:
                        unique_queries.append(query.strip())

            all_queries = [question] + unique_queries

            logger.info("Query expansion complete", extra={
                "original_query": question[:100],
                "num_variations": len(unique_queries),
                "total_queries": len(all_queries)
            })

            return all_queries

        except Exception as e:
            logger.warning("Query expansion failed, using original query", extra={
                "error": str(e),
                "question": question[:100]
            })
            return [question]
