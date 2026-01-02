# Contributing to CornerGuide

Thank you for your interest in contributing to CornerGuide! This document provides guidelines and instructions for contributors.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Module Boundaries](#module-boundaries)
- [Adding Features](#adding-features)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

---

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key
- Cohere API key
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cornerguide.git
cd cornerguide

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.template .env
# Add your API keys to .env

# Validate installation
python validate.py

# Run the application
streamlit run app.py
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### 2. Make Changes

Follow the [Code Standards](#code-standards) and [Module Boundaries](#module-boundaries) guidelines.

### 3. Test Your Changes

```bash
# Run the application
streamlit run app.py

# Test with golden dataset (when available)
python -m src.evaluation.ragas_evaluator
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "Brief description of changes"
```

Commit message format:
```
<type>: <subject>

<optional body>

<optional footer>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:
```
feat: Add NAGA federation support

- Add NAGA enum to Federation
- Update PDF processor to handle NAGA rules
- Add NAGA filter to retrieval agent

Closes #123
```

---

## Code Standards

### Python Style

- Follow **PEP 8** style guide
- Use **black** for formatting (line length: 88)
- Use **type hints** for function signatures
- Use **docstrings** for all public functions

Example:
```python
def retrieve_chunks(self, queries: List[str], federation_filter: str = None) -> List[RuleChunk]:
    """
    Retrieve rule chunks using semantic search.

    Args:
        queries: List of search queries
        federation_filter: Optional federation to filter by (IBJJF, ADCC)

    Returns:
        List of RuleChunk objects with retrieval scores
    """
    pass
```

### Logging

- Use **structured logging** (not print statements)
- Include context in `extra={}` dict
- Use appropriate log levels:
  - `DEBUG` - Detailed diagnostic info
  - `INFO` - General informational messages
  - `WARNING` - Warning messages (recoverable)
  - `ERROR` - Error messages (failures)
  - `CRITICAL` - Critical errors (system cannot continue)

Example:
```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Retrieved chunks",
    extra={"num_chunks": len(chunks), "query": query[:100]}
)
```

### Import Organization

Order imports as follows:
1. Standard library imports
2. Third-party imports
3. Local imports

```python
import logging
from typing import List, Dict

import streamlit as st
from langchain_openai import ChatOpenAI

from config import LLM_MODEL
from src.models.rules import RuleChunk
```

---

## Module Boundaries

**CRITICAL:** Respect these architectural boundaries:

### `app.py` - Entry Point
- ✅ Setup logging
- ✅ Validate environment
- ✅ Launch UI
- ❌ NO business logic
- ❌ NO UI rendering

### `startup/` - Initialization
- ✅ Environment validation
- ✅ System initialization
- ❌ NO UI code
- ❌ NO business logic

### `ui/` - User Interface
- ✅ Streamlit widgets and layout
- ✅ User interaction handling
- ✅ Display logic
- ❌ NO business logic
- ❌ NO direct DB access

### `src/agents/` - RAG Agents
- ✅ Retrieval logic
- ✅ Answer generation
- ✅ Medical research
- ❌ Retrieval should NOT call LLMs (migration in progress)
- ❌ Generation should NOT access DB

### `src/orchestration/` - Workflows
- ✅ LangGraph state machines
- ✅ Multi-step orchestration
- ✅ Routing logic
- ❌ NO direct LLM calls (use agents)

See [docs/architecture/overview.md](docs/architecture/overview.md) for detailed boundaries.

---

## Adding Features

### Adding a New Federation

1. **Add enum** to `src/models/enums.py`:
```python
class Federation(str, Enum):
    IBJJF = "IBJJF"
    ADCC = "ADCC"
    NAGA = "NAGA"  # New
    ALL = "All"
```

2. **Add PDF** to `assets/` and update `config.py`:
```python
PDF_FILES = [
    "IBJJF_Rules.pdf",
    "ADCC_Rules.pdf",
    "NAGA_Rules.pdf",  # New
    ...
]
```

3. **Update UI** in `ui/streamlit_ui.py`:
```python
federation = st.selectbox(
    "Select Federation:",
    options=["All (Compare)", "IBJJF", "ADCC", "NAGA"],  # Add NAGA
    ...
)
```

4. **Test end-to-end** with a NAGA-specific query

5. **Document** in `docs/decisions/` if architectural changes needed

### Adding a New Agent

1. Create file in `src/agents/your_agent.py`
2. Follow existing agent patterns (`retrieval_agent.py`, `answer_generator.py`)
3. Add to workflow in `src/orchestration/workflow.py`
4. Add logging throughout
5. Update architecture docs

---

## Testing

### Manual Testing

```bash
# Run application
streamlit run app.py

# Test queries
# - "Are heel hooks legal for brown belts in IBJJF?"
# - "What's the difference between IBJJF and ADCC scoring?"
```

### Evaluation Testing

```bash
# Run RAGAS evaluation on golden dataset
python -m src.evaluation.ragas_evaluator
```

Expected metrics:
- Faithfulness: > 0.70
- Answer Relevancy: > 0.65
- Context Precision: > 0.90
- Context Recall: > 0.75

### Future: Unit Tests

(Coming in Phase 2)

```bash
pytest tests/
```

---

## Documentation

### When to Update Docs

- **New feature**: Add how-to guide in `docs/guides/`
- **Architectural change**: Create ADR in `docs/decisions/`
- **Module change**: Update `docs/architecture/overview.md`
- **API change**: Update README.md

### Documentation Files

- `README.md` - Overview, quick start, project structure
- `docs/architecture/overview.md` - System architecture
- `docs/decisions/*.md` - Architecture Decision Records (ADRs)
- `docs/guides/*.md` - How-to guides
- `CLAUDE.md` - AI agent instructions

### ADR Template

When making architectural decisions, create an ADR:

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated

## Context
What is the issue we're addressing?

## Decision
What is the change we're making?

## Consequences
Positive, negative, and neutral consequences
```

---

## Pull Request Process

### Before Submitting

1. ✅ Code follows style guide
2. ✅ Logging added (no print statements)
3. ✅ Module boundaries respected
4. ✅ Manual testing completed
5. ✅ Documentation updated
6. ✅ Commit messages are clear

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guide
- [ ] Logging added
- [ ] Module boundaries respected
- [ ] Documentation updated
- [ ] Tested manually
```

### Review Process

1. Submit PR with clear description
2. Wait for maintainer review
3. Address feedback
4. PR merged once approved

---

## Questions?

- Open an issue for bugs or feature requests
- Check [docs/architecture/overview.md](docs/architecture/overview.md) for architecture questions
- Read [CLAUDE.md](CLAUDE.md) for project guidelines

---

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Welcome newcomers
- Follow the project's architectural principles

---

Thank you for contributing to CornerGuide! 🥋
