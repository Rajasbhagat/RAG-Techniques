import streamlit as st
import os

import time
from rag_engine import RAGEngine
from icons_config import TECHNIQUE_ICONS
from rag_config import SECTION_INFO, RAG_TECHNIQUES
from styles import load_css

# --- CONFIGURATION ---
st.set_page_config(
    page_title="RAG Learning Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTS ---
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# --- SECTION DESCRIPTIONS ---
# Imported from rag_config.py

# --- COMPREHENSIVE RAG TECHNIQUES DATA ---
# Imported from rag_config.py

# --- CUSTOM CSS ---
# Imported from styles.py

# --- HELPER FUNCTIONS ---
def render_section_header(section_key, category):
    """Render a styled section header."""
    info = SECTION_INFO[category][section_key]
    st.markdown(f"""
        <div class="section-header-styled">
            <div class="section-title-styled">{info['title']}</div>
            <div class="section-desc-styled">{info['description']}</div>
        </div>
    """, unsafe_allow_html=True)

def render_technique_button(technique, idx):
    """Render a clickable card using st.button."""
    icon = TECHNIQUE_ICONS.get(technique['id'], "🔧")
    
    # Use larger font for title, ensuring icon is prominent
    label = f"""### {icon} &nbsp; {idx}. {technique['name']}  \n\n{technique['description']}"""
    
    if st.button(label, key=f"card_{technique['id']}", type="secondary", use_container_width=True):
        show_technique_dialog(technique)

# --- DIALOG FOR TECHNIQUE DETAILS ---
@st.dialog("Technique Details", width="large")
def show_technique_dialog(technique):
    """Show detailed technique information in a dialog."""
    st.markdown(f"## #{technique['number']} {technique['name']}")
    st.markdown(technique['description'])

    st.divider()

    # Pros and Cons
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Pros**")
        for pro in technique.get('pros', []):
            st.markdown(f"<span style='color: #10b981;'>✓ {pro}</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("**Cons**")
        for con in technique.get('cons', []):
            st.markdown(f"<span style='color: #f43f5e;'>✗ {con}</span>", unsafe_allow_html=True)

    st.divider()

    # When to use
    st.markdown(f"**Best for:** {technique.get('when_to_use', 'General use')}")

    st.divider()

    # Code Example
    st.markdown("**Code Example**")
    st.code(technique.get('code', '# No code available'), language='python')

    # Flow Diagram
    st.markdown("**Flow Diagram (Mermaid)**")
    st.code(technique.get('diagram', 'No diagram'), language='mermaid')

# --- INITIALIZATION ---
if 'rag' not in st.session_state:
    st.session_state.rag = RAGEngine()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "learning_mode" not in st.session_state:
    st.session_state.learning_mode = True

if "last_response_chunks" not in st.session_state:
    st.session_state.last_response_chunks = []

# --- MAIN APP ---
def main():
    load_css()

    # --- Sidebar ---
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 2.5rem;">⚡</div>
                <div class="main-title" style="font-size: 1.5rem;">RAG Learning Hub</div>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">
                    Master 20+ RAG techniques
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.divider()

        # --- Model Management ---
        st.markdown("#### 🧠 AI Model Manager")

        model_options = st.session_state.rag.AVAILABLE_MODELS

        selected_model_id = st.radio(
            "Select Model",
            options=list(model_options.keys()),
            format_func=lambda x: f"{model_options[x]['icon']} {model_options[x]['name']}",
            key="model_selection_radio"
        )

        model_info = model_options[selected_model_id]

        st.markdown(f"""
        <div style="background: rgba(59, 130, 246, 0.1); border-radius: 8px; padding: 10px; margin-bottom: 10px; border: 1px solid rgba(59, 130, 246, 0.3);">
            <div style="font-weight: 600; color: #93c5fd; margin-bottom: 4px;">{model_info['role']}</div>
            <div style="font-size: 0.85em; margin-bottom: 4px;">✅ {model_info['pros']}</div>
            <div style="font-size: 0.85em; color: #fca5a5;">⚠ {model_info['cons']}</div>
        </div>
        """, unsafe_allow_html=True)

        col_start, col_stop = st.columns(2)

        current_running = st.session_state.rag.llm_model

        with col_start:
            start_disabled = (current_running == selected_model_id)
            if st.button("▶ Start", type="primary", use_container_width=True, disabled=start_disabled):
                with st.spinner(f"Starting {model_options[selected_model_id]['name']}..."):
                    st.session_state.rag.switch_model(selected_model_id)
                st.rerun()

        with col_stop:
            stop_disabled = (current_running is None)
            if st.button("⏹ Stop", type="secondary", use_container_width=True, disabled=stop_disabled):
                st.session_state.rag.unload_model()
                st.session_state.rag.llm_model = None
                st.rerun()

        if current_running:
            running_name = model_options.get(current_running, {}).get('name', current_running)
            st.success(f"Active: {running_name}")
        else:
            st.error("No Model Running")

        st.divider()

        # Learning Mode
        st.markdown("#### Settings")
        learning_mode = st.toggle("Learning Mode", value=st.session_state.learning_mode)
        st.session_state.learning_mode = learning_mode

        st.divider()

        # === INGESTION CONFIG ===
        st.markdown("#### 📥 Ingestion")

        with st.expander("Chunking Strategy", expanded=False):
            chunking_strategy = st.radio(
                "Method",
                ["Fixed", "Semantic", "Sentence Window", "Proposition"],
                help="How documents are split into chunks"
            )

            if chunking_strategy == "Fixed":
                chunk_size = st.slider("Chunk Size", 512, 2048, 1000, 128)
            elif chunking_strategy == "Sentence Window":
                window_size = st.slider("Window Size (sentences)", 3, 10, 5)
            else:
                chunk_size = 1000
                window_size = 5

        with st.expander("Enhancements", expanded=False):
            enrich_context = st.checkbox("Context Enrichment", help="Add AI summaries")
            add_headers = st.checkbox("Header Extraction", help="Preserve structure")
            augment_qa = st.checkbox("Q&A Augmentation", help="Generate Q&A pairs")

        st.divider()

        # === RETRIEVAL CONFIG ===
        st.markdown("#### 🔍 Retrieval")

        with st.expander("Query Strategy", expanded=True):
            query_strategy = st.radio(
                "Method",
                ["Direct", "Query Rewrite", "Multi-Query", "HyDE"],
                help="How your question is processed"
            )

        with st.expander("Post-Retrieval", expanded=False):
            enable_reranker = st.checkbox("Reranker", help="CrossEncoder re-scoring")
            enable_fusion = st.checkbox("Fusion (RRF)", help="Combine multiple result lists")
            compress_context = st.checkbox("Context Compression", help="Remove irrelevant parts")

        with st.expander("Advanced (Agentic)", expanded=False):
            enable_adaptive = st.checkbox("Adaptive RAG", help="Route by query complexity")
            enable_self_rag = st.checkbox("Self-RAG", help="LLM validates retrieval")
            enable_crag = st.checkbox("CRAG", help="Corrective RAG")
            use_sentence_window = st.checkbox("Sentence Window Retrieval", help="Use sentence index")

        st.divider()

        # Actions
        if st.session_state.messages:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        # Feedback Stats
        stats = st.session_state.rag.get_feedback_stats()
        if stats["total"] > 0:
            st.markdown("#### 📊 Feedback")
            st.markdown(f"Total: {stats['total']} | Avg: {stats['avg_rating']:.1f}")

    # --- Main Content ---
    st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h1 class="main-title">RAG Learning Hub</h1>
            <p class="subtitle">Explore 20+ RAG techniques through hands-on experimentation</p>
        </div>
    """, unsafe_allow_html=True)

    tab_learn, tab_chat, tab_manage = st.tabs(["📚 Learn RAG", "💬 Experiment", "📂 Knowledge Base"])

    # === TAB 1: LEARN RAG ===
    with tab_learn:
        st.markdown("### RAG Techniques Encyclopedia")
        st.markdown("Click any card to explore details.")

        col_ing, col_ret = st.columns(2)

        # === INGESTION COLUMN ===
        with col_ing:
            st.markdown("## 📥 Ingestion Techniques")
            
            # Counter for independent sequential numbering
            ingestion_counter = 1

            # Chunking Strategy Section
            render_section_header("chunking_strategy", "ingestion")
            for tech in RAG_TECHNIQUES["ingestion"]["chunking_strategy"]:
                render_technique_button(tech, ingestion_counter)
                ingestion_counter += 1

            # Enhancements Section
            render_section_header("enhancements", "ingestion")
            for tech in RAG_TECHNIQUES["ingestion"]["enhancements"]:
                render_technique_button(tech, ingestion_counter)
                ingestion_counter += 1

        # === RETRIEVAL COLUMN ===
        with col_ret:
            st.markdown("## 🔍 Retrieval Techniques")
            
            # Counter for independent sequential numbering
            retrieval_counter = 1

            # Query Strategy Section
            render_section_header("query_strategy", "retrieval")
            for tech in RAG_TECHNIQUES["retrieval"]["query_strategy"]:
                render_technique_button(tech, retrieval_counter)
                retrieval_counter += 1

            # Post-Retrieval Section
            render_section_header("post_retrieval", "retrieval")
            for tech in RAG_TECHNIQUES["retrieval"]["post_retrieval"]:
                render_technique_button(tech, retrieval_counter)
                retrieval_counter += 1

            # Agentic Section
            render_section_header("agentic", "retrieval")
            for tech in RAG_TECHNIQUES["retrieval"]["agentic"]:
                render_technique_button(tech, retrieval_counter)
                retrieval_counter += 1

    # === TAB 2: CHAT ===
    with tab_chat:
        # Context Selection
        col1, col2 = st.columns(2)
        subjects = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]

        with col1:
            active_subject = st.selectbox("Subject", ["All"] + subjects)
        with col2:
            cases = []
            if active_subject != "All":
                try:
                    cases = [c for c in os.listdir(os.path.join(DATA_DIR, active_subject)) if not c.startswith('.')]
                except:
                    pass
            active_case = st.selectbox("Document", ["All"] + cases)

        # Active Pipeline Display
        if learning_mode:
            with st.expander("📊 Active Pipeline", expanded=True):
                col_p1, col_p2 = st.columns(2)

                with col_p1:
                    st.markdown("**Ingestion**")
                    st.markdown(f"• Chunking: **{chunking_strategy}**")
                    if enrich_context: st.markdown("• Context Enrichment ✓")
                    if add_headers: st.markdown("• Header Extraction ✓")
                    if augment_qa: st.markdown("• Q&A Augmentation ✓")

                with col_p2:
                    st.markdown("**Retrieval**")
                    st.markdown(f"• Query: **{query_strategy}**")
                    if enable_reranker: st.markdown("• Reranker ✓")
                    if enable_fusion: st.markdown("• Fusion (RRF) ✓")
                    if compress_context: st.markdown("• Compression ✓")
                    if enable_adaptive: st.markdown("• Adaptive RAG ✓")
                    if enable_self_rag: st.markdown("• Self-RAG ✓")
                    if use_sentence_window: st.markdown("• Sentence Window ✓")

        st.divider()

        # Welcome State
        if not st.session_state.messages:
            st.markdown("""
                <div style='text-align: center; padding: 3rem; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px solid var(--border-color);'>
                    <div style='font-size: 3rem;'>🧪</div>
                    <h2>Ready to Experiment</h2>
                    <p style='color: var(--text-secondary);'>
                        Configure techniques in the sidebar, upload documents, then ask questions.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # Chat History
        for msg in st.session_state.messages:
            avatar = "👤" if msg["role"] == "user" else "🧠"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if "pipeline_info" in msg and learning_mode:
                    with st.expander("🔧 Pipeline Details", expanded=False):
                        st.markdown("**Steps Executed:**")
                        for step in msg.get("pipeline_info", {}).get("steps", []):
                            st.markdown(f"• {step}")
                        if msg.get("pipeline_info", {}).get("query_complexity"):
                            st.caption(f"Query Complexity: {msg['pipeline_info']['query_complexity'].upper()}")

        # Chat Input
        if prompt := st.chat_input("Ask a question about the case..."):
            if not st.session_state.rag.llm_model:
                st.error("⚠️ No AI Model is running! Please select and START a model from the Sidebar.")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)

                with st.chat_message("assistant", avatar="🧠"):
                    status = st.status("🧠 Processing...", expanded=True)
                    response_area = st.empty()

                    # Build configs
                    chunk_strat_map = {
                        "Fixed": "fixed", "Semantic": "semantic",
                        "Sentence Window": "sentence_window", "Proposition": "proposition"
                    }
                    query_strat_map = {
                        "Direct": "direct", "Query Rewrite": "query_rewrite",
                        "Multi-Query": "multi_query", "HyDE": "hyde"
                    }

                    retrieval_config = {
                        "query_strategy": query_strat_map.get(query_strategy, "direct"),
                        "enable_reranker": enable_reranker,
                        "enable_fusion": enable_fusion,
                        "compress_context": compress_context,
                        "enable_adaptive": enable_adaptive,
                        "enable_self_rag": enable_self_rag,
                        "context_logic": "sentence_window" if use_sentence_window else "standard",
                        "n_results": 3,
                    }

                    try:
                        subj_filter = active_subject if active_subject != "All" else None
                        case_filter = active_case if active_case != "All" else None

                        stream, chunks, pipeline_info = st.session_state.rag.query(
                            prompt, subj_filter, case_filter,
                            retrieval_config=retrieval_config
                        )

                        # Show pipeline steps
                        if learning_mode and pipeline_info.get("steps"):
                            status.markdown("**Pipeline:**\n" + "\n".join(f"• {s}" for s in pipeline_info["steps"]))

                        full_response = ""
                        thought_buffer = ""
                        is_thinking = False

                        for chunk in stream:
                            content = chunk['message']['content']

                            if "<think>" in content:
                                is_thinking = True
                                content = content.replace("<think>", "")
                            if "</think>" in content:
                                is_thinking = False
                                content = content.replace("</think>", "")
                                status.update(label="✅ Complete", state="complete", expanded=False)

                            if is_thinking:
                                thought_buffer += content
                                status.markdown(thought_buffer[:500] + "...")
                            else:
                                full_response += content
                                response_area.markdown(full_response + "▌")

                        response_area.markdown(full_response)
                        st.session_state.last_response_chunks = chunks

                        # Sources
                        if chunks:
                            with st.expander(f"📚 Sources ({len(chunks)})"):
                                for i, c in enumerate(chunks):
                                    st.code(c[:300] + "...", language=None)

                        # Feedback UI
                        st.markdown("**Was this helpful?**")
                        col_fb1, col_fb2, col_fb3 = st.columns([1, 1, 4])
                        with col_fb1:
                            if st.button("👍", key="fb_up"):
                                st.session_state.rag.record_feedback(prompt, full_response, chunks, 5)
                                st.toast("Thanks for the feedback!")
                        with col_fb2:
                            if st.button("👎", key="fb_down"):
                                st.session_state.rag.record_feedback(prompt, full_response, chunks, 1)
                                st.toast("Feedback recorded")

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response,
                            "pipeline_info": pipeline_info
                        })

                    except Exception as e:
                        st.error(f"Error: {e}")
                        status.update(label="❌ Error", state="error")

    # === TAB 3: MANAGE ===
    with tab_manage:
        st.markdown("### Knowledge Base")

        col_create, col_upload = st.columns(2)

        with col_create:
            st.markdown("**Create Subject**")
            new_subject = st.text_input("Name", placeholder="e.g. Finance")
            if st.button("Create", use_container_width=True):
                if new_subject:
                    path = os.path.join(DATA_DIR, new_subject)
                    if not os.path.exists(path):
                        os.makedirs(path)
                        st.toast(f"✅ Created '{new_subject}'")
                        st.rerun()

        with col_upload:
            st.markdown("**Upload Documents**")
            current_subjects = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]

            if current_subjects:
                target_sub = st.selectbox("Target Subject", current_subjects)

                if learning_mode:
                    st.info(f"Will use: **{chunking_strategy}** chunking")

                files = st.file_uploader("Files", type=['pdf', 'txt', 'md'], accept_multiple_files=True)

                if files and st.button(f"Process {len(files)} Files", use_container_width=True):
                    progress = st.progress(0)

                    chunk_strat_map = {
                        "Fixed": "fixed", "Semantic": "semantic",
                        "Sentence Window": "sentence_window", "Proposition": "proposition"
                    }

                    ingestion_config = {
                        "chunking_strategy": chunk_strat_map.get(chunking_strategy, "fixed"),
                        "chunk_size": chunk_size if 'chunk_size' in dir() else 1000,
                        "sentence_window_size": window_size if 'window_size' in dir() else 5,
                        "enrich_context": enrich_context,
                        "add_headers": add_headers,
                        "augment_qa": augment_qa,
                        "overlap": 200,
                    }

                    for i, f in enumerate(files):
                        save_path = os.path.join(DATA_DIR, target_sub, f.name)
                        with open(save_path, "wb") as fp:
                            fp.write(f.getbuffer())
                        st.session_state.rag.ingest_file(save_path, target_sub, config=ingestion_config)
                        progress.progress((i + 1) / len(files))

                    st.toast("🚀 Complete!")
                    st.rerun()
            else:
                st.info("Create a subject first.")

        # Stats
        st.divider()
        stats = st.session_state.rag.get_technique_stats()
        st.markdown(f"**Database Stats:** {stats['main_chunks']} chunks | {stats['sentence_chunks']} sentences")

if __name__ == "__main__":
    main()
