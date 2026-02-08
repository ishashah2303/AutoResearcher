import streamlit as st
import requests
import time
import json
from datetime import datetime
import io

# ==================== CONFIG ====================
API_URL = "http://127.0.0.1:8000"
st.set_page_config(
    page_title="AutoResearcher AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SESSION STATE ====================
if 'research_history' not in st.session_state:
    st.session_state.research_history = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = None
if 'current_sources' not in st.session_state:
    st.session_state.current_sources = []

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    /* Main container */
    .main {
        padding-top: 2rem;
    }
    
    /* Title styling */
    .title-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .title-text {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-align: center;
    }
    
    .subtitle-text {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    
    /* Progress bar container */
    .progress-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    
    /* Source cards */
    .source-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .source-score {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .score-high {
        background: #d4edda;
        color: #155724;
    }
    
    .score-medium {
        background: #fff3cd;
        color: #856404;
    }
    
    .score-low {
        background: #f8d7da;
        color: #721c24;
    }
    
    /* History item */
    .history-item {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e9ecef;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .history-item:hover {
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102,126,234,0.2);
    }
    
    /* Stats boxes */
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown("""
<div class="title-container">
    <h1 class="title-text">🧠 AutoResearcher AI</h1>
    <p class="subtitle-text">Agentic Research Assistant • Plan • Search • Evaluate • Synthesize</p>
</div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Research depth
    research_depth = st.select_slider(
        "Research Depth",
        options=["Quick", "Standard", "Deep"],
        value="Standard",
        help="Controls number of sources and analysis depth"
    )
    
    # Max sources
    max_sources = st.slider(
        "Max Sources per Step",
        min_value=3,
        max_value=10,
        value=5,
        help="Number of sources to retrieve per research step"
    )
    
    st.divider()
    
    # History section
    st.header("📚 Research History")
    
    if st.session_state.research_history:
        for idx, item in enumerate(reversed(st.session_state.research_history)):
            with st.container():
                if st.button(
                    f"📄 {item['topic'][:30]}...",
                    key=f"history_{idx}",
                    use_container_width=True
                ):
                    st.session_state.current_report = item['report']
                    st.session_state.current_sources = item['sources']
                    st.rerun()
                st.caption(f"🕐 {item['timestamp']}")
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.research_history = []
            st.rerun()
    else:
        st.info("No research history yet")
    
    st.divider()
    
    # Stats
    st.header("📊 Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Researches", len(st.session_state.research_history))
    with col2:
        total_sources = sum(len(item.get('sources', [])) for item in st.session_state.research_history)
        st.metric("Sources Analyzed", total_sources)

# ==================== MAIN AREA ====================

# Input section
col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input(
        "🔍 Research Topic",
        placeholder="e.g., Impact of AI on healthcare, Climate change solutions, Quantum computing applications...",
        label_visibility="collapsed"
    )
with col2:
    run_button = st.button("🚀 Start Research", type="primary", use_container_width=True, disabled=not topic)

# Example topics
with st.expander("💡 Example Topics"):
    examples = [
        "Impact of AI on healthcare diagnostics",
        "Latest developments in quantum computing",
        "Climate change mitigation strategies",
        "Ethical implications of gene editing",
        "Future of renewable energy technologies"
    ]
    cols = st.columns(len(examples))
    for idx, example in enumerate(examples):
        if cols[idx].button(example, key=f"example_{idx}", use_container_width=True):
            st.session_state.example_topic = example
            st.rerun()

# Use example topic if set
if 'example_topic' in st.session_state:
    topic = st.session_state.example_topic
    del st.session_state.example_topic
    run_button = True

# ==================== RESEARCH EXECUTION ====================
if run_button and topic:
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    step_info = st.empty()
    
    try:
        status_text.info("🎯 Initializing research pipeline...")
        
        # Call API
        response = requests.post(
            f"{API_URL}/research",
            params={"topic": topic},
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            report = data.get("report", "")
            sources = data.get("sources", [])
            
            # Update session state
            st.session_state.current_report = report
            st.session_state.current_sources = sources
            
            # Add to history
            st.session_state.research_history.append({
                'topic': topic,
                'report': report,
                'sources': sources,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
            progress_bar.progress(100)
            status_text.success("✅ Research completed successfully!")
            time.sleep(1)
            st.rerun()
            
        else:
            st.error(f"❌ API Error: {response.status_code}")
            st.code(response.text)
            
    except requests.exceptions.RequestException as e:
        st.error("❌ Could not connect to backend. Make sure the API is running.")
        st.code(str(e))

# ==================== DISPLAY RESULTS ====================
if st.session_state.current_report:
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Download as Markdown
        md_bytes = st.session_state.current_report.encode()
        st.download_button(
            "📥 Download MD",
            data=md_bytes,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        # Download as TXT
        st.download_button(
            "📄 Download TXT",
            data=st.session_state.current_report,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        # Copy to clipboard button
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            st.code(st.session_state.current_report, language=None)
            st.success("Content ready to copy!")
    
    with col4:
        # New research button
        if st.button("🔄 New Research", use_container_width=True):
            st.session_state.current_report = None
            st.session_state.current_sources = []
            st.rerun()
    
    # Tabs for report and sources
    tab1, tab2 = st.tabs(["📝 Research Report", "🔗 Sources"])
    
    with tab1:
        st.markdown(st.session_state.current_report)
    
    with tab2:
        if st.session_state.current_sources:
            st.subheader(f"📚 {len(st.session_state.current_sources)} Sources Analyzed")
            
            for idx, source in enumerate(st.session_state.current_sources, 1):
                score = source.get('score', 0)
                
                # Determine score class
                if score >= 0.75:
                    score_class = "score-high"
                    score_label = "High Quality"
                elif score >= 0.5:
                    score_class = "score-medium"
                    score_label = "Medium Quality"
                else:
                    score_class = "score-low"
                    score_label = "Low Quality"
                
                st.markdown(f"""
                <div class="source-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>Source {idx}</strong>
                        <span class="source-score {score_class}">{score_label} ({score:.2f})</span>
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <a href="{source.get('url', '#')}" target="_blank" style="color: #667eea; text-decoration: none;">
                            🔗 {source.get('url', 'No URL')}
                        </a>
                    </div>
                    <div style="margin-top: 0.5rem; color: #6c757d; font-size: 0.9rem;">
                        {source.get('content', 'No content preview')[:200]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No sources available")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 1rem;">
    <p>🧠 <strong>AutoResearcher AI</strong> • Powered by Gemini & Tavily • Built with LangGraph</p>
</div>
""", unsafe_allow_html=True)
