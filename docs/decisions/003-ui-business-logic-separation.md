# ADR-003: Separate UI from Business Logic

## Status
✅ Accepted (2026-01-02)

## Context

The original `app.py` (216 lines) mixed multiple concerns:
- Streamlit UI rendering (CSS, layout, widgets)
- System initialization (Qdrant, PDFProcessor, Workflow)
- Business logic orchestration (query processing)
- Application startup (logging, environment validation)

This violated the **Single Responsibility Principle** and created several problems:

1. **Testing**: Impossible to test initialization without Streamlit runtime
2. **Portability**: Can't swap UI frameworks (e.g., FastAPI) without rewriting business logic
3. **Clarity**: New developers couldn't easily understand system boundaries
4. **Maintainability**: Changes to UI could accidentally break business logic

Additionally, `run.py` duplicated environment validation logic.

## Decision

We refactored to a **layered architecture** with clear module boundaries:

```
cornerguide/
├── app.py                      # Entry point: logging setup + launch
├── startup/
│   ├── validation.py          # Environment validation
│   └── initialization.py      # System initialization (Qdrant, PDF processing)
└── ui/
    └── streamlit_ui.py        # All Streamlit UI logic
```

### Responsibilities

- **app.py**:
  - Initialize structured logging
  - Validate environment variables
  - Launch UI (or API in the future)

- **startup/validation.py**:
  - Check required environment variables (API keys)
  - Fail fast with clear error messages

- **startup/initialization.py**:
  - Create QdrantManager, PDFProcessor, BJJRuleWorkflow
  - Process PDFs and create vectorstore
  - Streamlit-cached for performance

- **ui/streamlit_ui.py**:
  - All Streamlit-specific code (page config, CSS, widgets)
  - User interaction handlers
  - Display logic for answers and medical research

### Changes Made

1. **Created** `startup/` module with validation and initialization
2. **Created** `ui/` module with all Streamlit logic
3. **Rewrote** `app.py` as thin entry point (50 lines, down from 216)
4. **Deleted** `run.py` (consolidated into `app.py`)
5. **Added** structured logging infrastructure (`config.py` + `setup_logging()`)

## Consequences

### Positive

✅ **Testable**: Each module can be unit tested independently
✅ **Portable**: Can add FastAPI routes without touching UI
✅ **Clear boundaries**: Developers immediately understand system structure
✅ **Maintainable**: Changes to UI don't risk breaking initialization
✅ **Logging-ready**: Foundation for adding logging to all modules
✅ **Single entry point**: `streamlit run app.py` instead of `python run.py`

### Negative

⚠️ **More files**: 3 new files instead of 1 monolithic `app.py`
⚠️ **Import paths changed**: Need to update any external scripts importing from old `app.py`

### Neutral

- Deployment command changed from `python run.py` to `streamlit run app.py`
- README needs updating to reflect new structure

## Implementation Notes

**Before:**
```python
# app.py (216 lines)
# - Streamlit config
# - CSS styling
# - initialize_system()
# - main() with UI rendering
# - get_answer() with display logic
```

**After:**
```python
# app.py (50 lines)
def setup_logging(): ...
def main():
    setup_logging()
    validate_environment()
    run_ui()

# startup/initialization.py
@st.cache_resource
def initialize_system(): ...

# ui/streamlit_ui.py (230 lines)
def run_ui(): ...
def process_query(): ...
def display_answer(): ...
```

## Related

- [Architecture Overview](../architecture/overview.md)
- Next: Add logging to all agent files (Phase 2)
- Future: Add FastAPI routes in `api/` module

## References

- [Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)
- [Separation of Concerns](https://en.wikipedia.org/wiki/Separation_of_concerns)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) by Robert C. Martin
