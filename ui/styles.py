"""
NeuraDocs - Complete CSS Design System & Theme Styles
=====================================================
High-end Dark and Light glassmorphic styles, modern typography,
responsive layout, custom scrollbars, chat bubble cards, and micro-interactions.
"""


def get_css_styles(theme: str = "dark") -> str:
    is_dark = theme == "dark"

    if is_dark:
        bg_0 = "#05060a"
        bg_1 = "#0c0e18"
        bg_2 = "#141726"
        panel_bg = "rgba(20, 24, 40, 0.65)"
        panel_border = "rgba(255, 255, 255, 0.08)"
        text_hi = "#f4f6fb"
        text_mid = "#b0b6cf"
        text_lo = "#6d7594"
        card_bg = "rgba(255, 255, 255, 0.03)"
        sidebar_grad = "linear-gradient(180deg, #090a12 0%, #05060a 100%)"
        chat_user_bg = "linear-gradient(135deg, rgba(124, 92, 255, 0.22), rgba(53, 213, 255, 0.12))"
        chat_asst_bg = "rgba(255, 255, 255, 0.035)"
        gradient_glow = """
            radial-gradient(circle at 12% 0%, rgba(124, 92, 255, 0.18), transparent 45%),
            radial-gradient(circle at 88% 12%, rgba(53, 213, 255, 0.14), transparent 40%),
            radial-gradient(circle at 50% 100%, rgba(255, 92, 173, 0.08), transparent 50%),
            #05060a
        """
    else:
        bg_0 = "#f8f9fd"
        bg_1 = "#ffffff"
        bg_2 = "#eef1f8"
        panel_bg = "rgba(255, 255, 255, 0.85)"
        panel_border = "rgba(0, 0, 0, 0.08)"
        text_hi = "#0f1423"
        text_mid = "#3f4660"
        text_lo = "#75809e"
        card_bg = "rgba(0, 0, 0, 0.02)"
        sidebar_grad = "linear-gradient(180deg, #ffffff 0%, #f3f5fc 100%)"
        chat_user_bg = "linear-gradient(135deg, rgba(124, 92, 255, 0.12), rgba(53, 213, 255, 0.08))"
        chat_asst_bg = "#ffffff"
        gradient_glow = """
            radial-gradient(circle at 10% 0%, rgba(124, 92, 255, 0.07), transparent 45%),
            radial-gradient(circle at 90% 10%, rgba(53, 213, 255, 0.06), transparent 40%),
            #f8f9fd
        """

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

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
    --accent-1: #7c5cff;
    --accent-2: #35d5ff;
    --accent-3: #ff5cad;
    --accent-glow: rgba(124, 92, 255, 0.35);
}}

/* Universal Typography */
html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-hi);
}}

.stApp {{
    background: {gradient_glow};
    color: var(--text-hi);
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

/* Main Title Gradient — animated color-shift */
.neura-brand {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.3rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #8b6aff, #38d6ff, #ff62b0, #ffaa44, #38d6ff, #8b6aff);
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.2rem;
    animation: neuraColorCycle 5s ease infinite;
}}

/* Sidebar smaller version of same animated logo */
.neura-sidebar-brand {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.3rem;
    line-height: 1.1;
    background: linear-gradient(90deg, #8b6aff, #38d6ff, #ff62b0, #ffaa44, #38d6ff, #8b6aff);
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: neuraColorCycle 5s ease infinite;
    display: inline-block;
}}

@keyframes neuraColorCycle {{
    0%   {{ background-position: 0% 50%; }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

/* Developer Badge — premium pill */
.dev-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 14px;
    border-radius: 999px;
    border: 1px solid rgba(124, 92, 255, 0.45);
    background: linear-gradient(135deg, rgba(124,92,255,0.10), rgba(53,213,255,0.07));
    backdrop-filter: blur(8px);
    font-size: 0.78rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
    color: var(--text-mid);
    box-shadow: 0 0 12px rgba(124,92,255,0.18), inset 0 0 8px rgba(53,213,255,0.06);
    animation: devBadgeGlow 3s ease-in-out infinite alternate;
}}
.dev-badge .dev-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c5cff, #35d5ff);
    animation: devDotPulse 2s ease-in-out infinite;
    flex-shrink: 0;
}}
.dev-badge b {{
    background: linear-gradient(90deg, #a07cff, #35d5ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
}}
@keyframes devBadgeGlow {{
    from {{ box-shadow: 0 0 8px rgba(124,92,255,0.15), inset 0 0 6px rgba(53,213,255,0.04); border-color: rgba(124,92,255,0.35); }}
    to   {{ box-shadow: 0 0 18px rgba(53,213,255,0.25), inset 0 0 10px rgba(124,92,255,0.08); border-color: rgba(53,213,255,0.55); }}
}}
@keyframes devDotPulse {{
    0%, 100% {{ opacity:1; transform:scale(1); }}
    50%       {{ opacity:0.5; transform:scale(0.7); }}
}}

.neura-subhead {{
    color: var(--text-mid);
    font-size: 0.95rem;
    margin-bottom: 1.2rem;
}}

/* Glass Cards & Containers */
.glass-panel {{
    background: var(--panel);
    border: 1px solid var(--panel-border);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    margin-bottom: 1rem;
}}

.stat-box {{
    background: var(--card-bg);
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    padding: 12px 14px;
    text-align: center;
    transition: transform 0.2s ease, border-color 0.2s ease;
}}
.stat-box:hover {{
    transform: translateY(-2px);
    border-color: var(--accent-1);
}}
.stat-number {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent-2);
}}
.stat-label {{
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-lo);
    font-weight: 600;
}}

/* Status Badge Pills */
.pill-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 600;
    border: 1px solid var(--panel-border);
}}
.pill-success {{
    background: rgba(46, 213, 115, 0.12);
    color: #2ed573;
    border-color: rgba(46, 213, 115, 0.3);
}}
.pill-info {{
    background: rgba(53, 213, 255, 0.12);
    color: #35d5ff;
    border-color: rgba(53, 213, 255, 0.3);
}}
.pill-warning {{
    background: rgba(255, 171, 0, 0.12);
    color: #ffab00;
    border-color: rgba(255, 171, 0, 0.3);
}}
.pill-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    animation: pulseBadge 1.8s infinite;
}}
@keyframes pulseBadge {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.4; transform: scale(0.8); }}
}}

/* Action Buttons */
.stButton > button {{
    background: linear-gradient(135deg, #7c5cff, #a05cff);
    color: white !important;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.88rem;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease;
    box-shadow: 0 4px 14px var(--accent-glow);
}}
.stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(124, 92, 255, 0.5);
    filter: brightness(1.1);
}}
.stButton > button:active {{
    transform: translateY(0);
}}

/* Secondary / Ghost button */
button[kind="secondary"] {{
    background: var(--card-bg) !important;
    border: 1px solid var(--panel-border) !important;
    color: var(--text-hi) !important;
    box-shadow: none !important;
}}
button[kind="secondary"]:hover {{
    background: rgba(124, 92, 255, 0.15) !important;
    border-color: var(--accent-1) !important;
    color: var(--text-hi) !important;
}}

/* Chat Messages */
div[data-testid="stChatMessage"] {{
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 10px;
    border: 1px solid var(--panel-border);
    animation: fadeInSlide 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}}

@keyframes fadeInSlide {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* Citation Source Cards */
.src-card {{
    background: var(--card-bg);
    border: 1px solid var(--panel-border);
    border-left: 3px solid var(--accent-2);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.85rem;
    line-height: 1.45;
}}
.src-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    color: var(--text-hi);
    margin-bottom: 4px;
}}
.src-preview {{
    color: var(--text-mid);
    font-size: 0.82rem;
}}

/* Prompt Chips */
.chip-btn {{
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    background: var(--card-bg);
    border: 1px solid var(--panel-border);
    color: var(--text-mid);
    font-size: 0.84rem;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-right: 8px;
    margin-bottom: 8px;
}}
.chip-btn:hover {{
    background: rgba(124, 92, 255, 0.16);
    border-color: var(--accent-1);
    color: var(--text-hi);
    transform: translateY(-1px);
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
}}

/* Voice Button iframe transparency */
iframe[title="streamlit_component"] {{
    background: transparent !important;
    border: none !important;
}}

/* AI Animation label */
#neura-anim-label {{
    animation: labelFade 1.4s infinite alternate;
}}
@keyframes labelFade {{
    from {{ opacity: 0.6; }}
    to   {{ opacity: 1.0; }}
}}

/* Hide Streamlit branding */
#MainMenu, footer {{ visibility: hidden; }}
</style>
"""
