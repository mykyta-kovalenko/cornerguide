from abc import ABC, abstractmethod
from typing import Dict, Any
import PyPDF2
from unstructured.partition.pdf import partition_pdf

class TextExtractor(ABC):
    @abstractmethod
    def extract(self, pdf_path: str) -> Dict[str, Any]:
        pass

class FastTextExtractor(TextExtractor):
    def extract(self, pdf_path: str) -> Dict[str, Any]:
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                return {'text': text, 'tables': []}
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return {'text': "", 'tables': []}

class StructuredExtractor(TextExtractor):
    def _clean_table_text(self, table_text: str) -> str:
        if not table_text:
            return ""
        
        lines = table_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line in ['|', '|-', '+', '-']:
                line = ' '.join(line.split())
                cleaned_lines.append(line)
        
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = cleaned_text.replace('|', ' ')
        cleaned_text = cleaned_text.replace('+', '')
        cleaned_text = cleaned_text.replace('-', '')
        cleaned_text = ' '.join(cleaned_text.split())
        
        return cleaned_text
    
    def extract(self, pdf_path: str) -> Dict[str, Any]:
        try:
            elements = partition_pdf(
                filename=pdf_path,
                strategy="hi_res",
                infer_table_structure=True,
                extract_images_in_pdf=False
            )
            
            text_content = ""
            tables = []
            
            for element in elements:
                element_type = str(type(element).__name__)
                
                if element_type == 'Table':
                    table_text = element.text
                    page_number = None
                    
                    if hasattr(element, 'metadata') and element.metadata:
                        if hasattr(element.metadata, 'page_number'):
                            page_number = element.metadata.page_number
                    
                    if table_text and len(table_text.strip()) > 20:
                        cleaned_table = self._clean_table_text(table_text)
                        tables.append({
                            'text': cleaned_table,
                            'page_number': page_number
                        })
                        text_content += f"\n{cleaned_table}\n"
                else:
                    text_content += element.text + "\n"
            
            return {'text': text_content, 'tables': tables}
        except Exception as e:
            print(f"Error processing {pdf_path} with structured extraction: {e}")
            return self._fallback_extract(pdf_path)
    
    def _fallback_extract(self, pdf_path: str) -> Dict[str, Any]:
        fallback_extractor = FastTextExtractor()
        return fallback_extractor.extract(pdf_path)