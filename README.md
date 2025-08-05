# CornerGuide 🥋

**Your BJJ Rules Assistant - Never Get Penalized Again**

CornerGuide is an AI-powered BJJ rules assistant that prevents costly mistakes by providing instant, authoritative answers about IBJJF and ADCC rules differences.

## 🎯 Problem

BJJ athletes and coaches routinely get penalized or DQ'd because IBJJF and ADCC rules differ on illegal moves, scoring, and uniform requirements. Digging through PDFs or relying on forum hearsay leads to avoidable mistakes during competition.

## 💡 Solution

One-stop, always-current rules reference that's faster and more reliable than manual rule lookup. Ask any rules question and get authoritative answers with citations, highlighting exact differences between federations.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   LangGraph      │    │    Qdrant       │
│   Frontend      │───▶│   Orchestration  │───▶│  Vector Store   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Agent Pipeline │
                    │                  │
                    │ • Federation     │
                    │   Router         │
                    │ • Retrieval      │
                    │   Agent          │
                    │ • Answer Agent   │
                    └──────────────────┘
```

## 🛠️ Tech Stack

### Core Framework
- **LangChain**: RAG pipeline foundation
- **LangGraph**: Agent orchestration and workflow
- **LangSmith**: Tracing and monitoring

### AI Models
- **GPT-4o**: Answer generation and comparison
- **OpenAI text-embedding-3-large**: Embeddings

### Data & Infrastructure
- **Qdrant**: Vector database (in-memory)
- **Pydantic**: Structured data extraction
- **Streamlit**: User interface

### Evaluation
- **RAGAS**: Answer relevancy, faithfulness, context recall
- **LangSmith**: Performance tracking

## 📁 Project Structure

```
cornerguide/
├── assets/                 # PDF rulebooks
├── src/
│   ├── models/            # Pydantic data models
│   ├── extraction/        # PDF processing & chunking
│   ├── agents/            # Individual agent implementations
│   ├── graph/             # LangGraph orchestration
│   ├── retrieval/         # Vector search & reranking
│   └── evaluation/        # RAGAS evaluation pipeline
├── app.py                 # Streamlit frontend
├── config.py              # Configuration & settings
└── requirements.txt       # Dependencies
```

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   cp .env.template .env
   # Edit .env with your OpenAI API key
   ```

2. **Start App**
   ```bash
   python run.py
   ```
   The app will automatically process PDFs on first run.

## 🎯 Success Metrics

- **≥85%** helpful-vote rate in LangSmith feedback
- **<3s** average response time
- **Repeat usage** across competition cycles

## 🔄 Data Pipeline

1. **Extraction**: PDFs → Pydantic models → Structured chunks
2. **Embedding**: OpenAI embeddings → Qdrant in-memory storage
3. **Retrieval**: Similarity search → Top 10 results
4. **Generation**: GPT-4o with citations → Optional comparison

## 📊 Evaluation Framework

- **Automated**: RAGAS metrics on 50 labeled Q&A pairs
- **Manual**: LangSmith human feedback collection
- **Continuous**: Weekly performance monitoring

---

*Built for BJJ athletes who compete across federations and need instant rule clarity.*