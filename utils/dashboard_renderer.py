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
        if adm:
            meta_rows.append(
                f"<div class='meta-row'><span>📝 Admission</span><span>{_esc(adm)}</span></div>"
            )
        if pre:
            meta_rows.append(
                f"<div class='meta-row'><span>📚 Prereqs</span><span>{_esc(pre)}</span></div>"
            )

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
            {''.join(meta_rows) if meta_rows else "<div class='meta-hint'>Details appear as available.</div>"}
            {link_html}
          </div>
        </div>
        """)

    return f"<div class='prog-grid'>{''.join(cards)}</div>"


# ✅ Checklist now expects "projects" (unique from timeline)
# (still compatible with old "phases" if needed)
def render_checklist(projects):
    if not projects:
        return "<div class='card-empty'>No checklist yet.</div>"

    blocks = []
    for pr in projects[:6]:
        title = pr.get("title", "Checklist")
        items = pr.get("items", []) or []

        checks = "".join(
            f"<label class='chk'><input type='checkbox'/> <span>{_esc(it)}</span></label>"
            for it in items[:12]
        )

        blocks.append(f"""
          <div class="phase">
            <div class="phase-title">✅ {_esc(title)}</div>
            <div class="chk-wrap">{checks}</div>
          </div>
        """)

    return f"<div class='phase-wrap'>{''.join(blocks)}</div>"


def render_timeline(profile: Dict[str, Any], timeline_events: List[Dict[str, Any]]) -> str:
    # Profile chips
    chips = []
    if profile.get("interest"):
        chips.append(f"<span class='chip'>🎯 {_esc(profile['interest'])}</span>")
    if profile.get("grade"):
        g = profile["grade"]
        if profile.get("avg") is not None and profile.get("avg") != "":
            g = f"{g} • {profile['avg']}%"
        chips.append(f"<span class='chip'>📊 {_esc(g)}</span>")
    if profile.get("subjects"):
        chips.append(f"<span class='chip chip-wide'>📚 {_esc(profile['subjects'])}</span>")

    header = ""
    if chips:
        header = f"""
        <div class="profile-card">
          <div class="profile-title">Your Profile</div>
          <div class="chip-row">{''.join(chips)}</div>
        </div>
        """

    if not timeline_events:
        return f"<div class='timeline-wrap'>{header}<div class='card-empty'>Generate a roadmap to see a timeline.</div></div>"

    items_html = []
    for ev in timeline_events[:8]:
        d = ev.get("date", "")
        title = ev.get("title", "")
        items = ev.get("items", []) or []
        li = "".join([f"<li>{_esc(x)}</li>" for x in items[:7]])

        items_html.append(f"""
        <div class="t-item">
          <div class="t-dot"></div>
          <div class="t-card">
            <div class="t-title">{_esc(d)} — {_esc(title)}</div>
            <ul class="t-list">{li}</ul>
          </div>
        </div>
        """)

    return f"""
    <div class="timeline-wrap">
      {header}
      <div class="timeline-head">OUAC Timeline</div>
      <div class="timeline">{''.join(items_html)}</div>
    </div>
    """