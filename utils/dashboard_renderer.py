# utils/dashboard_renderer.py
import html
import re
from typing import Dict, List, Any

IDX_RE = re.compile(r"^\s*(\d+)\.")  # used by Compare selection like "1. [93%] ..."

def _esc(s: str) -> str:
    return html.escape(str(s or ""), quote=True)


def render_program_cards(programs: List[Dict[str, Any]]) -> str:
    if not programs:
        return "<div class='card-empty'>No programs yet. Generate a roadmap to see program cards.</div>"

    cards = []
    for p in programs[:12]:
        name = p.get("program_name", "")
        uni = p.get("university_name", "")
        pct = int(p.get("match_percent") or 0)
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
    """
    sections: [{ "title": "...", "items": ["...", ...] }, ...]
    """
    if not sections:
        return "<div class='card-empty'>No checklist yet.</div>"

    blocks = []
    for sec in sections[:8]:
        title = sec.get("title", "Checklist")
        items = [x for x in (sec.get("items", []) or []) if str(x).strip()]
        if not items:
            continue

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

    if not blocks:
        return "<div class='card-empty'>No checklist yet.</div>"

    return f"<div class='phase-wrap'>{''.join(blocks)}</div>"


def render_timeline(profile: Dict[str, Any], timeline_events: List[Dict[str, Any]]) -> str:
    """
    timeline_events: [{date:'YYYY-MM-DD', title:'...', items:[...], meta:{days_left:int}}, ...]
    """
    chips = []
    if profile.get("interest"):
        chips.append(f"<span class='chip'>🎯 {_esc(profile['interest'])}</span>")
    if profile.get("grade"):
        g = profile["grade"]
        if profile.get("avg") is not None:
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
    for ev in timeline_events[:10]:
        d = ev.get("date", "")
        title = ev.get("title", "")
        items = ev.get("items", []) or []
        li = "".join([f"<li>{_esc(x)}</li>" for x in items[:8]])

        meta = ev.get("meta") or {}
        days_left = meta.get("days_left")
        days_badge = f"<span class='pill pill-soft'>⏳ {int(days_left)} days left</span>" if isinstance(days_left, (int, float)) else ""

        items_html.append(f"""
        <div class="t-item">
          <div class="t-dot"></div>
          <div class="t-card">
            <div class="t-title">
              <span class="t-date">{_esc(d)}</span>
              <span class="t-name">{_esc(title)}</span>
              {days_badge}
            </div>
            <ul class="t-list">{li}</ul>
          </div>
        </div>
        """)

    return f"""
    <div class="timeline-wrap">
      {header}
      <div class="timeline-head">Timeline to OUAC</div>
      <div class="timeline">{''.join(items_html)}</div>
    </div>
    """


def render_compare(selected: List[str], programs: List[Dict[str, Any]]) -> str:
    if not selected:
        return "<div class='card-empty'>Pick programs to compare.</div>"

    programs = programs or []
    picks: List[Dict[str, Any]] = []

    for s in (selected or [])[:4]:
        m = IDX_RE.match(s or "")
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(programs):
            picks.append(programs[idx])

    if not picks:
        return "<div class='card-empty'>Pick programs to compare.</div>"

    rows = []
    for p in picks:
        rows.append(f"""
        <tr>
          <td>{_esc(p.get('program_name',''))}</td>
          <td>{_esc(p.get('university_name',''))}</td>
          <td>{_esc(p.get('match_percent',0))}%</td>
          <td>{"✅" if p.get("co_op_available") else "—"}</td>
          <td>{_esc(p.get('prerequisites',''))}</td>
          <td>{_esc(p.get('admission_average',''))}</td>
        </tr>
        """)

    return f"""
    <div class="table-wrap">
      <table class="cmp">
        <thead>
          <tr>
            <th>Program</th>
            <th>University</th>
            <th>Match</th>
            <th>Co-op</th>
            <th>Prereqs</th>
            <th>Admission</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """
