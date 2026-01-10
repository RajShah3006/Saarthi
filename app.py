# app.py
import gradio as gr
import logging
import sys
import re
import inspect
from typing import Any, Dict, Tuple, List
from datetime import date, timedelta

from services.github_issues import GitHubIssuesClient
from config import Config
from controllers import Controllers
from ui.layout import create_ui_layout
from ui.styles import get_css

from utils.dashboard_renderer import render_program_cards, render_checklist, render_timeline
from services.submissions_store import SubmissionStore
from services.email_builder import build_email_from_submission

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("saarthi")

store = SubmissionStore()
gh = GitHubIssuesClient()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def create_app() -> gr.Blocks:
    config = Config()
    controllers = Controllers(config)
    css = get_css(config)
    theme = gr.themes.Soft(primary_hue="slate", secondary_hue="indigo", neutral_hue="slate")

    # Gradio 6: pass css/theme to launch(), not Blocks()
    with gr.Blocks(title="Saarthi AI - University Guidance") as app:
        components = create_ui_layout(config)
        wire_events(components, controllers, config)

    # Attach launch args on the app object for __main__
    app._saarthi_css = css
    app._saarthi_theme = theme
    return app


def wire_events(components: dict, controllers: Controllers, config: Config):
    session_state = components["session_state"]
    name_state = components["name_state"]
    view_state = components["view_state"]
    programs_state = components["programs_state"]

    login = components["login"]
    student = components["student"]

    # ---------------- helpers ----------------
    def safe_plan_dict(plan: Any) -> Dict[str, Any]:
        if isinstance(plan, dict):
            return plan
        return {"md": plan or "", "profile": {}, "programs": [], "timeline_events": [], "projects": []}

    def parse_resume_code(code: str) -> Tuple[int, str]:
        code = (code or "").strip()
        if ":" not in code:
            return (0, "")
        a, b = code.split(":", 1)
        try:
            return (int(a.strip()), b.strip())
        except Exception:
            return (0, "")

    def valid_email(email: str) -> bool:
        return bool(EMAIL_RE.match((email or "").strip()))

    def ouac_deadline() -> date:
        today = date.today()
        dl = date(today.year, 1, 15)
        if today > dl:
            dl = date(today.year + 1, 1, 15)
        return dl

    def build_fallback_timeline() -> List[Dict[str, Any]]:
        today = date.today()
        dl = ouac_deadline()
        days_left = max(0, (dl - today).days)
        wk1 = today + timedelta(days=7)
        wk3 = today + timedelta(days=21)

        # NOTE: renderer may not display "date", so we bake it into title too.
        return [
            {"date": today.isoformat(), "title": f"{today.isoformat()} — Start here", "items": [
                "Confirm your top 6 Grade 12 U/M courses + prerequisites",
                "Pick 6–10 programs (safe / target / reach)",
            ]},
            {"date": wk1.isoformat(), "title": f"{wk1.isoformat()} — Within 7 days", "items": [
                "Save links + requirements for each shortlisted program",
                "Start a simple tracker (program, prereqs, admission notes, link)",
            ]},
            {"date": wk3.isoformat(), "title": f"{wk3.isoformat()} — Within 3 weeks", "items": [
                "Build 1 supplementary portfolio piece (project write-up / GitHub / design)",
                "Draft your activities list (role, dates, impact, proof)",
            ]},
            {"date": dl.isoformat(), "title": f"{dl.isoformat()} — OUAC equal consideration (Jan 15) • {days_left} days left", "items": [
                "Submit for equal consideration",
                "Double-check supplementary requirements per program",
            ]},
        ]

    def build_interest_hint(tags: List[str], details: str) -> str:
        tags = tags or []
        d = (details or "").strip().lower()
        if not tags and not d:
            return ""
        base = ", ".join(tags[:4]) if tags else "your interests"
        lines = [f"**Hint:** Based on {base}, Saarthi will prioritize programs aligned with your pathway."]
        if "robot" in d or "mechat" in d or "engineering" in " ".join([t.lower() for t in tags]):
            lines.append("- Consider a robotics/mechatronics portfolio project (1–2 weeks) to strengthen supplementary apps.")
        if "computer" in " ".join([t.lower() for t in tags]) or "cs" in d:
            lines.append("- A small GitHub project + short write-up is a big differentiator.")
        return "\n".join(lines)

    def build_prereq_hint(subjects: List[str], tags: List[str]) -> str:
        subjects = subjects or []
        s = " ".join(subjects).lower()
        t = " ".join(tags or []).lower()
        missing = []
        if ("engineering" in t) or ("computer science" in t) or ("math" in t):
            if "english (eng4u)" not in s:
                missing.append("English (ENG4U)")
            if "advanced functions (mhf4u)" not in s:
                missing.append("Advanced Functions (MHF4U)")
        if "engineering" in t:
            if "calculus & vectors (mcv4u)" not in s:
                missing.append("Calculus & Vectors (MCV4U)")
            if "physics (sph4u)" not in s:
                missing.append("Physics (SPH4U)")
        if missing:
            return "⚠️ **Possible missing prereqs (common requirements):** " + ", ".join(missing[:6])
        return "✅ Looks good — your subjects appear aligned with common prerequisites."

    def build_review(grade, average, location, tags, details, wants_email, email, subjects, extracurriculars, preferences):
        tags_str = ", ".join(tags or []) or "—"
        subjects_str = ", ".join(subjects or []) or "—"
        email_line = "No"
        if wants_email:
            email_line = f"Yes ({email.strip()})" if valid_email(email) else "Yes (missing/invalid email!)"
        return (
            f"**Grade:** {grade}  \n"
            f"**Average:** {average}%  \n"
            f"**Location:** {location or '—'}  \n\n"
            f"**Interests:** {tags_str}  \n"
            f"**Details:** {(details or '—').strip()}  \n\n"
            f"**Subjects:** {subjects_str}  \n\n"
            f"**Extracurriculars:** {(extracurriculars or '—').strip()}  \n"
            f"**Preferences:** {(preferences or '—').strip()}  \n\n"
            f"**Email response:** {email_line}"
        )

    def set_step(step: int):
        step = max(1, min(4, int(step)))
        return (
            step,
            gr.update(value=f"**Step {step} of 4**"),
            gr.update(visible=(step == 1)),
            gr.update(visible=(step == 2)),
            gr.update(visible=(step == 3)),
            gr.update(visible=(step == 4)),
            gr.update(visible=(step > 1)),
            gr.update(visible=(step < 4)),
            gr.update(interactive=(step == 4)),
        )

    def save_generated_plan_compat(submission_id: int, full_md: str, programs: list, timeline_events: list, projects: list):
        """
        Backward compatible wrapper for SubmissionStore.save_generated_plan
        because your store signature may differ across versions.
        """
        try:
            sig = inspect.signature(store.save_generated_plan)
            # parameters include "self"
            n = len(sig.parameters)
            if n >= 6:
                # self, id, md, programs, timeline, projects
                store.save_generated_plan(int(submission_id), full_md or "", programs or [], timeline_events or [], projects or [])
            else:
                # self, id, md, programs, phases
                # reuse phases column for projects
                store.save_generated_plan(int(submission_id), full_md or "", programs or [], projects or [])
        except Exception:
            # last resort attempts
            try:
                store.save_generated_plan(int(submission_id), full_md or "", programs or [], timeline_events or [], projects or [])
            except Exception:
                store.save_generated_plan(int(submission_id), full_md or "", programs or [], projects or [])

    def sync_github_status(submission_id: int, desired_label: str, close: bool = False):
        """Sync submission status to GitHub issue labels"""
        try:
            sub = store.admin_get(int(submission_id))
            if not sub:
                logger.warning(f"sync_github_status: submission {submission_id} not found")
                return
                
            issue_no = sub.get("github_issue_number")
            if not issue_no:
                logger.debug(f"sync_github_status: submission {submission_id} has no GitHub issue")
                return
                
            result = gh.set_issue_status(int(issue_no), desired_label, close=close)
            
            if result.success:
                try:
                    store.set_github_status(int(submission_id), desired_label)
                except Exception as e:
                    logger.warning(f"Failed to update local github_status: {e}")
            else:
                logger.error(f"Failed to sync GitHub status: {result.error_message}")
                try:
                    store.set_github_status(int(submission_id), f"ERROR: {result.error_message[:50]}")
                except Exception:
                    pass
                
                # Add comment about the failure
                try:
                    gh.comment(int(issue_no), f"⚠️ Saarthi failed to set label `{desired_label}`: {result.error_message}")
                except Exception:
                    pass
                    
        except Exception as e:
            logger.exception(f"sync_github_status failed: {e}")

    # ---------------- student UX: show/hide email textbox ----------------
    def on_email_toggle(wants: bool):
        if wants:
            return gr.update(visible=True), gr.update(value="📩 You’ll receive an email after team approval.")
        return gr.update(visible=False, value=""), gr.update(value="")

    student["wants_email"].change(
        fn=on_email_toggle,
        inputs=[student["wants_email"]],
        outputs=[student["student_email"], student["email_hint"]],
    )

    # ---------------- hints ----------------
    def on_interest_change(tags, details):
        return gr.update(value=build_interest_hint(tags or [], details or ""))

    student["interest_tags_input"].change(
        fn=on_interest_change,
        inputs=[student["interest_tags_input"], student["interest_details_input"]],
        outputs=[student["interest_hint"]],
    )
    student["interest_details_input"].change(
        fn=on_interest_change,
        inputs=[student["interest_tags_input"], student["interest_details_input"]],
        outputs=[student["interest_hint"]],
    )

    def on_subjects_change(subjects, tags):
        return gr.update(value=build_prereq_hint(subjects or [], tags or []))

    student["subjects_input"].change(
        fn=on_subjects_change,
        inputs=[student["subjects_input"], student["interest_tags_input"]],
        outputs=[student["prereq_hint"]],
    )

    # ---------------- login ----------------
    def on_start(name: str):
        hide_login, show_student, welcome_md, sess_id = controllers.handle_start_session(name)
        return (
            hide_login,
            show_student,
            welcome_md,
            sess_id,
            (name or "Student"),
            gr.update(visible=True),
            gr.update(visible=False),
            "inputs",
            gr.update(value=""),
        )

    login["start_btn"].click(
        fn=on_start,
        inputs=[login["name_input"]],
        outputs=[
            login["section"],
            student["section"],
            student["output_display"],
            session_state,
            name_state,
            student["inputs_view"],
            student["outputs_view"],
            view_state,
            student["wizard_error"],
        ],
    )

    # ---------------- resume: chain properly (NO double click) ----------------
    def on_resume_from_login(code: str):
        sid, token = parse_resume_code(code)
        if not sid or not token:
            return gr.update(value="❌ Invalid code. Use `id:token`"), gr.update(), gr.update()
        sub = store.get_by_resume_code(sid, token)
        if not sub:
            return gr.update(value="❌ Not found. Check the code again."), gr.update(), gr.update()
        return (gr.update(value="✅ Loaded saved roadmap."), gr.update(visible=False), gr.update(visible=True))

    def render_resumed(code: str):
        sid, token = parse_resume_code(code)
        sub = store.get_by_resume_code(sid, token)
        if not sub:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                "inputs",
                gr.update(value="❌ Not found."),
                gr.update(value=""),
                gr.update(value="<div class='card-empty'>No timeline yet.</div>"),
                gr.update(value="<div class='card-empty'>No programs yet.</div>"),
                gr.update(value="<div class='card-empty'>No checklist yet.</div>"),
                gr.update(value=""),
                gr.update(value=[]),
                gr.update(choices=[], value=[]),
                gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
            )

        sub_u = store.unpack(sub)
        profile = {
            "interest": sub_u.get("interests", ""),
            "grade": sub_u.get("grade", ""),
            "avg": sub_u.get("average", ""),
            "subjects": ", ".join((sub_u.get("subjects") or [])[:6]),
        }

        programs = sub_u.get("ui_programs", []) or []
        timeline_events = sub_u.get("ui_timeline", []) or build_fallback_timeline()
        projects = sub_u.get("ui_projects", []) or sub_u.get("ui_phases", []) or []

        timeline_html = render_timeline(profile, timeline_events)
        programs_html = render_program_cards(programs)
        checklist_html = render_checklist(projects)
        full_md = sub_u.get("roadmap_md", "") or ""

        choices = [f"{p.get('program_name','')} — {p.get('university_name','')}".strip(" —") for p in programs[:12]]

        return (
            gr.update(visible=False),
            gr.update(visible=True),
            "outputs",
            gr.update(value=f"**Resume code:** `{sid}:{token}`"),
            gr.update(value=f"{sid}:{token}"),
            timeline_html,
            programs_html,
            checklist_html,
            full_md,
            gr.update(value=programs),
            gr.update(choices=choices, value=[]),
            gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
        )

    resume_evt = login["resume_btn"].click(
        fn=on_resume_from_login,
        inputs=[login["resume_code_input"]],
        outputs=[login["resume_login_status"], login["section"], student["section"]],
    )
    resume_evt.then(
        fn=render_resumed,
        inputs=[login["resume_code_input"]],
        outputs=[
            student["inputs_view"],
            student["outputs_view"],
            view_state,
            student["submission_code_out"],
            student["resume_code_store"],
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
            programs_state,
            student["compare_select"],
            student["compare_table"],
        ],
    )

    # ---------------- wizard nav with validation ----------------
    def on_next(step, grade, average, location, tags, details, wants_email, email, subjects, extracurriculars, preferences):
        step = int(step)

        if step == 1:
            if not tags or len(tags) < 2:
                return (*set_step(1), gr.update(value="❌ Please pick at least 2 Interest Areas."), gr.update())
            if wants_email and not valid_email(email):
                return (*set_step(1), gr.update(value="❌ Please enter a valid email address."), gr.update())
            return (*set_step(2), gr.update(value=""), gr.update())

        if step == 2:
            if not subjects or len(subjects) == 0:
                return (*set_step(2), gr.update(value="❌ Please select your current/planned subjects."), gr.update())
            return (*set_step(3), gr.update(value=""), gr.update())

        if step == 3:
            base = set_step(4)
            review = build_review(grade, average, location, tags, details, wants_email, email, subjects, extracurriculars, preferences)
            return (*base, gr.update(value=""), gr.update(value=review))

        return (*set_step(4), gr.update(value=""), gr.update())

    student["next_btn"].click(
        fn=on_next,
        inputs=[
            student["wizard_step"],
            student["grade_input"],
            student["average_input"],
            student["location_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["wants_email"],
            student["student_email"],
            student["subjects_input"],
            student["extracurriculars_input"],
            student["preferences_input"],
        ],
        outputs=[
            student["wizard_step"],
            student["step_label"],
            student["step1"], student["step2"], student["step3"], student["step4"],
            student["back_btn"], student["next_btn"],
            student["generate_btn"],
            student["wizard_error"],
            student["review_box"],
        ],
    )

    def on_back(step: int):
        step = max(1, int(step) - 1)
        return (*set_step(step), gr.update(value=""))

    student["back_btn"].click(
        fn=on_back,
        inputs=[student["wizard_step"]],
        outputs=[
            student["wizard_step"],
            student["step_label"],
            student["step1"], student["step2"], student["step3"], student["step4"],
            student["back_btn"], student["next_btn"],
            student["generate_btn"],
            student["wizard_error"],
        ],
    )

    # ---------------- generate ----------------
    def generate_and_show(
        grade, average, location,
        tags, details,
        subjects, extracurriculars, preferences,
        wants_email, student_email,
        sess_id, student_name
    ):
        tags = tags or []
        details = (details or "").strip()

        if tags and details:
            interests_str = f"{', '.join(tags)}; Details: {details}"
        elif tags:
            interests_str = ", ".join(tags)
        else:
            interests_str = details

        # email validation
        if wants_email and not valid_email(student_email):
            return (
                gr.update(value="❌ Please enter a valid email."),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(visible=True),
                gr.update(visible=False),
                "inputs",
                gr.update(value="", visible=False),
                gr.update(visible=True),
                gr.update(value="<div class='card-empty'>No timeline yet.</div>"),
                gr.update(value="<div class='card-empty'>No programs yet.</div>"),
                gr.update(value="<div class='card-empty'>No checklist yet.</div>"),
                gr.update(value=""),
                gr.update(value=[]),
                gr.update(choices=[], value=[]),
                gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
            )

        created = store.create_submission({
            "student_name": student_name or "Student",
            "student_email": (student_email or "").strip(),
            "wants_email": bool(wants_email),
            "grade": grade,
            "average": float(average),
            "subjects": subjects or [],
            "interests": interests_str,
            "extracurriculars": extracurriculars or "",
            "location": location or "",
            "preferences": preferences or "",
        })
        resume_code = f"{created['id']}:{created['resume_token']}"
        note = f"**Resume code:** `{resume_code}`"

        # In generate_and_show function, after creating submission:
        
        # If email requested: create issue, DO NOT generate roadmap for student
        if wants_email:
            github_status_msg = ""
            github_error = False
            
            if not gh.enabled:
                github_status_msg = "⚠️ GitHub integration not configured. Admin will need to check manually."
                logger.warning("GitHubIssuesClient not enabled — check GITHUB_TOKEN / GITHUB_OWNER / GITHUB_REPO")
            else:
                result = gh.create_email_request_issue(
                    submission_id=created["id"],
                    resume_code=resume_code,
                    grade=str(grade),
                    average=float(average),
                    interests=interests_str,
                )
                
                if result.success:
                    try:
                        store.set_github_issue(
                            created["id"],
                            result.issue_number,
                            result.issue_url or "",
                            result.assignee or "",
                            "status:NEW"
                        )
                        github_status_msg = f"✅ Tracking issue created: [#{result.issue_number}]({result.issue_url})"
                    except Exception as e:
                        logger.exception(f"Failed to save GitHub issue reference: {e}")
                        github_status_msg = f"✅ Issue #{result.issue_number} created, but failed to save reference."
                else:
                    github_error = True
                    github_status_msg = f"⚠️ Could not create tracking issue: {result.error_message}"
                    logger.error(f"GitHub issue creation failed: {result.error_type} - {result.error_message}")
                    
                    # Try to log the error in the database
                    try:
                        store.set_github_status(created["id"], f"ERROR: {result.error_message[:100]}")
                    except Exception:
                        pass
        
            notice = (
                "✅ **Request received!**\n\n"
                "A team member will review your personalized roadmap and email it to you shortly.\n\n"
                f"{note}\n\n"
                f"_{github_status_msg}_"
            )
        
            # Switch to outputs view but hide dashboard
            return (
                gr.update(value=""),                    # wizard_error
                gr.update(value=note),                  # submission_code_out
                gr.update(value=resume_code),           # resume_code_store
                gr.update(visible=False),               # inputs_view
                gr.update(visible=True),                # outputs_view
                "outputs",
                gr.update(value=notice, visible=True),  # email_only_notice
                gr.update(visible=False),               # dashboard_wrap
                "<div class='card-empty'>Roadmap will be emailed.</div>",
                "<div class='card-empty'>Roadmap will be emailed.</div>",
                "<div class='card-empty'>Roadmap will be emailed.</div>",
                "",                                     # full plan hidden
                gr.update(value=[]),                    # programs_state
                gr.update(choices=[], value=[]),
                gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
            )

        # Otherwise: generate immediately + show dashboard
        plan_raw = controllers.handle_generate_roadmap(
            subjects, interests_str, extracurriculars, average, grade, location, preferences, sess_id
        )
        plan = safe_plan_dict(plan_raw)

        programs = plan.get("programs", []) or []
        timeline_events = plan.get("timeline_events", []) or build_fallback_timeline()
        projects = plan.get("projects", []) or []
        full_md = plan.get("md", "") or ""

        profile = plan.get("profile") or {
            "interest": interests_str,
            "grade": grade,
            "avg": average,
            "subjects": ", ".join((subjects or [])[:6]),
        }

        save_generated_plan_compat(created["id"], full_md, programs, timeline_events, projects)

        timeline_html = render_timeline(profile, timeline_events)
        programs_html = render_program_cards(programs)
        checklist_html = render_checklist(projects)

        choices = [f"{p.get('program_name','')} — {p.get('university_name','')}".strip(" —") for p in programs[:12]]

        return (
            gr.update(value=""),                 # wizard_error
            gr.update(value=note),               # submission_code_out
            gr.update(value=resume_code),        # resume_code_store
            gr.update(visible=False),            # inputs_view
            gr.update(visible=True),             # outputs_view
            "outputs",
            gr.update(value="", visible=False),  # email_only_notice
            gr.update(visible=True),             # dashboard_wrap
            timeline_html,
            programs_html,
            checklist_html,
            full_md,
            gr.update(value=programs),           # programs_state
            gr.update(choices=choices, value=[]),
            gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
        )

    student["generate_btn"].click(
        fn=generate_and_show,
        inputs=[
            student["grade_input"],
            student["average_input"],
            student["location_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["subjects_input"],
            student["extracurriculars_input"],
            student["preferences_input"],
            student["wants_email"],
            student["student_email"],
            session_state,
            name_state,
        ],
        outputs=[
            student["wizard_error"],
            student["submission_code_out"],
            student["resume_code_store"],
            student["inputs_view"],
            student["outputs_view"],
            view_state,
            student["email_only_notice"],
            student["dashboard_wrap"],
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
            programs_state,
            student["compare_select"],
            student["compare_table"],
        ],
    )

    # ---------------- back to inputs ----------------
    def go_edit_inputs():
        return gr.update(visible=True), gr.update(visible=False), "inputs"

    student["edit_inputs_btn"].click(
        fn=go_edit_inputs,
        inputs=[],
        outputs=[student["inputs_view"], student["outputs_view"], view_state],
    )

    # ---------------- clear form ----------------
    student["clear_btn"].click(
        fn=controllers.handle_clear_form,
        inputs=[],
        outputs=[
            student["subjects_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["extracurriculars_input"],
            student["average_input"],
            student["grade_input"],
            student["location_input"],
            student["preferences_input"],
        ],
    )

    # ---------------- compare tab ----------------
    def render_compare(selected: List[str], programs: List[Dict[str, Any]]):
        if not selected:
            return "<div class='card-empty'>Pick programs to compare.</div>"

        labels = [f"{p.get('program_name','')} — {p.get('university_name','')}".strip(" —") for p in programs[:12]]
        pick = []
        for s in selected[:4]:
            if s in labels:
                pick.append(programs[labels.index(s)])

        if not pick:
            return "<div class='card-empty'>Pick programs to compare.</div>"

        rows = []
        for p in pick:
            rows.append(f"""
            <tr>
              <td>{p.get('program_name','')}</td>
              <td>{p.get('university_name','')}</td>
              <td>{p.get('match_percent',0)}%</td>
              <td>{"✅" if p.get("co_op_available") else "—"}</td>
              <td>{p.get('prerequisites','')}</td>
              <td>{p.get('admission_average','')}</td>
            </tr>
            """)

        return f"""
        <div class="table-wrap">
          <table class="cmp">
            <thead>
              <tr><th>Program</th><th>University</th><th>Match</th><th>Co-op</th><th>Prereqs</th><th>Admission</th></tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
          </table>
        </div>
        """

    student["compare_select"].change(
        fn=render_compare,
        inputs=[student["compare_select"], programs_state],
        outputs=[student["compare_table"]],
    )

    # ---------------- follow-up ----------------
    def followup(question, current_md, sess_id):
        cleared_q, new_md = controllers.handle_followup(question, current_md, sess_id)
        return cleared_q, gr.update(), gr.update(), gr.update(), new_md

    student["send_btn"].click(
        fn=followup,
        inputs=[student["followup_input"], student["output_display"], session_state],
        outputs=[
            student["followup_input"],
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
        ],
    )
    student["followup_input"].submit(
        fn=followup,
        inputs=[student["followup_input"], student["output_display"], session_state],
        outputs=[
            student["followup_input"],
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
        ],
    )

    # =========================
    # ADMIN (approval workflow)
    # =========================
    def admin_unlock(pin: str):
        expected = getattr(config, "ADMIN_PIN", "") or ""
        if not expected:
            return gr.update(value="⚠️ ADMIN_PIN not set in config/env."), gr.update(visible=False)
        if (pin or "").strip() != expected:
            return gr.update(value="❌ Wrong PIN."), gr.update(visible=False)
        return gr.update(value="✅ Admin unlocked."), gr.update(visible=True)

    student["admin_login_btn"].click(
        fn=admin_unlock,
        inputs=[student["admin_pin"]],
        outputs=[student["admin_status"], student["admin_section"]],
    )

    def refresh_queue(status_filter: str, query: str):
        rows = store.list_queue(status_filter=status_filter, query=query, limit=200)
        return [[r["id"], r["created_at"], r["student_name"], r["student_email"], r["status"]] for r in rows]

    student["refresh_queue_btn"].click(
        fn=refresh_queue,
        inputs=[student["status_filter"], student["search_query"]],
        outputs=[student["queue_table"]],
    )

    def open_next():
        nxt = store.get_next_pending()
        if not nxt:
            return gr.update(value="✅ No pending items."), gr.update(value=None)
        return gr.update(value=f"Loaded next pending: #{nxt['id']}"), gr.update(value=float(nxt["id"]))

    student["open_next_btn"].click(
        fn=open_next,
        inputs=[],
        outputs=[student["admin_status"], student["review_id"]],
    )

    def admin_load(submission_id: float):
        if submission_id is None:
            return "", "", "", "", [], []

        sub = store.admin_get(int(submission_id))
        if not sub:
            return "❌ Not found.", "", "", "", [], []

        sub_u = store.unpack(sub)

        plan_md = sub_u.get("roadmap_md", "") or ""
        subj = sub_u.get("email_subject", "") or ""
        body = sub_u.get("email_body_text", "") or ""

        email = (sub_u.get("student_email") or "").strip()
        mailto = ""
        if email:
            import urllib.parse
            mailto = (
                f"<a target='_blank' href='mailto:{urllib.parse.quote(email)}"
                f"?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(body)}'>Open email draft in mail client</a>"
            )

        actions = store.get_actions(int(submission_id), limit=200)
        actions_table = [[a["created_at"], a["actor"], a["action"], a["details"]] for a in actions]

        return plan_md, subj, body, (mailto or ""), actions_table, actions_table

    student["load_btn"].click(
        fn=admin_load,
        inputs=[student["review_id"]],
        outputs=[student["admin_plan_md"], student["email_subject"], student["email_body"], student["gmail_helper"], student["actions_table"], student["actions_table"]],
    )

    def admin_autofill(submission_id: float, admin_name: str):
        sub = store.admin_get(int(submission_id))
        if not sub:
            return "", "", "❌ Not found.", []

        sub_u = store.unpack(sub)

        # If roadmap not generated yet (email-request flow), generate now (admin-triggered)
        if not (sub_u.get("roadmap_md") or "").strip():
            try:
                subjects = sub_u.get("subjects", []) or []
                interests = sub_u.get("interests", "") or ""
                extracurriculars = sub_u.get("extracurriculars", "") or ""
                average = sub_u.get("average", 0) or 0
                grade = sub_u.get("grade", "") or ""
                location = sub_u.get("location", "") or ""
                preferences = sub_u.get("preferences", "") or ""

                plan_raw = controllers.handle_generate_roadmap(
                    subjects, interests, extracurriculars, average, grade, location, preferences, ""
                )
                plan = safe_plan_dict(plan_raw)

                programs = plan.get("programs", []) or []
                timeline_events = plan.get("timeline_events", []) or build_fallback_timeline()
                projects = plan.get("projects", []) or []
                full_md = plan.get("md", "") or ""

                save_generated_plan_compat(int(submission_id), full_md, programs, timeline_events, projects)
                sub = store.admin_get(int(submission_id))
                sub_u = store.unpack(sub) if sub else sub_u
                sync_github_status(int(submission_id), "status:GENERATED", close=False)
            except Exception:
                logger.exception("Admin-triggered roadmap generation failed")

        email = build_email_from_submission(sub_u)

        token = f"SRT-{sub_u.get('id')}"
        subject = (email.get("subject") or "Your Saarthi Roadmap").strip()
        if token not in subject:
            subject = f"{subject} [{token}]"

        body = email.get("body_text") or ""
        actor = (admin_name or "").strip() or "admin"

        store.admin_save_email(int(submission_id), subject, body, actor=actor)
        sync_github_status(int(submission_id), "status:DRAFTED", close=False)
        store.log_action(int(submission_id), actor, "AUTOFILL_EMAIL", "Generated email draft")

        actions = store.get_actions(int(submission_id), limit=200)
        actions_table = [[a["created_at"], a["actor"], a["action"], a["details"]] for a in actions]
        return subject, body, "✅ Auto-filled + saved.", actions_table

    student["autofill_email_btn"].click(
        fn=admin_autofill,
        inputs=[student["review_id"], student["admin_name"]],
        outputs=[student["email_subject"], student["email_body"], student["admin_status"], student["actions_table"]],
    )

    def admin_save(submission_id: float, subject: str, body: str, admin_name: str):
        actor = (admin_name or "").strip() or "admin"
        store.admin_save_email(int(submission_id), subject or "", body or "", actor=actor)
        sync_github_status(int(submission_id), "status:DRAFTED", close=False)
        store.log_action(int(submission_id), actor, "SAVE_EMAIL", "Saved email draft edits")

        actions = store.get_actions(int(submission_id), limit=200)
        actions_table = [[a["created_at"], a["actor"], a["action"], a["details"]] for a in actions]
        return "✅ Draft saved.", actions_table

    student["save_email_btn"].click(
        fn=admin_save,
        inputs=[student["review_id"], student["email_subject"], student["email_body"], student["admin_name"]],
        outputs=[student["admin_status"], student["actions_table"]],
    )

    def admin_mark_sent(submission_id: float, admin_name: str):
        actor = (admin_name or "").strip() or "admin"
        store.admin_mark_sent(int(submission_id), actor=actor)
        sync_github_status(int(submission_id), "status:SENT", close=True)
        store.log_action(int(submission_id), actor, "MARK_SENT", "Marked as sent")

        actions = store.get_actions(int(submission_id), limit=200)
        actions_table = [[a["created_at"], a["actor"], a["action"], a["details"]] for a in actions]
        return "✅ Marked as SENT.", actions_table

    student["mark_sent_btn"].click(
        fn=admin_mark_sent,
        inputs=[student["review_id"], student["admin_name"]],
        outputs=[student["admin_status"], student["actions_table"]],
    )

    def run_github_diagnostics():
        from services.github_issues import diagnose_github_config
        return gr.update(value=diagnose_github_config())
    
    student["github_diag_btn"].click(
        fn=run_github_diagnostics,
        inputs=[],
        outputs=[student["github_diag_output"]],
    )

    # Startup diagnostics
    def run_startup_checks():
        """Run diagnostics on startup"""
        logger.info("=" * 60)
        logger.info("SAARTHI AI — STARTUP DIAGNOSTICS")
        logger.info("=" * 60)
        
        # Check Gemini API
        if config.GEMINI_API_KEY:
            logger.info("✅ Gemini API: Configured")
        else:
            logger.warning("⚠️ Gemini API: Not configured (will use demo mode)")
        
        # Check GitHub
        if gh.enabled:
            result = gh.test_connection()
            if result.success:
                logger.info(f"✅ GitHub API: Connected to {gh.owner}/{gh.repo}")
            else:
                logger.error(f"❌ GitHub API: {result.error_message}")
        else:
            logger.warning("⚠️ GitHub API: Not configured (email workflow disabled)")
        
        # Check database
        try:
            count = len(store.list_queue(limit=1))
            logger.info(f"✅ Database: Connected ({store.db_path})")
        except Exception as e:
            logger.error(f"❌ Database: {e}")
        
        # Check programs
        try:
            prog_count = controllers.program_search.program_count
            has_embeddings = controllers.program_search.has_embeddings
            logger.info(f"✅ Programs: {prog_count} loaded ({'with' if has_embeddings else 'without'} embeddings)")
        except Exception as e:
            logger.error(f"❌ Programs: {e}")
        
        logger.info("=" * 60)
    
    
    # Run checks on module load
    run_startup_checks()

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=getattr(app, "_saarthi_css", None),
        theme=getattr(app, "_saarthi_theme", None),
    )
