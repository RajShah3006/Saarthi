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

    """