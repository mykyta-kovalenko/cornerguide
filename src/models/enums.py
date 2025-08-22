from enum import Enum

class Federation(str, Enum):
    ADCC = "ADCC"
    IBJJF = "IBJJF"
    ALL = "all"

class Category(str, Enum):
    SCORING = "scoring"
    TIME_LIMITS = "time_limits"
    TECHNIQUES = "techniques"
    PENALTIES = "penalties"
    DIVISIONS = "divisions"
    GENERAL = "general"

class BeltLevel(str, Enum):
    WHITE = "white"
    BLUE = "blue"
    PURPLE = "purple"
    BROWN = "brown"
    BLACK = "black"
    MASTER = "master"
    JUVENILE = "juvenile"
    ADULT = "adult"

class AnswerType(str, Enum):
    COMPARISON = "comparison"
    SINGLE_FEDERATION = "single_federation"
    NO_CONTEXT = "no_context"