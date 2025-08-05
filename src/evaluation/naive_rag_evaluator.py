import pandas as pd
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_qdrant import Qdrant
import os

from src.vector_db.qdrant_setup import QdrantManager
from src.evaluation.golden_dataset import get_golden_dataset
from config import EMBEDDING_MODEL

class NaiveRAGEvaluator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.qdrant_manager = QdrantManager()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
    
    def naive_process_pdfs(self) -> List[Document]:
        print("Processing PDFs with naive fixed-size chunking...")
        all_chunks = []
        
        pdf_folder = "assets"
        pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
        
        for i, filename in enumerate(pdf_files, 1):
            print(f"Processing {filename}... ({i}/{len(pdf_files)})")
            file_path = os.path.join(pdf_folder, filename)
            
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            text_chunks = self.text_splitter.split_documents(documents)
            
            federation = "IBJJF" if "IBJJF" in filename else "ADCC"
            
            for chunk_doc in text_chunks:
                chunk_doc.metadata["federation"] = federation
                chunk_doc.metadata["source_file"] = filename
                all_chunks.append(chunk_doc)
        
        print(f"Created {len(all_chunks)} naive chunks total")
        return all_chunks
    
    def initialize_system(self):
        print("Initializing naive RAG system...")
        
        documents = self.naive_process_pdfs()
        
        self.qdrant_manager.vectorstore = Qdrant.from_documents(
            documents,
            self.qdrant_manager.embeddings,
            location=":memory:",
            collection_name="naive_chunks"
        )
        
        print(f"Naive system initialized with {len(documents)} rule chunks")
    
    def naive_retrieve(self, question: str, k: int = 5) -> List[str]:
        results = self.qdrant_manager.vectorstore.similarity_search(question, k=k)
        return [doc.page_content for doc in results]
    
    def naive_generate_answer(self, question: str, contexts: List[str]) -> str:
        context_text = "\n\n".join(contexts)
        
        prompt = f"""Based on the following BJJ rules context, answer the question directly and concisely.

Context:
{context_text}

Question: {question}

Answer:"""
        
        response = self.llm.invoke(prompt)
        return response.content
    
    def generate_system_responses(self, test_data: List[Dict[str, Any]]) -> Dataset:
        responses = []
        contexts = []
        
        for i, item in enumerate(test_data, 1):
            question = item["question"]
            
            print(f"Processing {i}/{len(test_data)}: {question[:50]}...")
            
            context_list = self.naive_retrieve(question)
            answer = self.naive_generate_answer(question, context_list)
            
            responses.append(answer)
            contexts.append(context_list)
        
        dataset_dict = {
            "question": [item["question"] for item in test_data],
            "answer": responses,
            "contexts": contexts,
            "ground_truth": [item["ground_truth"] for item in test_data]
        }
        
        return Dataset.from_dict(dataset_dict)
    
    def run_evaluation(self) -> Dict[str, float]:
        self.initialize_system()
        
        print("Loading complete golden dataset...")
        test_data = get_golden_dataset()
        print(f"Evaluating naive RAG on {len(test_data)} test cases")
        
        print("Generating naive system responses...")
        dataset = self.generate_system_responses(test_data)
        
        print("Running RAGAS evaluation on naive RAG...")
        
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
        print("NAIVE RAG EVALUATION RESULTS - BASELINE COMPARISON")
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
        print(f"NAIVE RAG PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Average Score: {avg_score:.3f}")
        
        if avg_score >= 0.75:
            print("🟢 Naive system performs well")
        elif avg_score >= 0.65:
            print("🟡 Naive system shows acceptable performance")
        else:
            print("🔴 Naive system requires improvements")
        
        return results_dict

def main():
    evaluator = NaiveRAGEvaluator()
    results = evaluator.run_evaluation()
    evaluator.print_results_table(results)

if __name__ == "__main__":
    main()