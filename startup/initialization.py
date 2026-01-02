"""System initialization for CornerGuide."""

import logging

import streamlit as st

from src.extraction.pdf_processor import PDFProcessor
from src.orchestration.workflow import BJJRuleWorkflow
from src.vector_db.qdrant_setup import QdrantManager

logger = logging.getLogger(__name__)


@st.cache_resource(hash_funcs={"_thread.RLock": lambda _: None})
def initialize_system():
    """
    Initialize the complete system including PDF processing.

    Returns:
        tuple: (BJJRuleWorkflow, QdrantManager)
    """
    logger.info("Initializing CornerGuide system")

    # Initialize components
    qdrant_manager = QdrantManager()
    processor = PDFProcessor()
    workflow = BJJRuleWorkflow(qdrant_manager)

    if not qdrant_manager.vectorstore:
        # Process PDFs and create vectorstore
        with st.status("Initializing CornerGuide...", expanded=True) as status:
            status_text = st.empty()

            def update_status(message):
                status_text.text(f"📄 {message}")
                logger.debug(f"PDF processing: {message}")

            # Process PDFs with status updates
            chunks = processor.process_all_pdfs(status_callback=update_status)

            if chunks:
                status_text.text("🔗 Creating vector database...")
                # Create in-memory vectorstore
                success = qdrant_manager.create_from_chunks(chunks)

                if success:
                    status_text.text(f"✅ Ready with {len(chunks)} rule chunks!")
                    status.update(label="✅ CornerGuide Ready!", state="complete")
                    logger.info(
                        "System initialized successfully", extra={"num_chunks": len(chunks)}
                    )
                else:
                    status_text.text("❌ Failed to create vectorstore")
                    status.update(label="❌ Initialization Failed", state="error")
                    logger.error("Failed to create vectorstore")
            else:
                status_text.text("⚠️ No rule documents found")
                status.update(label="⚠️ No Documents Found", state="error")
                logger.warning("No PDF documents found for processing")

    return workflow, qdrant_manager
