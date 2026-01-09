# app.py
import gradio as gr
import logging
import sys
from typing import Any, Dict, Tuple, List
from datetime import date

from config import Config
from controllers import Controllers
from ui.layout import create_ui_layout
from ui.styles import get_css

from utils.dashboard_renderer import (
    render_program_cards,
    render_checklist,
    render_timeline,
    render_compare,
)
from services.submissions_store import SubmissionStore
from services.email_builder import build_email_from_submission

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("saarthi")

store = SubmissionStore()

def parse_resume_code(code: str) -> Tuple[int, str]:
    code = (code or "").strip()
    if ":" not in code:
        return (0, "")
    a, b = code.split(":", 1)
    try:
        return (int(a.strip()), b.strip())
    except Exception:
        return (0, "")

def make_compare_choices(programs: List[Dict[str, Any]]) -> List[str]:
    choices = []
    for i, p in enumerate((programs or [])[:12], start=1):
        prog = (p.get("program_name") or "").strip()
        uni = (p.get("university_name") or "").strip()
        pct = int(p.get("match_percent", 0) or 0)
        choices.append(f"{i}. [{pct}%] {prog} — {uni}".strip(" —"))
    return choices

def safe_plan_dict(plan: Any) -> Dict[str, Any]:
    if isinstance(plan, dict):
        return plan
    # fallback: markdown only
    return {"md": plan or "", "profile": {}, "programs": [], "timeline_events": [], "projects": []}

def create_app():
    config = Config()
    controllers = Controllers(config)

    css = get_css(config)
    theme = gr.themes.Soft(primary_hue="blue", secondary_hue="purple", neutral_hue="slate")

    with gr.Blocks(title="Saarthi AI - University Guidance") as app:
        components = create_ui_layout(config)
        wire_events(components, controllers, config)

    return app, css, theme

def wire_events(components: dict, controllers: Controllers, config: Config):
    session_state = components["session_state"]
    name_state = components["name_state"]
    view_state = components["view_state"]

    programs_state = components["programs_state"]
    timeline_state = components["timeline_state"]
    projects_state = components["projects_state"]

    login = components["login"]
    student = components["student"]

    # ---------------- email checkbox -> show/hide email textbox ----------------
    def toggle_email_box(wants: bool):
        return gr.update(visible=bool(wants))
    student["wants_email"].change(
        fn=toggle_email_box,
        inputs=[student["wants_email"]],
        outputs=[student["student_email"]],
    )

    # ---------------- Login start ----------------
    def on_start(name: str):
        hide_login, show_student, welcome_md, sid = controllers.handle_start_session(name)
        return (
            hide_login,
            show_student,
            welcome_md,
            sid,
            (name or "Student"),
            gr.update(visible=True),    # inputs_view
            gr.update(visible=False),   # outputs_view
            "inputs",
            "",                         # student_message_out
            "",                         # submission_code_out
        )

    login["start_btn"].click(
        fn=on_start,
        inputs=[login["name_input"]],
        outputs=[
            login["section"],
            student["section"],
            student["output_display"],   # welcome text in Full Plan tab (ok)
            session_state,
            name_state,
            student["inputs_view"],
            student["outputs_view"],
            view_state,
            student["student_message_out"],
            student["submission_code_out"],
        ],
    )

    # ---------------- Wizard navigation ----------------
    def build_review(
        grade, average, location,
        wants_email, email,
        subjects, tags, details,
        extracurriculars, preferences
    ):
        subjects_str = ", ".join(subjects or []) or "—"
        tags_str = ", ".join(tags or []) or "—"
        details = (details or "").strip() or "—"
        extracurriculars = (extracurriculars or "").strip() or "—"
        preferences = (preferences or "").strip() or "—"
        location = (location or "").strip() or "—"
        email_line = "Yes" if wants_email else "No"
        if wants_email:
            email_line = f"Yes ({(email or '').strip() or 'MISSING EMAIL'})"

        return (
            f"**Grade:** {grade}  \n"
            f"**Average:** {average}%  \n"
            f"**Location:** {location}  \n\n"
            f"**Email response:** {email_line}  \n\n"
            f"**Subjects:** {subjects_str}  \n\n"
            f"**Interests:** {tags_str}  \n"
            f"**Details:** {details}  \n\n"
            f"**Extracurriculars:** {extracurriculars}  \n"
            f"**Preferences:** {preferences}"
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
            gr.update(visible=(step > 1)),     # back
            gr.update(visible=(step < 4)),     # next
            gr.update(interactive=(step == 4)) # enable generate only at step 4
        )

    def on_next(step, grade, avg, location, wants_email, email, subjects, tags, details, extra, prefs):
        new_step = min(4, int(step) + 1)
        base = set_step(new_step)
        review = gr.update()
        if new_step == 4:
            review = gr.update(value=build_review(
                grade, avg, location,
                wants_email, email,
                subjects, tags, details,
                extra, prefs
            ))
        return (*base, review)

    def on_back(step):
        return set_step(max(1, int(step) - 1))

    student["next_btn"].click(
        fn=on_next,
        inputs=[
            student["wizard_step"],
            student["grade_input"],
            student["average_input"],
            student["location_input"],
            student["wants_email"],
            student["student_email"],
            student["subjects_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["extracurriculars_input"],
            student["preferences_input"],
        ],
        outputs=[
            student["wizard_step"],
            student["step_label"],
            student["step1"], student["step2"], student["step3"], student["step4"],
            student["back_btn"], student["next_btn"],
            student["generate_btn"],
            student["review_box"],
        ],
    )

    student["back_btn"].click(
        fn=on_back,
        inputs=[student["wizard_step"]],
        outputs=[
            student["wizard_step"],
            student["step_label"],
            student["step1"], student["step2"], student["step3"], student["step4"],
            student["back_btn"], student["next_btn"],
            student["generate_btn"],
        ],
    )

    # ---------------- Resume (from login screen) ----------------
    def on_resume(code: str):
        sid, token = parse_resume_code(code)
        if not sid or not token:
            return gr.update(value="❌ Invalid code. Use format: `id:token`")

        sub = store.get_by_resume_code(sid, token)
        if not sub:
            return gr.update(value="❌ Not found. Check the code again.")

        sub_u = store.unpack(sub)

        # If it was an email request and plan not generated yet
        if (sub_u.get("wants_email") == 1) and (sub_u.get("status") in ("NEW",)) and not (sub_u.get("roadmap_md") or "").strip():
            return gr.update(value="✅ Request found. Your team will email you after review.")

        # Otherwise show outputs view by setting student page after start
        return gr.update(value="✅ Loaded. Click Start Session to view it in dashboard (or generate again).")

    login["resume_btn"].click(
        fn=on_resume,
        inputs=[login["resume_code_input"]],
        outputs=[login["resume_status"]],
    )

    # ---------------- Generate / Submit ----------------
    def generate_or_submit(
        grade, average, location,
        wants_email, student_email,
        subjects, tags, details,
        extracurriculars, preferences,
        session_id, student_name
    ):
        # interests string
        tags_clean = [t.strip() for t in (tags or []) if t and t.strip()]
        details_clean = (details or "").strip()
        if tags_clean and details_clean:
            interests = f"{', '.join(tags_clean)}; Details: {details_clean}"
        elif tags_clean:
            interests = ", ".join(tags_clean)
        else:
            interests = details_clean

        # validate email if wants_email
        if wants_email and not (student_email or "").strip():
            return (
                gr.update(value="❌ Email is required if you want an email response."),
                gr.update(value=""),
                gr.update(visible=True),
                gr.update(visible=False),
                "inputs",
                "",  # student_message_out
                "",  # submission_code_out
                [], [], [],
                "<div class='card-empty'>No timeline yet.</div>",
                "<div class='card-empty'>No programs yet.</div>",
                "<div class='card-empty'>No checklist yet.</div>",
                "<div class='card-empty'>Pick programs to compare.</div>",
                gr.update(choices=[], value=[]),
                "",
            )

        created = store.create_submission({
            "student_name": student_name or "Student",
            "student_email": (student_email or "").strip(),
            "wants_email": bool(wants_email),
            "grade": grade,
            "average": float(average),
            "subjects": subjects or [],
            "interests": interests or "",
            "extracurriculars": extracurriculars or "",
            "location": location or "",
            "preferences": preferences or "",
        })

        resume_code = f"{created['id']}:{created['resume_token']}"

        # If wants email: DO NOT show roadmap; keep it internal for admin
        if wants_email:
            msg = (
                "✅ **Request received.**\n\n"
                "A team member will review your information and send a personalized email.\n\n"
                f"**Resume code:** `{resume_code}` (keep this safe)"
            )
            return (
                gr.update(value=""),                 # resume_status (unused here)
                gr.update(value=""),                 # resume_status placeholder
                gr.update(visible=False),            # inputs_view
                gr.update(visible=True),             # outputs_view
                "outputs",
                msg,                                 # student_message_out
                f"**Resume code:** `{resume_code}`",  # submission_code_out
                [], [], [],
                "<div class='card-empty'>Email requested — no dashboard preview.</div>",
                "<div class='card-empty'>Email requested — no dashboard preview.</div>",
                "<div class='card-empty'>Email requested — no dashboard preview.</div>",
                "<div class='card-empty'>Email requested — no compare preview.</div>",
                gr.update(choices=[], value=[]),
                "",                                  # full plan
            )

        # Otherwise generate and show
        plan_raw = controllers.handle_generate_roadmap(
            subjects or [],
            interests,
            extracurriculars or "",
            average,
            grade,
            location or "",
            preferences or "",
            session_id
        )
        plan = safe_plan_dict(plan_raw)

        programs = plan.get("programs", []) or []
        timeline_events = plan.get("timeline_events", []) or []
        projects = plan.get("projects", []) or []
        profile = plan.get("profile", {}) or {}

        full_md = plan.get("md", "") or ""

        # Persist generated content
        store.save_generated_plan(
            created["id"],
            full_md,
            programs,
            timeline_events,
            projects
        )

        # Render tabs
        timeline_html = render_timeline(profile, timeline_events)
        programs_html = render_program_cards(programs)
        checklist_html = render_checklist(projects)

        compare_choices = make_compare_choices(programs)

        return (
            gr.update(value=""),
            gr.update(value=""),
            gr.update(visible=False),                # inputs_view
            gr.update(visible=True),                 # outputs_view
            "outputs",
            "",                                      # student_message_out empty
            f"**Resume code:** `{resume_code}`",
            programs, timeline_events, projects,     # states
            timeline_html,
            programs_html,
            checklist_html,
            "<div class='card-empty'>Pick programs to compare.</div>",
            gr.update(choices=compare_choices, value=[]),
            full_md,
        )

    student["generate_btn"].click(
        fn=generate_or_submit,
        inputs=[
            student["grade_input"],
            student["average_input"],
            student["location_input"],
            student["wants_email"],
            student["student_email"],
            student["subjects_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["extracurriculars_input"],
            student["preferences_input"],
            session_state,
            name_state,
        ],
        outputs=[
            login["resume_status"],               # harmless placeholder
            login["resume_status"],               # harmless placeholder
            student["inputs_view"],
            student["outputs_view"],
            view_state,
            student["student_message_out"],
            student["submission_code_out"],
            programs_state,
            timeline_state,
            projects_state,
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["compare_table"],
            student["compare_select"],
            student["output_display"],
        ],
    )

    # Compare change
    def on_compare_change(selected, programs):
        return render_compare(selected or [], programs or [])

    student["compare_select"].change(
        fn=on_compare_change,
        inputs=[student["compare_select"], programs_state],
        outputs=[student["compare_table"]],
    )

    # Back to inputs view
    def go_edit_inputs():
        return gr.update(visible=True), gr.update(visible=False), "inputs"

    student["edit_inputs_btn"].click(
        fn=go_edit_inputs,
        inputs=[],
        outputs=[student["inputs_view"], student["outputs_view"], view_state],
    )

    # Clear form (keep view)
    student["clear_btn"].click(
        fn=controllers.handle_clear_form,
        inputs=[],
        outputs=[
            student["subjects_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["extracurriculars_input"],
            student["preferences_input"],
            student["student_email"],
            student["wants_email"],
        ],
    )

    # Follow-up
    def followup(question, current_md, session_id):
        try:
            cleared_q, new_md = controllers.handle_followup(question, current_md, session_id)
            return cleared_q, new_md
        except TypeError:
            # if your controller is (question, session_id)
            new_md = controllers.handle_followup(question, session_id)
            return "", new_md

    student["send_btn"].click(
        fn=followup,
        inputs=[student["followup_input"], student["output_display"], session_state],
        outputs=[student["followup_input"], student["output_display"]],
    )
    student["followup_input"].submit(
        fn=followup,
        inputs=[student["followup_input"], student["output_display"], session_state],
        outputs=[student["followup_input"], student["output_display"]],
    )

    # ---------------- ADMIN ----------------
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

    def refresh_queue():
        rows = store.list_queue(limit=200)
        table = [[r["id"], r["created_at"], r["student_name"], r["student_email"], r["status"]] for r in rows]
        return table

    student["refresh_queue_btn"].click(fn=refresh_queue, inputs=[], outputs=[student["queue_table"]])

    def admin_load(submission_id: float):
        if submission_id is None:
            return "", "", "", "", ""
        sub = store.admin_get(int(submission_id))
        if not sub:
            return "❌ Not found.", "", "", "", ""
        sub_u = store.unpack(sub)

        plan_md = sub_u.get("roadmap_md", "") or "(No plan generated yet.)"
        subj = sub_u.get("email_subject", "") or ""
        body = sub_u.get("email_body_text", "") or ""

        email = (sub_u.get("student_email") or "").strip()
        helper = ""
        if email and subj and body:
            import urllib.parse
            helper = (
                f"<a target='_blank' href='mailto:{urllib.parse.quote(email)}"
                f"?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(body)}'>"
                "Open email draft in mail client</a>"
            )
        return plan_md, subj, body, helper, "✅ Loaded."

    student["load_btn"].click(
        fn=admin_load,
        inputs=[student["review_id"]],
        outputs=[student["admin_plan_md"], student["email_subject"], student["email_body"], student["gmail_helper"], student["admin_status"]],
    )

    def admin_generate_plan(submission_id: float):
        sub = store.admin_get(int(submission_id))
        if not sub:
            return "❌ Not found."
        sub_u = store.unpack(sub)

        # if already generated
        if (sub_u.get("roadmap_md") or "").strip():
            return "✅ Plan already generated."

        subjects = sub_u.get("subjects") or []
        interests = sub_u.get("interests") or ""
        extracurriculars = sub_u.get("extracurriculars") or ""
        average = sub_u.get("average")
        grade = sub_u.get("grade") or ""
        location = sub_u.get("location") or ""
        preferences = sub_u.get("preferences") or ""

        plan_raw = controllers.handle_generate_roadmap(
            subjects, interests, extracurriculars, average, grade, location, preferences, session_state.value if hasattr(session_state, "value") else ""
        )
        plan = safe_plan_dict(plan_raw)

        store.save_generated_plan(
            int(submission_id),
            plan.get("md", "") or "",
            plan.get("programs", []) or [],
            plan.get("timeline_events", []) or [],
            plan.get("projects", []) or [],
        )
        return "✅ Generated plan."

    student["admin_generate_btn"].click(
        fn=admin_generate_plan,
        inputs=[student["review_id"]],
        outputs=[student["admin_status"]],
    )

    def admin_autofill(submission_id: float):
        sub = store.admin_get(int(submission_id))
        if not sub:
            return "", "", "❌ Not found."
        sub_u = store.unpack(sub)

        if not (sub_u.get("roadmap_md") or "").strip():
            return "", "", "⚠️ Generate plan first."

        email = build_email_from_submission(sub_u)
        store.admin_save_email(int(submission_id), email["subject"], email["body_text"])
        return email["subject"], email["body_text"], "✅ Auto-filled + saved."

    student["autofill_email_btn"].click(
        fn=admin_autofill,
        inputs=[student["review_id"]],
        outputs=[student["email_subject"], student["email_body"], student["admin_status"]],
    )

    def admin_save(submission_id: float, subject: str, body: str):
        store.admin_save_email(int(submission_id), subject or "", body or "")
        return "✅ Draft saved."

    student["save_email_btn"].click(
        fn=admin_save,
        inputs=[student["review_id"], student["email_subject"], student["email_body"]],
        outputs=[student["admin_status"]],
    )

    def admin_mark_sent(submission_id: float):
        store.admin_mark_sent(int(submission_id))
        return "✅ Marked as SENT."

    student["mark_sent_btn"].click(
        fn=admin_mark_sent,
        inputs=[student["review_id"]],
        outputs=[student["admin_status"]],
    )

if __name__ == "__main__":
    app, css, theme = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=css,
        theme=theme,
    )
