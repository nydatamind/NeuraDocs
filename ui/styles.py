"""
NeuraDocs - Premium CSS Cyber-Hacker Design System & Theme Styles
=================================================================
High-end Dark and Light glassmorphic styles, terminal aesthetics,
neon green/cyan accents, and custom styling for action elements.
"""

def get_css_styles(theme: str = "dark") -> str:
    is_dark = theme == "dark"

    if is_dark:
        bg_0 = "#030508"
        bg_1 = "#080c14"
        bg_2 = "#0e1522"
        panel_bg = "rgba(10, 16, 28, 0.8)"
        panel_border = "rgba(0, 255, 200, 0.15)"
        text_hi = "#e0f2f1"
        text_mid = "#80cbd6"
        text_lo = "#4f7a82"
        card_bg = "rgba(0, 255, 136, 0.03)"
        sidebar_grad = "linear-gradient(180deg, #04080f 0%, #020407 100%)"
        chat_user_bg = "linear-gradient(135deg, rgba(0, 255, 200, 0.15), rgba(0, 150, 255, 0.1))"
        chat_asst_bg = "rgba(10, 20, 30, 0.5)"
        gradient_glow = """
            radial-gradient(circle at 10% 0%, rgba(0, 255, 136, 0.12), transparent 40%),
            radial-gradient(circle at 90% 10%, rgba(0, 229, 255, 0.1), transparent 35%),
            #030508
        """
        accent_1 = "#00ff88"
        accent_2 = "#00e5ff"
        accent_glow = "rgba(0, 255, 136, 0.3)"
    else:
        bg_0 = "#f5f9f9"
        bg_1 = "#ffffff"
        bg_2 = "#e0f2f1"
        panel_bg = "rgba(240, 250, 248, 0.9)"
        panel_border = "rgba(0, 150, 136, 0.2)"
        text_hi = "#00332c"
        text_mid = "#006d60"
        text_lo = "#52857f"
        card_bg = "rgba(0, 150, 136, 0.04)"
        sidebar_grad = "linear-gradient(180deg, #ffffff 0%, #e0f2f1 100%)"
        chat_user_bg = "linear-gradient(135deg, rgba(0, 150, 136, 0.1), rgba(0, 188, 212, 0.08))"
        chat_asst_bg = "#ffffff"
        gradient_glow = """
            radial-gradient(circle at 10% 0%, rgba(0, 150, 136, 0.06), transparent 45%),
            #f5f9f9
        """
        accent_1 = "#00897b"
        accent_2 = "#00acc1"
        accent_glow = "rgba(0, 137, 123, 0.15)"

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

:root {{
    --bg-0: {bg_0};
    --bg-1: {bg_1};
    --bg-2: {bg_2};
    --panel: {panel_bg};
    --panel-border: {panel_border};
    --text-hi: {text_hi};
    --text-mid: {text_mid};
    --text-lo: {text_lo};
    --card-bg: {card_bg};
    --accent-1: {accent_1};
    --accent-2: {accent_2};
    --accent-glow: {accent_glow};
}}

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: var(--text-hi);
}}

.stApp {{
    background: {gradient_glow};
    color: var(--text-hi);
}}

/* Scanline / Terminal Background Effect */
.stApp::before {{
    content: " ";
    display: block;
    position: fixed;
    top: 0; left: 0; bottom: 0; right: 0;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
    z-index: 999999;
    background-size: 100% 3px, 6px 100%;
    pointer-events: none;
}}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {{
    width: 320px !important;
}}

section[data-testid="stSidebar"] > div {{
    background: {sidebar_grad} !important;
    border-right: 1px solid var(--panel-border) !important;
    padding-top: 1rem;
}}

/* Nitin Yadav Futuristic Glow Header Styling */
.neura-brand-container {{
    text-align: center;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--panel-border);
    box-shadow: 0 0 15px var(--accent-glow);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
    backdrop-filter: blur(10px);
}}

.neura-brand {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: 2px;
    background: linear-gradient(90deg, #00ff88 0%, #00e5ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    margin: 0;
    line-height: 1.1;
}}

.neura-subhead {{
    font-family: 'Share Tech Mono', monospace;
    color: var(--text-mid);
    font-size: 0.95rem;
    letter-spacing: 1px;
    margin-top: 5px;
    text-transform: uppercase;
}}

.dev-by {{
    font-size: 0.75rem;
    color: var(--text-lo);
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-top: 15px;
}}

.dev-name {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
    background: linear-gradient(135deg, #00ff88, #00e5ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 10px rgba(0, 255, 200, 0.8);
    display: inline-block;
    padding: 2px 10px;
    border: 1px solid var(--panel-border);
    border-radius: 4px;
    margin-top: 5px;
}}

/* Glass Panels */
.glass-panel {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 0 10px rgba(0, 255, 200, 0.05);
    margin-bottom: 1.5rem;
}}

.stat-box {{
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    transition: all 0.3s ease;
}}
.stat-box:hover {{
    border-color: var(--accent-1);
    box-shadow: 0 0 10px var(--accent-glow);
    transform: translateY(-2px);
}}
.stat-number {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.3rem;
    color: var(--accent-2);
    font-weight: 700;
}}
.stat-label {{
    font-size: 0.7rem;
    color: var(--text-lo);
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* Action Buttons & Custom Controls */
.stButton > button {{
    background: linear-gradient(135deg, #00897b, #00acc1) !important;
    color: #ffffff !important;
    border: 1px solid var(--panel-border) !important;
    border-radius: 8px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 10px rgba(0, 255, 136, 0.15) !important;
}}
.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px var(--accent-glow) !important;
    filter: brightness(1.2) !important;
    border-color: var(--accent-1) !important;
}}

/* Tabular & Document Cards */
.src-card {{
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--panel-border);
    border-left: 4px solid var(--accent-1);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    font-family: 'Inter', sans-serif;
}}
.src-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'Share Tech Mono', monospace;
    color: var(--text-hi);
    border-bottom: 1px solid rgba(0, 255, 136, 0.1);
    padding-bottom: 6px;
    margin-bottom: 8px;
}}
.src-preview {{
    color: var(--text-mid);
    font-size: 0.85rem;
    white-space: pre-wrap;
}}

/* Custom Scrollbars */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: transparent;
}}
::-webkit-scrollbar-thumb {{
    background: var(--panel-border);
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: var(--accent-1);
    box-shadow: 0 0 8px var(--accent-glow);
}}

#MainMenu, footer {{ visibility: hidden; }}

/* ChatGPT layout elements */
.custom-chat-input-container {{
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(10, 20, 30, 0.85);
    border: 1px solid var(--panel-border);
    border-radius: 24px;
    padding: 6px 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}}

.action-bar-btn {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.2);
    color: var(--text-mid);
    border-radius: 6px;
    padding: 4px 8px;
    margin-right: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}
.action-bar-btn:hover {{
    background: rgba(0, 255, 136, 0.15);
    border-color: var(--accent-1);
    color: #ffffff;
    box-shadow: 0 0 5px var(--accent-glow);
}}

.attachment-badge {{
    background: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.3);
    color: #00e5ff;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 4px;
}}
</style>
"""
