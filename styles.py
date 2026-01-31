import streamlit as st

# --- CUSTOM CSS ---
def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --bg-primary: #0a0f1a;
            --bg-secondary: #111827;
            --bg-card: #1a2332;
            --bg-card-hover: #1f2937;
            --border-color: #2d3748;
            --border-accent: #3b82f6;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --gradient-blue: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            --gradient-green: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 16px;
        }

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        code, .stCode, pre {
            font-family: 'JetBrains Mono', monospace !important;
        }

        .stApp { background: var(--bg-primary); }

        section[data-testid="stSidebar"] {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
        }

        h1, h2, h3, h4 {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }

        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: var(--gradient-blue);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }

        .section-header {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1rem 1.25rem;
            margin: 1.5rem 0 1rem 0;
        }

        .section-title {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }

        .section-desc {
            color: var(--text-secondary);
            font-size: 0.85rem;
            line-height: 1.5;
        }

        .section-location {
            color: var(--accent-blue);
            font-size: 0.75rem;
            margin-top: 0.5rem;
        }

        .technique-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            margin-bottom: 0.75rem;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .technique-card:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-accent);
            transform: translateY(-2px);
        }

        .technique-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: var(--gradient-blue);
            border-radius: 50%;
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
            margin-right: 0.75rem;
        }

        .technique-name {
            font-weight: 600;
            color: var(--text-primary);
        }

        .technique-description {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }

        .technique-benefit {
            display: inline-block;
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            font-size: 0.75rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            margin-top: 0.75rem;
        }

        .click-hint {
            color: var(--text-muted);
            font-size: 0.7rem;
            margin-top: 0.5rem;
        }

        .pro-item { color: var(--accent-green); }
        .con-item { color: var(--accent-rose); }

        .stChatMessage { background-color: transparent !important; border: none !important; }

        div[data-testid="stChatMessageContent"] {
            border-radius: var(--radius-md);
            padding: 1rem;
            color: var(--text-primary);
        }

        /* Targeted Card Styling using Key Class */
        div[class*="st-key-card"] button {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-primary) !important;
            
            /* FLEXBOX ALIGNMENT FIX */
            display: flex !important;
            flex-direction: row !important;
            align-items: flex-start !important;
            justify-content: flex-start !important;
            text-align: left !important;
            
            padding: 1.25rem !important;
            width: 100% !important;
            height: auto !important;
            min-height: 140px !important;
            white-space: pre-wrap !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
        }

        /* Target the internal container of the button to fix text alignment */
        div[class*="st-key-card"] button > div {
            flex-direction: column !important;
            align-items: flex-start !important;
        }

        div[class*="st-key-card"] button:hover {
            border-color: var(--border-accent) !important;
            transform: translateY(-2px);
            background: var(--bg-card-hover) !important;
            color: var(--accent-blue) !important;
        }

        div[class*="st-key-card"] button p {
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 400;
            margin-top: 4px; /* Space between title and description */
            line-height: 1.4;
        }

        .section-header-styled {
            background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
            border-left: 4px solid var(--accent-blue);
            padding: 1rem;
            margin: 1.5rem 0 1rem 0;
            border-radius: 0 8px 8px 0;
        }
        
        .section-title-styled {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }

        .section-desc-styled {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        </style>
    """, unsafe_allow_html=True)
