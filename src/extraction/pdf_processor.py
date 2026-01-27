import logging
from pathlib import Path
from typing import List

from config import ASSETS_DIR
from src.models.rules import RuleChunk
from src.models.enums import Federation
from .processing_strategy import FastProcessingStrategy, StructuredProcessingStrategy
from .metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)

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
            logger.warning("No PDF files found", extra={"assets_dir": ASSETS_DIR})
            return []
        
        for i, pdf_file in enumerate(pdf_files):
            filename = pdf_file.name
            current_status = f"Processing {filename}... ({i+1}/{len(pdf_files)})"
            
            if status_callback:
                status_callback(current_status)
            else:
                logger.info(current_status)
            
            federation = self.metadata_extractor.determine_federation(filename)
            strategy = self._select_strategy(filename)
            
            logger.debug("Processing PDF", extra={"strategy": strategy.__class__.__name__, "filename": filename})
            chunks = strategy.process(str(pdf_file), federation, filename)

            all_chunks.extend(chunks)
            logger.info("Created chunks from PDF", extra={"chunk_count": len(chunks), "filename": filename})

        logger.info("PDF processing complete", extra={"total_chunks": len(all_chunks)})
        return all_chunks