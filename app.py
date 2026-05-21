import streamlit as st
import requests
import uuid
from token_tracker import TokenTracker
from file_utils import extract_text_from_file
import history_manager

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="LangGraph + MCP + Gemini Research Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Custom Sleek Dark-Themed CSS Styling
st.markdown("""
<style>
    /* Dark Theme Background and Font styling */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1c24 100%);
        color: #f0f2f6;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Glassmorphic Cards & Containers */
    .stSidebar {
        background-color: rgba(22, 28, 41, 0.9) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Title Styling */
    h1 {
        background: linear-gradient(90deg, #a78bfa 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 20px;
        text-shadow: 0 4px 10px rgba(99, 102, 241, 0.15);
    }
    
    /* Token and Info Metric Box */
    .metric-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        backdrop-filter: blur(10px);
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #a78bfa;
    }
    
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #9ca3af;
    }

    /* Custom Chat Message Styling */
    .user-msg {
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 15px 15px 0 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    .assistant-msg {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 15px 15px 15px 0;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* Styled Button Hover Effects */
    button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f0f2f6 !important;
        transition: all 0.3s ease;
    }
    button[kind="secondary"]:hover {
        border-color: #a78bfa !important;
        background-color: rgba(167, 139, 250, 0.1) !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "current_chat_id" not in st.session_state:
    # Try to load the most recent chat from history
    chats = history_manager.get_all_chats()
    if chats:
        most_recent_id = chats[0]["id"]
        chat_data = history_manager.load_chat(most_recent_id)
        if chat_data:
            st.session_state.current_chat_id = most_recent_id
            st.session_state.messages = chat_data.get("messages", [])
            st.session_state.file_context = chat_data.get("file_context", "")
            st.session_state.last_uploaded_filename = chat_data.get("last_uploaded_filename", None)
            
            tracker = TokenTracker()
            tracker_data = chat_data.get("token_tracker_data", {})
            tracker.prompt_tokens = tracker_data.get("prompt_tokens", 0)
            tracker.completion_tokens = tracker_data.get("completion_tokens", 0)
            tracker.total_tokens = tracker_data.get("total_tokens", 0)
            st.session_state.token_tracker = tracker
        else:
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.file_context = ""
            st.session_state.last_uploaded_filename = None
            st.session_state.token_tracker = TokenTracker()
    else:
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.file_context = ""
        st.session_state.last_uploaded_filename = None
        st.session_state.token_tracker = TokenTracker()

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

def switch_to_chat(chat_id):
    chat_data = history_manager.load_chat(chat_id)
    if chat_data:
        st.session_state.current_chat_id = chat_id
        st.session_state.messages = chat_data.get("messages", [])
        st.session_state.file_context = chat_data.get("file_context", "")
        st.session_state.last_uploaded_filename = chat_data.get("last_uploaded_filename", None)
        
        tracker = TokenTracker()
        tracker_data = chat_data.get("token_tracker_data", {})
        tracker.prompt_tokens = tracker_data.get("prompt_tokens", 0)
        tracker.completion_tokens = tracker_data.get("completion_tokens", 0)
        tracker.total_tokens = tracker_data.get("total_tokens", 0)
        st.session_state.token_tracker = tracker
        st.session_state.pending_question = None

def start_new_chat():
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.file_context = ""
    st.session_state.last_uploaded_filename = None
    st.session_state.token_tracker = TokenTracker()
    st.session_state.pending_question = None

# Backend API Endpoint URL
BACKEND_URL = "http://localhost:8000/chat"

# App Header
st.title("LangGraph + MCP + Gemini Research Chatbot")

# --- SIDEBAR ---
st.sidebar.markdown("### 📁 Context & Configurations")

# Sidebar File Uploader (key is tied to chat ID so it resets when chat ID changes)
uploaded_file = st.sidebar.file_uploader(
    "Upload context document (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"],
    key=f"uploader_{st.session_state.current_chat_id}"
)

# Extract and Cache Uploaded File Text
if uploaded_file:
    if st.session_state.last_uploaded_filename != uploaded_file.name:
        with st.spinner("Parsing uploaded file..."):
            extracted_text = extract_text_from_file(uploaded_file)
            if extracted_text.startswith("Error"):
                st.sidebar.error(extracted_text)
                st.session_state.file_context = ""
                st.session_state.last_uploaded_filename = None
            else:
                st.sidebar.success(f"Successfully loaded: {uploaded_file.name}")
                st.session_state.file_context = extracted_text
                st.session_state.last_uploaded_filename = uploaded_file.name
                
                # Save chat to persist new file context
                chat_title = st.session_state.messages[0]["content"] if st.session_state.messages else "New Chat"
                history_manager.save_chat(
                    st.session_state.current_chat_id,
                    chat_title,
                    st.session_state.messages,
                    st.session_state.file_context,
                    st.session_state.last_uploaded_filename,
                    st.session_state.token_tracker.summary()
                )
else:
    # If the user removes the file, clear the context
    if st.session_state.last_uploaded_filename is not None:
        st.session_state.file_context = ""
        st.session_state.last_uploaded_filename = None
        chat_title = st.session_state.messages[0]["content"] if st.session_state.messages else "New Chat"
        history_manager.save_chat(
            st.session_state.current_chat_id,
            chat_title,
            st.session_state.messages,
            st.session_state.file_context,
            st.session_state.last_uploaded_filename,
            st.session_state.token_tracker.summary()
        )

# Show Context Summary in Sidebar if file is present
if st.session_state.file_context:
    st.sidebar.info(f"File Context Loaded: {len(st.session_state.file_context)} characters.")
    if st.session_state.last_uploaded_filename:
        st.sidebar.success(f"📄 Active Document: {st.session_state.last_uploaded_filename}")

# Sidebar Settings
st.sidebar.markdown("### ⚙️ View Preferences")
show_reasoning = st.sidebar.checkbox("Show Reasoning Trace", value=True)

# Sidebar Cumulative Token Tracker Summary
st.sidebar.markdown("### 📊 Cumulative Session Tokens")
tokens_summary = st.session_state.token_tracker.summary()

st.sidebar.markdown(f"""
<div class="metric-container">
    <div class="metric-label">Total Input Tokens</div>
    <div class="metric-value">{tokens_summary['prompt_tokens']}</div>
</div>
<div class="metric-container">
    <div class="metric-label">Total Output Tokens</div>
    <div class="metric-value">{tokens_summary['completion_tokens']}</div>
</div>
<div class="metric-container">
    <div class="metric-label">Total Tokens</div>
    <div class="metric-value">{tokens_summary['total_tokens']}</div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Reset Session Tokens"):
    st.session_state.token_tracker.reset()
    # Save chat with reset tokens
    chat_title = st.session_state.messages[0]["content"] if st.session_state.messages else "New Chat"
    history_manager.save_chat(
        st.session_state.current_chat_id,
        chat_title,
        st.session_state.messages,
        st.session_state.file_context,
        st.session_state.last_uploaded_filename,
        st.session_state.token_tracker.summary()
    )
    st.sidebar.success("Counters reset!")
    st.rerun()

# --- CHAT HISTORY SECTION IN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 💬 Chat History")

# New Chat Button
if st.sidebar.button("➕ New Chat", use_container_width=True):
    start_new_chat()
    st.rerun()

all_chats = history_manager.get_all_chats()

for chat in all_chats:
    chat_id = chat["id"]
    title = chat["title"]
    
    # Trim title if too long
    display_title = title if len(title) <= 25 else title[:22] + "..."
    
    # Highlight current chat
    is_active = (chat_id == st.session_state.current_chat_id)
    btn_type = "primary" if is_active else "secondary"
    
    col1, col2 = st.sidebar.columns([0.8, 0.2])
    with col1:
        if st.button(f"💬 {display_title}", key=f"chat_btn_{chat_id}", type=btn_type, use_container_width=True):
            switch_to_chat(chat_id)
            st.rerun()
    with col2:
        if st.button("🗑️", key=f"delete_btn_{chat_id}", use_container_width=True, help="Delete this chat"):
            history_manager.delete_chat(chat_id)
            if is_active:
                remaining_chats = history_manager.get_all_chats()
                if remaining_chats:
                    switch_to_chat(remaining_chats[0]["id"])
                else:
                    start_new_chat()
            st.rerun()

# --- MAIN CONVERSATION DISPLAY ---

# Render Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Check if there is a pending question from clicking follow-up suggestions
user_query = st.chat_input("Ask about your document or recent world events...")

if st.session_state.pending_question:
    user_query = st.session_state.pending_question
    st.session_state.pending_question = None

# If user submits a question
if user_query:
    # Display user question
    with st.chat_message("user"):
        st.write(user_query)

    # Immediately add User Question to history to persist UI representation
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Save immediately with the first user question as the title if it's the first message!
    chat_title = st.session_state.messages[0]["content"] if st.session_state.messages else "New Chat"
    history_manager.save_chat(
        st.session_state.current_chat_id,
        chat_title,
        st.session_state.messages,
        st.session_state.file_context,
        st.session_state.last_uploaded_filename,
        st.session_state.token_tracker.summary()
    )

    # Call Backend API
    with st.spinner("Agent compiling research..."):
        try:
            payload = {
                "question": user_query,
                "file_context": st.session_state.file_context,
                "messages": st.session_state.messages[:-1] # History up to this question
            }
            
            response = requests.post(BACKEND_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                answer = data["answer"]
                reasoning_trace = data["reasoning_trace"]
                token_info = data["token_info"]
                followups = data["followups"]
                
                # Display Assistant Answer
                with st.chat_message("assistant"):
                    st.write(answer)
                    
                    # Collapsible Reasoning Trace (if enabled)
                    if show_reasoning and reasoning_trace:
                        with st.expander("🔍 Step-by-Step Reasoning Trace", expanded=True):
                            for step in reasoning_trace:
                                st.markdown(f"- {step}")
                                
                    # Response-Specific Token Usage
                    with st.expander("⚡ Response Token Usage", expanded=False):
                        st.markdown(f"""
                        * **Prompt Tokens**: `{token_info['prompt_tokens']}`
                        * **Completion Tokens**: `{token_info['completion_tokens']}`
                        * **Total Tokens**: `{token_info['total_tokens']}`
                        """)
                
                # Update Chat History
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Update Cumulative Token Tracker
                st.session_state.token_tracker.update(
                    token_info['prompt_tokens'],
                    token_info['completion_tokens'],
                    token_info['total_tokens']
                )
                
                # Auto-save changes with updated assistant response and tokens
                history_manager.save_chat(
                    st.session_state.current_chat_id,
                    chat_title,
                    st.session_state.messages,
                    st.session_state.file_context,
                    st.session_state.last_uploaded_filename,
                    st.session_state.token_tracker.summary()
                )
                
                # Render Follow-Up Questions (as action buttons)
                if followups:
                    st.markdown("### Suggested Follow-up Questions:")
                    cols = st.columns(len(followups))
                    for idx, q in enumerate(followups):
                        with cols[idx]:
                            if st.button(q, key=f"fup_{idx}_{len(st.session_state.messages)}"):
                                st.session_state.pending_question = q
                                st.rerun()
            else:
                st.error(f"Backend API Error: {response.text}")
                
        except Exception as e:
            st.error(f"Failed to communicate with FastAPI backend: {str(e)}")
            st.info("Make sure the backend is running with `uvicorn api:app --reload` on port 8000.")
