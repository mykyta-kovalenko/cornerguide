"""Configuration settings for CornerGuide."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# LangSmith Configuration
LANGSMITH_PROJECT = "cornerguide"
LANGSMITH_TRACING = True

# Model Configuration
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4o"

# Vector Database Configuration  
COLLECTION_NAME = "bjj_rules"

# Retrieval Configuration
TOP_K_RETRIEVAL = 5
CHUNK_SIZE = 800
CHUNK_OVERLAP = 160
RERANK_TOP_K = 20

# Data Paths
ASSETS_DIR = "assets"
PDF_FILES = [
    "ADCC_Rules.pdf",
    "IBJJF_Rules.pdf", 
    "ADCC_Legal_Techniques.pdf",
    "IBJJF_Legal_Techniques.pdf",
    "ADCC_Weight_Classes_Divisions_Categories.pdf",
    "IBJJF_RULES_UPDATE_GUIDE.pdf"
]