'''
# ui/styles.py - Unified Cosmic Theme (Blended with HTML Wrapper)
from config import Config


def get_css(config: Config) -> str:
    return """
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Outfit:wght@700;800&family=JetBrains+Mono:wght@500&display=swap');
    
    :root {
        /* Core Space Colors - Matching HTML Wrapper */
        --bg-primary: #030014;
        --bg-secondary: #0a0520;
        --bg-tertiary: #0f0a1a;
        
        /* Neon Palette - Exact match with wrapper */
        --neon-cyan: #22d3ee;
        --neon-purple: #a78bfa;
        --neon-pink: #f472b6;
        --neon-blue: #60a5fa;
        --neon-indigo: #6366f1;
        
        /* Accent Colors */
        --aurora-green: #10b981;
        --aurora-yellow: #fbbf24;
        --aurora-orange: #f97316;
        
        /* Text Colors */
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #64748b;
        
        /* Glass Effects */
        --glass-bg: rgba(10, 5, 30, 0.7);
        --glass-bg-light: rgba(15, 10, 40, 0.5);
        --glass-border: rgba(99, 102, 241, 0.2);
        --glass-border-hover: rgba(139, 92, 246, 0.4);
        --glass-glow: rgba(99, 102, 241, 0.15);
        
        /* Gradients */
        --gradient-primary: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
        --gradient-border: linear-gradient(135deg, rgba(34, 211, 238, 0.5), rgba(168, 85, 247, 0.5), rgba(244, 114, 182, 0.5));
    }
    
    /* === BASE CONTAINER === */
    .gradio-container {
        background: transparent !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
        color: var(--text-primary) !important;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    /* === COSMIC BACKGROUND LAYERS === */
    .gradio-container::before {
        content: "";
        position: fixed;
        inset: 0;
        background: 
            radial-gradient(ellipse at 0% 0%, rgba(34, 211, 238, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 100% 0%, rgba(168, 85, 247, 0.1) 0%, transparent 50%),
            radial-gradient(ellipse at 100% 100%, rgba(244, 114, 182, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 0% 100%, rgba(96, 165, 250, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
        animation: cosmicPulse 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes cosmicPulse {
        0%, 100% { 
            opacity: 0.6;
            filter: hue-rotate(0deg);
        }
        33% { 
            opacity: 0.8;
            filter: hue-rotate(10deg);
        }
        66% { 
            opacity: 0.7;
            filter: hue-rotate(-10deg);
        }
    }
    
    /* Floating Star Particles */
    .gradio-container::after {
        content: "";
        position: fixed;
        inset: 0;
        background-image: 
            radial-gradient(1.5px 1.5px at 10% 20%, rgba(34, 211, 238, 0.6), transparent),
            radial-gradient(1px 1px at 20% 50%, rgba(255, 255, 255, 0.4), transparent),
            radial-gradient(1.5px 1.5px at 30% 80%, rgba(168, 85, 247, 0.5), transparent),
            radial-gradient(1px 1px at 40% 30%, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(2px 2px at 50% 60%, rgba(244, 114, 182, 0.4), transparent),
            radial-gradient(1px 1px at 60% 10%, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(1.5px 1.5px at 70% 70%, rgba(96, 165, 250, 0.5), transparent),
            radial-gradient(1px 1px at 80% 40%, rgba(255, 255, 255, 0.4), transparent),
            radial-gradient(1.5px 1.5px at 90% 90%, rgba(34, 211, 238, 0.4), transparent);
        background-size: 250px 250px;
        animation: starDrift 120s linear infinite;
        pointer-events: none;
        z-index: 0;
        opacity: 0.8;
    }
    
    @keyframes starDrift {
        from { transform: translateY(0) rotate(0deg); }
        to { transform: translateY(-250px) rotate(5deg); }
    }
    
    .gradio-container > * {
        position: relative;
        z-index: 1;
    }
    
    /* === GLASS MORPHISM PANELS === */
    .gr-panel, .gr-box, .gr-form, .gr-group {
        background: linear-gradient(
            135deg,
            rgba(10, 5, 30, 0.8) 0%,
            rgba(15, 10, 40, 0.6) 50%,
            rgba(10, 5, 30, 0.8) 100%
        ) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 20px !important;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.5),
            0 0 0 1px rgba(99, 102, 241, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05),
            inset 0 -1px 0 rgba(0, 0, 0, 0.2) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    
    /* Subtle animated border glow on hover */
    .gr-panel::before, .gr-box::before {
        content: "";
        position: absolute;
        inset: -1px;
        border-radius: 21px;
        padding: 1px;
        background: linear-gradient(135deg, 
            rgba(34, 211, 238, 0), 
            rgba(168, 85, 247, 0), 
            rgba(244, 114, 182, 0));
        -webkit-mask: 
            linear-gradient(#fff 0 0) content-box, 
            linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        opacity: 0;
        transition: all 0.5s ease;
        pointer-events: none;
    }
    
    .gr-panel:hover::before, .gr-box:hover::before {
        background: linear-gradient(135deg, 
            rgba(34, 211, 238, 0.6), 
            rgba(168, 85, 247, 0.6), 
            rgba(244, 114, 182, 0.6));
        opacity: 1;
    }
    
    .gr-panel:hover, .gr-box:hover {
        border-color: var(--glass-border-hover) !important;
        box-shadow: 
            0 20px 60px rgba(99, 102, 241, 0.2),
            0 0 0 1px rgba(139, 92, 246, 0.3),
            0 0 80px rgba(99, 102, 241, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        transform: translateY(-4px);
    }
    
    /* === TEXT INPUTS === */
    textarea, input[type="text"], input[type="number"], .gr-textbox, .gr-text-input, select {
        background: rgba(5, 5, 20, 0.8) !important;
        border: 1px solid rgba(99, 102, 241, 0.25) !important;
        border-radius: 14px !important;
        color: var(--text-primary) !important;
        padding: 16px 18px !important;
        font-size: 15px !important;
        font-family: 'Inter', sans-serif !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    textarea:focus, input[type="text"]:focus, input[type="number"]:focus, select:focus {
        border-color: var(--neon-cyan) !important;
        box-shadow: 
            0 0 0 3px rgba(34, 211, 238, 0.15),
            0 0 30px rgba(34, 211, 238, 0.1),
            inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        outline: none !important;
    }
    
    textarea::placeholder, input::placeholder {
        color: var(--text-muted) !important;
        opacity: 0.7 !important;
    }
    
    /* === BUTTONS === */
    button {
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.2) 0%, 
            rgba(139, 92, 246, 0.15) 50%,
            rgba(99, 102, 241, 0.2) 100%) !important;
        border: 1px solid rgba(99, 102, 241, 0.35) !important;
        border-radius: 14px !important;
        color: var(--text-primary) !important;
        padding: 14px 28px !important;
        font-weight: 600 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 0.5px !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 4px 15px rgba(99, 102, 241, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        position: relative;
        overflow: hidden;
    }
    
    button::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(255, 255, 255, 0.1) 50%, 
            transparent 100%);
        transform: translateX(-100%);
        transition: transform 0.6s ease;
    }
    
    button:hover::before {
        transform: translateX(100%);
    }
    
    button:hover {
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.35) 0%, 
            rgba(139, 92, 246, 0.3) 50%,
            rgba(99, 102, 241, 0.35) 100%) !important;
        border-color: var(--neon-purple) !important;
        transform: translateY(-3px) !important;
        box-shadow: 
            0 10px 30px rgba(99, 102, 241, 0.25),
            0 0 40px rgba(99, 102, 241, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Primary Button - Cosmic Neon */
    .primary-btn, button.primary, .gr-button-primary {
        background: linear-gradient(135deg, 
            var(--neon-indigo) 0%, 
            var(--neon-purple) 50%, 
            var(--neon-pink) 100%) !important;
        background-size: 200% 200% !important;
        animation: gradientFlow 4s ease infinite !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        box-shadow: 
            0 4px 25px rgba(99, 102, 241, 0.4),
            0 0 50px rgba(168, 85, 247, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .primary-btn:hover, button.primary:hover, .gr-button-primary:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 
            0 12px 40px rgba(99, 102, 241, 0.5),
            0 0 80px rgba(168, 85, 247, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
    }
    
    /* === MARKDOWN OUTPUT - Matching Wrapper Style === */
    .gr-markdown, .gr-html {
        background: linear-gradient(
            180deg,
            rgba(10, 5, 30, 0.85) 0%,
            rgba(5, 5, 20, 0.9) 100%
        ) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 20px !important;
        padding: 28px 32px !important;
        color: var(--text-primary) !important;
        line-height: 1.85 !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.03) !important;
    }
    
    /* Headers with Animated Gradient */
    .gr-markdown h1, .gr-markdown h2 {
        font-family: 'Outfit', 'Space Grotesk', sans-serif !important;
        background: linear-gradient(135deg, 
            var(--neon-cyan) 0%, 
            var(--neon-purple) 50%, 
            var(--neon-pink) 100%);
        background-size: 200% auto;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 700 !important;
        margin-top: 28px !important;
        margin-bottom: 16px !important;
        animation: textGradient 6s ease infinite;
        filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));
    }
    
    @keyframes textGradient {
        0%, 100% { background-position: 0% center; }
        50% { background-position: 200% center; }
    }
    
    .gr-markdown h1 { font-size: 2.2em !important; }
    .gr-markdown h2 { font-size: 1.6em !important; }
    
    .gr-markdown h3 {
        color: var(--neon-cyan) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.25em !important;
        margin-top: 24px !important;
        border-bottom: 1px solid rgba(34, 211, 238, 0.25);
        padding-bottom: 10px;
        text-shadow: 0 0 20px rgba(34, 211, 238, 0.3);
    }
    
    .gr-markdown h4 {
        color: var(--neon-purple) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        margin-top: 20px !important;
    }
    
    .gr-markdown strong, .gr-markdown b {
        color: var(--aurora-yellow) !important;
        font-weight: 600 !important;
        text-shadow: 0 0 10px rgba(251, 191, 36, 0.3);
    }
    
    .gr-markdown em, .gr-markdown i {
        color: var(--neon-pink) !important;
        font-style: italic;
    }
    
    /* Links with Neon Effect */
    .gr-markdown a {
        color: var(--neon-cyan) !important;
        text-decoration: none !important;
        position: relative;
        transition: all 0.3s ease;
        padding-bottom: 2px;
    }
    
    .gr-markdown a::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 0;
        height: 1px;
        background: linear-gradient(90deg, var(--neon-cyan), var(--neon-pink));
        transition: width 0.3s ease;
    }
    
    .gr-markdown a:hover {
        color: var(--neon-pink) !important;
        text-shadow: 0 0 15px rgba(244, 114, 182, 0.5);
    }
    
    .gr-markdown a:hover::after {
        width: 100%;
    }
    
    /* Code Blocks */
    .gr-markdown code {
        background: rgba(99, 102, 241, 0.15) !important;
        color: var(--neon-cyan) !important;
        padding: 4px 10px !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 0.9em !important;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    .gr-markdown pre {
        background: rgba(5, 5, 20, 0.9) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 14px !important;
        padding: 20px !important;
        overflow-x: auto;
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    .gr-markdown pre code {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        color: var(--text-secondary) !important;
    }
    
    /* Horizontal Rule - Neon Gradient */
    .gr-markdown hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, 
            transparent 0%, 
            var(--neon-cyan) 20%,
            var(--neon-purple) 50%,
            var(--neon-pink) 80%,
            transparent 100%
        ) !important;
        margin: 32px 0 !important;
        opacity: 0.6;
    }
    
    /* Tables with Glass Effect */
    .gr-markdown table {
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        margin: 20px 0 !important;
        background: rgba(10, 5, 30, 0.6) !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
    }
    
    .gr-markdown th {
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.25) 0%, 
            rgba(168, 85, 247, 0.2) 100%) !important;
        color: var(--neon-cyan) !important;
        padding: 14px 18px !important;
        text-align: left !important;
        font-weight: 600 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        border-bottom: 1px solid rgba(99, 102, 241, 0.3) !important;
        text-transform: uppercase;
        font-size: 0.85em;
        letter-spacing: 0.5px;
    }
    
    .gr-markdown td {
        padding: 14px 18px !important;
        border-bottom: 1px solid rgba(99, 102, 241, 0.1) !important;
        transition: background 0.2s ease;
    }
    
    .gr-markdown tr:last-child td {
        border-bottom: none !important;
    }
    
    .gr-markdown tr:hover td {
        background: rgba(99, 102, 241, 0.08) !important;
    }
    
    /* Blockquotes */
    .gr-markdown blockquote {
        border-left: 3px solid var(--neon-purple) !important;
        background: linear-gradient(90deg, 
            rgba(168, 85, 247, 0.1) 0%, 
            transparent 100%) !important;
        padding: 16px 24px !important;
        margin: 20px 0 !important;
        border-radius: 0 14px 14px 0 !important;
        font-style: italic;
        color: var(--text-secondary);
    }
    
    /* Lists */
    .gr-markdown ul, .gr-markdown ol {
        padding-left: 24px !important;
        margin: 16px 0 !important;
    }
    
    .gr-markdown li {
        margin: 10px 0 !important;
        position: relative;
    }
    
    .gr-markdown ul li::marker {
        color: var(--neon-cyan) !important;
    }
    
    .gr-markdown ol li::marker {
        color: var(--neon-purple) !important;
        font-weight: 600;
    }
    
    /* === LABELS === */
    label, .gr-label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        letter-spacing: 0.4px !important;
        margin-bottom: 10px !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* === DROPDOWNS === */
    .gr-dropdown, select {
        background: rgba(5, 5, 20, 0.8) !important;
        border-radius: 14px !important;
        border: 1px solid rgba(99, 102, 241, 0.25) !important;
    }
    
    .gr-dropdown:hover, select:hover {
        border-color: var(--neon-purple) !important;
    }
    
    /* === SLIDER === */
    input[type="range"] {
        -webkit-appearance: none !important;
        background: linear-gradient(90deg, 
            rgba(99, 102, 241, 0.3), 
            rgba(168, 85, 247, 0.3)) !important;
        border-radius: 10px !important;
        height: 6px !important;
        border: none !important;
    }
    
    input[type="range"]::-webkit-slider-thumb {
        -webkit-appearance: none !important;
        width: 22px !important;
        height: 22px !important;
        background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple)) !important;
        border-radius: 50% !important;
        cursor: pointer !important;
        box-shadow: 
            0 0 20px rgba(34, 211, 238, 0.5),
            0 0 40px rgba(168, 85, 247, 0.3) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.2s ease;
    }
    
    input[type="range"]::-webkit-slider-thumb:hover {
        transform: scale(1.15);
        box-shadow: 
            0 0 25px rgba(34, 211, 238, 0.7),
            0 0 50px rgba(168, 85, 247, 0.4) !important;
    }
    
    /* === CHECKBOX & RADIO === */
    input[type="checkbox"], input[type="radio"] {
        accent-color: var(--neon-purple) !important;
    }
    
    /* === ACCORDION === */
    .gr-accordion {
        background: rgba(10, 5, 30, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 16px !important;
        overflow: hidden;
    }
    
    .gr-accordion summary {
        padding: 16px 20px !important;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    /* --- Accordion icon: force proper chevron --- */
    .gr-accordion summary .icon,
    .gr-accordion summary svg {
      display: none !important;   /* hides Gradio's triangle/icon */
    }
    
    .gr-accordion summary::-webkit-details-marker { display: none !important; }
    .gr-accordion summary::marker { content: "" !important; }
    
    .gr-accordion summary{
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      gap: 12px !important;
      list-style: none !important;
    }
    
    .gr-accordion summary::after{
      content: "▾" !important;
      opacity: 0.85 !important;
      transform: rotate(-90deg) !important;
      transition: transform 0.2s ease, opacity 0.2s ease !important;
      font-weight: 900 !important;
      color: var(--text-secondary) !important;
    }
    
    .gr-accordion[open] summary::after{
      transform: rotate(0deg) !important;
      opacity: 1 !important;
      color: var(--neon-cyan) !important;
    }

    /* === ACCORDION CHEVRON FIX === */
    
    /* remove default marker */
    .gr-accordion summary::-webkit-details-marker { display: none; }
    .gr-accordion summary::marker { content: ""; }
    
    /* make header layout consistent */
    .gr-accordion summary{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      list-style: none;
    }
    
    /* custom chevron on the right */
    .gr-accordion summary::after{
      content: "▾";
      opacity: 0.8;
      transform: rotate(-90deg);
      transition: transform 0.2s ease, opacity 0.2s ease;
      font-weight: 800;
      color: var(--text-secondary);
    }
    
    /* rotate when open */
    .gr-accordion[open] summary::after{
      transform: rotate(0deg);
      opacity: 1;
      color: var(--neon-cyan);
    }
    
    /* give content some padding */
    .gr-accordion > div, .gr-accordion .wrap{
      padding: 12px 16px 16px 16px;
    }

    
    .gr-accordion summary:hover {
        background: rgba(99, 102, 241, 0.1) !important;
    }
    
    /* === TABS === */
    .gr-tabs {
        border-bottom: 1px solid rgba(99, 102, 241, 0.2) !important;
    }
    
    .gr-tab-button {
        background: transparent !important;
        border: none !important;
        color: var(--text-muted) !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        position: relative;
    }
    
    .gr-tab-button::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple));
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .gr-tab-button:hover {
        color: var(--text-primary) !important;
    }
    
    .gr-tab-button.selected {
        color: var(--neon-cyan) !important;
    }
    
    .gr-tab-button.selected::after {
        transform: scaleX(1);
    }
    
    /* === CUSTOM SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(5, 5, 20, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--neon-indigo), var(--neon-purple));
        border-radius: 10px;
        border: 2px solid rgba(5, 5, 20, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--neon-cyan), var(--neon-pink));
    }
    
    /* === HEADER AREA === */
    .header-container {
        text-align: center;
        padding: 30px 20px 15px;
        position: relative;
    }
    
    /* Main Title - Matching HTML Wrapper */
    .gradient-text {
        font-family: 'Outfit', sans-serif !important;
        font-size: 2.8em !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, 
            #fff 0%, 
            var(--neon-cyan) 25%, 
            var(--neon-purple) 50%, 
            var(--neon-pink) 75%, 
            #fff 100%
        );
        background-size: 300% auto;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        animation: titleShimmer 8s ease infinite;
        margin: 0;
        filter: drop-shadow(0 0 30px rgba(139, 92, 246, 0.4));
        letter-spacing: 1px;
    }
    
    @keyframes titleShimmer {
        0% { background-position: 0% center; }
        50% { background-position: 100% center; }
        100% { background-position: 0% center; }
    }
    
    .subtitle {
        color: var(--text-secondary);
        font-size: 1.1em;
        margin-top: 8px;
        font-weight: 400;
        letter-spacing: 1.5px;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    /* === STATUS BADGES === */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        margin: 12px auto;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 30px;
        color: var(--aurora-green);
        font-size: 0.85em;
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: 0.5px;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
    }
    
    .status-badge::before {
        content: '';
        width: 8px;
        height: 8px;
        background: var(--aurora-green);
        border-radius: 50%;
        animation: statusPulse 2s ease infinite;
    }
    
    @keyframes statusPulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
        50% { opacity: 0.6; box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    }
    
    /* === OUTPUT BOX === */
    .output-box {
        background: linear-gradient(
            180deg,
            rgba(10, 5, 30, 0.9) 0%,
            rgba(5, 5, 20, 0.95) 100%
        ) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 20px !important;
        padding: 28px !important;
        max-height: 70vh !important;
        overflow-y: auto !important;
        position: relative;
    }
    
    .output-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(34, 211, 238, 0.5), 
            rgba(168, 85, 247, 0.5), 
            transparent);
    }
    
    /* === LOADING STATES === */
    .wrap.pending {
        background: rgba(99, 102, 241, 0.05) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        animation: loadingPulse 2s ease infinite !important;
    }
    
    @keyframes loadingPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.2); }
        50% { box-shadow: 0 0 20px 5px rgba(99, 102, 241, 0.1); }
    }
    
    .progress-bar, .eta-bar {
        display: none !important;
    }
    
    /* === HIDE GRADIO FOOTER === */
    footer, .gradio-container footer, .built-with-gradio, 
    .footer, div[class*="footer"], .gradio-container > footer {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    
    /* === RESPONSIVE DESIGN === */
    @media (max-width: 768px) {
        .gradient-text {
            font-size: 2em !important;
        }
        
        .gr-panel, .gr-box {
            border-radius: 16px !important;
            padding: 16px !important;
        }
        
        .gr-markdown, .gr-html {
            padding: 20px !important;
            border-radius: 16px !important;
        }
        
        button {
            padding: 12px 20px !important;
        }
        
        .header-container {
            padding: 20px 15px 10px;
        }
    }
    
    @media (max-width: 480px) {
        .gradient-text {
            font-size: 1.6em !important;
        }
        
        .subtitle {
            font-size: 0.95em;
        }
        
        .gr-markdown h1 { font-size: 1.6em !important; }
        .gr-markdown h2 { font-size: 1.3em !important; }
    }
    
    /* === ANIMATIONS FOR ELEMENTS === */
    .gr-panel, .gr-box, .gr-form {
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Staggered animation for multiple elements */
    .gr-panel:nth-child(1) { animation-delay: 0.1s; }
    .gr-panel:nth-child(2) { animation-delay: 0.2s; }
    .gr-panel:nth-child(3) { animation-delay: 0.3s; }
    .gr-panel:nth-child(4) { animation-delay: 0.4s; }
    
    /* === INFO/WARNING/ERROR BOXES === */
    .gr-info {
        background: rgba(34, 211, 238, 0.1) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        border-radius: 12px !important;
        color: var(--neon-cyan) !important;
    }
    
    .gr-warning {
        background: rgba(251, 191, 36, 0.1) !important;
        border: 1px solid rgba(251, 191, 36, 0.3) !important;
        border-radius: 12px !important;
        color: var(--aurora-yellow) !important;
    }
    
    .gr-error {
        background: rgba(244, 114, 182, 0.1) !important;
        border: 1px solid rgba(244, 114, 182, 0.3) !important;
        border-radius: 12px !important;
        color: var(--neon-pink) !important;
    }

    /* =========================
   Roadmap Dashboard Widgets
   ========================= */

    #roadmap_tabs {
      margin-top: 8px;
    }
    
    .card-empty{
      padding: 16px;
      border-radius: 16px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      color: var(--text-secondary);
    }
    
    /* Timeline */
    .timeline-wrap{
      padding: 8px 2px;
    }
    
    .timeline-head{
      font-family: 'Space Grotesk', sans-serif;
      font-weight: 700;
      font-size: 18px;
      margin: 6px 0 12px 0;
      color: var(--text-primary);
    }
    
    .timeline{
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding-left: 6px;
      position: relative;
    }
    
    .timeline:before{
      content: "";
      position: absolute;
      left: 14px;
      top: 8px;
      bottom: 8px;
      width: 2px;
      background: rgba(255,255,255,0.10);
    }
    
    .t-item{
      display: grid;
      grid-template-columns: 28px 1fr;
      gap: 12px;
      align-items: start;
    }
    
    .t-dot{
      width: 12px;
      height: 12px;
      border-radius: 999px;
      margin-top: 14px;
      background: rgba(255,255,255,0.35);
      border: 2px solid rgba(255,255,255,0.15);
      box-shadow: 0 0 0 6px rgba(255,255,255,0.04);
      justify-self: center;
      z-index: 1;
    }
    
    .t-card{
      border-radius: 18px;
      padding: 14px 14px 12px 14px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
    }
    
    .t-title{
      font-weight: 700;
      margin-bottom: 8px;
      color: var(--text-primary);
    }
    
    .t-list{
      margin: 0;
      padding-left: 18px;
      color: var(--text-secondary);
    }
    
    .t-list li{
      margin: 6px 0;
    }
    
    /* Program cards */
    .prog-grid{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    
    @media (max-width: 900px){
      .prog-grid{ grid-template-columns: 1fr; }
    }
    
    .prog-card{
      border-radius: 18px;
      padding: 14px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
    }
    
    .prog-title{
      font-weight: 800;
      color: var(--text-primary);
      margin-bottom: 6px;
    }
    
    .prog-desc{
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.35;
    }
    
    /* Checklist */
    .chk-wrap{
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 4px 2px;
    }
    
    .chk{
      display: flex;
      gap: 10px;
      align-items: flex-start;
      padding: 10px 12px;
      border-radius: 16px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      color: var(--text-secondary);
    }
    
    .chk input{
      transform: translateY(2px);
    }

    /* Profile header */
    .profile-card{
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      margin-bottom: 12px;
    }
    .profile-title{
      font-weight: 800;
      margin-bottom: 10px;
      color: var(--text-primary);
    }
    .chip-row{
      display:flex; flex-wrap:wrap; gap:8px;
    }
    .chip-row-tight{ margin-top: 10px; }
    .chip{
      display:inline-flex;
      align-items:center;
      gap:6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
      color: var(--text-secondary);
      font-size: 13px;
    }
    .chip-wide{ max-width: 100%; }
    .chip-missing{
      background: rgba(255, 200, 100, 0.10);
      border-color: rgba(255, 200, 100, 0.18);
    }
    
    /* Programs card improvements */
    .prog-top{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
    .prog-uni{ color: var(--text-secondary); font-size: 13px; margin-top: 2px; }
    .prog-side{ display:flex; flex-direction:column; gap:8px; align-items:flex-end; }
    .badge{
      padding: 6px 10px;
      border-radius: 999px;
      font-weight: 800;
      font-size: 13px;
      border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.08);
    }
    .badge-good{ background: rgba(120, 255, 180, 0.10); border-color: rgba(120, 255, 180, 0.20); }
    .badge-mid{ background: rgba(255, 220, 120, 0.10); border-color: rgba(255, 220, 120, 0.20); }
    .badge-low{ background: rgba(255, 140, 140, 0.10); border-color: rgba(255, 140, 140, 0.20); }
    
    .pill{
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.06);
      color: var(--text-secondary);
    }
    
    .meta{ margin-top: 12px; }
    .meta-row{
      display:flex;
      justify-content:space-between;
      gap:12px;
      padding: 8px 0;
      border-top: 1px solid rgba(255,255,255,0.08);
      color: var(--text-secondary);
      font-size: 13px;
    }
    .meta-row span:first-child{ color: var(--text-primary); font-weight: 700; }
    .meta-hint{
      padding-top: 10px;
      border-top: 1px solid rgba(255,255,255,0.08);
      color: var(--text-secondary);
      font-size: 13px;
    }
    
    /* Checklist phases */
    .phase-wrap{ display:flex; flex-direction:column; gap:14px; }
    .phase{
      border-radius: 18px;
      padding: 12px 12px 6px 12px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
    }
    .phase-title{
      font-weight: 800;
      color: var(--text-primary);
      margin-bottom: 10px;
    }

    /* =========================
   Dashboard polish fixes
   ========================= */

    /* Profile header */
    .profile-card{
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      margin-bottom: 12px;
    }
    .profile-title{
      font-weight: 800;
      margin-bottom: 10px;
      color: var(--text-primary);
    }
    .chip-row{
      display:flex; flex-wrap:wrap; gap:8px;
    }
    .chip-row-tight{ margin-top: 10px; }
    .chip{
      display:inline-flex;
      align-items:center;
      gap:6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
      color: var(--text-secondary);
      font-size: 13px;
    }
    .chip-wide{ max-width: 100%; }
    .chip-missing{
      background: rgba(255, 200, 100, 0.10);
      border-color: rgba(255, 200, 100, 0.18);
    }
    
    /* Programs card header row */
    .prog-top{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
    .prog-uni{ color: var(--text-secondary); font-size: 13px; margin-top: 2px; }
    .prog-side{ display:flex; flex-direction:column; gap:8px; align-items:flex-end; }
    .badge{
      padding: 6px 10px;
      border-radius: 999px;
      font-weight: 800;
      font-size: 13px;
      border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.08);
    }
    .badge-good{ background: rgba(120, 255, 180, 0.10); border-color: rgba(120, 255, 180, 0.20); }
    .badge-mid{ background: rgba(255, 220, 120, 0.10); border-color: rgba(255, 220, 120, 0.20); }
    .badge-low{ background: rgba(255, 140, 140, 0.10); border-color: rgba(255, 140, 140, 0.20); }
    
    .pill{
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.06);
      color: var(--text-secondary);
    }
    
    .meta{ margin-top: 12px; }
    .meta-row{
      display:flex;
      justify-content:space-between;
      gap:12px;
      padding: 8px 0;
      border-top: 1px solid rgba(255,255,255,0.08);
      color: var(--text-secondary);
      font-size: 13px;
    }
    .meta-row span:first-child{ color: var(--text-primary); font-weight: 700; }
    .meta-hint{
      padding-top: 10px;
      border-top: 1px solid rgba(255,255,255,0.08);
      color: var(--text-secondary);
      font-size: 13px;
    }
    
    /* Link button */
    .link-btn{
      display:inline-flex;
      margin-top: 10px;
      padding: 8px 10px;
      border-radius: 12px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      color: var(--text-primary);
      text-decoration: none;
      font-weight: 700;
      font-size: 13px;
    }
    .link-btn:hover{
      background: rgba(255,255,255,0.10);
    }
    
    /* Checklist phases */
    .phase-wrap{ display:flex; flex-direction:column; gap:14px; }
    .phase{
      border-radius: 18px;
      padding: 12px 12px 6px 12px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
    }
    .phase-title{
      font-weight: 800;
      color: var(--text-primary);
      margin-bottom: 10px;
    }

    .badge-na{
      background: rgba(255,255,255,0.06);
      border-color: rgba(255,255,255,0.12);
    }

    /* Interest preset buttons */
    .chip-btn button{
      padding: 8px 12px !important;
      border-radius: 999px !important;
      font-size: 12px !important;
      font-weight: 700 !important;
    }

    /* Collapsible sidebar toggle */
    #sidebar_toggle_btn{
      width: fit-content;
      min-width: 140px;
      padding: 8px 12px;
      border-radius: 14px;
      margin: 2px 0 10px 0;
    }
    
    /* Optional: make the button look nice + not huge */
    #sidebar_toggle_btn button{
      font-weight: 700;
    }

    @media (max-width: 1200px){
      #sidebar_toggle_btn{ min-width: 120px; padding: 7px 10px; }
    }

    /* Force the main dashboard row to behave like a flex layout */
    #dash_row {
      display: flex !important;
      gap: 18px;
      align-items: stretch;
    }
    
    /* Sidebar: fixed-ish width, doesn’t grow */
    #sidebar_col {
      flex: 0 0 360px;     /* adjust width if you want */
      max-width: 420px;
    }
    
    /* Main column: fills remaining space */
    #main_col {
      flex: 1 1 auto;
      min-width: 0;        /* IMPORTANT: prevents overflow causing layout issues */
    }
    
    /* When Gradio hides sidebar (display:none), main should become full width */
    #sidebar_col[style*="display: none"] + #main_col {
      flex: 1 1 100% !important;
      max-width: 100% !important;
    }

    /* Wizard polish */
    #inputs_view h2, #inputs_view h3 { letter-spacing: 0.2px; }
    .output-box { padding: 14px 16px; border-radius: 14px; }
    
    .secondary-btn { border-radius: 14px; }
    .primary-btn { border-radius: 14px; font-weight: 600; }
    
    .phase { border-radius: 16px; }
    .prog-card { border-radius: 18px; } /* won’t change Programs layout, just nicer */
    
    /* Checklist */
    .chk { display:block; padding:10px 12px; border-radius:12px; }
    .chk:hover { background: rgba(255,255,255,0.04); }
    .chk input { transform: scale(1.05); margin-right: 10px; }

    /* =========================================================
   REMOVE GRADIO BLUE BORDERS / OUTLINES (global override)
   ========================================================= */

    /* Your missing classes (so Gradio doesn't use default bordered blocks) */
    .glass-panel {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
    }
    
    .glass-input input,
    .glass-input textarea,
    .glass-input select {
      background: rgba(4, 7, 16, 0.55) !important;
      border: 1px solid rgba(255,255,255,0.10) !important;
      color: rgba(255,255,255,0.92) !important;
      border-radius: 14px !important;
      box-shadow: none !important;
    }
    
    .glass-input input:focus,
    .glass-input textarea:focus,
    .glass-input select:focus {
      outline: none !important;
      border-color: rgba(255,255,255,0.18) !important;
      box-shadow: 0 0 0 2px rgba(255,255,255,0.06) !important;
    }
    
    /* Kill borders on Gradio wrappers that create those blue lines */
    .gradio-container .wrap,
    .gradio-container .block,
    .gradio-container .gr-panel,
    .gradio-container .gr-box,
    .gradio-container .gr-form,
    .gradio-container .gr-accordion,
    .gradio-container .gr-group,
    .gradio-container .form,
    .gradio-container .container {
      border: none !important;
      outline: none !important;
      box-shadow: none !important;
    }
    
    /* Also remove focus ring Gradio applies to some buttons/components */
    .gradio-container button:focus,
    .gradio-container button:focus-visible {
      outline: none !important;
      box-shadow: none !important;
    }
    
    /* Make markdown separators subtle (your --- lines) */
    .gradio-container hr {
      border: 0 !important;
      height: 1px !important;
      background: rgba(255,255,255,0.10) !important;
      margin: 16px 0 !important;
    }
    
    /* Optional: reduce the “boxed” feeling on markdown blocks */
    .gradio-container .markdown,
    .gradio-container .prose {
      border: none !important;
      box-shadow: none !important;
    }
    
    """
'''

# ui/styles.py - MAGNIFICENT Cosmic Theme
from config import Config


def get_css(config: Config) -> str:
    return """
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Outfit:wght@700;800;900&family=JetBrains+Mono:wght@500&family=Orbitron:wght@700;900&display=swap');
    
    :root {
        /* Core Space Colors */
        --bg-void: #020010;
        --bg-primary: #030014;
        --bg-secondary: #0a0520;
        --bg-tertiary: #0f0a1a;
        --bg-card: #0d0825;
        
        /* Neon Palette - Intensified */
        --neon-cyan: #00f5ff;
        --neon-cyan-dim: #22d3ee;
        --neon-purple: #a855f7;
        --neon-purple-bright: #c084fc;
        --neon-pink: #ec4899;
        --neon-pink-bright: #f472b6;
        --neon-blue: #3b82f6;
        --neon-indigo: #6366f1;
        --neon-violet: #8b5cf6;
        
        /* Aurora Colors */
        --aurora-green: #10b981;
        --aurora-teal: #14b8a6;
        --aurora-yellow: #fbbf24;
        --aurora-orange: #f97316;
        --aurora-red: #ef4444;
        
        /* Text Colors */
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #64748b;
        --text-glow: #ffffff;
        
        /* Glass Effects - Enhanced */
        --glass-bg: rgba(10, 5, 32, 0.75);
        --glass-bg-light: rgba(15, 10, 45, 0.6);
        --glass-bg-dark: rgba(5, 2, 18, 0.85);
        --glass-border: rgba(139, 92, 246, 0.2);
        --glass-border-hover: rgba(168, 85, 247, 0.5);
        --glass-glow: rgba(139, 92, 246, 0.25);
        
        /* Gradients */
        --gradient-cosmic: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
        --gradient-aurora: linear-gradient(135deg, #10b981, #06b6d4, #8b5cf6, #ec4899);
        --gradient-sunset: linear-gradient(135deg, #f97316, #ec4899, #8b5cf6);
        --gradient-ocean: linear-gradient(135deg, #0ea5e9, #6366f1, #a855f7);
        
        /* Shadows */
        --shadow-neon: 0 0 40px rgba(139, 92, 246, 0.3), 0 0 80px rgba(139, 92, 246, 0.1);
        --shadow-glow-cyan: 0 0 30px rgba(0, 245, 255, 0.4);
        --shadow-glow-purple: 0 0 30px rgba(168, 85, 247, 0.4);
        --shadow-glow-pink: 0 0 30px rgba(236, 72, 153, 0.4);
    }
    
    /* === UNIVERSAL RESETS === */
    *, *::before, *::after {
        box-sizing: border-box;
    }
    
    /* === BASE CONTAINER === */
    .gradio-container {
        background: var(--bg-void) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary) !important;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    /* === COSMIC NEBULA BACKGROUND === */
    .gradio-container::before {
        content: "";
        position: fixed;
        inset: 0;
        background: 
            /* Central nebula */
            radial-gradient(ellipse 80% 50% at 50% 50%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
            /* Corner nebulae */
            radial-gradient(ellipse 60% 60% at 0% 0%, rgba(0, 245, 255, 0.15) 0%, transparent 45%),
            radial-gradient(ellipse 60% 60% at 100% 0%, rgba(168, 85, 247, 0.12) 0%, transparent 45%),
            radial-gradient(ellipse 60% 60% at 100% 100%, rgba(236, 72, 153, 0.12) 0%, transparent 45%),
            radial-gradient(ellipse 60% 60% at 0% 100%, rgba(59, 130, 246, 0.12) 0%, transparent 45%),
            /* Floating orbs */
            radial-gradient(circle at 20% 80%, rgba(16, 185, 129, 0.08) 0%, transparent 25%),
            radial-gradient(circle at 80% 20%, rgba(244, 114, 182, 0.08) 0%, transparent 25%);
        animation: nebulaShift 30s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes nebulaShift {
        0%, 100% { 
            opacity: 0.8;
            transform: scale(1) rotate(0deg);
        }
        25% { 
            opacity: 0.9;
            transform: scale(1.02) rotate(0.5deg);
        }
        50% { 
            opacity: 0.85;
            transform: scale(1.01) rotate(-0.5deg);
        }
        75% { 
            opacity: 0.95;
            transform: scale(1.03) rotate(0.3deg);
        }
    }
    
    /* === STAR FIELD LAYER === */
    .gradio-container::after {
        content: "";
        position: fixed;
        inset: 0;
        background-image: 
            /* Bright stars */
            radial-gradient(2px 2px at 10% 15%, rgba(255, 255, 255, 0.9), transparent),
            radial-gradient(2px 2px at 25% 35%, rgba(0, 245, 255, 0.8), transparent),
            radial-gradient(1.5px 1.5px at 40% 20%, rgba(255, 255, 255, 0.7), transparent),
            radial-gradient(2px 2px at 55% 55%, rgba(168, 85, 247, 0.8), transparent),
            radial-gradient(1.5px 1.5px at 70% 30%, rgba(255, 255, 255, 0.6), transparent),
            radial-gradient(2px 2px at 85% 65%, rgba(236, 72, 153, 0.7), transparent),
            radial-gradient(1.5px 1.5px at 90% 10%, rgba(255, 255, 255, 0.8), transparent),
            /* Medium stars */
            radial-gradient(1px 1px at 5% 50%, rgba(255, 255, 255, 0.5), transparent),
            radial-gradient(1px 1px at 15% 70%, rgba(255, 255, 255, 0.4), transparent),
            radial-gradient(1px 1px at 30% 90%, rgba(0, 245, 255, 0.5), transparent),
            radial-gradient(1px 1px at 45% 10%, rgba(255, 255, 255, 0.4), transparent),
            radial-gradient(1px 1px at 60% 80%, rgba(168, 85, 247, 0.5), transparent),
            radial-gradient(1px 1px at 75% 45%, rgba(255, 255, 255, 0.5), transparent),
            radial-gradient(1px 1px at 95% 85%, rgba(255, 255, 255, 0.4), transparent),
            /* Dim stars */
            radial-gradient(0.5px 0.5px at 8% 25%, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(0.5px 0.5px at 22% 60%, rgba(255, 255, 255, 0.25), transparent),
            radial-gradient(0.5px 0.5px at 38% 45%, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(0.5px 0.5px at 52% 75%, rgba(255, 255, 255, 0.25), transparent),
            radial-gradient(0.5px 0.5px at 68% 15%, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(0.5px 0.5px at 82% 55%, rgba(255, 255, 255, 0.25), transparent);
        background-size: 200px 200px, 250px 250px, 180px 180px, 220px 220px, 
                         190px 190px, 230px 230px, 210px 210px,
                         150px 150px, 170px 170px, 160px 160px, 180px 180px,
                         175px 175px, 165px 165px, 155px 155px,
                         120px 120px, 130px 130px, 140px 140px, 125px 125px,
                         135px 135px, 145px 145px;
        animation: starFloat 180s linear infinite;
        pointer-events: none;
        z-index: 0;
        opacity: 0.9;
    }
    
    @keyframes starFloat {
        0% { transform: translateY(0) translateX(0); }
        50% { transform: translateY(-100px) translateX(50px); }
        100% { transform: translateY(-200px) translateX(0); }
    }
    
    /* === SHOOTING STARS (CSS-only) === */
    @keyframes shootingStar {
        0% { 
            transform: translateX(-100px) translateY(-100px) rotate(45deg);
            opacity: 0;
        }
        10% { opacity: 1; }
        30% { opacity: 1; }
        100% { 
            transform: translateX(calc(100vw + 100px)) translateY(calc(50vh + 100px)) rotate(45deg);
            opacity: 0;
        }
    }
    
    .gradio-container > * {
        position: relative;
        z-index: 1;
    }
    
    /* === AURORA BORDER ANIMATION === */
    @keyframes auroraBorder {
        0% { 
            background-position: 0% 50%;
            filter: hue-rotate(0deg);
        }
        50% { 
            background-position: 100% 50%;
            filter: hue-rotate(15deg);
        }
        100% { 
            background-position: 0% 50%;
            filter: hue-rotate(0deg);
        }
    }
    
    /* === GLASS MORPHISM PANELS === */
    .gr-panel, .gr-box, .gr-form, .gr-group {
        background: linear-gradient(
            165deg,
            rgba(15, 8, 40, 0.85) 0%,
            rgba(10, 5, 30, 0.9) 50%,
            rgba(8, 4, 25, 0.85) 100%
        ) !important;
        backdrop-filter: blur(24px) saturate(200%) brightness(1.1) !important;
        -webkit-backdrop-filter: blur(24px) saturate(200%) brightness(1.1) !important;
        border: 1px solid transparent !important;
        border-radius: 24px !important;
        box-shadow: 
            0 10px 40px rgba(0, 0, 0, 0.5),
            0 0 0 1px rgba(139, 92, 246, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.08),
            inset 0 -1px 0 rgba(0, 0, 0, 0.3) !important;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    
    /* Animated gradient border */
    .gr-panel::before, .gr-box::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 24px;
        padding: 1px;
        background: linear-gradient(
            135deg,
            rgba(0, 245, 255, 0.5),
            rgba(168, 85, 247, 0.5),
            rgba(236, 72, 153, 0.5),
            rgba(59, 130, 246, 0.5),
            rgba(0, 245, 255, 0.5)
        );
        background-size: 300% 300%;
        -webkit-mask: 
            linear-gradient(#fff 0 0) content-box, 
            linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        opacity: 0;
        animation: auroraBorder 8s ease infinite;
        transition: opacity 0.5s ease;
        pointer-events: none;
    }
    
    .gr-panel:hover::before, .gr-box:hover::before {
        opacity: 1;
    }
    
    /* Inner glow on hover */
    .gr-panel::after, .gr-box::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 24px;
        background: radial-gradient(
            ellipse at 50% 0%,
            rgba(139, 92, 246, 0.15) 0%,
            transparent 60%
        );
        opacity: 0;
        transition: opacity 0.5s ease;
        pointer-events: none;
    }
    
    .gr-panel:hover::after, .gr-box:hover::after {
        opacity: 1;
    }
    
    .gr-panel:hover, .gr-box:hover {
        transform: translateY(-6px) scale(1.005);
        box-shadow: 
            0 25px 70px rgba(139, 92, 246, 0.25),
            0 0 0 1px rgba(168, 85, 247, 0.3),
            0 0 100px rgba(139, 92, 246, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    }
    
    /* === TEXT INPUTS - Holographic Style === */
    textarea, input[type="text"], input[type="number"], input[type="email"], 
    .gr-textbox, .gr-text-input, select {
        background: linear-gradient(
            135deg,
            rgba(5, 2, 15, 0.9) 0%,
            rgba(10, 5, 25, 0.85) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 16px !important;
        color: var(--text-primary) !important;
        padding: 18px 20px !important;
        font-size: 15px !important;
        font-family: 'Inter', sans-serif !important;
        backdrop-filter: blur(12px) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            inset 0 2px 6px rgba(0, 0, 0, 0.4),
            inset 0 0 20px rgba(139, 92, 246, 0.03) !important;
        position: relative;
    }
    
    textarea:focus, input[type="text"]:focus, input[type="number"]:focus, 
    input[type="email"]:focus, select:focus {
        border-color: var(--neon-cyan) !important;
        box-shadow: 
            0 0 0 4px rgba(0, 245, 255, 0.1),
            0 0 40px rgba(0, 245, 255, 0.15),
            0 0 80px rgba(0, 245, 255, 0.05),
            inset 0 2px 6px rgba(0, 0, 0, 0.4),
            inset 0 0 30px rgba(0, 245, 255, 0.03) !important;
        outline: none !important;
    }
    
    textarea::placeholder, input::placeholder {
        color: var(--text-muted) !important;
        opacity: 0.6 !important;
        font-style: italic;
    }
    
    /* === BUTTONS - Neon Cyberpunk Style === */
    button {
        background: linear-gradient(
            135deg,
            rgba(99, 102, 241, 0.15) 0%,
            rgba(139, 92, 246, 0.1) 50%,
            rgba(99, 102, 241, 0.15) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.35) !important;
        border-radius: 16px !important;
        color: var(--text-primary) !important;
        padding: 16px 32px !important;
        font-weight: 600 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 0.5px !important;
        backdrop-filter: blur(12px) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 4px 20px rgba(99, 102, 241, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1),
            inset 0 0 20px rgba(139, 92, 246, 0.05) !important;
        position: relative;
        overflow: hidden;
        cursor: pointer;
    }
    
    /* Shimmer effect */
    button::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.15) 50%,
            transparent 100%
        );
        transition: left 0.6s ease;
    }
    
    button:hover::before {
        left: 100%;
    }
    
    /* Glow ring effect */
    button::after {
        content: "";
        position: absolute;
        inset: -2px;
        border-radius: 18px;
        background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
        background-size: 200% 200%;
        opacity: 0;
        z-index: -1;
        animation: auroraBorder 4s ease infinite;
        transition: opacity 0.3s ease;
    }
    
    button:hover::after {
        opacity: 0.7;
        filter: blur(8px);
    }
    
    button:hover {
        background: linear-gradient(
            135deg,
            rgba(99, 102, 241, 0.25) 0%,
            rgba(139, 92, 246, 0.2) 50%,
            rgba(99, 102, 241, 0.25) 100%
        ) !important;
        border-color: var(--neon-purple) !important;
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 
            0 15px 40px rgba(139, 92, 246, 0.3),
            0 0 60px rgba(139, 92, 246, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    }
    
    button:active {
        transform: translateY(-2px) scale(1.01) !important;
    }
    
    /* === PRIMARY BUTTON - Epic Gradient === */
    .primary-btn, button.primary, .gr-button-primary {
        background: linear-gradient(
            135deg,
            var(--neon-indigo) 0%,
            var(--neon-purple) 33%,
            var(--neon-pink) 66%,
            var(--neon-indigo) 100%
        ) !important;
        background-size: 300% 300% !important;
        animation: gradientFlow 5s ease infinite !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        box-shadow: 
            0 6px 30px rgba(139, 92, 246, 0.5),
            0 0 60px rgba(168, 85, 247, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.25),
            inset 0 -1px 0 rgba(0, 0, 0, 0.2) !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .primary-btn:hover, button.primary:hover, .gr-button-primary:hover {
        transform: translateY(-5px) scale(1.03) !important;
        box-shadow: 
            0 15px 50px rgba(139, 92, 246, 0.6),
            0 0 100px rgba(168, 85, 247, 0.35),
            0 0 150px rgba(236, 72, 153, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        filter: brightness(1.1);
    }
    
    /* === SECONDARY BUTTON === */
    .secondary-btn, button.secondary, .gr-button-secondary {
        background: transparent !important;
        border: 2px solid rgba(139, 92, 246, 0.4) !important;
        color: var(--neon-purple-bright) !important;
    }
    
    .secondary-btn:hover, button.secondary:hover {
        background: rgba(139, 92, 246, 0.1) !important;
        border-color: var(--neon-purple) !important;
        box-shadow: 
            0 0 30px rgba(139, 92, 246, 0.3),
            inset 0 0 20px rgba(139, 92, 246, 0.05) !important;
    }
    
    /* === MARKDOWN OUTPUT - Holographic Display === */
    .gr-markdown, .gr-html {
        background: linear-gradient(
            180deg,
            rgba(10, 5, 32, 0.9) 0%,
            rgba(8, 4, 25, 0.95) 50%,
            rgba(5, 2, 18, 0.9) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
        border-radius: 24px !important;
        padding: 32px 36px !important;
        color: var(--text-primary) !important;
        line-height: 1.9 !important;
        backdrop-filter: blur(24px) !important;
        box-shadow: 
            0 10px 40px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.05),
            inset 0 0 60px rgba(139, 92, 246, 0.03) !important;
        position: relative;
        overflow: hidden;
    }
    
    /* Top highlight bar */
    .gr-markdown::before, .gr-html::before {
        content: '';
        position: absolute;
        top: 0;
        left: 10%;
        right: 10%;
        height: 1px;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(0, 245, 255, 0.5),
            rgba(168, 85, 247, 0.5),
            rgba(236, 72, 153, 0.5),
            transparent
        );
    }
    
    /* === HEADERS - Animated Cosmic Gradient === */
    .gr-markdown h1, .gr-markdown h2 {
        font-family: 'Outfit', 'Space Grotesk', sans-serif !important;
        background: linear-gradient(
            135deg,
            #fff 0%,
            var(--neon-cyan) 20%,
            var(--neon-purple) 40%,
            var(--neon-pink) 60%,
            var(--neon-cyan) 80%,
            #fff 100%
        );
        background-size: 400% auto;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 800 !important;
        margin-top: 32px !important;
        margin-bottom: 20px !important;
        animation: textGradientFlow 8s ease infinite;
        filter: drop-shadow(0 0 30px rgba(139, 92, 246, 0.4))
                drop-shadow(0 0 60px rgba(0, 245, 255, 0.2));
        letter-spacing: 0.5px;
    }
    
    @keyframes textGradientFlow {
        0%, 100% { background-position: 0% center; }
        50% { background-position: 100% center; }
    }
    
    .gr-markdown h1 { 
        font-size: 2.4em !important; 
        letter-spacing: 1px;
    }
    .gr-markdown h2 { 
        font-size: 1.8em !important; 
    }
    
    .gr-markdown h3 {
        color: var(--neon-cyan) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.35em !important;
        margin-top: 28px !important;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(0, 245, 255, 0.2);
        text-shadow: 0 0 30px rgba(0, 245, 255, 0.4);
        position: relative;
    }
    
    .gr-markdown h3::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 60px;
        height: 2px;
        background: linear-gradient(90deg, var(--neon-cyan), transparent);
    }
    
    .gr-markdown h4 {
        color: var(--neon-purple-bright) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        margin-top: 24px !important;
        text-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
    }
    
    /* Bold & Italic */
    .gr-markdown strong, .gr-markdown b {
        color: var(--aurora-yellow) !important;
        font-weight: 700 !important;
        text-shadow: 0 0 15px rgba(251, 191, 36, 0.4);
    }
    
    .gr-markdown em, .gr-markdown i {
        color: var(--neon-pink-bright) !important;
        font-style: italic;
    }
    
    /* === LINKS - Neon Underline === */
    .gr-markdown a {
        color: var(--neon-cyan) !important;
        text-decoration: none !important;
        position: relative;
        transition: all 0.3s ease;
        padding-bottom: 3px;
        font-weight: 500;
    }
    
    .gr-markdown a::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--neon-cyan), var(--neon-pink));
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
    }
    
    .gr-markdown a:hover {
        color: var(--neon-pink) !important;
        text-shadow: 0 0 20px rgba(236, 72, 153, 0.5);
    }
    
    .gr-markdown a:hover::after {
        width: 100%;
    }
    
    /* === CODE BLOCKS - Terminal Style === */
    .gr-markdown code {
        background: linear-gradient(
            135deg,
            rgba(139, 92, 246, 0.15) 0%,
            rgba(99, 102, 241, 0.1) 100%
        ) !important;
        color: var(--neon-cyan) !important;
        padding: 5px 12px !important;
        border-radius: 10px !important;
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 0.9em !important;
        border: 1px solid rgba(0, 245, 255, 0.2);
        box-shadow: 0 0 10px rgba(0, 245, 255, 0.1);
    }
    
    .gr-markdown pre {
        background: linear-gradient(
            180deg,
            rgba(5, 2, 15, 0.95) 0%,
            rgba(8, 4, 20, 0.9) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 18px !important;
        padding: 24px !important;
        overflow-x: auto;
        box-shadow: 
            inset 0 2px 15px rgba(0, 0, 0, 0.4),
            0 0 30px rgba(139, 92, 246, 0.1);
        position: relative;
    }
    
    .gr-markdown pre::before {
        content: '● ● ●';
        position: absolute;
        top: 12px;
        left: 16px;
        font-size: 10px;
        letter-spacing: 4px;
        color: rgba(255, 255, 255, 0.3);
    }
    
    .gr-markdown pre code {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        color: var(--text-secondary) !important;
        box-shadow: none;
    }
    
    /* === HORIZONTAL RULE - Neon Line === */
    .gr-markdown hr {
        border: none !important;
        height: 2px !important;
        background: linear-gradient(
            90deg,
            transparent 0%,
            var(--neon-cyan) 15%,
            var(--neon-purple) 50%,
            var(--neon-pink) 85%,
            transparent 100%
        ) !important;
        margin: 40px 0 !important;
        border-radius: 2px;
        box-shadow: 
            0 0 20px rgba(0, 245, 255, 0.3),
            0 0 40px rgba(168, 85, 247, 0.2);
        animation: hrPulse 3s ease-in-out infinite;
    }
    
    @keyframes hrPulse {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    
    /* === TABLES - Holographic Display === */
    .gr-markdown table {
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        margin: 24px 0 !important;
        background: rgba(10, 5, 30, 0.7) !important;
        border-radius: 18px !important;
        overflow: hidden !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 40px rgba(139, 92, 246, 0.1);
    }
    
    .gr-markdown th {
        background: linear-gradient(
            135deg,
            rgba(139, 92, 246, 0.25) 0%,
            rgba(168, 85, 247, 0.2) 50%,
            rgba(99, 102, 241, 0.25) 100%
        ) !important;
        color: var(--neon-cyan) !important;
        padding: 16px 20px !important;
        text-align: left !important;
        font-weight: 700 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        border-bottom: 1px solid rgba(0, 245, 255, 0.2) !important;
        text-transform: uppercase;
        font-size: 0.85em;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
    }
    
    .gr-markdown td {
        padding: 16px 20px !important;
        border-bottom: 1px solid rgba(139, 92, 246, 0.1) !important;
        transition: all 0.3s ease;
    }
    
    .gr-markdown tr:last-child td {
        border-bottom: none !important;
    }
    
    .gr-markdown tr:hover td {
        background: rgba(139, 92, 246, 0.08) !important;
    }
    
    /* === BLOCKQUOTES - Glowing Border === */
    .gr-markdown blockquote {
        border-left: 4px solid var(--neon-purple) !important;
        background: linear-gradient(
            90deg,
            rgba(168, 85, 247, 0.12) 0%,
            transparent 100%
        ) !important;
        padding: 20px 28px !important;
        margin: 24px 0 !important;
        border-radius: 0 18px 18px 0 !important;
        font-style: italic;
        color: var(--text-secondary);
        position: relative;
        box-shadow: 
            0 0 30px rgba(168, 85, 247, 0.1),
            inset 0 0 20px rgba(168, 85, 247, 0.05);
    }
    
    .gr-markdown blockquote::before {
        content: '"';
        position: absolute;
        top: 10px;
        left: 15px;
        font-size: 48px;
        color: rgba(168, 85, 247, 0.3);
        font-family: Georgia, serif;
        line-height: 1;
    }
    
    /* === LISTS - Neon Bullets === */
    .gr-markdown ul, .gr-markdown ol {
        padding-left: 28px !important;
        margin: 20px 0 !important;
    }
    
    .gr-markdown li {
        margin: 12px 0 !important;
        position: relative;
        padding-left: 8px;
    }
    
    .gr-markdown ul li::marker {
        color: var(--neon-cyan) !important;
        font-size: 1.2em;
    }
    
    .gr-markdown ol li::marker {
        color: var(--neon-purple) !important;
        font-weight: 700;
    }
    
    /* Custom bullet glow */
    .gr-markdown ul li::before {
        content: '';
        position: absolute;
        left: -20px;
        top: 50%;
        transform: translateY(-50%);
        width: 6px;
        height: 6px;
        background: var(--neon-cyan);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--neon-cyan);
        display: none; /* Enable if you want custom bullets */
    }
    
    /* === LABELS === */
    label, .gr-label {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 12px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        text-transform: uppercase;
    }
    
    /* === DROPDOWNS === */
    .gr-dropdown, select {
        background: rgba(5, 2, 15, 0.9) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(139, 92, 246, 0.25) !important;
        cursor: pointer;
    }
    
    .gr-dropdown:hover, select:hover {
        border-color: var(--neon-purple) !important;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
    }
    
    /* === SLIDER - Neon Track === */
    input[type="range"] {
        -webkit-appearance: none !important;
        background: linear-gradient(
            90deg,
            rgba(0, 245, 255, 0.3),
            rgba(168, 85, 247, 0.3)
        ) !important;
        border-radius: 10px !important;
        height: 8px !important;
        border: none !important;
        box-shadow: 
            0 0 15px rgba(139, 92, 246, 0.3),
            inset 0 1px 3px rgba(0, 0, 0, 0.3);
    }
    
    input[type="range"]::-webkit-slider-thumb {
        -webkit-appearance: none !important;
        width: 26px !important;
        height: 26px !important;
        background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple)) !important;
        border-radius: 50% !important;
        cursor: pointer !important;
        box-shadow: 
            0 0 25px rgba(0, 245, 255, 0.6),
            0 0 50px rgba(168, 85, 247, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        border: 3px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.3s ease;
    }
    
    input[type="range"]::-webkit-slider-thumb:hover {
        transform: scale(1.2);
        box-shadow: 
            0 0 35px rgba(0, 245, 255, 0.8),
            0 0 70px rgba(168, 85, 247, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
    }
    
    /* === CHECKBOX & RADIO - Neon Style === */
    input[type="checkbox"], input[type="radio"] {
        accent-color: var(--neon-purple) !important;
        width: 20px;
        height: 20px;
        cursor: pointer;
    }
    
    input[type="checkbox"]:checked, input[type="radio"]:checked {
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.5);
    }
    
    /* === ACCORDION - Collapsible Panels === */
    .gr-accordion {
        background: rgba(10, 5, 30, 0.7) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 20px !important;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .gr-accordion summary {
        padding: 18px 24px !important;
        cursor: pointer;
        transition: all 0.3s ease;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: space-between;
        list-style: none;
    }
    
    .gr-accordion summary::-webkit-details-marker { display: none; }
    .gr-accordion summary::marker { content: ""; }
    
    .gr-accordion summary::after {
        content: "▾";
        opacity: 0.7;
        transform: rotate(-90deg);
        transition: transform 0.3s ease, color 0.3s ease;
        font-weight: 900;
        color: var(--text-secondary);
        font-size: 14px;
    }
    
    .gr-accordion[open] summary::after {
        transform: rotate(0deg);
        color: var(--neon-cyan);
    }
    
    .gr-accordion summary:hover {
        background: rgba(139, 92, 246, 0.1) !important;
    }
    
    .gr-accordion > div, .gr-accordion .wrap {
        padding: 16px 24px 24px;
    }
    
    /* === TABS - Underline Style === */
    .gr-tabs {
        border-bottom: 1px solid rgba(139, 92, 246, 0.2) !important;
        margin-bottom: 20px;
    }
    
    .gr-tab-button {
        background: transparent !important;
        border: none !important;
        color: var(--text-muted) !important;
        padding: 14px 28px !important;
        transition: all 0.3s ease !important;
        position: relative;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
    }
    
    .gr-tab-button::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple));
        border-radius: 3px 3px 0 0;
        transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.5);
    }
    
    .gr-tab-button:hover {
        color: var(--text-primary) !important;
    }
    
    .gr-tab-button.selected {
        color: var(--neon-cyan) !important;
        text-shadow: 0 0 20px rgba(0, 245, 255, 0.4);
    }
    
    .gr-tab-button.selected::after {
        width: 80%;
    }
    
    /* === CUSTOM SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(5, 2, 15, 0.8);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--neon-indigo), var(--neon-purple));
        border-radius: 10px;
        border: 2px solid rgba(5, 2, 15, 0.8);
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--neon-cyan), var(--neon-pink));
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.4);
    }
    
    /* === HEADER AREA === */
    .header-container {
        text-align: center;
        padding: 40px 20px 20px;
        position: relative;
    }
    
    /* === MAIN TITLE - Epic Animated === */
    .gradient-text {
        font-family: 'Outfit', sans-serif !important;
        font-size: 3.2em !important;
        font-weight: 900 !important;
        background: linear-gradient(
            135deg,
            #fff 0%,
            var(--neon-cyan) 15%,
            #fff 25%,
            var(--neon-purple) 40%,
            #fff 50%,
            var(--neon-pink) 65%,
            #fff 75%,
            var(--neon-cyan) 90%,
            #fff 100%
        );
        background-size: 400% auto;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        animation: titleShimmer 10s ease infinite;
        margin: 0;
        filter: 
            drop-shadow(0 0 40px rgba(139, 92, 246, 0.5))
            drop-shadow(0 0 80px rgba(0, 245, 255, 0.3));
        letter-spacing: 2px;
        line-height: 1.2;
    }
    
    @keyframes titleShimmer {
        0% { background-position: 0% center; }
        50% { background-position: 100% center; }
        100% { background-position: 0% center; }
    }
    
    .subtitle {
        color: var(--text-secondary);
        font-size: 1.2em;
        margin-top: 12px;
        font-weight: 400;
        letter-spacing: 3px;
        font-family: 'Space Grotesk', sans-serif;
        text-transform: uppercase;
        opacity: 0.8;
    }
    
    /* === STATUS BADGES === */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 22px;
        margin: 16px auto;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 999px;
        color: var(--aurora-green);
        font-size: 0.9em;
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: 0.5px;
        box-shadow: 
            0 0 30px rgba(16, 185, 129, 0.2),
            inset 0 0 20px rgba(16, 185, 129, 0.05);
    }
    
    .status-badge::before {
        content: '';
        width: 10px;
        height: 10px;
        background: var(--aurora-green);
        border-radius: 50%;
        animation: statusPulse 2s ease infinite;
        box-shadow: 0 0 10px var(--aurora-green);
    }
    
    @keyframes statusPulse {
        0%, 100% { 
            opacity: 1; 
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); 
            transform: scale(1);
        }
        50% { 
            opacity: 0.8; 
            box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); 
            transform: scale(1.1);
        }
    }
    
    /* === OUTPUT BOX === */
    .output-box {
        background: linear-gradient(
            180deg,
            rgba(10, 5, 32, 0.95) 0%,
            rgba(5, 2, 18, 0.98) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 24px !important;
        padding: 32px !important;
        max-height: 75vh !important;
        overflow-y: auto !important;
        position: relative;
        box-shadow: 
            0 15px 50px rgba(0, 0, 0, 0.5),
            inset 0 0 60px rgba(139, 92, 246, 0.03);
    }
    
    .output-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 5%;
        right: 5%;
        height: 2px;
        background: linear-gradient(
            90deg,
            transparent,
            var(--neon-cyan),
            var(--neon-purple),
            var(--neon-pink),
            transparent
        );
        border-radius: 2px;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.5);
    }
    
    /* === LOADING STATES === */
    .wrap.pending {
        background: rgba(139, 92, 246, 0.05) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        animation: loadingPulse 2s ease infinite !important;
        position: relative;
        overflow: hidden;
    }
    
    .wrap.pending::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(139, 92, 246, 0.1),
            transparent
        );
        animation: loadingSweep 1.5s ease infinite;
    }
    
    @keyframes loadingPulse {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.3); 
        }
        50% { 
            box-shadow: 0 0 30px 10px rgba(139, 92, 246, 0.15); 
        }
    }
    
    @keyframes loadingSweep {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .progress-bar, .eta-bar {
        display: none !important;
    }
    
    /* === HIDE GRADIO FOOTER === */
    footer, .gradio-container footer, .built-with-gradio,
    .footer, div[class*="footer"], .gradio-container > footer {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    
    /* === INFO/WARNING/ERROR BOXES === */
    .gr-info {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.1), rgba(0, 245, 255, 0.05)) !important;
        border: 1px solid rgba(0, 245, 255, 0.3) !important;
        border-radius: 16px !important;
        color: var(--neon-cyan) !important;
        box-shadow: 0 0 25px rgba(0, 245, 255, 0.15);
    }
    
    .gr-warning {
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(251, 191, 36, 0.05)) !important;
        border: 1px solid rgba(251, 191, 36, 0.3) !important;
        border-radius: 16px !important;
        color: var(--aurora-yellow) !important;
        box-shadow: 0 0 25px rgba(251, 191, 36, 0.15);
    }
    
    .gr-error {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05)) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 16px !important;
        color: var(--aurora-red) !important;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.15);
    }
    
    /* =========================================================
       ROADMAP DASHBOARD WIDGETS - MAGNIFICENT EDITION
       ========================================================= */
    
    #roadmap_tabs {
        margin-top: 12px;
    }
    
    .card-empty {
        padding: 40px 24px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            rgba(139, 92, 246, 0.08) 0%,
            rgba(99, 102, 241, 0.05) 100%
        );
        border: 1px dashed rgba(139, 92, 246, 0.3);
        color: var(--text-muted);
        text-align: center;
        font-style: italic;
    }
    
    /* === TIMELINE === */
    .timeline-wrap {
        padding: 12px 4px;
    }
    
    .timeline-head {
        font-family: 'Outfit', 'Space Grotesk', sans-serif;
        font-weight: 800;
        font-size: 22px;
        margin: 8px 0 20px 0;
        background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .timeline {
        display: flex;
        flex-direction: column;
        gap: 18px;
        padding-left: 8px;
        position: relative;
    }
    
    .timeline::before {
        content: "";
        position: absolute;
        left: 17px;
        top: 12px;
        bottom: 12px;
        width: 3px;
        background: linear-gradient(
            180deg,
            var(--neon-cyan) 0%,
            var(--neon-purple) 50%,
            var(--neon-pink) 100%
        );
        border-radius: 3px;
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
    }
    
    .t-item {
        display: grid;
        grid-template-columns: 36px 1fr;
        gap: 16px;
        align-items: start;
    }
    
    .t-dot {
        width: 16px;
        height: 16px;
        border-radius: 999px;
        margin-top: 16px;
        background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
        border: 3px solid var(--bg-card);
        box-shadow: 
            0 0 0 4px rgba(139, 92, 246, 0.2),
            0 0 20px rgba(0, 245, 255, 0.5);
        justify-self: center;
        z-index: 1;
        animation: dotPulse 3s ease-in-out infinite;
    }
    
    @keyframes dotPulse {
        0%, 100% { box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2), 0 0 20px rgba(0, 245, 255, 0.5); }
        50% { box-shadow: 0 0 0 8px rgba(139, 92, 246, 0.1), 0 0 30px rgba(0, 245, 255, 0.7); }
    }
    
    .t-card {
        border-radius: 20px;
        padding: 18px 18px 14px;
        background: linear-gradient(
            145deg,
            rgba(15, 8, 40, 0.9) 0%,
            rgba(10, 5, 30, 0.85) 100%
        );
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
    }
    
    .t-card:hover {
        transform: translateX(8px);
        border-color: rgba(0, 245, 255, 0.4);
        box-shadow: 
            0 12px 40px rgba(0, 245, 255, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    
    .t-title {
        font-weight: 800;
        margin-bottom: 10px;
        color: var(--text-primary);
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .t-list {
        margin: 0;
        padding-left: 20px;
        color: var(--text-secondary);
    }
    
    .t-list li {
        margin: 8px 0;
        line-height: 1.5;
    }
    
    .t-list li::marker {
        color: var(--neon-cyan);
    }
    
    /* === PROGRAM CARDS === */
    .prog-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
    }
    
    @media (max-width: 1000px) {
        .prog-grid { grid-template-columns: 1fr; }
    }
    
    .prog-card {
        border-radius: 22px;
        padding: 20px;
        background: linear-gradient(
            155deg,
            rgba(15, 8, 45, 0.92) 0%,
            rgba(10, 5, 30, 0.88) 50%,
            rgba(8, 4, 25, 0.92) 100%
        );
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 
            0 10px 40px rgba(0, 0, 0, 0.35),
            inset 0 1px 0 rgba(255, 255, 255, 0.06);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .prog-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
        opacity: 0;
        transition: opacity 0.3s ease;
    }

        .prog-card:hover::before {
        opacity: 1;
    }
    
    .prog-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: rgba(0, 245, 255, 0.4);
        box-shadow: 
            0 20px 60px rgba(139, 92, 246, 0.25),
            0 0 80px rgba(0, 245, 255, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .prog-title {
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 6px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1em;
    }
    
    .prog-desc {
        color: var(--text-secondary);
        font-size: 14px;
        line-height: 1.45;
    }
    
    .prog-top {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: flex-start;
    }
    
    .prog-uni {
        color: var(--neon-purple-bright);
        font-size: 13px;
        margin-top: 4px;
        font-weight: 500;
    }
    
    .prog-side {
        display: flex;
        flex-direction: column;
        gap: 10px;
        align-items: flex-end;
    }
    
    /* Match Badges */
    .badge {
        padding: 8px 14px;
        border-radius: 999px;
        font-weight: 800;
        font-size: 13px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        background: rgba(255, 255, 255, 0.08);
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: 0.5px;
    }
    
    .badge-good {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(20, 184, 166, 0.15));
        border-color: rgba(16, 185, 129, 0.4);
        color: #34d399;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
    }
    
    .badge-mid {
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.15));
        border-color: rgba(251, 191, 36, 0.4);
        color: #fbbf24;
        box-shadow: 0 0 20px rgba(251, 191, 36, 0.2);
    }
    
    .badge-low {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(244, 63, 94, 0.15));
        border-color: rgba(239, 68, 68, 0.4);
        color: #f87171;
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
    }
    
    .badge-na {
        background: rgba(100, 116, 139, 0.15);
        border-color: rgba(100, 116, 139, 0.3);
        color: var(--text-muted);
    }
    
    .pill {
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        border: 1px solid rgba(139, 92, 246, 0.25);
        background: rgba(139, 92, 246, 0.1);
        color: var(--neon-purple-bright);
        font-weight: 600;
    }
    
    .meta {
        margin-top: 16px;
    }
    
    .meta-row {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        padding: 10px 0;
        border-top: 1px solid rgba(139, 92, 246, 0.1);
        color: var(--text-secondary);
        font-size: 13px;
    }
    
    .meta-row span:first-child {
        color: var(--text-primary);
        font-weight: 700;
    }
    
    .meta-hint {
        padding-top: 12px;
        border-top: 1px solid rgba(139, 92, 246, 0.1);
        color: var(--text-muted);
        font-size: 13px;
        font-style: italic;
    }
    
    /* Program Link Button */
    .link-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-top: 14px;
        padding: 10px 16px;
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.1), rgba(139, 92, 246, 0.1));
        border: 1px solid rgba(0, 245, 255, 0.25);
        color: var(--neon-cyan);
        text-decoration: none;
        font-weight: 700;
        font-size: 13px;
        transition: all 0.3s ease;
    }
    
    .link-btn:hover {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.2), rgba(139, 92, 246, 0.15));
        border-color: var(--neon-cyan);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 245, 255, 0.2);
    }
    
    .link-btn::after {
        content: '→';
        transition: transform 0.3s ease;
    }
    
    .link-btn:hover::after {
        transform: translateX(4px);
    }
    
    /* === PROFILE CARD === */
    .profile-card {
        padding: 20px;
        border-radius: 22px;
        background: linear-gradient(
            145deg,
            rgba(0, 245, 255, 0.08) 0%,
            rgba(139, 92, 246, 0.06) 50%,
            rgba(236, 72, 153, 0.05) 100%
        );
        border: 1px solid rgba(0, 245, 255, 0.2);
        margin-bottom: 16px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    .profile-title {
        font-weight: 800;
        margin-bottom: 14px;
        color: var(--text-primary);
        font-family: 'Space Grotesk', sans-serif;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .profile-title::before {
        content: '✦';
        color: var(--neon-cyan);
        font-size: 16px;
    }
    
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    
    .chip-row-tight {
        margin-top: 12px;
    }
    
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(99, 102, 241, 0.1));
        border: 1px solid rgba(139, 92, 246, 0.25);
        color: var(--text-secondary);
        font-size: 13px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .chip:hover {
        background: rgba(139, 92, 246, 0.2);
        border-color: var(--neon-purple);
        transform: translateY(-2px);
    }
    
    .chip-wide {
        max-width: 100%;
    }
    
    .chip-missing {
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.1));
        border-color: rgba(251, 191, 36, 0.3);
        color: var(--aurora-yellow);
    }
    
    .chip-missing::before {
        content: '⚠';
        font-size: 12px;
    }
    
    /* === CHECKLIST === */
    .chk-wrap {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 6px 4px;
    }
    
    .chk {
        display: flex;
        gap: 14px;
        align-items: flex-start;
        padding: 14px 16px;
        border-radius: 18px;
        background: linear-gradient(
            135deg,
            rgba(15, 8, 40, 0.85) 0%,
            rgba(10, 5, 30, 0.8) 100%
        );
        border: 1px solid rgba(139, 92, 246, 0.15);
        color: var(--text-secondary);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .chk:hover {
        background: rgba(139, 92, 246, 0.1);
        border-color: rgba(139, 92, 246, 0.3);
        transform: translateX(6px);
    }
    
    .chk input[type="checkbox"] {
        transform: scale(1.2) translateY(2px);
        accent-color: var(--neon-cyan);
        cursor: pointer;
    }
    
    .chk input[type="checkbox"]:checked + span {
        color: var(--aurora-green);
        text-decoration: line-through;
        opacity: 0.7;
    }
    
    /* === PHASE BLOCKS === */
    .phase-wrap {
        display: flex;
        flex-direction: column;
        gap: 18px;
    }
    
    .phase {
        border-radius: 22px;
        padding: 18px 18px 12px;
        background: linear-gradient(
            155deg,
            rgba(15, 8, 45, 0.9) 0%,
            rgba(10, 5, 30, 0.85) 100%
        );
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        position: relative;
        overflow: hidden;
    }
    
    .phase::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
        border-radius: 4px 0 0 4px;
    }
    
    .phase-title {
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 14px;
        font-family: 'Space Grotesk', sans-serif;
        padding-left: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .phase-duration {
        font-size: 12px;
        color: var(--neon-cyan);
        font-weight: 600;
        padding: 4px 10px;
        background: rgba(0, 245, 255, 0.1);
        border-radius: 999px;
        border: 1px solid rgba(0, 245, 255, 0.2);
    }
    
    .phase-why {
        font-size: 13px;
        color: var(--text-muted);
        font-style: italic;
        margin-bottom: 12px;
        padding-left: 8px;
        border-left: 2px solid rgba(139, 92, 246, 0.3);
        margin-left: 8px;
    }
    
    /* === COMPARE TABLE === */
    .table-wrap {
        overflow-x: auto;
        border-radius: 18px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        background: rgba(10, 5, 30, 0.8);
    }
    
    table.cmp {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    
    table.cmp th {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.15));
        color: var(--neon-cyan);
        padding: 16px;
        text-align: left;
        font-weight: 700;
        font-family: 'Space Grotesk', sans-serif;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 1px;
        border-bottom: 1px solid rgba(0, 245, 255, 0.2);
    }
    
    table.cmp td {
        padding: 14px 16px;
        border-bottom: 1px solid rgba(139, 92, 246, 0.1);
        transition: background 0.3s ease;
    }
    
    table.cmp tr:hover td {
        background: rgba(139, 92, 246, 0.08);
    }
    
    table.cmp tr:last-child td {
        border-bottom: none;
    }
    
    /* === INTEREST PRESET BUTTONS === */
    .chip-btn button {
        padding: 10px 16px !important;
        border-radius: 999px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(99, 102, 241, 0.1)) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .chip-btn button:hover {
        background: rgba(139, 92, 246, 0.25) !important;
        border-color: var(--neon-purple) !important;
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.25) !important;
    }
    
    /* === SIDEBAR TOGGLE === */
    #sidebar_toggle_btn {
        width: fit-content;
        min-width: 160px;
        padding: 10px 16px;
        border-radius: 16px;
        margin: 4px 0 14px 0;
    }
    
    #sidebar_toggle_btn button {
        font-weight: 700;
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.1), rgba(139, 92, 246, 0.1)) !important;
        border: 1px solid rgba(0, 245, 255, 0.25) !important;
    }
    
    #sidebar_toggle_btn button:hover {
        background: rgba(0, 245, 255, 0.15) !important;
        border-color: var(--neon-cyan) !important;
    }
    
    /* === LAYOUT: Dashboard Row === */
    #dash_row {
        display: flex !important;
        gap: 20px;
        align-items: stretch;
    }
    
    #sidebar_col {
        flex: 0 0 380px;
        max-width: 440px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    #main_col {
        flex: 1 1 auto;
        min-width: 0;
    }
    
    #sidebar_col[style*="display: none"] + #main_col {
        flex: 1 1 100% !important;
        max-width: 100% !important;
    }
    
    /* === WIZARD POLISH === */
    #inputs_view h2, #inputs_view h3 {
        letter-spacing: 0.3px;
    }
    
    /* === GLASS OVERRIDES === */
    .glass-panel {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    
    .glass-input input,
    .glass-input textarea,
    .glass-input select {
        background: rgba(5, 2, 18, 0.85) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        color: var(--text-primary) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }
    
    .glass-input input:focus,
    .glass-input textarea:focus,
    .glass-input select:focus {
        outline: none !important;
        border-color: var(--neon-cyan) !important;
        box-shadow: 0 0 0 3px rgba(0, 245, 255, 0.1) !important;
    }
    
    /* Remove Gradio default borders */
    .gradio-container .wrap,
    .gradio-container .block,
    .gradio-container .gr-panel,
    .gradio-container .gr-box,
    .gradio-container .gr-form,
    .gradio-container .gr-accordion,
    .gradio-container .gr-group,
    .gradio-container .form,
    .gradio-container .container {
        border: none !important;
        outline: none !important;
    }
    
    .gradio-container button:focus,
    .gradio-container button:focus-visible {
        outline: none !important;
    }
    
    .gradio-container hr {
        border: 0 !important;
        height: 2px !important;
        background: linear-gradient(90deg, transparent, var(--neon-purple), transparent) !important;
        margin: 20px 0 !important;
    }
    
    .gradio-container .markdown,
    .gradio-container .prose {
        border: none !important;
        box-shadow: none !important;
    }
    
    /* === FLOATING ACTION ELEMENTS === */
    .floating-orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.3;
        pointer-events: none;
        z-index: 0;
        animation: orbFloat 20s ease-in-out infinite;
    }
    
    @keyframes orbFloat {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(30px, -20px) scale(1.1); }
        50% { transform: translate(-20px, 30px) scale(0.9); }
        75% { transform: translate(20px, 20px) scale(1.05); }
    }
    
    /* === SUCCESS ANIMATION === */
    @keyframes successPop {
        0% { transform: scale(0.8); opacity: 0; }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .success-message {
        animation: successPop 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* === RESPONSIVE DESIGN === */
    @media (max-width: 1200px) {
        #sidebar_col {
            flex: 0 0 320px;
            max-width: 360px;
        }
        
        #sidebar_toggle_btn {
            min-width: 140px;
            padding: 8px 12px;
        }
    }
    
    @media (max-width: 768px) {
        .gradient-text {
            font-size: 2.2em !important;
        }
        
        .subtitle {
            font-size: 1em;
            letter-spacing: 2px;
        }
        
        .gr-panel, .gr-box {
            border-radius: 18px !important;
            padding: 18px !important;
        }
        
        .gr-markdown, .gr-html {
            padding: 24px !important;
            border-radius: 18px !important;
        }
        
        button {
            padding: 14px 24px !important;
        }
        
        .header-container {
            padding: 25px 15px 15px;
        }
        
        .prog-grid {
            grid-template-columns: 1fr;
        }
        
        #dash_row {
            flex-direction: column;
        }
        
        #sidebar_col {
            flex: 1 1 auto;
            max-width: 100%;
        }
    }
    
    @media (max-width: 480px) {
        .gradient-text {
            font-size: 1.8em !important;
            letter-spacing: 1px;
        }
        
        .subtitle {
            font-size: 0.9em;
            letter-spacing: 1.5px;
        }
        
        .gr-markdown h1 { font-size: 1.5em !important; }
        .gr-markdown h2 { font-size: 1.3em !important; }
        
        .t-item {
            grid-template-columns: 28px 1fr;
            gap: 12px;
        }
        
        .t-card {
            padding: 14px;
        }
        
        .prog-card {
            padding: 16px;
        }
        
        .chip {
            padding: 6px 12px;
            font-size: 12px;
        }
    }
    
    /* === ENTRANCE ANIMATIONS === */
    .gr-panel, .gr-box, .gr-form {
        animation: panelEnter 0.7s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    @keyframes panelEnter {
        from {
            opacity: 0;
            transform: translateY(30px) scale(0.98);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    /* Staggered animation */
    .gr-panel:nth-child(1) { animation-delay: 0.05s; }
    .gr-panel:nth-child(2) { animation-delay: 0.1s; }
    .gr-panel:nth-child(3) { animation-delay: 0.15s; }
    .gr-panel:nth-child(4) { animation-delay: 0.2s; }
    .gr-panel:nth-child(5) { animation-delay: 0.25s; }
    
    /* === SPECIAL EFFECTS === */
    
    /* Glowing cursor for inputs */
    textarea:focus, input[type="text"]:focus {
        caret-color: var(--neon-cyan);
    }
    
    /* Selection highlight */
    ::selection {
        background: rgba(139, 92, 246, 0.4);
        color: #fff;
    }
    
    ::-moz-selection {
        background: rgba(139, 92, 246, 0.4);
        color: #fff;
    }
    
    /* Focus visible for accessibility */
    *:focus-visible {
        outline: 2px solid var(--neon-cyan) !important;
        outline-offset: 2px;
    }
    
    /* Print styles */
    @media print {
        .gradio-container::before,
        .gradio-container::after {
            display: none !important;
        }
        
        .gr-panel, .gr-box {
            background: #fff !important;
            color: #000 !important;
            border: 1px solid #ccc !important;
            box-shadow: none !important;
        }
    }

    /* === SLIDER NUMBER INPUT FIX === */
    input[type="number"],
    .gr-slider input[type="number"],
    .gr-number input,
    .gr-box input[type="number"],
    div[data-testid="number-input"] input,
    .gr-slider-container input {
        background: linear-gradient(
            135deg,
            rgba(15, 8, 40, 0.9) 0%,
            rgba(10, 5, 30, 0.85) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 14px !important;
        color: var(--neon-cyan) !important;
        font-family: 'Space Grotesk', 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        text-align: center !important;
        padding: 12px 16px !important;
        min-width: 80px !important;
        box-shadow: 
            inset 0 2px 8px rgba(0, 0, 0, 0.4),
            0 0 20px rgba(139, 92, 246, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    input[type="number"]:focus,
    .gr-slider input[type="number"]:focus {
        border-color: var(--neon-cyan) !important;
        box-shadow: 
            0 0 0 3px rgba(0, 245, 255, 0.15),
            0 0 30px rgba(0, 245, 255, 0.2),
            inset 0 2px 8px rgba(0, 0, 0, 0.4) !important;
        color: var(--neon-cyan) !important;
    }
    
    /* Remove default spinner buttons */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
    }
    
    input[type="number"] {
        -moz-appearance: textfield !important;
    }
    
    /* Slider container layout fix */
    .gr-slider, 
    div[class*="slider"] {
        display: flex !important;
        align-items: center !important;
        gap: 16px !important;
    }
    
    /* The reset/clear button next to number input */
    .gr-slider button,
    .gr-number button,
    div[data-testid="number-input"] button {
        background: linear-gradient(
            135deg,
            rgba(139, 92, 246, 0.2) 0%,
            rgba(99, 102, 241, 0.15) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 12px !important;
        color: var(--neon-purple-bright) !important;
        padding: 10px 12px !important;
        min-width: 44px !important;
        height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease !important;
    }
    
    .gr-slider button:hover,
    .gr-number button:hover {
        background: rgba(139, 92, 246, 0.3) !important;
        border-color: var(--neon-purple) !important;
        transform: scale(1.05) !important;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3) !important;
    }
    
    /* Number input wrapper/container */
    .gr-number,
    div[data-testid="number-input"],
    .gr-slider > div {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        background: transparent !important;
        border: none !important;
    }
    
    /* Make the input + button group look cohesive */
    .gr-number > div,
    .gr-slider > div > div {
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
        background: linear-gradient(
            135deg,
            rgba(10, 5, 30, 0.8) 0%,
            rgba(15, 8, 40, 0.7) 100%
        ) !important;
        border: 1px solid rgba(139, 92, 246, 0.25) !important;
        border-radius: 16px !important;
        padding: 4px !important;
        box-shadow: 
            0 4px 15px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Slider label styling */
    .gr-slider label,
    .gr-number label {
        color: var(--text-secondary) !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* Slider min/max labels */
    .gr-slider span,
    .gr-slider .min-max {
        color: var(--text-muted) !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    """