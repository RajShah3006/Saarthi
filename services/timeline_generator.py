# services/timeline_generator.py
"""
Timeline Generator Service
Generates personalized Grade 9-12 improvement timelines via prompts.
No stored YAML/JSON — everything is prompt-driven.
"""

import logging
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("saarthi.timeline")


class TimelineMode:
    TRAJECTORY = "trajectory"
    EXPLORATION = "exploration"
    CATCHUP = "catchup"


@dataclass
class TimelineModeInfo:
    """Mode metadata for UI display"""
    mode: str
    emoji: str
    label: str
    description: str
    color: str


MODE_INFO = {
    TimelineMode.TRAJECTORY: TimelineModeInfo(
        mode=TimelineMode.TRAJECTORY,
        emoji="🎯",
        label="Trajectory Mode",
        description="You know where you're going. Let's map the fastest path.",
        color="#22c55e"  # green
    ),
    TimelineMode.EXPLORATION: TimelineModeInfo(
        mode=TimelineMode.EXPLORATION,
        emoji="🔍",
        label="Exploration Mode",
        description="Keeping doors open while you figure things out.",
        color="#3b82f6"  # blue
    ),
    TimelineMode.CATCHUP: TimelineModeInfo(
        mode=TimelineMode.CATCHUP,
        emoji="🚀",
        label="Catch-up Mode",
        description="Recovery plan to get you back on track.",
        color="#f97316"  # orange
    ),
}


@dataclass
class TimelineContext:
    """Context for timeline generation"""
    # Core profile
    grade: str = "Grade 12"
    current_average: float = 80.0
    interests: str = ""
    subjects: List[str] = field(default_factory=list)
    extracurriculars: str = ""
    location: str = ""
    preferences: str = ""
    
    # Mode detection inputs
    academic_status: str = "on-track"  # behind | on-track | ahead
    confidence_level: int = 3  # 1-5 scale
    
    # Trajectory mode inputs
    target_programs: List[str] = field(default_factory=list)
    target_universities: List[str] = field(default_factory=list)
    
    # Catch-up mode inputs
    missing_prereqs: List[str] = field(default_factory=list)
    recovery_timeline: str = "next semester"  # asap | next semester | summer | next year
    
    # Detected mode (set after detection)
    mode: str = ""
    
    # Program search results (passed in)
    matched_programs: List[Dict[str, Any]] = field(default_factory=list)


def detect_timeline_mode(ctx: TimelineContext) -> str:
    """
    Auto-detect the appropriate timeline mode based on student profile.
    Priority: Catch-up > Trajectory > Exploration
    """
    # Catch-up takes priority
    if (ctx.current_average < 75 or 
        ctx.academic_status == "behind" or 
        len(ctx.missing_prereqs) >= 2):
        return TimelineMode.CATCHUP
    
    # Clear target with high confidence = trajectory
    if (ctx.target_programs and 
        len(ctx.target_programs) > 0 and 
        ctx.confidence_level >= 4):
        return TimelineMode.TRAJECTORY
    
    # Strong confidence even without explicit targets
    if ctx.confidence_level >= 4 and ctx.interests:
        return TimelineMode.TRAJECTORY
    
    # Default to exploration
    return TimelineMode.EXPLORATION


def get_mode_info(mode: str) -> TimelineModeInfo:
    """Get mode metadata for UI display"""
    return MODE_INFO.get(mode, MODE_INFO[TimelineMode.EXPLORATION])


def _calculate_remaining_time(grade: str, current_month: int) -> str:
    """Calculate remaining academic time in human-readable format"""
    grade_num = 12  # default
    if "9" in grade:
        grade_num = 9
    elif "10" in grade:
        grade_num = 10
    elif "11" in grade:
        grade_num = 11
    elif "12" in grade:
        grade_num = 12
    
    if grade_num >= 12:
        if current_month >= 9:
            return "~8 months until applications due. Final semester to optimize."
        elif current_month >= 1:
            return "~4 months until graduation. Focus on maintaining grades."
        else:
            return "Final stretch. Maintain grades and prepare for offers."
    elif grade_num == 11:
        return "~1.5 years until applications. Strong position to build profile."
    elif grade_num == 10:
        return "~2.5 years. Excellent time to explore and build foundations."
    else:
        return "~3+ years. Maximum flexibility to explore interests."


def _get_ouac_deadline() -> date:
    """Get next OUAC equal consideration deadline (Jan 15)"""
    today = date.today()
    yr = today.year
    dl = date(yr, 1, 15)
    if today > dl:
        dl = date(yr + 1, 1, 15)
    return dl


def build_timeline_prompt(ctx: TimelineContext) -> str:
    """
    Build the LLM prompt for timeline generation.
    All logic is in the prompt — no stored templates.
    """
    
    # Auto-detect mode if not set
    if not ctx.mode:
        ctx.mode = detect_timeline_mode(ctx)
    
    mode = ctx.mode
    today = date.today()
    current_month = today.strftime("%B %Y")
    remaining = _calculate_remaining_time(ctx.grade, today.month)
    deadline = _get_ouac_deadline()
    days_left = max(0, (deadline - today).days)
    
    # Format subjects
    subjects_str = ", ".join(ctx.subjects[:8]) if ctx.subjects else "Not specified"
    
    # Format matched programs for context
    programs_context = ""
    if ctx.matched_programs:
        prog_lines = []
        for i, p in enumerate(ctx.matched_programs[:5], 1):
            prog_lines.append(
                f"{i}. {p.get('program_name', '')} at {p.get('university_name', '')} "
                f"(Match: {p.get('match_percent', 0)}%, Prereqs: {p.get('prerequisites', 'N/A')})"
            )
        programs_context = "\n".join(prog_lines)
    
    base_context = f"""You are an expert academic advisor creating a personalized Grade 9-12 improvement timeline for an Ontario high school student.

## STUDENT PROFILE
- Current Grade: {ctx.grade}
- Current Month: {current_month}
- Current Average: {ctx.current_average}%
- Academic Status: {ctx.academic_status}
- Location: {ctx.location or 'Ontario, Canada'}
- Confidence in Direction: {ctx.confidence_level}/5

## COURSES (Current/Planned)
{subjects_str}

## INTERESTS
{ctx.interests or 'Not specified'}

## EXTRACURRICULARS
{ctx.extracurriculars or 'None listed'}

## PREFERENCES
{ctx.preferences or 'None specified'}

## TIME CONTEXT
- {remaining}
- OUAC Equal Consideration Deadline: January 15 ({days_left} days away)

## TOP MATCHED PROGRAMS (from database)
{programs_context or 'No specific programs matched yet.'}
"""

    # Mode-specific prompt section
    if mode == TimelineMode.TRAJECTORY:
        mode_section = _build_trajectory_section(ctx)
    elif mode == TimelineMode.CATCHUP:
        mode_section = _build_catchup_section(ctx)
    else:
        mode_section = _build_exploration_section(ctx)
    
    output_format = _build_output_format(mode)
    
    return base_context + mode_section + output_format


def _build_trajectory_section(ctx: TimelineContext) -> str:
    """Build prompt section for Trajectory Mode"""
    targets = ", ".join(ctx.target_programs) if ctx.target_programs else "Based on interests"
    unis = ", ".join(ctx.target_universities) if ctx.target_universities else "Competitive Ontario universities"
    
    return f"""
## MODE: TRAJECTORY (Target Program Known)
- Target Programs: {targets}
- Target Universities: {unis}

Generate a FOCUSED roadmap with:

### 1. PREREQUISITE MAP
- List required courses for target programs (use Ontario course codes like MCV4U, SPH4U)
- Identify which prerequisites the student already has vs. missing
- Flag any at-risk courses based on their current average
- Suggest backup courses if a prerequisite fails

### 2. GRADE STRATEGY
- Which courses to prioritize for maximum admission average impact
- Realistic target average per semester (based on current {ctx.current_average}%)
- Specific study tactics for challenging courses
- Which electives could boost overall average

### 3. PORTFOLIO TRACK (term-by-term projects)
- 1-2 concrete projects per term directly relevant to target program
- Progression: foundational → intermediate → showcase-ready
- For engineering/CS: technical projects (Arduino, GitHub, competitions)
- Include estimated time commitment (e.g., "2 weekends")

### 4. KEY DEADLINES
- OUAC application window
- Supplementary application deadlines
- Scholarship deadlines
- Early admission cutoffs

### 5. CONTINGENCIES
- "If average drops below X by [date] → [specific action]"
- "If you don't get into Program A → [backup path]"
- "If interest shifts → [which courses/activities transfer]"
"""


def _build_exploration_section(ctx: TimelineContext) -> str:
    """Build prompt section for Exploration Mode"""
    interests = ctx.interests or "various fields"
    
    # Try to extract two interests
    interest_parts = [i.strip() for i in interests.replace(",", "/").split("/") if i.strip()]
    interest_a = interest_parts[0] if interest_parts else "Interest A"
    interest_b = interest_parts[1] if len(interest_parts) > 1 else "Interest B (related field)"
    
    return f"""
## MODE: EXPLORATION (Still Deciding)
- Primary Interest: {interest_a}
- Secondary Interest: {interest_b}
- Confidence Level: {ctx.confidence_level}/5

Generate a DUAL-TRACK roadmap with:

### 1. PARALLEL TRACKS
Create two distinct but manageable pathways:

**Track A ({interest_a}):**
- Required/recommended courses
- Relevant clubs and activities
- Sample portfolio projects

**Track B ({interest_b}):**
- Required/recommended courses
- Relevant clubs and activities
- Sample portfolio projects

### 2. NO-REGRET COURSE SET
- Courses that keep BOTH doors open (typically: MHF4U, MCV4U, ENG4U + sciences)
- Explain why each course is "safe" for multiple pathways
- Warn about courses that close doors if dropped

### 3. MICRO-TESTS (2-6 hour validation activities)
For each interest:
- Free online resource or mini-course to try
- Weekend project to test if they enjoy the work
- Questions to ask someone in the field
- Competition or challenge to enter

### 4. DECISION CHECKPOINTS
- "By end of Grade X, decide Y based on Z criteria"
- What specific information helps make the decision
- How to evaluate: enjoyment, aptitude, opportunity

### 5. DOORS CLOSE/OPEN TABLE
Show consequences of course choices:
- "Dropping Physics closes: [programs]"
- "Taking Data Management opens: [programs]"
"""


def _build_catchup_section(ctx: TimelineContext) -> str:
    """Build prompt section for Catch-up Mode"""
    missing = ", ".join(ctx.missing_prereqs) if ctx.missing_prereqs else "To be identified"
    recovery = ctx.recovery_timeline or "next semester"
    
    return f"""
## MODE: CATCH-UP (Recovery Plan Needed)
- Current Average: {ctx.current_average}%
- Academic Status: {ctx.academic_status}
- Missing/At-Risk Prerequisites: {missing}
- Recovery Timeline: {recovery}

Generate a REALISTIC recovery roadmap with:

### 1. RESCUE PLAN (Immediate Priorities)
- Top 3 courses to focus on RIGHT NOW for maximum GPA lift
- Courses to consider dropping if overloaded
- Specific study hours per subject per week
- "Triage" advice: what to prioritize vs. let slide

### 2. PREREQUISITE RECOVERY OPTIONS
For each missing/at-risk prerequisite:
- Summer school (timing, availability)
- Night school / continuing education
- Online credit options (ILC, virtual schools)
- Private school credit recovery
- Repeat in regular day school

Be honest about difficulty and time requirements.

### 3. REALISTIC PATHWAYS
Given current situation, map out:
- Direct university admission (what's needed if still possible)
- College-to-university transfer pathways
- Bridging programs / foundation years
- Gap year + upgrading strategy

Show that doors aren't fully closed, but be realistic.

### 4. STUDY ROUTINES (Specific and actionable)
- Weekly schedule template (Mon-Sun with hours)
- Study technique recommendations (Pomodoro, active recall, etc.)
- Which subjects need tutoring vs. self-study
- Free resources (Khan Academy, specific YouTube channels)
- When and how to ask teachers for help

### 5. MILESTONE TARGETS (Concrete checkpoints)
- "By [specific date], achieve [specific average] in [specific course]"
- Monthly check-ins with specific metrics
- Warning triggers: "If below X by Y, escalate to Z"
- Small wins to celebrate along the way
"""


def _build_output_format(mode: str) -> str:
    """Build the output format instructions"""
    mode_upper = mode.upper()
    
    return f"""

## OUTPUT FORMAT (Follow this structure exactly)

### SUMMARY_CARD

MODE: {mode_upper}
TIMELINE_SPAN: [Today's date] → [Target milestone]
PLAN_STRENGTH: [Score 0-100]
QUICK_WINS:

1. [Something they can do THIS WEEK]
2. [Second actionable item]
3. [Third actionable item]


### TIMELINE_BLOCKS

For EACH time period, use this exact format:

---
BLOCK_START
DATE_RANGE: [Grade X - Semester Y] or [Month - Month Year]
TITLE: [Descriptive title]

ACADEMIC:
- [Course recommendation with reasoning]
- [Target average for this period]
- [Priority focus]

PORTFOLIO:
- [Concrete project with time estimate]
- [Artifact to produce]

EXPLORATION:
- [Micro-test or validation activity]
- [Club/competition opportunity]

CHECKPOINT:
- Target Average: X%
- Prereqs Status: [On track / At risk / Missing]
- Portfolio Milestone: [Describable artifact]

CONTINGENCY:
- If average < X%: [Specific action]
- If interest shifts: [Adjustment plan]
BLOCK_END
---

### CHECKLIST_ITEMS
List 10-15 actionable items in order:
- [ ] Week 1: [Task]
- [ ] Week 2: [Task]
- [ ] Month 1: [Milestone]
... continue

### PLAN_STRENGTH_BREAKDOWN
ACADEMICS: [X]/20 - [Brief reason]
PREREQUISITES: [X]/20 - [Brief reason]
PORTFOLIO: [X]/20 - [Brief reason]
EXTRACURRICULARS: [X]/20 - [Brief reason]
FEASIBILITY: [X]/20 - [Brief reason]
TOTAL: [X]/100


### IMPROVEMENTS
Top 3 ways to raise the plan strength score:
1. [Highest impact improvement]
2. [Second improvement]
3. [Third improvement]

### UNIVERSAL_ADVICE
[One paragraph of advice that applies regardless of which specific path they take]
"""


def parse_timeline_response(response_text: str, mode: str) -> Dict[str, Any]:
    """
    Parse the LLM response into structured data for rendering.
    Extracts timeline events, checklist items, scores, etc.
    """
    result = {
        "mode": mode,
        "mode_info": get_mode_info(mode).__dict__,
        "summary": {
            "plan_strength": 0,
            "timeline_span": "",
            "quick_wins": []
        },
        "timeline_events": [],
        "checklist": [],
        "plan_strength_breakdown": {},
        "improvements": [],
        "universal_advice": "",
        "full_md": response_text
    }
    
    try:
        # Extract summary card
        summary_match = re.search(
            r'PLAN_STRENGTH:\s*(\d+)',
            response_text, re.IGNORECASE
        )
        if summary_match:
            result["summary"]["plan_strength"] = int(summary_match.group(1))
        
        span_match = re.search(
            r'TIMELINE_SPAN:\s*(.+?)(?:\n|$)',
            response_text, re.IGNORECASE
        )
        if span_match:
            result["summary"]["timeline_span"] = span_match.group(1).strip()
        
        # Extract quick wins
        quick_wins_section = re.search(
            r'QUICK_WINS:(.*?)(?:###|TIMELINE_BLOCKS|$)',
            response_text, re.IGNORECASE | re.DOTALL
        )
        if quick_wins_section:
            wins = re.findall(r'\d+\.\s*(.+)', quick_wins_section.group(1))
            result["summary"]["quick_wins"] = [w.strip() for w in wins[:3]]
        
        # Extract timeline blocks
        blocks = re.findall(r'BLOCK_START(.*?)BLOCK_END', response_text, re.DOTALL | re.IGNORECASE)
        
        for block in blocks:
            event = parse_timeline_block(block)
            if event:
                result["timeline_events"].append(event)
        
        # Fallback: if no BLOCK_START/BLOCK_END, try to find date-based sections
        if not result["timeline_events"]:
            result["timeline_events"] = parse_timeline_fallback(response_text)
        
        # Extract checklist
        checklist_section = re.search(
            r'CHECKLIST_ITEMS(.*?)(?:###|PLAN_STRENGTH|$)',
            response_text, re.IGNORECASE | re.DOTALL
        )
        if checklist_section:
            items = re.findall(r'-\s*$$\s*$$\s*(.+)', checklist_section.group(1))
            result["checklist"] = [item.strip() for item in items[:15]]
        
        # Extract plan strength breakdown
        breakdown_section = re.search(
            r'PLAN_STRENGTH_BREAKDOWN(.*?)(?:###|IMPROVEMENTS|$)',
            response_text, re.IGNORECASE | re.DOTALL
        )
        if breakdown_section:
            for category in ["ACADEMICS", "PREREQUISITES", "PORTFOLIO", "EXTRACURRICULARS", "FEASIBILITY", "TOTAL"]:
                match = re.search(
                    rf'{category}:\s*(\d+)/(\d+)',
                    breakdown_section.group(1), re.IGNORECASE
                )
                if match:
                    result["plan_strength_breakdown"][category.lower()] = {
                        "score": int(match.group(1)),
                        "max": int(match.group(2))
                    }
        
        # Extract improvements
        improvements_section = re.search(
            r'IMPROVEMENTS(.*?)(?:###|UNIVERSAL|$)',
            response_text, re.IGNORECASE | re.DOTALL
        )
        if improvements_section:
            imps = re.findall(r'\d+\.\s*(.+)', improvements_section.group(1))
            result["improvements"] = [i.strip() for i in imps[:3]]
        
        # Extract universal advice
        advice_match = re.search(
            r'UNIVERSAL_ADVICE\s*\n(.+?)(?:###|$)',
            response_text, re.IGNORECASE | re.DOTALL
        )
        if advice_match:
            result["universal_advice"] = advice_match.group(1).strip()
        
    except Exception as e:
        logger.warning(f"Error parsing timeline response: {e}")
    
    return result


def parse_timeline_block(block_text: str) -> Optional[Dict[str, Any]]:
    """Parse a single timeline block"""
    try:
        event = {
            "date": "",
            "title": "",
            "items": [],
            "academic": [],
            "portfolio": [],
            "exploration": [],
            "checkpoint": {},
            "contingencies": []
        }
        
        # Extract date range
        date_match = re.search(r'DATE_RANGE:\s*(.+?)(?:\n|$)', block_text, re.IGNORECASE)
        if date_match:
            event["date"] = date_match.group(1).strip()
        
        # Extract title
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', block_text, re.IGNORECASE)
        if title_match:
            event["title"] = title_match.group(1).strip()
        
        # Extract sections
        sections = {
            "ACADEMIC": "academic",
            "PORTFOLIO": "portfolio",
            "EXPLORATION": "exploration",
            "CONTINGENCY": "contingencies"
        }
        
        for section_name, key in sections.items():
            section_match = re.search(
                rf'{section_name}:(.*?)(?:ACADEMIC:|PORTFOLIO:|EXPLORATION:|CHECKPOINT:|CONTINGENCY:|BLOCK_END|$)',
                block_text, re.IGNORECASE | re.DOTALL
            )
            if section_match:
                items = re.findall(r'-\s*(.+)', section_match.group(1))
                event[key] = [item.strip() for item in items]
        
        # Extract checkpoint
        checkpoint_match = re.search(
            r'CHECKPOINT:(.*?)(?:CONTINGENCY:|BLOCK_END|$)',
            block_text, re.IGNORECASE | re.DOTALL
        )
        if checkpoint_match:
            cp_text = checkpoint_match.group(1)
            
            avg_match = re.search(r'Target Average:\s*(\d+)%?', cp_text, re.IGNORECASE)
            if avg_match:
                event["checkpoint"]["target_avg"] = int(avg_match.group(1))
            
            prereq_match = re.search(r'Prereqs Status:\s*(.+?)(?:\n|$)', cp_text, re.IGNORECASE)
            if prereq_match:
                event["checkpoint"]["prereqs_status"] = prereq_match.group(1).strip()
            
            portfolio_match = re.search(r'Portfolio Milestone:\s*(.+?)(?:\n|$)', cp_text, re.IGNORECASE)
            if portfolio_match:
                event["checkpoint"]["portfolio_milestone"] = portfolio_match.group(1).strip()
        
        # Build flat items list for backward compatibility
        event["items"] = event["academic"] + event["portfolio"] + event["exploration"]
        
        return event if (event["date"] or event["title"]) else None
        
    except Exception as e:
        logger.warning(f"Error parsing timeline block: {e}")
        return None


def parse_timeline_fallback(response_text: str) -> List[Dict[str, Any]]:
    """Fallback parser for less structured responses"""
    events = []
    
    # Try to find date-based headers
    patterns = [
        r'(\*\*[^*]+\*\*)\s*\n((?:[-•]\s*.+\n?)+)',  # **Header**\n- items
        r'(Grade \d+[^:]*:?)\s*\n((?:[-•]\s*.+\n?)+)',  # Grade X:\n- items
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December)[^:]*:?)\s*\n((?:[-•]\s*.+\n?)+)',  # Month-based
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        for title, items_text in matches:
            items = re.findall(r'[-•]\s*(.+)', items_text)
            if items:
                events.append({
                    "date": "",
                    "title": title.strip("*: "),
                    "items": [i.strip() for i in items[:8]],
                    "academic": [],
                    "portfolio": [],
                    "exploration": [],
                    "checkpoint": {},
                    "contingencies": []
                })
    
    return events[:10]


def build_compare_prompt(
    profile: Dict[str, Any],
    option_a: Dict[str, Any],
    option_b: Dict[str, Any]
) -> str:
    """Build prompt for comparing two programs/paths"""
    return f"""Compare these two university program options for a student:

## STUDENT PROFILE
- Grade: {profile.get('grade', 'Grade 12')}
- Average: {profile.get('average', 80)}%
- Interests: {profile.get('interests', 'Not specified')}
- Subjects: {', '.join(profile.get('subjects', [])[:6])}

## OPTION A
- Program: {option_a.get('program_name', '')}
- University: {option_a.get('university_name', '')}
- Prerequisites: {option_a.get('prerequisites', 'N/A')}
- Admission Average: {option_a.get('admission_average', 'N/A')}
- Co-op: {'Yes' if option_a.get('co_op_available') else 'No'}

## OPTION B
- Program: {option_b.get('program_name', '')}
- University: {option_b.get('university_name', '')}
- Prerequisites: {option_b.get('prerequisites', 'N/A')}
- Admission Average: {option_b.get('admission_average', 'N/A')}
- Co-op: {'Yes' if option_b.get('co_op_available') else 'No'}

## TASK
Create a side-by-side comparison table and recommendation:

| Factor | Option A | Option B |
|--------|----------|----------|
| Prerequisite Fit | [How well student's courses match] | [How well student's courses match] |
| Admission Chance | [Safe/Target/Reach based on average] | [Safe/Target/Reach based on average] |
| Co-op Value | [Rating and why] | [Rating and why] |
| Career Alignment | [Based on interests] | [Based on interests] |
| Overall Fit | [Score /10] | [Score /10] |

**Recommendation:** [A or B] because [specific reasons for THIS student]

**If choosing the other:** [What would need to change]
"""