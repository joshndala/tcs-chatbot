"""
TCS Multi-Agent Chatbot - Streamlit Application
Main interface for interacting with the multi-agent system.
"""
import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from agents.graph import multi_agent_graph
from database.vector_store import vector_store
from utils.pdf_processor import process_pdf


# Page configuration
st.set_page_config(
    page_title="Executive Assistant for John",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the file uploader's built-in file list (we use our own "Uploaded Documents" section)
st.markdown("""
<style>
    /* Hide the file list that appears under the uploader */
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] + div {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    if 'process_query' not in st.session_state:
        st.session_state.process_query = False


def process_uploaded_pdf(uploaded_file):
    """
    Process an uploaded PDF file and add to vector store.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
    """
    try:
        # Save PDF to disk
        print(f"\\n🔄 Uploading: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
        pdf_path = settings.pdf_dir / uploaded_file.name
        with open(pdf_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        print(f"   ✓ Saved to disk")
        
        # Process PDF
        with st.spinner(f"Processing {uploaded_file.name}..."):
            print(f"   Extracting text and chunking...")
            pdf_data = process_pdf(
                pdf_path,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            print(f"   ✓ Created {pdf_data['num_chunks']} chunks")
            
            # Add to vector store
            vector_store.add_pdf_chunks(
                chunks=pdf_data['chunks'],
                filename=uploaded_file.name,
                metadata={
                    'upload_date': datetime.now().isoformat(),
                    'num_pages': pdf_data.get('num_pages', 0)
                }
            )
            
            # Track uploaded file
            st.session_state.uploaded_files.append({
                'name': uploaded_file.name,
                'num_chunks': pdf_data['num_chunks'],
                'upload_date': datetime.now()
            })
            
            st.success(f"✅ Successfully processed {uploaded_file.name} ({pdf_data['num_chunks']} chunks)")
    
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")


def delete_uploaded_file(filename):
    """Delete a file and mark as deleted to prevent re-upload."""
    try:
        print(f"\n🗑️ Deleting: {filename}")
        
        # 1. Remove from Vector Store
        vector_store.delete_by_metadata({'filename': filename})
        
        # 2. Remove from Disk
        file_path = settings.pdf_dir / filename
        if file_path.exists():
            file_path.unlink()
            
        # 3. Update Session State
        st.session_state.uploaded_files = [
            f for f in st.session_state.uploaded_files 
            if f['name'] != filename
        ]
        
        st.success(f"Deleted {filename}")
        
    except Exception as e:
        st.error(f"Error deleting {filename}: {str(e)}")


def render_sidebar():
    """Render the sidebar with PDF upload and settings."""
    with st.sidebar:
        st.title("📄 Company Policies")
        
        # ... (Buttons section unchange) ...
        # 1. Action Buttons (Top for easy access)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("⚠️ Reset DB", use_container_width=True):
                vector_store.reset_collection()
                st.session_state.uploaded_files = []
                st.session_state.uploader_key += 1  # Reset uploader widget
                for pdf_file in settings.pdf_dir.glob("*.pdf"):
                    pdf_file.unlink()
                st.success("Reset!")
                st.rerun()

        st.divider()
        
        # 2. Uploaded Documents List (Moved up for better visibility)
        if st.session_state.uploaded_files:
            st.subheader("📚 Uploaded Documents")
            for file_info in st.session_state.uploaded_files:
                with st.expander(f"📑 {file_info['name']}"):
                    st.write(f"**Chunks:** {file_info['num_chunks']}")
                    st.write(f"**Uploaded:** {file_info['upload_date'].strftime('%Y-%m-%d %H:%M')}")
                    
                    if st.button("🗑️ Delete File", key=f"del_{file_info['name']}", use_container_width=True):
                        delete_uploaded_file(file_info['name'])
                        st.session_state.uploader_key += 1  # Reset uploader widget
                        st.rerun()
            st.divider()
        
        # 3. PDF Upload
        upload_widget_files = st.file_uploader(
            "Upload Policy PDFs",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload insurance policy documents",
            key=f"uploader_{st.session_state.uploader_key}"
        )
        
        if upload_widget_files:
            needs_rerun = False
            for uploaded_file in upload_widget_files:
                # Check if already processed
                if uploaded_file.name not in [f['name'] for f in st.session_state.uploaded_files]:
                    process_uploaded_pdf(uploaded_file)
                    needs_rerun = True
            
            # Refresh UI to show newly uploaded documents
            if needs_rerun:
                st.rerun()
        
        # 4. Stats
        doc_count = vector_store.get_document_count()
        if doc_count > 0:
            st.metric("Indexed Chunks", doc_count)


def render_chat_interface():
    """Render the main chat interface."""
    st.title("👔 Executive Assistant for John")
    st.caption("Customer Support Analytics & Policy Search")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    
    # Process query if there's one pending (from example button or previous input)
    if st.session_state.get('process_query'):
        query_to_process = st.session_state.messages[-1]['content']
        st.session_state.process_query = False
        
        # Display user message - REMOVED (already shown in history loop above)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Run multi-agent workflow with full conversation history
                    result = multi_agent_graph.run(
                        query=query_to_process,
                        messages=st.session_state.messages[:-1]  # Pass conversation context
                    )
                    
                    # Extract response
                    response = result.get('response', 'I apologize, but I could not generate a response.')
                    agent_type = result.get('agent_type', 'Unknown')
                    
                    # Display response
                    st.markdown(response)
                    
                    # Show debug info in expander
                    with st.expander("🔍 Debug Info"):
                        st.write(f"**Agent Used:** {agent_type}")
                        
                        if result.get('sql_query'):
                            st.code(result['sql_query'], language='sql')
                        
                        if result.get('search_results'):
                            st.write("**Retrieved Chunks:**")
                            for i, chunk in enumerate(result['search_results'][:3], 1):
                                st.text_area(f"Chunk {i}", chunk, height=100)
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': response
                    })
                
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': error_msg
                    })
        
        # Rerun to show chat input again
        st.rerun()
    
    # Chat input - always show
    if prompt := st.chat_input("Ask a question about accounts or policies..."):
        # Add user message
        st.session_state.messages.append({
            'role': 'user',
            'content': prompt
        })
        # Mark for processing on next rerun
        st.session_state.process_query = True
        st.rerun()


def render_example_queries():
    """Render example queries for users."""
    st.subheader("💡 Example Queries")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Customer Support Queries:**")
        examples = [
            "Show breakdown of Refund requests by Product",
            "Avg resolution time for Technical issues with GoPro Hero",
            "Identify customers with multiple Critical tickets",
            "Compare CSAT scores: Chat vs Phone"
        ]
        for example in examples:
            if st.button(example, key=f"account_{example}"):
                # Add to messages and mark for processing
                st.session_state.messages.append({'role': 'user', 'content': example})
                st.session_state.process_query = True
                st.rerun()
    
    with col2:
        st.markdown("**Policy Queries:**")
        examples = [
            "What does our refund policy say?",
            "Explain the customer support escalation process",
            "What are the warranty terms?",
            "What's our policy on damaged products?"
        ]
        for example in examples:
            if st.button(example, key=f"policy_{example}"):
                # Add to messages and mark for processing
                st.session_state.messages.append({'role': 'user', 'content': example})
                st.session_state.process_query = True
                st.rerun()


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main chat interface
    render_chat_interface()
    
    # Show example queries if no messages
    if not st.session_state.messages:
        st.divider()
        render_example_queries()
        
        # Welcome message
        st.info("""
        👋 **Welcome, John!**
        
        I can help you with:
        - 📊 Customer support ticket analytics
        - 👥 Customer profile information
        - 💬 Ticket status and resolution times
        - 📄 Company policy information (upload PDFs first)
        
        Upload policy documents using the sidebar, then ask your questions!
        """)


if __name__ == "__main__":
    main()
