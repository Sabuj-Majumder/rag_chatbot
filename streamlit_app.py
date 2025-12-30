import streamlit as st
import requests
import base64
import time

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="RAG Master | Elite",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS
st.markdown("""
<style>
    /* Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');

    /* Global */
    .stApp {
        background-color: #0F172A; /* Deep Navy Background */
        color: #F8FAFC;
        font-family: 'Inter', sans-serif;
    }
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }


    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    [data-testid="stToolbar"] {
        display: none !important;
    }

    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    .stDeployButton {
        display: none !important;
    }

    .block-container {
        padding-top: 0rem !important;
        margin-top: 1rem !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1E293B; /* Slightly lighter navy */
        border-right: 1px solid #334155;
    }

    .title-text {
        font-family: 'Playfair Display', serif;
        background: linear-gradient(135deg, #E2E8F0 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    
    .subtitle {
        color: #64748B;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background-color: transparent;
        border: 1px solid #94A3B8;
        color: #94A3B8;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        border-color: #F8FAFC;
        color: #F8FAFC;
    }

    .upload-btn > button {
        background: linear-gradient(135deg, #B45309 0%, #78350F 100%); /* Classy Bronze */
        color: white;
        border: none;
        font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .upload-btn > button:hover {
        background: linear-gradient(135deg, #D97706 0%, #92400E 100%);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        color: #64748B;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #F8FAFC;
        border-bottom: 2px solid #D97706; /* Bronze Accent */
    }

    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
    }
    
    code {
        color: #E2E8F0;
        background-color: #0F172A;
        border: 1px solid #334155;
    }

</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### Knowledge Vault")
    
    uploaded_files = st.file_uploader(
        "Secure Upload", 
        type=["pdf", "docx", "txt", "csv", "db", "png", "jpg"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    st.markdown('<div class="upload-btn">', unsafe_allow_html=True)
    if st.button("📥 Secure Ingest", use_container_width=True):
        if uploaded_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, file in enumerate(uploaded_files):
                status_text.caption(f"Encrypting & Indexing {file.name}...")
                files = {"file": (file.name, file, file.type)}
                try:
                    res = requests.post(f"{API_URL}/upload", files=files)
                    if res.status_code == 200:
                        st.toast(f"Archived: {file.name}", icon="🔐")
                    else:
                        st.toast(f"Failed: {file.name}", icon="❌")
                except:
                    pass
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            time.sleep(0.5)
            status_text.empty()
            progress_bar.empty()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Delete History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

col1, col2 = st.columns([12, 1])
with col1:
    st.markdown('<div class="title-text">RAG Master</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Executive Intelligence Suite</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
            if msg.get("image_url"):
                st.image(msg["image_url"], width=400)
        else:
            # Assistant Message with Tabs
            tab1, tab2, tab3 = st.tabs(["Analysis", "Context", "Audit Trail"])
            
            with tab1:
                st.markdown(msg["content"])
            
            with tab2:
                for src in msg.get("sources", []):
                     with st.expander(f"Reference: {src['filename']}"):
                        st.markdown(f"```text\n{src['page_content']}\n```")
            
            with tab3:
                for src in msg.get("sources", []):
                    st.caption(f"📁 {src['filename']}")



if prompt := st.chat_input("Enter executive query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    payload = {"question": prompt}
    
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                response = requests.post(f"{API_URL}/query", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display Result Immediately
                    tab1, tab2, tab3 = st.tabs(["Analysis", "Context", "Audit Trail"])
                    
                    with tab1:
                        st.markdown(data["answer"])
                    
                    with tab2:
                        for src in data["sources"]:
                             with st.expander(f"Reference: {src['filename']}"):
                                st.markdown(f"```text\n{src['page_content']}\n```")
                    
                    with tab3:
                        for src in data["sources"]:
                            st.caption(f"📁 {src['filename']}")
                    
                    # Save to History
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["answer"],
                        "sources": data["sources"]
                    })
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")


with st.sidebar:
    st.markdown("### Visual Intelligence")
    query_image = st.file_uploader("Upload Schematic/Image", type=["png", "jpg"], key="vis_query")
    if query_image and st.button("Analyze Visual", key="vis_btn"):

        bytes_data = query_image.getvalue()
        b64_str = base64.b64encode(bytes_data).decode('utf-8')

        st.session_state.messages.append({"role": "user", "content": "Analyze this visual asset", "image_url": query_image})
        
        with st.spinner("Analyzing visual data..."):
            try:
                payload = {"question": "Provide a detailed executive summary of this image.", "image_base64": b64_str}
                res = requests.post(f"{API_URL}/query", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["answer"],
                        "sources": data["sources"]
                    })
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")