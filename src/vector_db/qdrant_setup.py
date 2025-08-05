from langchain_qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from typing import List, Dict, Any
from config import COLLECTION_NAME, EMBEDDING_MODEL
from src.models.rules import RuleChunk

class QdrantManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.vectorstore = None
    
    def create_from_chunks(self, chunks: List[RuleChunk]) -> bool:
        if not chunks:
            print("Warning: No chunks to create vectorstore from")
            return False
        
        try:
            documents = []
            for chunk in chunks:
                metadata = {
                    "federation": chunk.federation,
                    "category": chunk.category,
                    "belt_level": chunk.belt_level,
                    "technique": chunk.technique,
                    "source_page": chunk.source_page
                }
                doc = Document(
                    page_content=chunk.content,
                    metadata=metadata
                )
                documents.append(doc)
            
            self.vectorstore = Qdrant.from_documents(
                documents,
                self.embeddings,
                location=":memory:",
                collection_name=COLLECTION_NAME
            )
            
            print(f"Created vectorstore with {len(chunks)} chunks")
            return True
        except Exception as e:
            print(f"Error: Failed to create vectorstore: {e}")
            return False
    
    def search_similar(self, query: str, federation_filter: str = None, category_filter: str = None, 
                      belt_level_filter: str = None, limit: int = 10) -> List[dict]:
        if not self.vectorstore:
            print("Error: Vectorstore not initialized")
            return []
        
        try:
            filter_dict = {}
            
            if federation_filter and federation_filter != "All":
                filter_dict["federation"] = federation_filter
            
            if category_filter:
                filter_dict["category"] = category_filter
                
            if belt_level_filter:
                filter_dict["belt_level"] = belt_level_filter
            
            results = self.vectorstore.similarity_search_with_score(
                query,
                k=limit,
                filter=filter_dict if filter_dict else None
            )
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "federation": doc.metadata.get("federation"),
                    "category": doc.metadata.get("category"),
                    "belt_level": doc.metadata.get("belt_level"),
                    "technique": doc.metadata.get("technique"),
                    "score": score,
                    "metadata": doc.metadata
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error: Search failed: {e}")
            return []
