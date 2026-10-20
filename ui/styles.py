"""Nocturne Gastronomy Concierge Design System for Zomato AI Dining Concierge.

Based on stitch_zomato_ai_dining_concierge specifications:
- Palette: Pitch Black Canvas (#0A0C10), Midnight Base (#12151C), Elevated Glass (#181C26)
- Brand Accent: Electric Crimson (#FF385C / #E23744) with crimson glow
- AI Accent: Violet/Indigo gradient (#1E1630 to #141122), AI Purple (#8B5CF6)
- Metrics: Gastronomy Emerald (#10B981), Cellar Amber (#F59E0B)
- Typography: Plus Jakarta Sans for Display/Labels, Inter for Body
- Icons: Google Material Symbols Outlined
"""

NOCTURNE_DARK_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">

<style>
/* ==========================================================================
   1. CSS RESET, DESIGN TOKENS & ROOT THEME
   ========================================================================== */
:root {
    --canvas-black: #0A0C10;
    --surface-lowest: #0C0E12;
    --surface-midnight: #12151C;
    --surface-elevated: #181C26;
    --surface-container-high: #242938;
    --surface-border-subdued: rgba(255, 255, 255, 0.08);
    --surface-border-highlight: rgba(255, 255, 255, 0.16);

    --crimson-core: #FF385C;
    --crimson-deep: #E23744;
    --crimson-glow: rgba(255, 56, 92, 0.35);

    --ai-purple: #8B5CF6;
    --ai-purple-light: #D0BCFF;
    --ai-purple-glow: rgba(139, 92, 246, 0.35);
    --ai-card-grad-start: #1E1630;
    --ai-card-grad-end: #141122;

    --emerald-green: #10B981;
    --emerald-border: rgba(16, 185, 129, 0.35);
    --amber-cellar: #F59E0B;
    --amber-border: rgba(245, 158, 11, 0.35);

    --text-high-contrast: #F9FAFB;
    --text-on-surface: #E2E2E8;
    --text-muted: #9CA3AF;
    --text-ghost: #4B5563;

    color-scheme: dark;
}

/* Material Symbols configuration */
.material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    display: inline-block;
    vertical-align: middle;
    line-height: 1;
}

/* Global Font & Theme */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--canvas-black) !important;
    color: var(--text-on-surface) !important;
}

/* App Viewport Container */
.stApp {
    background: radial-gradient(circle at 20% -10%, rgba(87, 27, 193, 0.15) 0%, transparent 45%),
                radial-gradient(circle at 85% 30%, rgba(226, 55, 68, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 10% 70%, rgba(87, 27, 193, 0.08) 0%, transparent 35%),
                #0A0C10 !important;
    min-height: 100vh;
}

.main .block-container {
    max-width: 1560px !important;
    padding-top: 1.25rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* Hide default Streamlit decoration header & deploy button */
header[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: blur(12px) !important;
}
#MainMenu, footer, header[data-testid="stHeader"] > div:first-child {
    visibility: visible;
}

/* ==========================================================================
   2. TOP NAVIGATION HEADER
   ========================================================================== */
.nocturne-navbar {
    width: 100%;
    background: rgba(12, 14, 18, 0.88);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 12px 24px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 12px 36px -10px rgba(0, 0, 0, 0.7);
}

.navbar-brand-group {
    display: flex;
    align-items: center;
    gap: 14px;
}

.brand-icon-box {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #FF385C 0%, #E23744 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px -2px rgba(255, 56, 92, 0.5);
    color: white;
}

.brand-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text-high-contrast);
    display: flex;
    align-items: center;
    gap: 8px;
}

.brand-title span.zomato-red {
    color: #FF385C;
}

.edition-pill {
    padding: 3px 10px;
    border-radius: 9999px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(87, 27, 193, 0.35);
    color: #D0BCFF;
    border: 1px solid rgba(208, 188, 255, 0.3);
}

.navbar-status-group {
    display: flex;
    align-items: center;
    gap: 12px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 9999px;
    background: #181C26;
    border: 1px solid rgba(255, 255, 255, 0.08);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-on-surface);
}

.status-indicator-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--emerald-green);
    box-shadow: 0 0 10px var(--emerald-green);
    position: relative;
}

.status-indicator-dot::after {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 50%;
    border: 1px solid var(--emerald-green);
    animation: pulse 2s infinite ease-out;
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 0.8; }
    100% { transform: scale(2.2); opacity: 0; }
}

.maitre-d-badge {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.maitre-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 2px solid rgba(255, 56, 92, 0.5);
    background: #1E2024;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

.maitre-tag {
    position: absolute;
    bottom: -4px;
    right: -4px;
    background: #D0BCFF;
    color: #23005C;
    font-size: 9px;
    font-weight: 800;
    padding: 1px 4px;
    border-radius: 9999px;
    border: 1px solid #0A0C10;
}

/* ==========================================================================
   3. QUICK-VIBE PILLS SECTION
   ========================================================================== */
.vibe-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.vibe-header-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--text-high-contrast);
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Style for Streamlit buttons rendered as vibe pills */
div[data-testid="column"] > div > div > div > button.vibe-pill-btn,
.vibe-grid button {
    background: #161A23 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 9999px !important;
    color: var(--text-on-surface) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    white-space: nowrap !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}

.vibe-grid button:hover {
    border-color: rgba(255, 56, 92, 0.5) !important;
    background: #1E2230 !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 16px -2px rgba(255, 56, 92, 0.3) !important;
    transform: translateY(-1px);
}

/* ==========================================================================
   4. LEFT FILTER PANEL & FORM CONTROLS
   ========================================================================== */
.nocturne-filter-panel {
    background: rgba(18, 21, 28, 0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.7);
    margin-bottom: 24px;
}

.filter-panel-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text-high-contrast);
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 18px;
}

/* Streamlit Inputs Styling (Dark Obsidian Luxury) */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background-color: #0E1117 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    color: var(--text-on-surface) !important;
    font-size: 14px !important;
}

.stSelectbox > div > div:hover,
.stMultiSelect > div > div:hover {
    border-color: rgba(139, 92, 246, 0.5) !important;
}

.stSelectbox > div > div:focus-within,
.stMultiSelect > div > div:focus-within {
    border-color: var(--ai-purple) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25) !important;
}

/* MultiSelect chips */
span[data-baseweb="tag"] {
    background: rgba(87, 27, 193, 0.4) !important;
    border: 1px solid rgba(208, 188, 255, 0.35) !important;
    border-radius: 9999px !important;
    color: #D0BCFF !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}

/* Textarea input */
.stTextArea textarea {
    background-color: #0E1117 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    color: var(--text-on-surface) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 12px 14px !important;
}

.stTextArea textarea:focus {
    border-color: var(--ai-purple) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25) !important;
}

/* Slider */
.stSlider [data-baseweb="slider"] {
    accent-color: #FF385C !important;
}

/* Radio buttons (Segmented Budget) */
div[data-testid="stRadio"] > div {
    background-color: #0C0E12 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 6px !important;
}

div[data-testid="stRadio"] label {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px !important;
    color: var(--text-muted) !important;
}

div[data-testid="stRadio"] label:hover {
    color: var(--text-high-contrast) !important;
}

/* Primary Search CTA Button */
div[data-testid="stButton"] > button[kind="primary"],
.primary-search-btn button {
    width: 100% !important;
    background: linear-gradient(135deg, #FF385C 0%, #E23744 100%) !important;
    color: #FFFFFF !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 14px 20px !important;
    box-shadow: 0 6px 25px -4px rgba(255, 56, 92, 0.45) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    letter-spacing: 0.01em !important;
}

div[data-testid="stButton"] > button[kind="primary"]:hover,
.primary-search-btn button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(255, 56, 92, 0.6) !important;
    filter: brightness(1.08) !important;
}

/* ==========================================================================
   5. RIGHT CANVAS: 4-METRIC SUMMARY BAR
   ========================================================================== */
.nocturne-metrics-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    background: rgba(18, 21, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 20px;
    backdrop-filter: blur(16px);
}

@media (max-width: 768px) {
    .nocturne-metrics-bar {
        grid-template-columns: repeat(2, 1fr);
    }
}

.metric-cell {
    background: rgba(12, 14, 18, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 10px 14px;
}

.metric-label {
    display: block;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
}

.metric-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.01em;
    color: var(--text-high-contrast);
}

.metric-value.emerald {
    color: var(--emerald-green);
}

.metric-value.purple {
    color: var(--ai-purple-light);
}

/* ==========================================================================
   6. AI CONCIERGE OVERVIEW CARD (CHEF D'HÔTEL SYNTHESIS)
   ========================================================================== */
.ai-lens-card {
    background: linear-gradient(135deg, rgba(30, 22, 48, 0.92) 0%, rgba(20, 17, 34, 0.96) 100%);
    border: 1px solid rgba(139, 92, 246, 0.35);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 24px;
    box-shadow: inset 0 1px 1px 0 rgba(139, 92, 246, 0.35), 0 12px 30px -10px rgba(0, 0, 0, 0.5);
    position: relative;
    overflow: hidden;
}

.ai-lens-card::before {
    content: '';
    position: absolute;
    bottom: -30px;
    right: -30px;
    width: 140px;
    height: 140px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.25) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.ai-lens-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.ai-lens-title-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.ai-lens-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: rgba(139, 92, 246, 0.3);
    border: 1px solid rgba(139, 92, 246, 0.5);
    color: #D0BCFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
}

.ai-lens-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: #D0BCFF;
    text-transform: uppercase;
}

.ai-confidence-pill {
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    background: rgba(87, 27, 193, 0.5);
    color: #E9DDFF;
    border: 1px solid rgba(208, 188, 255, 0.3);
}

.ai-lens-body {
    font-family: 'Inter', sans-serif;
    font-size: 14.5px;
    line-height: 1.6;
    color: #F1F1F5;
    margin: 0;
}

/* ==========================================================================
   7. LUXURY RESTAURANT RECOMMENDATION CARDS
   ========================================================================== */
.nocturne-restaurant-card {
    background: #141720;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    margin-bottom: 24px;
    overflow: hidden;
    box-shadow: 0 12px 32px -8px rgba(0, 0, 0, 0.6);
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                border-color 0.25s ease,
                box-shadow 0.25s ease;
    display: grid;
    grid-template-columns: 380px 1fr;
}

@media (max-width: 992px) {
    .nocturne-restaurant-card {
        grid-template-columns: 1fr;
    }
}

.nocturne-restaurant-card:hover {
    transform: translateY(-3px);
    border-color: rgba(255, 56, 92, 0.4);
    box-shadow: 0 16px 40px -8px rgba(0, 0, 0, 0.8), 0 0 24px -6px rgba(255, 56, 92, 0.15);
}

/* Card Visual Column */
.card-media-box {
    position: relative;
    height: 100%;
    min-height: 250px;
    overflow: hidden;
    background: #0C0E12;
}

.card-media-box img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.nocturne-restaurant-card:hover .card-media-box img {
    transform: scale(1.05);
}

.card-media-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.3) 0%, transparent 40%, rgba(20, 23, 32, 0.95) 100%);
    pointer-events: none;
}

.card-media-badges {
    position: absolute;
    top: 14px;
    left: 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    align-items: flex-start;
    z-index: 2;
}

.rank-pill {
    padding: 5px 12px;
    border-radius: 9999px;
    background: linear-gradient(135deg, #FF385C 0%, #E23744 100%);
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.04em;
    box-shadow: 0 4px 12px rgba(226, 55, 68, 0.4);
}

.feature-pill {
    padding: 4px 10px;
    border-radius: 9999px;
    background: rgba(12, 14, 18, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #D0BCFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 600;
}

/* Card Content Column */
.card-content-box {
    padding: 22px 26px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 12px;
}

.restaurant-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--text-high-contrast);
    margin: 0 0 6px 0;
    line-height: 1.25;
}

.restaurant-locality {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 5px;
}

.locality-pin {
    color: #FF385C;
    font-size: 15px;
}

/* Rating Badge */
.emerald-rating-box {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    flex-shrink: 0;
}

.emerald-rating-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 5px 12px;
    border-radius: 8px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: var(--emerald-green);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px;
    font-weight: 800;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
}

.reviews-subtext {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
}

/* Meta strip */
.card-meta-strip {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 14px;
    padding: 10px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    margin-bottom: 14px;
    font-size: 13px;
}

.cost-tag {
    color: var(--amber-cellar);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.service-pill-dark {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 9999px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.service-pill-active {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #4EDEA3;
}

.service-pill-muted {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-ghost);
}

/* Cuisine chips */
.cuisine-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 16px;
}

.nocturne-cuisine-chip {
    padding: 3px 10px;
    border-radius: 9999px;
    background: #1E222E;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #C5CAD6;
    font-size: 11.5px;
    font-weight: 500;
}

/* Purple AI Concierge Note */
.ai-concierge-card-note {
    background: linear-gradient(135deg, rgba(30, 22, 48, 0.8) 0%, rgba(20, 17, 34, 0.85) 100%);
    border-left: 4px solid var(--ai-purple);
    border-radius: 0 10px 10px 0;
    border-top: 1px solid rgba(139, 92, 246, 0.15);
    border-right: 1px solid rgba(139, 92, 246, 0.15);
    border-bottom: 1px solid rgba(139, 92, 246, 0.15);
    padding: 12px 16px;
    margin-bottom: 18px;
}

.ai-concierge-note-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: #D0BCFF;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 4px;
}

.ai-concierge-note-text {
    font-family: 'Inter', sans-serif;
    font-size: 13.5px;
    line-height: 1.55;
    color: #DFE2EA;
    margin: 0;
}

/* Action buttons row */
.card-actions-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.btn-book-table {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 20px;
    border-radius: 9999px;
    background: linear-gradient(135deg, #FF385C 0%, #E23744 100%);
    color: #FFFFFF !important;
    text-decoration: none;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 700;
    box-shadow: 0 4px 14px rgba(226, 55, 68, 0.35);
    transition: all 0.2s ease;
}

.btn-book-table:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(226, 55, 68, 0.5);
    filter: brightness(1.1);
}

.btn-view-menu {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 18px;
    border-radius: 9999px;
    background: #1C202C;
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: var(--text-on-surface) !important;
    text-decoration: none;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    transition: all 0.2s ease;
}

.btn-view-menu:hover {
    background: #252B3C;
    border-color: rgba(255, 255, 255, 0.25);
    color: #FFFFFF !important;
}

/* ==========================================================================
   8. STATUS BANNERS & EMPTY STATES
   ========================================================================== */
.nocturne-banner {
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13.5px;
    font-weight: 500;
    line-height: 1.5;
}

.nocturne-banner.fallback {
    background: rgba(120, 53, 15, 0.2);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #FDE68A;
}

.nocturne-banner.relaxation {
    background: rgba(8, 51, 68, 0.25);
    border: 1px solid rgba(6, 182, 212, 0.35);
    color: #A5F3FC;
}

.nocturne-empty-card {
    background: #12151C;
    border: 2px dashed rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 48px 24px;
    text-align: center;
    margin: 24px 0;
}

.nocturne-empty-icon {
    font-size: 52px;
    margin-bottom: 14px;
    opacity: 0.85;
}

.nocturne-empty-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 20px;
    font-weight: 800;
    color: var(--text-high-contrast);
    margin-bottom: 8px;
}

.nocturne-empty-desc {
    color: var(--text-muted);
    font-size: 14px;
    max-width: 480px;
    margin: 0 auto 20px auto;
    line-height: 1.6;
}

.nocturne-empty-tips {
    background: #0C0E12;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px 20px;
    max-width: 440px;
    margin: 0 auto;
    text-align: left;
    font-size: 13px;
    color: #B2B8C6;
}

/* ==========================================================================
   9. LUXURY FOOTER
   ========================================================================== */
.nocturne-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding: 32px 0 16px 0;
    margin-top: 48px;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    font-size: 12.5px;
    color: var(--text-ghost);
}

.footer-brand {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    color: var(--text-muted);
}

.footer-links {
    display: flex;
    gap: 18px;
    flex-wrap: wrap;
}

.footer-links a {
    color: var(--text-muted);
    text-decoration: none;
    transition: color 0.15s ease;
}

.footer-links a:hover {
    color: #FF385C;
}
</style>
"""
