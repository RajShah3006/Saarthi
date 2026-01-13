'''
# utils/dashboard_renderer.py
import html
from typing import Dict, List, Any


def _esc(s: str) -> str:
    return html.escape(str(s or ""), quote=True)

def render_program_cards(programs: List[Dict[str, Any]]) -> str:
    if not programs:
        return "<div class='card-empty'>No programs yet. Generate a roadmap to see program cards.</div>"

    cards = []
    for p in programs[:12]:
        name = p.get("program_name", "")
        uni = p.get("university_name", "")
        pct = p.get("match_percent") or 0
        coop = bool(p.get("co_op_available", False))
        adm = p.get("admission_average", "") or "Check website"
        pre = p.get("prerequisites", "") or "Check website"
        miss = p.get("missing_prereqs", []) or []
        url = p.get("program_url", "") or ""

        badge_cls = "badge-low"
        if pct >= 85:
            badge_cls = "badge-good"
        elif pct >= 75:
            badge_cls = "badge-mid"

        miss_chips = ""
        if miss:
            chips = "".join([f"<span class='chip chip-missing'>⚠️ {_esc(x)}</span>" for x in miss[:6]])
            miss_chips = f"<div class='chip-row chip-row-tight'>{chips}</div>"

        meta_rows = []
        meta_rows.append(f"<div class='meta-row'><span>📝 Admission</span><span>{_esc(adm)}</span></div>")
        meta_rows.append(f"<div class='meta-row'><span>📚 Prereqs</span><span>{_esc(pre)}</span></div>")

        coop_html = "<span class='pill'>✅ Co-op</span>" if coop else ""
        link_html = (
            f"<a class='link-btn' href='{_esc(url)}' target='_blank' rel='noopener'>View Program</a>"
            if url
            else ""
        )

        cards.append(f"""
        <div class="prog-card">
          <div class="prog-top">
            <div class="prog-main">
              <div class="prog-title">{_esc(name)}</div>
              <div class="prog-uni">{_esc(uni)}</div>
            </div>
            <div class="prog-side">
              <div class="badge {badge_cls}">🌟 {_esc(pct)}%</div>
              {coop_html}
            </div>
          </div>
          {miss_chips}
          <div class="meta">
            {''.join(meta_rows)}
            {link_html}
          </div>
        </div>
        """)

    return f"<div class='prog-grid'>{''.join(cards)}</div>"


def render_checklist(sections: List[Dict[str, Any]]) -> str:
    if not sections:
        return "<div class='card-empty'>No checklist yet.</div>"

    blocks = []
    for sec in sections[:8]:
        title = sec.get("title", "Checklist")
        items = sec.get("items", []) or []
        checks = "".join(
            f"<label class='chk'><input type='checkbox'/> <span>{_esc(it)}</span></label>"
            for it in items[:12]
        )
        blocks.append(f"""
          <div class="phase">
            <div class="phase-title">{_esc(title)}</div>
            <div class="chk-wrap">{checks}</div>
          </div>
        """)

    return f"<div class='phase-wrap'>{''.join(blocks)}</div>"

def render_timeline(profile: Dict[str, Any], timeline_events: List[Dict[str, Any]]) -> str:
    """Enhanced timeline with mode awareness"""
    
    # Profile chips
    chips = []
    if profile.get("interest"):
        chips.append(f"<span class='chip'>🎯 {_esc(profile['interest'][:50])}</span>")
    if profile.get("grade"):
        g = profile["grade"]
        if profile.get("avg") is not None:
            g = f"{g} • {profile['avg']}%"
        chips.append(f"<span class='chip'>📊 {_esc(g)}</span>")
    if profile.get("subjects"):
        chips.append(f"<span class='chip chip-wide'>📚 {_esc(profile['subjects'][:60])}</span>")
    
    # Mode badge
    mode = profile.get("mode", "")
    mode_info = profile.get("mode_info", {})
    mode_badge = ""
    if mode and mode_info:
        mode_color = mode_info.get("color", "#3b82f6")
        mode_emoji = mode_info.get("emoji", "📋")
        mode_label = mode_info.get("label", "Your Plan")
        mode_badge = f"""
        <div class="mode-badge" style="background: {mode_color}; color: white; padding: 6px 14px; border-radius: 16px; display: inline-block; margin-bottom: 12px;">
            {mode_emoji} {_esc(mode_label)}
        </div>
        """
    
    header = ""
    if chips or mode_badge:
        header = f"""
        <div class="profile-card">
            {mode_badge}
            <div class="profile-title">Your Profile</div>
            <div class="chip-row">{''.join(chips)}</div>
        </div>
        """

    if not timeline_events:
        return f"<div class='timeline-wrap'>{header}<div class='card-empty'>Generate a roadmap to see a timeline.</div></div>"

    items_html = []
    for i, ev in enumerate(timeline_events[:10]):
        date_str = ev.get("date", "")
        title = ev.get("title", "")
        items = ev.get("items", []) or []
        
        # Categorized sections (if available)
        academic = ev.get("academic", [])
        portfolio = ev.get("portfolio", [])
        exploration = ev.get("exploration", [])
        contingencies = ev.get("contingencies", [])
        checkpoint = ev.get("checkpoint", {})
        
        sections_html = ""
        
        # Render categorized sections if available
        if academic:
            sections_html += _render_timeline_section("📚 Academics", academic, "#e0f2fe")
        if portfolio:
            sections_html += _render_timeline_section("🛠️ Portfolio", portfolio, "#fef3c7")
        if exploration:
            sections_html += _render_timeline_section("🔍 Explore", exploration, "#ede9fe")
        if contingencies:
            sections_html += _render_timeline_section("⚠️ Contingencies", contingencies, "#fee2e2")
        
        # Checkpoint badge
        checkpoint_html = ""
        if checkpoint:
            target_avg = checkpoint.get("target_avg")
            prereqs_status = checkpoint.get("prereqs_status", "")
            if target_avg or prereqs_status:
                checkpoint_html = f"""
                <div class="checkpoint-badge" style="background: #f0fdf4; border-left: 3px solid #22c55e; padding: 8px 12px; margin-top: 8px; border-radius: 4px; font-size: 13px;">
                    📊 <strong>Checkpoint:</strong>
                    {f'Target: {target_avg}%' if target_avg else ''}
                    {f' | {_esc(prereqs_status)}' if prereqs_status else ''}
                </div>
                """
        
        # Fallback to flat items if no categories
        if not sections_html and items:
            li = "".join([f"<li>{_esc(x)}</li>" for x in items[:8]])
            sections_html = f"<ul class='t-list'>{li}</ul>"
        
        items_html.append(f"""
        <div class="t-item">
          <div class="t-dot"></div>
          <div class="t-card">
            <div class="t-title">{_esc(date_str)} — {_esc(title)}</div>
            {sections_html}
            {checkpoint_html}
          </div>
        </div>
        """)

    return f"""
    <div class="timeline-wrap">
      {header}
      <div class="timeline-head">Your Improvement Timeline</div>
      <div class="timeline">{''.join(items_html)}</div>
    </div>
    """


def _render_timeline_section(title: str, items: List[str], bg_color: str) -> str:
    """Render a categorized section within a timeline event"""
    if not items:
        return ""
    
    item_html = "".join([f"<li style='margin: 2px 0;'>{_esc(x)}</li>" for x in items[:5]])
    
    return f"""
    <div class="t-section" style="background: {bg_color}; padding: 8px 12px; border-radius: 8px; margin: 8px 0;">
        <strong style="font-size: 13px;">{title}</strong>
        <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 13px;">
            {item_html}
        </ul>
    </div>
    """


def render_plan_strength(strength_data: Dict[str, Any]) -> str:
    """Render the plan strength score card"""
    total = strength_data.get("total", {}).get("score", 0)
    
    if total >= 80:
        color = "#22c55e"
        label = "Strong Plan"
    elif total >= 60:
        color = "#3b82f6"
        label = "Good Foundation"
    elif total >= 40:
        color = "#f97316"
        label = "Needs Work"
    else:
        color = "#ef4444"
        label = "Significant Gaps"
    
    breakdown_rows = ""
    for key in ["academics", "prerequisites", "portfolio", "extracurriculars", "feasibility"]:
        data = strength_data.get(key, {})
        if data:
            score = data.get("score", 0)
            max_score = data.get("max", 20)
            breakdown_rows += f"""
            <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #e5e7eb;">
                <span style="text-transform: capitalize;">{key}</span>
                <span><strong>{score}</strong>/{max_score}</span>
            </div>
            """
    
    return f"""
    <div class="strength-card" style="border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; background: white;">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
            <div style="font-size: 40px; font-weight: bold; color: {color};">{total}</div>
            <div>
                <div style="font-size: 14px; color: #6b7280;">Plan Strength Score</div>
                <div style="font-weight: 600; color: {color};">{label}</div>
            </div>
        </div>
        <div style="font-size: 14px;">
            {breakdown_rows}
        </div>
    </div>
    """


def render_quick_wins(quick_wins: List[str]) -> str:
    """Render quick wins as actionable cards"""
    if not quick_wins:
        return ""
    
    cards = ""
    for i, win in enumerate(quick_wins[:3], 1):
        cards += f"""
        <div style="display: flex; align-items: flex-start; gap: 12px; padding: 12px 16px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e; margin-bottom: 8px;">
            <span style="font-weight: bold; color: #22c55e; font-size: 18px;">{i}</span>
            <span style="font-size: 14px;">{_esc(win)}</span>
        </div>
        """
    
    return f"""
    <div class="quick-wins" style="margin: 16px 0;">
        <h4 style="margin-bottom: 12px; font-size: 16px;">⚡ Quick Wins (Do This Week)</h4>
        {cards}
    </div>
    """


def render_improvements(improvements: List[str]) -> str:
    """Render improvement suggestions"""
    if not improvements:
        return ""
    
    items = "".join([f"<li style='margin: 6px 0;'>{_esc(imp)}</li>" for imp in improvements[:3]])
    
    return f"""
    <div class="improvements" style="margin: 16px 0; padding: 16px; background: #fef3c7; border-radius: 8px;">
        <h4 style="margin: 0 0 12px 0; font-size: 16px;">📈 To Raise Your Score</h4>
        <ol style="margin: 0; padding-left: 20px; font-size: 14px;">
            {items}
        </ol>
    </div>
    """
'''
# utils/dashboard_renderer.py
import html
from typing import Dict, List, Any


def _esc(s: str) -> str:
    """Escape HTML entities"""
    return html.escape(str(s or ""), quote=True)


# =============================================================================
# PROGRAM CARDS (unchanged from your original)
# =============================================================================

def render_program_cards(programs: List[Dict[str, Any]]) -> str:
    if not programs:
        return "<div class='card-empty'>No programs yet. Generate a roadmap to see program cards.</div>"

    cards = []
    for p in programs[:12]:
        name = p.get("program_name", "")
        uni = p.get("university_name", "")
        pct = p.get("match_percent") or 0
        coop = bool(p.get("co_op_available", False))
        adm = p.get("admission_average", "") or "Check website"
        pre = p.get("prerequisites", "") or "Check website"
        miss = p.get("missing_prereqs", []) or []
        url = p.get("program_url", "") or ""

        badge_cls = "badge-low"
        if pct >= 85:
            badge_cls = "badge-good"
        elif pct >= 75:
            badge_cls = "badge-mid"

        miss_chips = ""
        if miss:
            chips = "".join([f"<span class='chip chip-missing'>⚠️ {_esc(x)}</span>" for x in miss[:6]])
            miss_chips = f"<div class='chip-row chip-row-tight'>{chips}</div>"

        meta_rows = []
        meta_rows.append(f"<div class='meta-row'><span>📝 Admission</span><span>{_esc(adm)}</span></div>")
        meta_rows.append(f"<div class='meta-row'><span>📚 Prereqs</span><span>{_esc(pre)}</span></div>")

        coop_html = "<span class='pill'>✅ Co-op</span>" if coop else ""
        link_html = (
            f"<a class='link-btn' href='{_esc(url)}' target='_blank' rel='noopener'>View Program</a>"
            if url
            else ""
        )

        cards.append(f"""
        <div class="prog-card">
          <div class="prog-top">
            <div class="prog-main">
              <div class="prog-title">{_esc(name)}</div>
              <div class="prog-uni">{_esc(uni)}</div>
            </div>
            <div class="prog-side">
              <div class="badge {badge_cls}">🌟 {_esc(pct)}%</div>
              {coop_html}
            </div>
          </div>
          {miss_chips}
          <div class="meta">
            {''.join(meta_rows)}
            {link_html}
          </div>
        </div>
        """)

    return f"<div class='prog-grid'>{''.join(cards)}</div>"


# =============================================================================
# CHECKLIST (unchanged from your original)
# =============================================================================

def render_checklist(sections: List[Dict[str, Any]]) -> str:
    if not sections:
        return "<div class='card-empty'>No checklist yet.</div>"

    blocks = []
    for sec in sections[:8]:
        title = sec.get("title", "Checklist")
        items = sec.get("items", []) or []
        checks = "".join(
            f"<label class='chk'><input type='checkbox'/> <span>{_esc(it)}</span></label>"
            for it in items[:12]
        )
        blocks.append(f"""
          <div class="phase">
            <div class="phase-title">{_esc(title)}</div>
            <div class="chk-wrap">{checks}</div>
          </div>
        """)

    return f"<div class='phase-wrap'>{''.join(blocks)}</div>"


# =============================================================================
# TIMELINE (ENHANCED with mode support)
# =============================================================================

def _render_timeline_section(title: str, items: List[str], bg_color: str) -> str:
    """Render a categorized section within a timeline event"""
    if not items:
        return ""
    
    item_html = "".join([f"<li style='margin: 2px 0;'>{_esc(x)}</li>" for x in items[:5]])
    
    return f"""
    <div class="t-section" style="background: {bg_color}; padding: 8px 12px; border-radius: 8px; margin: 8px 0;">
        <strong style="font-size: 13px;">{title}</strong>
        <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 13px;">
            {item_html}
        </ul>
    </div>
    """


def render_timeline(profile: Dict[str, Any], timeline_events: List[Dict[str, Any]]) -> str:
    """
    Enhanced timeline renderer with mode awareness.
    
    Supports both old format (just items) and new format (academic, portfolio, exploration, etc.)
    """
    
    # Build profile chips
    chips = []
    if profile.get("interest"):
        interest_display = profile["interest"]
        if len(interest_display) > 50:
            interest_display = interest_display[:47] + "..."
        chips.append(f"<span class='chip'>🎯 {_esc(interest_display)}</span>")
    
    if profile.get("grade"):
        g = profile["grade"]
        if profile.get("avg") is not None:
            g = f"{g} • {profile['avg']}%"
        chips.append(f"<span class='chip'>📊 {_esc(g)}</span>")
    
    if profile.get("subjects"):
        subjects_display = profile["subjects"]
        if len(subjects_display) > 60:
            subjects_display = subjects_display[:57] + "..."
        chips.append(f"<span class='chip chip-wide'>📚 {_esc(subjects_display)}</span>")

    # Mode badge (NEW)
    mode = profile.get("mode", "")
    mode_info = profile.get("mode_info", {})
    mode_badge = ""
    
    if mode and mode_info:
        mode_color = mode_info.get("color", "#3b82f6")
        mode_emoji = mode_info.get("emoji", "📋")
        mode_label = mode_info.get("label", "Your Plan")
        mode_desc = mode_info.get("description", "")
        
        mode_badge = f"""
        <div class="mode-badge" style="
            background: {mode_color}; 
            color: white; 
            padding: 8px 16px; 
            border-radius: 20px; 
            display: inline-block; 
            margin-bottom: 12px;
            font-weight: 500;
            font-size: 14px;
        ">
            {mode_emoji} {_esc(mode_label)}
        </div>
        """
        
        if mode_desc:
            mode_badge += f"""
            <div style="font-size: 13px; color: #6b7280; margin-bottom: 12px; font-style: italic;">
                {_esc(mode_desc)}
            </div>
            """

    # Build header
    header = ""
    if chips or mode_badge:
        header = f"""
        <div class="profile-card">
            {mode_badge}
            <div class="profile-title">Your Profile</div>
            <div class="chip-row">{''.join(chips)}</div>
        </div>
        """

    # Empty state
    if not timeline_events:
        return f"""
        <div class='timeline-wrap'>
            {header}
            <div class='card-empty'>Generate a roadmap to see a timeline.</div>
        </div>
        """

    # Build timeline items
    items_html = []
    for i, ev in enumerate(timeline_events[:10]):
        date_str = ev.get("date", "")
        title = ev.get("title", "")
        
        # Get categorized sections (new format)
        academic = ev.get("academic", [])
        portfolio = ev.get("portfolio", [])
        exploration = ev.get("exploration", [])
        contingencies = ev.get("contingencies", [])
        checkpoint = ev.get("checkpoint", {})
        
        # Get flat items (old format / fallback)
        items = ev.get("items", []) or []
        
        sections_html = ""
        
        # Render categorized sections if available (new format)
        if academic:
            sections_html += _render_timeline_section("📚 Academics", academic, "#e0f2fe")
        if portfolio:
            sections_html += _render_timeline_section("🛠️ Portfolio", portfolio, "#fef3c7")
        if exploration:
            sections_html += _render_timeline_section("🔍 Explore", exploration, "#ede9fe")
        if contingencies:
            sections_html += _render_timeline_section("⚠️ If Needed", contingencies, "#fee2e2")
        
        # Checkpoint badge (new format)
        checkpoint_html = ""
        if checkpoint:
            target_avg = checkpoint.get("target_avg")
            prereqs_status = checkpoint.get("prereqs_status", "")
            portfolio_milestone = checkpoint.get("portfolio_milestone", "")
            
            if target_avg or prereqs_status or portfolio_milestone:
                checkpoint_parts = []
                if target_avg:
                    checkpoint_parts.append(f"Target: {target_avg}%")
                if prereqs_status:
                    checkpoint_parts.append(_esc(prereqs_status))
                if portfolio_milestone:
                    checkpoint_parts.append(_esc(portfolio_milestone))
                
                checkpoint_html = f"""
                <div class="checkpoint-badge" style="
                    background: #f0fdf4; 
                    border-left: 3px solid #22c55e; 
                    padding: 8px 12px; 
                    margin-top: 8px; 
                    border-radius: 4px; 
                    font-size: 13px;
                ">
                    📊 <strong>Checkpoint:</strong> {' | '.join(checkpoint_parts)}
                </div>
                """
        
        # Fallback to flat items if no categories present (old format)
        if not sections_html and items:
            li = "".join([f"<li>{_esc(x)}</li>" for x in items[:8]])
            sections_html = f"<ul class='t-list'>{li}</ul>"
        
        # Build the timeline item
        items_html.append(f"""
        <div class="t-item">
          <div class="t-dot"></div>
          <div class="t-card">
            <div class="t-title">{_esc(date_str)} — {_esc(title)}</div>
            {sections_html}
            {checkpoint_html}
          </div>
        </div>
        """)

    # Determine timeline header based on mode
    timeline_header = "Your Improvement Timeline"
    if mode == "trajectory":
        timeline_header = "🎯 Your Path to Target Programs"
    elif mode == "exploration":
        timeline_header = "🔍 Your Exploration Timeline"
    elif mode == "catchup":
        timeline_header = "🚀 Your Recovery Timeline"

    return f"""
    <div class="timeline-wrap">
      {header}
      <div class="timeline-head">{timeline_header}</div>
      <div class="timeline">{''.join(items_html)}</div>
    </div>
    """


# =============================================================================
# NEW: PLAN STRENGTH CARD
# =============================================================================

def render_plan_strength(strength_data: Dict[str, Any]) -> str:
    """
    Render the plan strength score card.
    
    Expected input:
    {
        "academics": {"score": 15, "max": 20},
        "prerequisites": {"score": 18, "max": 20},
        "portfolio": {"score": 10, "max": 20},
        "extracurriculars": {"score": 12, "max": 20},
        "feasibility": {"score": 16, "max": 20},
        "total": {"score": 71, "max": 100}
    }
    """
    if not strength_data:
        return ""
    
    # Get total score
    total_data = strength_data.get("total", {})
    total = total_data.get("score", 0) if isinstance(total_data, dict) else 0
    
    # Determine color and label
    if total >= 80:
        color = "#22c55e"  # green
        label = "Strong Plan"
        emoji = "🌟"
    elif total >= 60:
        color = "#3b82f6"  # blue
        label = "Good Foundation"
        emoji = "👍"
    elif total >= 40:
        color = "#f97316"  # orange
        label = "Needs Work"
        emoji = "📈"
    else:
        color = "#ef4444"  # red
        label = "Significant Gaps"
        emoji = "⚠️"
    
    # Build breakdown rows
    breakdown_rows = ""
    categories = ["academics", "prerequisites", "portfolio", "extracurriculars", "feasibility"]
    category_labels = {
        "academics": "📚 Academics",
        "prerequisites": "✅ Prerequisites",
        "portfolio": "🛠️ Portfolio",
        "extracurriculars": "🎯 Extracurriculars",
        "feasibility": "⏱️ Feasibility"
    }
    
    for key in categories:
        data = strength_data.get(key, {})
        if data and isinstance(data, dict):
            score = data.get("score", 0)
            max_score = data.get("max", 20)
            pct = (score / max_score * 100) if max_score > 0 else 0
            
            # Color the bar based on percentage
            bar_color = "#22c55e" if pct >= 80 else "#3b82f6" if pct >= 60 else "#f97316" if pct >= 40 else "#ef4444"
            
            breakdown_rows += f"""
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-size: 13px;">{category_labels.get(key, key.title())}</span>
                    <span style="font-size: 13px; font-weight: 500;">{score}/{max_score}</span>
                </div>
                <div style="background: #e5e7eb; border-radius: 4px; height: 6px; overflow: hidden;">
                    <div style="background: {bar_color}; width: {pct}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """
    
    return f"""
    <div class="strength-card" style="
        border: 1px solid #e5e7eb; 
        border-radius: 12px; 
        padding: 20px; 
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px;">
            <div style="
                font-size: 48px; 
                font-weight: bold; 
                color: {color};
                line-height: 1;
            ">{total}</div>
            <div>
                <div style="font-size: 14px; color: #6b7280;">Plan Strength Score</div>
                <div style="font-weight: 600; color: {color}; font-size: 16px;">{emoji} {label}</div>
            </div>
        </div>
        <div style="border-top: 1px solid #e5e7eb; padding-top: 16px;">
            {breakdown_rows}
        </div>
    </div>
    """


# =============================================================================
# NEW: QUICK WINS CARD
# =============================================================================

def render_quick_wins(quick_wins: List[str]) -> str:
    """
    Render quick wins as actionable cards.
    
    Expected input: ["Do this first", "Then this", "Finally this"]
    """
    if not quick_wins:
        return ""
    
    cards = ""
    for i, win in enumerate(quick_wins[:3], 1):
        cards += f"""
        <div style="
            display: flex; 
            align-items: flex-start; 
            gap: 12px; 
            padding: 12px 16px; 
            background: #f0fdf4; 
            border-radius: 8px; 
            border-left: 4px solid #22c55e; 
            margin-bottom: 8px;
        ">
            <span style="
                font-weight: bold; 
                color: #22c55e; 
                font-size: 20px;
                line-height: 1.2;
            ">{i}</span>
            <span style="font-size: 14px; line-height: 1.4;">{_esc(win)}</span>
        </div>
        """
    
    return f"""
    <div class="quick-wins" style="margin: 16px 0;">
        <h4 style="
            margin: 0 0 12px 0; 
            font-size: 16px; 
            font-weight: 600;
        ">⚡ Quick Wins (Do This Week)</h4>
        {cards}
    </div>
    """


# =============================================================================
# NEW: IMPROVEMENTS CARD
# =============================================================================

def render_improvements(improvements: List[str]) -> str:
    """
    Render improvement suggestions.
    
    Expected input: ["Improvement 1", "Improvement 2", "Improvement 3"]
    """
    if not improvements:
        return ""
    
    items = "".join([
        f"<li style='margin: 8px 0; line-height: 1.4;'>{_esc(imp)}</li>" 
        for imp in improvements[:3]
    ])
    
    return f"""
    <div class="improvements" style="
        margin: 16px 0; 
        padding: 16px 20px; 
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-radius: 12px;
        border-left: 4px solid #f59e0b;
    ">
        <h4 style="
            margin: 0 0 12px 0; 
            font-size: 16px; 
            font-weight: 600;
            color: #92400e;
        ">📈 To Raise Your Score</h4>
        <ol style="
            margin: 0; 
            padding-left: 20px; 
            font-size: 14px;
            color: #78350f;
        ">
            {items}
        </ol>
    </div>
    """


# =============================================================================
# NEW: COMBINED DASHBOARD HEADER
# =============================================================================

def render_dashboard_header(
    mode_info: Dict[str, Any],
    plan_strength: int,
    quick_wins: List[str]
) -> str:
    """
    Render a combined dashboard header with mode, strength, and quick wins.
    Useful for showing at the top of the timeline tab.
    """
    
    # Mode badge
    mode_badge = ""
    if mode_info:
        color = mode_info.get("color", "#3b82f6")
        emoji = mode_info.get("emoji", "📋")
        label = mode_info.get("label", "Your Plan")
        desc = mode_info.get("description", "")
        
        mode_badge = f"""
        <div style="
            background: {color}; 
            color: white; 
            padding: 10px 20px; 
            border-radius: 24px; 
            display: inline-block;
            font-weight: 500;
            font-size: 15px;
            margin-bottom: 8px;
        ">
            {emoji} {_esc(label)}
        </div>
        """
        if desc:
            mode_badge += f"""
            <div style="font-size: 13px; color: #6b7280; font-style: italic;">
                {_esc(desc)}
            </div>
            """
    
    # Strength indicator (compact)
    strength_html = ""
    if plan_strength:
        if plan_strength >= 80:
            s_color = "#22c55e"
            s_label = "Strong"
        elif plan_strength >= 60:
            s_color = "#3b82f6"
            s_label = "Good"
        elif plan_strength >= 40:
            s_color = "#f97316"
            s_label = "Fair"
        else:
            s_color = "#ef4444"
            s_label = "Needs Work"
        
        strength_html = f"""
        <div style="
            display: flex; 
            align-items: center; 
            gap: 8px;
            padding: 8px 16px;
            background: #f9fafb;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        ">
            <span style="font-size: 24px; font-weight: bold; color: {s_color};">{plan_strength}</span>
            <div>
                <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase;">Strength</div>
                <div style="font-size: 13px; font-weight: 500; color: {s_color};">{s_label}</div>
            </div>
        </div>
        """
    
    # Quick wins (compact list)
    wins_html = ""
    if quick_wins:
        wins_items = "".join([
            f"<div style='padding: 4px 0; font-size: 13px;'>✓ {_esc(w)}</div>"
            for w in quick_wins[:3]
        ])
        wins_html = f"""
        <div style="
            background: #f0fdf4; 
            padding: 12px 16px; 
            border-radius: 8px;
            border-left: 3px solid #22c55e;
            flex: 1;
        ">
            <div style="font-size: 12px; font-weight: 600; color: #166534; margin-bottom: 6px;">
                ⚡ QUICK WINS
            </div>
            {wins_items}
        </div>
        """
    
    return f"""
    <div class="dashboard-header" style="
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin-bottom: 24px;
        padding: 20px;
        background: white;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div>{mode_badge}</div>
            {strength_html}
        </div>
        {wins_html}
    </div>
    """