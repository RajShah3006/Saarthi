'''
# services/email_builder.py
from typing import Dict, Any

def build_email_from_submission(sub: Dict[str, Any]) -> Dict[str, str]:
    name = (sub.get("student_name") or "Student").strip() or "Student"
    grade = sub.get("grade", "")
    avg = sub.get("average", "")
    interests = sub.get("interests", "")
    token = (sub.get("resume_token") or "")[:8]
    roadmap_md = (sub.get("roadmap_md") or "").strip()

    subject = f"Your Personalized University Roadmap ({token})"

    intro = (
        f"Hi {name},\n\n"
        "Thanks for submitting your info. Here is your personalized roadmap.\n\n"
        "Profile snapshot:\n"
        f"- Grade: {grade}\n"
        f"- Average: {avg}%\n"
        f"- Interests: {interests}\n\n"
    )

    outro = (
        "\n\nIf you’d like, reply with follow-up questions!.\n"
        "— Saarthi Team"
    )

    body_text = intro + roadmap_md + outro
    return {"subject": subject, "body_text": body_text}
'''
# services/email_builder.py
import re
from typing import Dict, Any, List


def markdown_to_plaintext(md: str) -> str:
    """
    Convert markdown to clean plain text suitable for emails.
    """
    if not md:
        return ""
    
    text = md
    
    # ═══════════════════════════════════════════════════════════
    # HEADERS → UPPERCASE WITH UNDERLINES
    # ═══════════════════════════════════════════════════════════
    
    # H1: # Header → HEADER with ═══
    def replace_h1(match):
        header = match.group(1).strip()
        line = "═" * min(len(header), 50)
        return f"\n{line}\n{header.upper()}\n{line}\n"
    text = re.sub(r'^# (.+)$', replace_h1, text, flags=re.MULTILINE)
    
    # H2: ## Header → HEADER with ───
    def replace_h2(match):
        header = match.group(1).strip()
        line = "─" * min(len(header), 40)
        return f"\n{header.upper()}\n{line}\n"
    text = re.sub(r'^## (.+)$', replace_h2, text, flags=re.MULTILINE)
    
    # H3: ### Header → Header:
    def replace_h3(match):
        header = match.group(1).strip()
        return f"\n▸ {header}\n"
    text = re.sub(r'^### (.+)$', replace_h3, text, flags=re.MULTILINE)
    
    # H4: #### Header → Header
    def replace_h4(match):
        header = match.group(1).strip()
        return f"\n  {header}:\n"
    text = re.sub(r'^#### (.+)$', replace_h4, text, flags=re.MULTILINE)
    
    # ═══════════════════════════════════════════════════════════
    # EMPHASIS
    # ═══════════════════════════════════════════════════════════
    
    # Bold + Italic: ***text*** or ___text___
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
    text = re.sub(r'___(.+?)___', r'\1', text)
    
    # Bold: **text** or __text__ → TEXT or *text*
    text = re.sub(r'\*\*(.+?)\*\*', lambda m: m.group(1).upper(), text)
    text = re.sub(r'__(.+?)__', lambda m: m.group(1).upper(), text)
    
    # Italic: *text* or _text_ → text
    text = re.sub(r'\*([^\*\n]+)\*', r'\1', text)
    text = re.sub(r'_([^_\n]+)_', r'\1', text)
    
    # Strikethrough: ~~text~~ → text
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    
    # ═══════════════════════════════════════════════════════════
    # LINKS & IMAGES
    # ═══════════════════════════════════════════════════════════
    
    # Images: ![alt](url) → [Image: alt]
    text = re.sub(r'!$$([^$$]*)\]$[^$]+\)', r'[Image: \1]', text)
    
    # Links: [text](url) → text (url)
    text = re.sub(r'$$([^$$]+)\]$([^$]+)\)', r'\1 (\2)', text)
    
    # Auto links: <url> → url
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
    
    # ═══════════════════════════════════════════════════════════
    # CODE
    # ═══════════════════════════════════════════════════════════
    
    # Code blocks: ```lang\ncode\n``` → indented code
    def replace_code_block(match):
        code = match.group(2) if match.group(2) else match.group(1)
        lines = code.strip().split('\n')
        indented = '\n'.join(f'    {line}' for line in lines)
        return f"\n{indented}\n"
    text = re.sub(r'```(?:\w+)?\n([\s\S]*?)```', replace_code_block, text)
    text = re.sub(r'```([\s\S]*?)```', replace_code_block, text)
    
    # Inline code: `code` → 'code'
    text = re.sub(r'`([^`]+)`', r"'\1'", text)
    
    # ═══════════════════════════════════════════════════════════
    # LISTS
    # ═══════════════════════════════════════════════════════════
    
    # Checkboxes: - [ ] item → ☐ item, - [x] item → ☑ item
    text = re.sub(r'^(\s*)- 
$$
 
$$ ', r'\1☐ ', text, flags=re.MULTILINE)
    text = re.sub(r'^(\s*)- 
$$
x
$$ ', r'\1☑ ', text, flags=re.MULTILINE)
    text = re.sub(r'^(\s*)- 
$$
X
$$ ', r'\1☑ ', text, flags=re.MULTILINE)
    
    # Unordered lists: - item or * item → • item
    text = re.sub(r'^(\s*)[-\*] ', r'\1• ', text, flags=re.MULTILINE)
    
    # Nested bullets (2 spaces or tab)
    text = re.sub(r'^  • ', r'  ◦ ', text, flags=re.MULTILINE)
    text = re.sub(r'^\t• ', r'  ◦ ', text, flags=re.MULTILINE)
    
    # Ordered lists: keep as is (1. 2. 3.)
    
    # ═══════════════════════════════════════════════════════════
    # TABLES → Formatted text
    # ═══════════════════════════════════════════════════════════
    
    def convert_table(match):
        table_text = match.group(0)
        lines = [l.strip() for l in table_text.strip().split('\n') if l.strip()]
        
        if len(lines) < 2:
            return table_text
        
        # Parse rows
        rows = []
        for line in lines:
            # Skip separator lines (|---|---|)
            if re.match(r'^\|[\s\-:]+\|$', line):
                continue
            # Split by | and clean
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]  # Remove empty
            if cells:
                rows.append(cells)
        
        if not rows:
            return table_text
        
        # Calculate column widths
        num_cols = max(len(row) for row in rows)
        col_widths = [0] * num_cols
        for row in rows:
            for i, cell in enumerate(row):
                if i < num_cols:
                    col_widths[i] = max(col_widths[i], len(cell))
        
        # Build formatted table
        result = []
        for row_idx, row in enumerate(rows):
            # Pad row if needed
            while len(row) < num_cols:
                row.append('')
            
            formatted_row = '  '.join(
                cell.ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            result.append(formatted_row)
            
            # Add separator after header
            if row_idx == 0:
                separator = '  '.join('─' * w for w in col_widths)
                result.append(separator)
        
        return '\n' + '\n'.join(result) + '\n'
    
    # Match markdown tables
    text = re.sub(
        r'^\|.+\|$(\n^\|.+\|$)+',
        convert_table,
        text,
        flags=re.MULTILINE
    )
    
    # ═══════════════════════════════════════════════════════════
    # HORIZONTAL RULES
    # ═══════════════════════════════════════════════════════════
    
    # --- or *** or ___ → ────────────
    text = re.sub(r'^[\-\*_]{3,}\s*$', '\n' + '─' * 40 + '\n', text, flags=re.MULTILINE)
    
    # ═══════════════════════════════════════════════════════════
    # BLOCKQUOTES
    # ═══════════════════════════════════════════════════════════
    
    # > quote → "quote"
    def replace_blockquote(match):
        lines = match.group(0).split('\n')
        quote_lines = []
        for line in lines:
            clean = re.sub(r'^>\s?', '', line)
            quote_lines.append(f'  │ {clean}')
        return '\n'.join(quote_lines)
    
    text = re.sub(r'(^>.*$(\n^>.*$)*)', replace_blockquote, text, flags=re.MULTILINE)
    
    # ═══════════════════════════════════════════════════════════
    # CLEANUP
    # ═══════════════════════════════════════════════════════════
    
    # Remove excessive blank lines (more than 2)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # Remove leading/trailing whitespace from lines (but keep indentation for lists)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Preserve intentional indentation (lists, code)
        if line.startswith('  ') or line.startswith('\t') or line.startswith('    '):
            cleaned_lines.append(line.rstrip())
        else:
            cleaned_lines.append(line.strip())
    text = '\n'.join(cleaned_lines)
    
    # Final trim
    text = text.strip()
    
    return text


def format_programs_list(programs: List[Dict[str, Any]]) -> str:
    """
    Format program list as clean text.
    """
    if not programs:
        return ""
    
    lines = ["\nTOP MATCHING PROGRAMS", "─" * 25]
    
    for i, prog in enumerate(programs[:10], 1):
        name = prog.get("program_name", "Unknown Program")
        uni = prog.get("university_name", "Unknown University")
        match = prog.get("match_percent", 0)
        prereqs = prog.get("prerequisites", "See website")
        coop = "Yes" if prog.get("co_op_available") else "No"
        url = prog.get("program_url", "")
        
        lines.append(f"\n{i}. {name}")
        lines.append(f"   University: {uni}")
        lines.append(f"   Match: {match}%  |  Co-op: {coop}")
        lines.append(f"   Prerequisites: {prereqs}")
        if url:
            lines.append(f"   Link: {url}")
    
    return '\n'.join(lines)


def format_timeline(timeline_events: List[Dict[str, Any]]) -> str:
    """
    Format timeline as clean text.
    """
    if not timeline_events:
        return ""
    
    lines = ["\nYOUR TIMELINE", "─" * 20]
    
    for event in timeline_events[:8]:
        date = event.get("date", "")
        title = event.get("title", "")
        items = event.get("items", [])
        
        lines.append(f"\n◆ {date} — {title}")
        for item in items[:5]:
            lines.append(f"  • {item}")
    
    return '\n'.join(lines)


def format_projects(projects: List[Dict[str, Any]]) -> str:
    """
    Format projects checklist as clean text.
    """
    if not projects:
        return ""
    
    lines = ["\nRECOMMENDED PROJECTS", "─" * 25]
    
    for proj in projects[:6]:
        title = proj.get("title", "Project")
        duration = proj.get("duration", "")
        items = proj.get("items", [])
        why = proj.get("why", "")
        
        header = f"\n▸ {title}"
        if duration:
            header += f" ({duration})"
        lines.append(header)
        
        if why:
            lines.append(f"  Why: {why}")
        
        for item in items[:6]:
            lines.append(f"  ☐ {item}")
    
    return '\n'.join(lines)


def build_email_from_submission(sub: Dict[str, Any]) -> Dict[str, str]:
    """
    Build a clean, professional email from submission data.
    """
    # Extract basic info
    name = (sub.get("student_name") or "Student").strip() or "Student"
    grade = sub.get("grade", "N/A")
    avg = sub.get("average", "N/A")
    interests = sub.get("interests", "Not specified")
    location = sub.get("location", "")
    subjects = sub.get("subjects", [])
    extracurriculars = sub.get("extracurriculars", "")
    
    submission_id = sub.get("id", "")
    token = (sub.get("resume_token") or "")[:8]
    
    # Get roadmap content
    roadmap_md = (sub.get("roadmap_md") or "").strip()
    programs = sub.get("ui_programs", []) or []
    timeline = sub.get("ui_timeline", []) or []
    projects = sub.get("ui_projects", []) or sub.get("ui_phases", []) or []
    
    # Build subject
    subject = f"Your Personalized University Roadmap"
    if token:
        subject += f" [SRT-{submission_id}]"
    
    # ═══════════════════════════════════════════════════════════
    # BUILD EMAIL BODY
    # ═══════════════════════════════════════════════════════════
    
    sections = []
    
    # Header
    sections.append("═" * 50)
    sections.append("SAARTHI AI — YOUR PERSONALIZED UNIVERSITY ROADMAP")
    sections.append("═" * 50)
    
    # Greeting
    sections.append(f"\nHi {name},\n")
    sections.append(
        "Thank you for using Saarthi AI! Below is your personalized "
        "university roadmap based on the information you provided.\n"
    )
    
    # Profile Summary
    sections.append("\nYOUR PROFILE")
    sections.append("─" * 20)
    sections.append(f"• Grade: {grade}")
    sections.append(f"• Average: {avg}%")
    sections.append(f"• Interests: {interests}")
    
    if location:
        sections.append(f"• Location: {location}")
    
    if subjects:
        subj_str = ", ".join(subjects[:6])
        if len(subjects) > 6:
            subj_str += f" (+{len(subjects) - 6} more)"
        sections.append(f"• Subjects: {subj_str}")
    
    if extracurriculars:
        ec_short = extracurriculars[:100]
        if len(extracurriculars) > 100:
            ec_short += "..."
        sections.append(f"• Extracurriculars: {ec_short}")
    
    # Programs (if available as structured data)
    if programs:
        sections.append(format_programs_list(programs))
    
    # Timeline (if available as structured data)
    if timeline:
        sections.append(format_timeline(timeline))
    
    # Projects (if available as structured data)
    if projects:
        sections.append(format_projects(projects))
    
    # Full Roadmap (converted from markdown)
    if roadmap_md:
        sections.append("\n")
        sections.append("═" * 50)
        sections.append("DETAILED ROADMAP")
        sections.append("═" * 50)
        sections.append(markdown_to_plaintext(roadmap_md))
    
    # Important Notes
    sections.append("\n")
    sections.append("─" * 40)
    sections.append("IMPORTANT NOTES")
    sections.append("─" * 40)
    sections.append(
        "• Always verify admission requirements on official university websites\n"
        "• Requirements and deadlines can change — check regularly\n"
        "• OUAC equal consideration deadline is typically January 15\n"
        "• Start supplementary applications early if required"
    )
    
    # Footer
    sections.append("\n")
    sections.append("─" * 40)
    sections.append(
        "Questions? Reply to this email and we'll help!\n\n"
        "Good luck with your applications! 🚀\n\n"
        "— The Saarthi AI Team\n"
        "   Your AI-Powered University Guidance Platform"
    )
    
    if submission_id:
        sections.append(f"\n[Reference: SRT-{submission_id}]")
    
    sections.append("─" * 40)
    
    # Join all sections
    body_text = '\n'.join(sections)
    
    return {
        "subject": subject,
        "body_text": body_text
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ALTERNATIVE: HTML EMAIL (if you want rich formatting)
# ═══════════════════════════════════════════════════════════════════════════════

def build_html_email_from_submission(sub: Dict[str, Any]) -> Dict[str, str]:
    """
    Build an HTML email (optional - for rich email clients).
    Returns both plain text and HTML versions.
    """
    # Get plain text version first
    plain = build_email_from_submission(sub)
    
    name = (sub.get("student_name") or "Student").strip()
    grade = sub.get("grade", "N/A")
    avg = sub.get("average", "N/A")
    interests = sub.get("interests", "")
    programs = sub.get("ui_programs", []) or []
    
    # Build HTML
    html_parts = [
        """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #6366f1, #a855f7); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px; }
                .header h1 { margin: 0; font-size: 24px; }
                .header p { margin: 10px 0 0; opacity: 0.9; }
                .section { background: #f8fafc; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
                .section h2 { color: #6366f1; margin-top: 0; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
                .profile-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
                .profile-item { background: white; padding: 12px; border-radius: 8px; }
                .profile-label { font-size: 12px; color: #64748b; text-transform: uppercase; }
                .profile-value { font-weight: 600; color: #1e293b; }
                .program-card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 12px; border-left: 4px solid #6366f1; }
                .program-name { font-weight: 700; color: #1e293b; margin-bottom: 5px; }
                .program-uni { color: #64748b; font-size: 14px; }
                .program-meta { display: flex; gap: 15px; margin-top: 10px; font-size: 13px; }
                .match-badge { background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 20px; font-weight: 600; }
                .footer { text-align: center; color: #64748b; font-size: 13px; padding: 20px; border-top: 1px solid #e2e8f0; margin-top: 30px; }
            </style>
        </head>
        <body>
        """,
        f"""
            <div class="header">
                <h1>🏹 Your University Roadmap</h1>
                <p>Personalized guidance from Saarthi AI</p>
            </div>
            
            <p>Hi <strong>{name}</strong>,</p>
            <p>Here's your personalized university roadmap based on your profile!</p>
            
            <div class="section">
                <h2>📊 Your Profile</h2>
                <div class="profile-grid">
                    <div class="profile-item">
                        <div class="profile-label">Grade</div>
                        <div class="profile-value">{grade}</div>
                    </div>
                    <div class="profile-item">
                        <div class="profile-label">Average</div>
                        <div class="profile-value">{avg}%</div>
                    </div>
                </div>
                <div class="profile-item" style="margin-top: 10px;">
                    <div class="profile-label">Interests</div>
                    <div class="profile-value">{interests}</div>
                </div>
            </div>
        """
    ]
    
    # Add programs
    if programs:
        html_parts.append('<div class="section"><h2>🎯 Top Matching Programs</h2>')
        for prog in programs[:6]:
            name_p = prog.get("program_name", "")
            uni = prog.get("university_name", "")
            match = prog.get("match_percent", 0)
            coop = "✓ Co-op" if prog.get("co_op_available") else ""
            prereqs = prog.get("prerequisites", "")
            
            html_parts.append(f"""
                <div class="program-card">
                    <div class="program-name">{name_p}</div>
                    <div class="program-uni">{uni}</div>
                    <div class="program-meta">
                        <span class="match-badge">{match}% Match</span>
                        <span>{coop}</span>
                    </div>
                    <div style="font-size: 13px; color: #64748b; margin-top: 8px;">
                        Prerequisites: {prereqs}
                    </div>
                </div>
            """)
        html_parts.append('</div>')
    
    # Footer
    html_parts.append("""
            <div class="footer">
                <p>Questions? Reply to this email!</p>
                <p><strong>— Saarthi AI Team</strong></p>
            </div>
        </body>
        </html>
    """)
    
    html_body = ''.join(html_parts)
    
    return {
        "subject": plain["subject"],
        "body_text": plain["body_text"],
        "body_html": html_body
    }