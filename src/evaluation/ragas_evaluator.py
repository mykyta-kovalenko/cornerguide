import pandas as pd
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.orchestration.workflow import BJJRuleWorkflow
from src.vector_db.qdrant_setup import QdrantManager
from src.extraction.pdf_processor import PDFProcessor
from src.evaluation.golden_dataset import get_golden_dataset
from src.models.enums import Federation
from config import EMBEDDING_MODEL

class ComprehensiveRAGASEvaluator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        
        self.pdf_processor = PDFProcessor()
        self.qdrant_manager = QdrantManager()
        self.workflow = None
    
    def initialize_system(self):
        print("Initializing CornerGuide system...")
        
        chunks = self.pdf_processor.process_all_pdfs()
        self.qdrant_manager.create_from_chunks(chunks)
        
        self.workflow = BJJRuleWorkflow(self.qdrant_manager)
        
        print(f"System initialized with {len(chunks)} rule chunks")
    
    def _map_federation_string(self, federation_str: str) -> Federation:
        mapping = {
            "All": Federation.ALL,
            "IBJJF": Federation.IBJJF,
            "ADCC": Federation.ADCC
        }
        return mapping.get(federation_str, Federation.ALL)
    
    def generate_system_responses(self, test_data: List[Dict[str, Any]]) -> Dataset:
        responses = []
        contexts = []
        
        for i, item in enumerate(test_data, 1):
            question = item["question"]
            federation_str = item["federation"]
            federation = self._map_federation_string(federation_str)
            
            print(f"Processing {i}/{len(test_data)}: {question[:50]}...")
            
            result = self.workflow.process_query(question, federation)
            
            if result["success"]:
                if result.get("retrieved_chunks"):
                    context_list = [chunk.content for chunk in result["retrieved_chunks"]]
                else:
                    context_list = ["No context retrieved"]
                
                responses.append(result["answer"])
                contexts.append(context_list)
            else:
                responses.append("Error generating response")
                contexts.append([])
        
        dataset_dict = {
            "question": [item["question"] for item in test_data],
            "answer": responses,
            "contexts": contexts,
            "ground_truth": [item["ground_truth"] for item in test_data]
        }
        
        return Dataset.from_dict(dataset_dict)
    
    def run_evaluation(self) -> Dict[str, float]:
        if not self.workflow:
            self.initialize_system()
        
        print("Loading complete golden dataset...")
        test_data = get_golden_dataset()
        print(f"Evaluating on {len(test_data)} test cases")
        
        print("Generating system responses...")
        dataset = self.generate_system_responses(test_data)
        
        print("Running RAGAS evaluation with all required metrics...")
        
        metrics = [
            faithfulness,
            answer_relevancy, 
            context_precision,
            context_recall
        ]
        
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=self.llm,
            embeddings=self.embeddings
        )
        
        return result
    
    def print_results_table(self, results):
        print("\n" + "="*60)
        print("RAGAS EVALUATION RESULTS - CORNERGUIDE BJJ RULES ASSISTANT")
        print("="*60)
        
        try:
            results_df = results.to_pandas()
            numeric_cols = results_df.select_dtypes(include=['number']).columns
            results_dict = results_df[numeric_cols].mean().to_dict()
        except Exception as e:
            print(f"Error processing results: {e}")
            return
        
        metrics_data = []
        descriptions = {
            "faithfulness": "Factual accuracy based on retrieved context",
            "answer_relevancy": "Relevance of answer to the question asked", 
            "context_precision": "Precision of retrieved context chunks",
            "context_recall": "Coverage of ground truth in retrieved context"
        }
        
        for metric, score in results_dict.items():
            if score >= 0.8:
                status = "🟢 Excellent"
            elif score >= 0.7:
                status = "🟢 Good"  
            elif score >= 0.6:
                status = "🟠 Acceptable"
            else:
                status = "🔴 Needs Improvement"
            
            metrics_data.append({
                "Metric": metric.replace("_", " ").title(),
                "Score": f"{score:.3f}",
                "Status": status,
                "Description": descriptions.get(metric, "")
            })
        
        df = pd.DataFrame(metrics_data)
        print(df.to_string(index=False))
        
        avg_score = sum(results_dict.values()) / len(results_dict)
        print(f"\n{'='*60}")
        print(f"OVERALL PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Average Score: {avg_score:.3f}")
        
        if avg_score >= 0.75:
            print("🟢 System performs well across all metrics")
        elif avg_score >= 0.65:
            print("🟡 System shows acceptable performance with room for improvement")
        else:
            print("🔴 System requires significant improvements")
        
        return results_dict

def main():
    evaluator = ComprehensiveRAGASEvaluator()
    results = evaluator.run_evaluation()
    evaluator.print_results_table(results)

if __name__ == "__main__":
    main()