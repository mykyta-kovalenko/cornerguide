import streamlit as st
import time

from src.orchestration.workflow import BJJRuleWorkflow
from src.extraction.pdf_processor import PDFProcessor
from src.vector_db.qdrant_setup import QdrantManager

st.set_page_config(
    page_title="CornerGuide - BJJ Rules Assistant",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
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
""", unsafe_allow_html=True)

@st.cache_resource(hash_funcs={"_thread.RLock": lambda _: None})
def initialize_system():
    """Initialize the complete system including PDF processing."""
    
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
            
            # Process PDFs with status updates
            chunks = processor.process_all_pdfs(status_callback=update_status)
            
            if chunks:
                status_text.text("🔗 Creating vector database...")
                # Create in-memory vectorstore
                success = qdrant_manager.create_from_chunks(chunks)
                
                if success:
                    status_text.text(f"✅ Ready with {len(chunks)} rule chunks!")
                    status.update(label="✅ CornerGuide Ready!", state="complete")
                else:
                    status_text.text("❌ Failed to create vectorstore")
                    status.update(label="❌ Initialization Failed", state="error")
            else:
                status_text.text("⚠️ No rule documents found")
                status.update(label="⚠️ No Documents Found", state="error")
    
    return workflow, qdrant_manager

def main():
    """Main Streamlit application."""
    
    # Initialize system on first load
    if 'system_initialized' not in st.session_state:
        workflow, qdrant_manager = initialize_system()
        st.session_state.system_initialized = True
        st.session_state.workflow = workflow
        st.session_state.qdrant_manager = qdrant_manager
    else:
        workflow = st.session_state.workflow
        qdrant_manager = st.session_state.qdrant_manager
    
    # Header
    st.markdown("<h1 style='text-align: center; color: #ff6b35; margin-bottom: 0.5rem;'>🥋 CornerGuide</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #fafafa; font-size: 1.1em; margin-bottom: 2rem;'>Your BJJ Rules Assistant - Avoid penalties, compete confidently</p>", unsafe_allow_html=True)
    
    # Main interface
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Federation selector
        st.markdown("<div class='federation-selector'>", unsafe_allow_html=True)
        federation = st.selectbox(
            "Select Federation:",
            options=["All (Compare)", "IBJJF", "ADCC"],
            index=0,
            help="Choose which federation rules to query"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Map display option to internal value
        federation_map = {
            "All (Compare)": "All",
            "IBJJF": "IBJJF", 
            "ADCC": "ADCC"
        }
        selected_federation = federation_map[federation]
        
        # Question input
        question = st.text_area(
            "Ask your BJJ rules question:",
            placeholder="e.g., 'Are heel hooks legal for blue belts?' or 'What's the difference in scoring between IBJJF and ADCC?'",
            height=100
        )
        
        # Submit button
        if st.button("🔍 Get Answer", type="primary", use_container_width=True):
            if question.strip():
                get_answer(question, selected_federation, workflow)
            else:
                st.warning("Please enter a question.")
    
    # Footer with database status
    if qdrant_manager.vectorstore:
        st.markdown("---")
        st.markdown(f"<p style='text-align: center; color: #999; font-size: 0.8em;'>Database: In-memory vectorstore ready</p>", unsafe_allow_html=True)

def get_answer(question: str, federation: str, workflow: BJJRuleWorkflow):
    """Process the question and display the answer."""
    
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
                    st.markdown(f"**Answer type:** {result['answer_type'].replace('_', ' ').title()}")
                
                # Display medical research if available
                if result.get("medical_research") and result["medical_research"]:
                    medical_info = result["medical_research"]
                    
                    st.markdown("---")
                    st.markdown("### 🏥 Medical Safety Information")
                    
                    with st.expander(f"📊 Safety Analysis: {medical_info['technique']}", expanded=False):
                        st.markdown(medical_info["medical_analysis"])
                        
                        if medical_info.get("affected_anatomy"):
                            st.markdown("**Body parts at risk:** " + ", ".join(medical_info["affected_anatomy"]))
                        
                        # Display actual PubMed articles
                        if medical_info.get("pubmed_articles") and medical_info["pubmed_articles"]:
                            st.markdown("#### 📚 Related Research Articles")
                            for i, article in enumerate(medical_info["pubmed_articles"], 1):
                                with st.container():
                                    st.markdown(f"**{i}. {article['title']}**")
                                    st.markdown(article["summary"])
                                    st.markdown("")
                        
                        if medical_info.get("pubmed_search_url"):
                            st.markdown(f"🔬 [**Search more articles on PubMed**]({medical_info['pubmed_search_url']})")
                        
                        if medical_info.get("disclaimer"):
                            st.warning(medical_info["disclaimer"])
            
        else:
            st.error(f"❌ Error: {result['error']}")
            
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()