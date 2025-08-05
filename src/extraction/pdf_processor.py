from pathlib import Path
from typing import List
from config import ASSETS_DIR
from src.models.rules import RuleChunk
from src.models.enums import Federation
from .processing_strategy import FastProcessingStrategy, StructuredProcessingStrategy
from .metadata_extractor import MetadataExtractor

class PDFProcessor:
    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
        self.fast_strategy = FastProcessingStrategy()
        self.structured_strategy = StructuredProcessingStrategy()
    
    def _select_strategy(self, filename: str):
        if "Legal_Techniques" in filename or "legal_techniques" in filename.lower():
            return self.structured_strategy
        else:
            return self.fast_strategy
    
    def process_all_pdfs(self, status_callback=None) -> List[RuleChunk]:
        all_chunks = []
        pdf_files = list(Path(ASSETS_DIR).glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {ASSETS_DIR}")
            return []
        
        for i, pdf_file in enumerate(pdf_files):
            filename = pdf_file.name
            current_status = f"Processing {filename}... ({i+1}/{len(pdf_files)})"
            
            if status_callback:
                status_callback(current_status)
            else:
                print(current_status)
            
            federation = self.metadata_extractor.determine_federation(filename)
            strategy = self._select_strategy(filename)
            
            print(f"Using {strategy.__class__.__name__} for {filename}")
            chunks = strategy.process(str(pdf_file), federation, filename)
            
            all_chunks.extend(chunks)
            print(f"Created {len(chunks)} chunks from {filename}")
        
        print(f"Created {len(all_chunks)} total chunks")
        return all_chunks