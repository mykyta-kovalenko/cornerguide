from abc import ABC, abstractmethod
from typing import List
from src.models.rules import RuleChunk
from src.models.enums import Federation
from .text_extractor import TextExtractor, FastTextExtractor, StructuredExtractor
from .content_categorizer import ContentCategorizer
from .metadata_extractor import MetadataExtractor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

class ProcessingStrategy(ABC):
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.categorizer = ContentCategorizer()
        self.metadata_extractor = MetadataExtractor()
    
    @abstractmethod
    def get_extractor(self) -> TextExtractor:
        pass
    
    def clean_text(self, text: str) -> str:
        text = " ".join(text.split())
        text = text.replace("© IBJJF", "")
        text = text.replace("© ADCC", "")
        text = text.replace("International Brazilian Jiu-Jitsu Federation", "IBJJF")
        text = text.replace("Abu Dhabi Combat Club", "ADCC")
        return text.strip()
    
    def process(self, pdf_path: str, federation: Federation, source_file: str) -> List[RuleChunk]:
        extractor = self.get_extractor()
        content_data = extractor.extract(pdf_path)
        
        if not content_data['text'] or len(content_data['text'].strip()) < 50:
            print(f"Warning: Little/no content extracted from {source_file}")
            return []
        
        return self._create_chunks(content_data['text'], federation, source_file)
    
    def _create_chunks(self, text: str, federation: Federation, source_file: str) -> List[RuleChunk]:
        raw_chunks = self.text_splitter.split_text(text)
        processed_chunks = []
        
        for chunk in raw_chunks:
            cleaned_chunk = self.clean_text(chunk)
            
            if not cleaned_chunk.strip() or len(cleaned_chunk.strip()) < 30:
                continue
            
            category = self.categorizer.categorize_content(cleaned_chunk)
            belt_level = self.metadata_extractor.extract_belt_level(cleaned_chunk)
            technique = self.metadata_extractor.extract_technique_name(cleaned_chunk)
            source_page = self.metadata_extractor.extract_source_page(cleaned_chunk)
            
            rule_chunk = RuleChunk(
                content=cleaned_chunk,
                federation=federation,
                category=category,
                belt_level=belt_level,
                technique=technique,
                source_page=source_page,
                metadata={"source_file": source_file}
            )
            processed_chunks.append(rule_chunk)
        
        return processed_chunks

class FastProcessingStrategy(ProcessingStrategy):
    def get_extractor(self) -> TextExtractor:
        return FastTextExtractor()

class StructuredProcessingStrategy(ProcessingStrategy):
    def get_extractor(self) -> TextExtractor:
        return StructuredExtractor()