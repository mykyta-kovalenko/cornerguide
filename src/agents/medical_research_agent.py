from typing import Dict, Any, List, Optional
from src.models.rules import RuleChunk
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import PubMedAPIWrapper
import urllib.parse

from config import LLM_MODEL

class InjuryAssessment(BaseModel):
    needs_research: bool
    technique_name: str
    potential_injuries: List[str]
    body_parts_affected: List[str]
    injury_mechanism: str
    research_keywords: List[str]

class MedicalResearchAgent:
    def __init__(self):
        self.creative_llm = ChatOpenAI(model=LLM_MODEL, temperature=0.7)
        self.research_llm = ChatOpenAI(model=LLM_MODEL, temperature=0.2)
        self.pubmed = PubMedAPIWrapper(top_k_results=3)
    
    def assess_injury_potential(self, question: str, answer: str, retrieved_chunks: List[RuleChunk]) -> InjuryAssessment:
        assessment_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a sports medicine expert analyzing BJJ techniques for injury potential.

Given a BJJ rules question and answer, determine if the technique mentioned has significant injury risks that would warrant medical research.

Focus on techniques that:
- Are banned/restricted due to injury risk (heel hooks, neck cranks, etc.)
- Target vulnerable anatomical areas (joints, spine, neck)
- Can cause serious injuries requiring medical attention
- Have documented injury patterns in grappling sports

Do NOT research for:
- Weight categories, time limits, uniform rules
- Basic positions without submission attempts
- General competition rules
- Point scoring systems

For techniques needing research, identify:
1. The specific technique name
2. Potential medical injuries/conditions
3. Body parts at risk
4. How injuries typically occur
5. Medical search terms for research (use anatomical/medical terms only, avoid BJJ, grappling, martial arts)

Be creative but medically sound. Focus on pure medical terminology for keywords."""),
            ("user", """Question: {question}

Answer: {answer}

Retrieved Context: {context}

Assess whether this warrants medical injury research.""")
        ])
        
        context_text = "\n".join([f"- {chunk.content[:200]}..." for chunk in retrieved_chunks[:3]])
        
        parser = PydanticOutputParser(pydantic_object=InjuryAssessment)
        
        assessment_prompt_with_format = ChatPromptTemplate.from_messages([
            ("system", """You are a sports medicine expert analyzing BJJ techniques for injury potential.

Given a BJJ rules question and answer, determine if the technique mentioned has significant injury risks that would warrant medical research.

Focus on techniques that:
- Are banned/restricted due to injury risk (heel hooks, neck cranks, etc.)
- Target vulnerable anatomical areas (joints, spine, neck)
- Can cause serious injuries requiring medical attention
- Have documented injury patterns in grappling sports

Do NOT research for:
- Weight categories, time limits, uniform rules
- Basic positions without submission attempts
- General competition rules
- Point scoring systems

For techniques needing research, identify:
1. The specific technique name
2. Potential medical injuries/conditions
3. Body parts at risk
4. How injuries typically occur
5. Medical search terms for research (use anatomical/medical terms only, avoid BJJ, grappling, martial arts)

Be creative but medically sound. Focus on pure medical terminology for keywords.

{format_instructions}"""),
            ("user", """Question: {question}

Answer: {answer}

Retrieved Context: {context}

Assess whether this warrants medical injury research.""")
        ])
        
        try:
            response = self.creative_llm.invoke(
                assessment_prompt_with_format.format_messages(
                    question=question,
                    answer=answer,
                    context=context_text,
                    format_instructions=parser.get_format_instructions()
                )
            )
            
            assessment = parser.parse(response.content)
            return assessment
            
        except Exception as e:
            print(f"Error in injury assessment: {e}")
            return InjuryAssessment(
                needs_research=False,
                technique_name="unknown",
                potential_injuries=[],
                body_parts_affected=[],
                injury_mechanism="",
                research_keywords=[]
            )
    
    def research_medical_safety(self, assessment: InjuryAssessment) -> Optional[Dict[str, Any]]:
        if not assessment.needs_research:
            return None
        
        research_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical researcher creating a comprehensive safety analysis for a BJJ technique.

Based on the injury assessment provided, create detailed medical safety information including:

1. **Injury Mechanisms**: How the technique causes damage anatomically
2. **Common Injuries**: Specific medical conditions and their severity
3. **Risk Factors**: What makes injuries more likely
4. **Prevention**: How to perform/defend safely
5. **Recovery**: Typical healing times and treatment approaches
6. **PubMed Search**: Most relevant medical search query

Use your medical knowledge to provide accurate, educational information. Include medical terminology but explain it clearly.

IMPORTANT: Always include a disclaimer that this is for educational purposes only."""),
            ("user", """Technique: {technique}
Potential Injuries: {injuries}
Body Parts: {body_parts}
Injury Mechanism: {mechanism}
Research Keywords: {keywords}

Provide comprehensive medical safety analysis.""")
        ])
        
        try:
            pubmed_articles = self._search_pubmed_articles(assessment.research_keywords)
            
            response = self.research_llm.invoke(
                research_prompt.format_messages(
                    technique=assessment.technique_name,
                    injuries=", ".join(assessment.potential_injuries),
                    body_parts=", ".join(assessment.body_parts_affected),
                    mechanism=assessment.injury_mechanism,
                    keywords=", ".join(assessment.research_keywords)
                )
            )
            
            search_terms = " ".join(assessment.research_keywords[:3])
            encoded_terms = urllib.parse.quote_plus(search_terms)
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_terms}"
            
            return {
                "technique": assessment.technique_name,
                "medical_analysis": response.content,
                "injury_categories": assessment.potential_injuries,
                "affected_anatomy": assessment.body_parts_affected,
                "pubmed_search_url": pubmed_url,
                "pubmed_articles": pubmed_articles,
                "search_keywords": assessment.research_keywords,
                "disclaimer": "This information is for educational purposes only. Consult qualified medical professionals for injury assessment and treatment."
            }
            
        except Exception as e:
            print(f"Error in medical research: {e}")
            return None
    
    def _search_pubmed_articles(self, keywords: List[str]) -> List[Dict[str, str]]:
        if not keywords:
            return []
        
        try:
            search_query = " AND ".join(keywords[:3])
            search_results = self.pubmed.run(search_query)
            
            articles = []
            if search_results and search_results != "No good PubMed Result was found":
                article_sections = search_results.split("\n\n")
                
                for section in article_sections[:3]:
                    if section.strip():
                        lines = section.strip().split("\n")
                        if len(lines) >= 2:
                            title = lines[0].replace("Published: ", "").replace("Title: ", "")
                            summary = "\n".join(lines[1:])
                            
                            articles.append({
                                "title": title,
                                "summary": summary[:300] + "..." if len(summary) > 300 else summary
                            })
            
            return articles
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def process_medical_research(self, question: str, answer: str, retrieved_chunks: List[RuleChunk]) -> Optional[Dict[str, Any]]:
        assessment = self.assess_injury_potential(question, answer, retrieved_chunks)
        if assessment.needs_research:
            return self.research_medical_safety(assessment)
        return None