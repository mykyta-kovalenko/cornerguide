from src.models.enums import Category, BeltLevel

class ContentCategorizer:
    def categorize_content(self, text: str) -> Category:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["points", "scoring", "advantage", "mount", "guard", "takedown"]):
            return Category.SCORING
        
        if any(word in text_lower for word in ["time", "minutes", "duration", "match"]):
            return Category.TIME_LIMITS
            
        if any(word in text_lower for word in ["technique", "legal", "illegal", "allowed", "prohibited", "submission", "leg lock", "heel hook"]):
            return Category.TECHNIQUES
            
        if any(word in text_lower for word in ["penalty", "infraction", "foul", "disqualification"]):
            return Category.PENALTIES
            
        if any(word in text_lower for word in ["belt", "division", "age", "weight", "category"]):
            return Category.DIVISIONS
            
        return Category.GENERAL