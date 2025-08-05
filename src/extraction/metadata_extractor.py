import re
from typing import Optional
from src.models.enums import BeltLevel, Federation

class MetadataExtractor:
    def extract_belt_level(self, text: str) -> Optional[BeltLevel]:
        text_lower = text.lower()
        
        if "white" in text_lower:
            return BeltLevel.WHITE
        elif "blue" in text_lower:
            return BeltLevel.BLUE
        elif "purple" in text_lower:
            return BeltLevel.PURPLE
        elif "brown" in text_lower:
            return BeltLevel.BROWN
        elif "black" in text_lower:
            return BeltLevel.BLACK
        elif "master" in text_lower:
            return BeltLevel.MASTER
        elif "juvenile" in text_lower:
            return BeltLevel.JUVENILE
        elif "adult" in text_lower:
            return BeltLevel.ADULT
        
        return None
    
    def extract_technique_name(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        techniques = [
            "heel hook", "leg lock", "ankle lock", "knee bar", "toe hold", "calf slicer", 
            "bicep slicer", "neck crank", "spine lock", "guard pull", "takedown", 
            "mount", "side control", "back control", "closed guard", "open guard"
        ]
        
        for technique in techniques:
            if technique in text_lower:
                return technique.replace(" ", "_")
        return None
    
    def extract_source_page(self, text: str) -> Optional[int]:
        if "--- Page" in text:
            try:
                match = re.search(r"--- Page (\d+) ---", text)
                if match:
                    return int(match.group(1))
            except:
                pass
        return None
    
    def determine_federation(self, filename: str) -> Federation:
        filename_upper = filename.upper()
        if "ADCC" in filename_upper:
            return Federation.ADCC
        elif "IBJJF" in filename_upper:
            return Federation.IBJJF
        else:
            return Federation.IBJJF