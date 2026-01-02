"""Streamlit UI for CornerGuide."""

import logging
import time

import streamlit as st

from src.orchestration.workflow import BJJRuleWorkflow
from startup.initialization import initialize_system

logger = logging.getLogger(__name__)


def configure_page():
    """Configure Streamlit page settings and CSS."""
    st.set_page_config(
        page_title="CornerGuide - BJJ Rules Assistant",
        page_icon="🥋",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
    <style>
        .federation-selector {
            margin: 1rem 0;
        }
        .answer-container {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .stMarkdown > div {
            margin-bottom: 0 !important;
        }
        .sources-info {
            color: #666;
            font-size: 0.9em;
            margin-top: 1rem;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_header():
    """Render application header."""
    st.markdown(
        "<h1 style='text-align: center; color: #ff6b35; margin-bottom: 0.5rem;'>🥋 CornerGuide</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #fafafa; font-size: 1.1em; margin-bottom: 2rem;'>"
        "Your BJJ Rules Assistant - Avoid penalties, compete confidently</p>",
        unsafe_allow_html=True,
    )


def render_query_interface(workflow: BJJRuleWorkflow):
    """Render the query input interface."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Federation selector
        st.markdown("<div class='federation-selector'>", unsafe_allow_html=True)
        federation = st.selectbox(
            "Select Federation:",
            options=["All (Compare)", "IBJJF", "ADCC"],
            index=0,
            help="Choose which federation rules to query",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Map display option to internal value
        federation_map = {"All (Compare)": "All", "IBJJF": "IBJJF", "ADCC": "ADCC"}
        selected_federation = federation_map[federation]

        # Question input
        question = st.text_area(
            "Ask your BJJ rules question:",
            placeholder="e.g., 'Are heel hooks legal for blue belts?' or 'What's the difference in scoring between IBJJF and ADCC?'",
            height=100,
        )

        # Submit button
        if st.button("🔍 Get Answer", type="primary", use_container_width=True):
            if question.strip():
                process_query(question, selected_federation, workflow)
            else:
                st.warning("Please enter a question.")


def render_footer(qdrant_manager):
    """Render application footer."""
    if qdrant_manager.vectorstore:
        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; color: #999; font-size: 0.8em;'>"
            "Database: In-memory vectorstore ready</p>",
            unsafe_allow_html=True,
        )


def process_query(question: str, federation: str, workflow: BJJRuleWorkflow):
    """Process user query and display results."""
    logger.info(
        "Processing query", extra={"question": question[:100], "federation": federation}
    )

    try:
        with st.spinner("🤔 Analyzing your question..."):
            # Add progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Refining question...")
            progress_bar.progress(25)
            time.sleep(0.3)

            status_text.text("Routing to appropriate federation(s)...")
            progress_bar.progress(50)
            time.sleep(0.3)

            status_text.text("Retrieving relevant rules...")
            progress_bar.progress(75)
            time.sleep(0.3)

            status_text.text("Generating comprehensive answer...")
            progress_bar.progress(85)
            time.sleep(0.3)

            status_text.text("Researching medical safety information...")
            progress_bar.progress(95)

            # Process the query
            result = workflow.process_query(question, federation)

            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()

        if result["success"]:
            display_answer(result)
        else:
            st.error(f"❌ Error: {result['error']}")
            logger.error(
                "Query failed",
                extra={"question": question[:100], "error": result["error"]},
            )

    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        logger.exception(
            "Unexpected error processing query", extra={"question": question[:100]}
        )


def display_answer(result: dict):
    """Display query results."""
    # Display the answer in a container
    with st.container():
        st.markdown("### 📋 Answer")
        st.markdown(result["answer"])

        # Display metadata
        with st.container():
            if result["federations_covered"]:
                federations_text = ", ".join(result["federations_covered"])
                st.markdown(f"**Federations covered:** {federations_text}")

            st.markdown(f"**Sources used:** {result['sources_used']} rule excerpts")
            st.markdown(
                f"**Answer type:** {result['answer_type'].replace('_', ' ').title()}"
            )

        # Display medical research if available
        if result.get("medical_research") and result["medical_research"]:
            display_medical_research(result["medical_research"])


def display_medical_research(medical_info: dict):
    """Display medical research information."""
    st.markdown("---")
    st.markdown("### 🏥 Medical Safety Information")

    with st.expander(
        f"📊 Safety Analysis: {medical_info['technique']}", expanded=False
    ):
        st.markdown(medical_info["medical_analysis"])

        if medical_info.get("affected_anatomy"):
            st.markdown(
                "**Body parts at risk:** " + ", ".join(medical_info["affected_anatomy"])
            )

        # Display actual PubMed articles
        if medical_info.get("pubmed_articles") and medical_info["pubmed_articles"]:
            st.markdown("#### 📚 Related Research Articles")
            for i, article in enumerate(medical_info["pubmed_articles"], 1):
                with st.container():
                    st.markdown(f"**{i}. {article['title']}**")
                    st.markdown(article["summary"])
                    st.markdown("")

        if medical_info.get("pubmed_search_url"):
            st.markdown(
                f"🔬 [**Search more articles on PubMed**]({medical_info['pubmed_search_url']})"
            )

        if medical_info.get("disclaimer"):
            st.warning(medical_info["disclaimer"])


def run_ui():
    """Main UI entry point."""
    configure_page()

    # Initialize system on first load
    if "system_initialized" not in st.session_state:
        workflow, qdrant_manager = initialize_system()
        st.session_state.system_initialized = True
        st.session_state.workflow = workflow
        st.session_state.qdrant_manager = qdrant_manager
    else:
        workflow = st.session_state.workflow
        qdrant_manager = st.session_state.qdrant_manager

    # Render UI
    render_header()
    render_query_interface(workflow)
    render_footer(qdrant_manager)
