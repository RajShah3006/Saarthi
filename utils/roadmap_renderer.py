# utils/roadmap_renderer.py
import re
import html
from typing import Dict, List, Tuple, Optional


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _norm_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _find_first(md: str, patterns: List[str]) -> Optional[str]:
    for p in patterns:
        m = re.search(p, md, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return _norm_spaces(m.group(1))
    return None


def _extract_profile(md: str) -> Dict[str, str]:
    interest = _find_first(md, [
        r"🎯\s*Interest\s*:\s*(.+)",
        r"\*\*🎯\s*Interest:\*\*\s*(.+)",
        r"Interest\s*:\s*(.+)",
    ]) or ""

    grade = _find_first(md, [
        r"📊\s*Grade\s*:\s*([^\n|]+)",
        r"\*\*📊\s*Grade:\*\*\s*([^\n|]+)",
        r"Grade\s*:\s*([^\n|]+)",
    ]) or ""

    avg = _find_first(md, [
        r"Average\s*:\s*([0-9]{1,3}(?:\.[0-9]+)?)\s*%?",
        r"\*\*Average:\*\*\s*([0-9]{1,3}(?:\.[0-9]+)?)",
        r"📊.*Average:\s*([0-9]{1,3}(?:\.[0-9]+)?)",
    ]) or ""

    subjects = _find_first(md, [
        r"📚\s*Subjects\s*:\s*(.+)",
        r"\*\*📚\s*Subjects:\*\*\s*(.+)",
        r"Subjects\s*:\s*(.+)",
    ]) or ""

    # Clean odd artifacts like double pipes and trailing punctuation
    subjects = _norm_spaces(subjects).strip(" .,-")

    return {"interest": interest, "grade": grade, "avg": avg, "subjects": subjects}


def _profile_header_html(profile: Dict[str, str]) -> str:
    chips = []
    if profile.get("interest"):
        chips.append(f"<span class='chip'>🎯 {_esc(profile['interest'])}</span>")
    if profile.get("grade"):
        g = profile["grade"]
        if profile.get("avg"):
            g = f"{g} • {profile['avg']}%"
        chips.append(f"<span class='chip'>📊 {_esc(g)}</span>")
    if profile.get("subjects"):
        chips.append(f"<span class='chip chip-wide'>📚 {_esc(profile['subjects'])}</span>")

    if not chips:
        return ""

    return f"""
    <div class="profile-card">
      <div class="profile-title">Your Profile</div>
      <div class="chip-row">{''.join(chips)}</div>
    </div>
    """


# ---------- Programs parsing ----------

def _extract_programs(md: str) -> List[Dict[str, str]]:
    programs: List[Dict[str, str]] = []

    # 1) Parse the "Full Plan" numbered program blocks (best quality)
    # Example:
    # 1. Program Name
    # Queen's University | 🌟 Excellent Match (90%)
    # 📝 Admission: ...
    # 📚 Prerequisites: ...
    # ⚠️ Missing: ...
    # ✅ Co-op Available
    block_re = re.compile(
        r"(?m)^\s*(\d+)\.\s*(.+?)\s*$\n"            # number + program name
        r"(.+?)\|\s*.*?\(\s*(\d{1,3})%\s*\)\s*$"    # university | ... (90%)
        r"([\s\S]*?)(?=^\s*\d+\.\s+|\Z)",           # rest until next program
        flags=re.MULTILINE
    )

    for m in block_re.finditer(md):
        name = _norm_spaces(m.group(2))
        uni = _norm_spaces(m.group(3))
        match = _norm_spaces(m.group(4))
        rest = m.group(5)

        admission = _find_first(rest, [r"📝\s*Admission\s*:\s*(.+)"]) or ""
        prereq = _find_first(rest, [r"📚\s*Prerequisites\s*:\s*(.+)"]) or ""
        missing = _find_first(rest, [r"⚠️\s*Missing\s*:\s*(.+)"]) or ""
        coop = "yes" if re.search(r"✅\s*Co-?op\s*Available", rest, flags=re.IGNORECASE) else "no"

        # Clean prereq garbage like ", ,"
        prereq = _norm_spaces(re.sub(r",\s*,+", ", ", prereq)).strip(" ,")
        missing = _norm_spaces(missing).strip(" ,")

        programs.append({
            "program": name,
            "university": uni,
            "match": match,
            "admission": admission,
            "prereq": prereq,
            "missing": missing,
            "coop": coop
        })

    if programs:
        return programs[:12]

    # 2) Fallback parse: simple university lines from earlier sections
    # **Queen's University** | 🌟 **Excellent Match** (90%)
    uni_line_re = re.compile(
        r"\*\*(.+?)\*\*\s*\|\s*.*?\(\s*(\d{1,3})%\s*\)",
        flags=re.IGNORECASE
    )
    for m in uni_line_re.finditer(md):
        programs.append({
            "program": "Recommended Program",
            "university": _norm_spaces(m.group(1)),
            "match": _norm_spaces(m.group(2)),
            "admission": "",
            "prereq": "",
            "missing": "",
            "coop": "no"
        })

    return programs[:8]


def _match_badge(match_str: str) -> Tuple[str, str]:
    """
    Returns (label, css_class)
    """
    try:
        pct = int(re.findall(r"\d{1,3}", match_str)[0])
    except Exception:
        pct = 0

    if pct >= 85:
        return (f"{pct}%", "badge-good")
    if pct >= 75:
        return (f"{pct}%", "badge-mid")
    return (f"{pct}%", "badge-low")


def _programs_html(md: str) -> str:
    progs = _extract_programs(md)

    if not progs:
        return "<div class='card-empty'>No program list detected yet. Generate a roadmap to see program cards.</div>"

    cards = []
    for p in progs:
        badge_txt, badge_cls = _match_badge(p.get("match", ""))

        missing_html = ""
        if p.get("missing"):
            # show missing courses as small chips
            miss = [x.strip() for x in re.split(r"[,\|/]+", p["missing"]) if x.strip()]
            miss = miss[:6]
            miss_chips = "".join([f"<span class='chip chip-missing'>⚠️ {_esc(x)}</span>" for x in miss])
            missing_html = f"<div class='chip-row chip-row-tight'>{miss_chips}</div>"

        meta_rows = []
        if p.get("admission"):
            meta_rows.append(f"<div class='meta-row'><span>📝 Admission</span><span>{_esc(p['admission'])}</span></div>")
        if p.get("prereq"):
            meta_rows.append(f"<div class='meta-row'><span>📚 Prereqs</span><span>{_esc(p['prereq'])}</span></div>")

        coop_html = ""
        if p.get("coop") == "yes":
            coop_html = "<span class='pill'>✅ Co-op</span>"

        cards.append(f"""
        <div class="prog-card">
          <div class="prog-top">
            <div class="prog-main">
              <div class="prog-title">{_esc(p.get("program",""))}</div>
              <div class="prog-uni">{_esc(p.get("university",""))}</div>
            </div>
            <div class="prog-side">
              <div class="badge {badge_cls}">🌟 {badge_txt}</div>
              {coop_html}
            </div>
          </div>
          {missing_html}
          <div class="meta">
            {''.join(meta_rows) if meta_rows else "<div class='meta-hint'>Details will appear here as the roadmap includes them.</div>"}
          </div>
        </div>
        """)

    return f"<div class='prog-grid'>{''.join(cards)}</div>"


# ---------- Checklist parsing ----------

def _extract_checklist(md: str) -> List[Tuple[str, List[str]]]:
    """
    Returns list of (phase_title, bullet_items)
    Priority: "Actionable Next Steps" section → phases like:
      This Semester..., Before Applications..., etc.
    """
    phases: List[Tuple[str, List[str]]] = []

    # Pull the "Actionable Next Steps" part if it exists
    start = re.search(r"(?i)Actionable Next Steps", md)
    chunk = md[start.start():] if start else md

    # Phase headings are often bold like **This Semester (or as soon as possible):**
    phase_re = re.compile(r"(?m)^\s*\*\*(.+?):\*\*\s*$")
    bullet_re = re.compile(r"(?m)^\s*[-*]\s+(.+?)\s*$")

    # If there are phase headings, split by them and collect bullets under each
    matches = list(phase_re.finditer(chunk))
    if matches:
        for i, mh in enumerate(matches):
            title = _norm_spaces(mh.group(1))
            seg_start = mh.end()
            seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(chunk)
            seg = chunk[seg_start:seg_end]
            items = [_norm_spaces(x) for x in bullet_re.findall(seg)]
            # Also accept plain lines that look like tasks if bullets are missing
            if not items:
                lines = [ln.strip() for ln in seg.splitlines() if ln.strip()]
                # take only task-ish lines (not headings, not separators)
                for ln in lines:
                    if ln.startswith(("---", "##", "#")):
                        continue
                    if len(ln) >= 8 and not ln.startswith("Metric"):
                        items.append(_norm_spaces(ln))
            items = [x for x in items if x and not x.startswith("🔗")]
            if items:
                phases.append((title, items[:8]))

    if phases:
        return phases[:6]

    # Fallback: find any bullet list anywhere
    items = [_norm_spaces(x) for x in bullet_re.findall(md)]
    items = [x for x in items if x and not x.startswith("🔗")]
    if items:
        return [("Next actions", items[:10])]

    return []


def _checklist_html(md: str) -> str:
    phases = _extract_checklist(md)
    if not phases:
        return "<div class='card-empty'>No checklist detected yet. Generate a roadmap to see actionable tasks.</div>"

    blocks = []
    for title, items in phases:
        checks = "".join([
            f"<label class='chk'><input type='checkbox'/> <span>{_esc(it)}</span></label>"
            for it in items
        ])
        blocks.append(f"""
        <div class="phase">
          <div class="phase-title">{_esc(title)}</div>
          <div class="chk-wrap">{checks}</div>
        </div>
        """)

    return f"<div class='phase-wrap'>{''.join(blocks)}</div>"


# ---------- Timeline (Roadmap) ----------

def _timeline_html(md: str) -> str:
    profile = _extract_profile(md)
    header = _profile_header_html(profile)

    phases = _extract_checklist(md)

    # If we have phases from checklist, turn them into timeline milestones.
    if phases:
        items_html = []
        for title, items in phases[:6]:
            li = "".join([f"<li>{_esc(x)}</li>" for x in items[:6]])
            items_html.append(f"""
            <div class="t-item">
              <div class="t-dot"></div>
              <div class="t-card">
                <div class="t-title">{_esc(title)}</div>
                <ul class="t-list">{li}</ul>
              </div>
            </div>
            """)
        return f"""
        <div class="timeline-wrap">
          {header}
          <div class="timeline-head">Roadmap Timeline</div>
          <div class="timeline">{''.join(items_html)}</div>
        </div>
        """

    # Fallback: show "missing prerequisites" as the roadmap (since that's the real next step)
    missing = _find_first(md, [r"⚠️\s*Missing\s*:\s*(.+)"]) or ""
    if missing:
        miss = [x.strip() for x in re.split(r"[,\|/]+", missing) if x.strip()]
        miss = miss[:8]
        li = "".join([f"<li>Complete <b>{_esc(x)}</b></li>" for x in miss])
        return f"""
        <div class="timeline-wrap">
          {header}
          <div class="timeline-head">Roadmap Timeline</div>
          <div class="timeline">
            <div class="t-item">
              <div class="t-dot"></div>
              <div class="t-card">
                <div class="t-title">Critical prerequisite gap</div>
                <ul class="t-list">{li}</ul>
              </div>
            </div>
          </div>
        </div>
        """

    return f"""
    <div class="timeline-wrap">
      {header}
      <div class="card-empty">Fill in your profile and click <b>Generate Roadmap</b> to see a timeline.</div>
    </div>
    """


# ---------- Public API ----------

def render_roadmap_bundle(md: str) -> Dict[str, str]:
    return {
        "timeline_html": _timeline_html(md),
        "programs_html": _programs_html(md),
        "checklist_html": _checklist_html(md),
        "full_md": md or ""
    }