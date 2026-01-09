# app.py
import gradio as gr
import logging
import sys
from typing import Any, Dict, Tuple, List

from config import Config
from controllers import Controllers
from ui.layout import create_ui_layout
from ui.styles import get_css
from datetime import date

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


def create_app() -> gr.Blocks:
    config = Config()
    controllers = Controllers(config)
    css = get_css(config)

    with gr.Blocks(
        title="Saarthi AI - University Guidance",
        css=css,
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="purple", neutral_hue="slate"),
    ) as app:
        components = create_ui_layout(config)
        wire_events(components, controllers, config)

    return app


def wire_events(components: dict, controllers: Controllers, config: Config):
    session_state = components["session_state"]
    name_state = components["name_state"]
    view_state = components["view_state"]

    login = components["login"]
    student = components["student"]

    # ---------------- Helpers ----------------
    def safe_plan_dict(plan: Any) -> Dict[str, Any]:
        # New format preferred:
        # {"md":..., "profile":..., "programs":..., "timeline_events":..., "projects":...}
        if isinstance(plan, dict):
            return plan
    
        # legacy tuple: (md, programs, phases, profile)
        if isinstance(plan, (list, tuple)) and len(plan) == 4:
            md, programs, phases, profile = plan
            return {
                "md": md or "",
                "programs": programs or [],
                "phases": phases or [],
                "profile": profile or {},
            }
    
        # fallback: treat as markdown string
        return {"md": plan or "", "profile": {}, "programs": [], "phases": [], "timeline_events": [], "projects": []}

    def build_timeline_events() -> List[Dict[str, Any]]:
        today = date.today()
        year = today.year
        deadline = date(year, 1, 15)
        if today > deadline:
            deadline = date(year + 1, 1, 15)
    
        days_left = max(0, (deadline - today).days)
    
        return [
            {
                "date": today.isoformat(),
                "title": "Today",
                "items": [
                    "Confirm your top 6 Grade 12 U/M courses",
                    "Shortlist 6–10 programs (safe/target/reach)",
                ],
            },
            {
                "date": deadline.isoformat(),
                "title": "OUAC equal consideration target (Jan 15)",
                "items": [
                    "Submit applications for equal consideration",
                    "Double-check supplementary requirements per program",
                    f"Days left: {days_left}",
                ],
            },
        ]
    
    def build_review(subjects, tags, details, extracurriculars, average, grade, location, preferences, wants_email, email):
        subjects_str = ", ".join(subjects or []) or "—"
        tags_str = ", ".join(tags or []) or "—"
        details = (details or "").strip() or "—"
        extracurriculars = (extracurriculars or "").strip() or "—"
        location = (location or "").strip() or "—"
        preferences = (preferences or "").strip() or "—"
        email_line = f"Yes ({email.strip()})" if wants_email and (email or "").strip() else ("Yes (missing email!)" if wants_email else "No")

        return (
            f"**Grade:** {grade}  \n"
            f"**Average:** {average}%  \n"
            f"**Location:** {location}  \n\n"
            f"**Subjects:** {subjects_str}  \n\n"
            f"**Interests:** {tags_str}  \n"
            f"**Details:** {details}  \n\n"
            f"**Extracurriculars:** {extracurriculars}  \n"
            f"**Preferences:** {preferences}  \n\n"
            f"**Email response:** {email_line}"
        )

    def parse_resume_code(code: str) -> Tuple[int, str]:
        # expected "id:token"
        code = (code or "").strip()
        if ":" not in code:
            return (0, "")
        a, b = code.split(":", 1)
        try:
            return (int(a.strip()), b.strip())
        except Exception:
            return (0, "")

    # ---------------- Login ----------------
    def on_start(name: str):
        # controllers returns: (hide login, show student, welcome_md, session_id)
        hide_login, show_student, welcome_md, session_id = controllers.handle_start_session(name)
        return (
            hide_login,
            show_student,
            welcome_md,
            session_id,
            (name or "Student"),
            gr.update(visible=True),   # inputs_view
            gr.update(visible=False),  # outputs_view
            "inputs",
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
        ],
    )

    # ---------------- Wizard nav ----------------
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

    def on_next(step, subjects, tags, details, extracurriculars, average, grade, location, preferences, wants_email, email):
        new_step = min(4, int(step) + 1)
        base = set_step(new_step)
        review = gr.update()
        if new_step == 4:
            review = gr.update(
                value=build_review(subjects, tags, details, extracurriculars, average, grade, location, preferences, wants_email, email)
            )
        return (*base, review)

    def on_back(step):
        return set_step(max(1, int(step) - 1))

    student["next_btn"].click(
        fn=on_next,
        inputs=[
            student["wizard_step"],
            student["subjects_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["extracurriculars_input"],
            student["average_input"],
            student["grade_input"],
            student["location_input"],
            student["preferences_input"],
            student["wants_email"],
            student["student_email"],
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

    # ---------------- Resume ----------------
    def on_resume(code: str):
        sid, token = parse_resume_code(code)
        if not sid or not token:
            return gr.update(value="❌ Invalid code. Use format: `id:token`"), gr.update()

        sub = store.get_by_resume_code(sid, token)
        if not sub:
            return gr.update(value="❌ Not found. Check the code again."), gr.update()

        sub_u = store.unpack(sub)
        # Switch to outputs view and render
        plan = {
            "md": sub_u.get("roadmap_md", ""),
            "profile": {
                "interest": sub_u.get("interests", ""),
                "grade": sub_u.get("grade", ""),
                "avg": sub_u.get("average", ""),
                "subjects": ", ".join(sub_u.get("subjects", [])[:5]),
            },
            "programs": sub_u.get("ui_programs", []),
            "phases": sub_u.get("ui_phases", []),
        }

        timeline_events = plan.get("timeline_events") or build_timeline_events()
        projects = plan.get("projects") or plan.get("phases") or []
        
        timeline_html = render_timeline(plan["profile"], timeline_events)
        programs_html = render_program_cards(plan["programs"])
        checklist_html = render_checklist(projects)
        full_md = plan["md"] or ""

        return (
            gr.update(value="✅ Loaded saved roadmap."),
            gr.update(value=f"**Resume code:** `{sid}:{token}`"),
            gr.update(visible=False),
            gr.update(visible=True),
            "outputs",
            timeline_html,
            programs_html,
            checklist_html,
            full_md,
        )

    student["resume_btn"].click(
        fn=on_resume,
        inputs=[student["resume_code_input"]],
        outputs=[
            student["resume_status"],
            student["submission_code_out"],
            student["inputs_view"],
            student["outputs_view"],
            view_state,
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
        ],
    )

    # ---------------- Generate (store + render + switch view) ----------------
    def generate_and_show(subjects, interest_tags, interest_details, extracurriculars, average, grade,
                          location, preferences, wants_email, student_email, session_id, student_name):

        tags = [t.strip() for t in (interest_tags or []) if t and t.strip()]
        details = (interest_details or "").strip()
        if tags and details:
            interests = f"{', '.join(tags)}; Details: {details}"
        elif tags:
            interests = ", ".join(tags)
        else:
            interests = details

        # validate email if wants_email
        if wants_email and not (student_email or "").strip():
            return (
                gr.update(value="❌ Please enter an email address (Step 4)."),
                gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
            )

        # 1) create submission row first
        created = store.create_submission({
            "student_name": student_name or "Student",
            "student_email": (student_email or "").strip(),
            "wants_email": bool(wants_email),
            "grade": grade,
            "average": float(average),
            "subjects": subjects or [],
            "interests": interests,
            "extracurriculars": extracurriculars or "",
            "location": location or "",
            "preferences": preferences or "",
        })

        # 2) generate plan from your existing controller/service
        plan_raw = controllers.handle_generate_roadmap(
            subjects, interests, extracurriculars, average, grade, location, preferences, session_id
        )
        plan = safe_plan_dict(plan_raw)

        # Must have phases/programs to render; if controller still returns md-only, it will render empty blocks.
        timeline_events = plan.get("timeline_events") or build_timeline_events()
        projects = plan.get("projects") or plan.get("phases") or []
        
        timeline_html = render_timeline(plan.get("profile", {}) or {}, timeline_events)
        programs_html = render_program_cards(plan.get("programs", []) or [])
        checklist_html = render_checklist(projects)
        full_md = plan.get("md", "") or ""

        # 3) store generated outputs
        store.save_generated_plan(
            created["id"],
            full_md,
            plan.get("programs", []) or [],
            projects,  # store projects in ui_phases_json (reusing column)
        )

        resume_code = f"{created['id']}:{created['resume_token']}"
        note = f"**Resume code:** `{resume_code}`"
        if wants_email:
            note += "\n\n✅ Email requested. A team member will review and send it."

        # 4) switch to outputs-only view
        return (
            gr.update(value=""),                 # resume_status clear
            gr.update(value=note),               # submission_code_out
            gr.update(visible=False),            # inputs_view
            gr.update(visible=True),             # outputs_view
            "outputs",
            timeline_html,
            programs_html,
            checklist_html,
            full_md,
        )

    student["generate_btn"].click(
        fn=generate_and_show,
        inputs=[
            student["subjects_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["extracurriculars_input"],
            student["average_input"],
            student["grade_input"],
            student["location_input"],
            student["preferences_input"],
            student["wants_email"],
            student["student_email"],
            session_state,
            name_state,
        ],
        outputs=[
            student["resume_status"],
            student["submission_code_out"],
            student["inputs_view"],
            student["outputs_view"],
            view_state,
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
        ],
    )

    # Back to inputs
    def go_edit_inputs():
        return gr.update(visible=True), gr.update(visible=False), "inputs"

    student["edit_inputs_btn"].click(
        fn=go_edit_inputs,
        inputs=[],
        outputs=[student["inputs_view"], student["outputs_view"], view_state],
    )

    # Clear form (doesn't change view)
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

    # ---------------- Follow-up (keeps outputs; only updates full_md) ----------------
    def followup(question, current_md, session_id):
        cleared_q, new_md = controllers.handle_followup(question, current_md, session_id)
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

    def refresh_queue():
        rows = store.list_queue(limit=200)
        table = [[r["id"], r["created_at"], r["student_name"], r["student_email"], r["status"]] for r in rows]
        return table

    student["refresh_queue_btn"].click(
        fn=refresh_queue,
        inputs=[],
        outputs=[student["queue_table"]],
    )

    def admin_load(submission_id: float):
        if submission_id is None:
            return "", "", "", "", ""
        sub = store.admin_get(int(submission_id))
        if not sub:
            return "❌ Not found.", "", "", "", ""
        sub_u = store.unpack(sub)

        plan_md = sub_u.get("roadmap_md", "") or ""
        subj = sub_u.get("email_subject", "") or ""
        body = sub_u.get("email_body_text", "") or ""

        # helper: mailto draft (no Gmail API needed yet)
        email = (sub_u.get("student_email") or "").strip()
        mailto = ""
        if email:
            import urllib.parse
            mailto = f"<a target='_blank' href='mailto:{urllib.parse.quote(email)}?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(body)}'>Open email draft in mail client</a>"
        return plan_md, subj, body, (mailto or ""), ""

    student["load_btn"].click(
        fn=admin_load,
        inputs=[student["review_id"]],
        outputs=[student["admin_plan_md"], student["email_subject"], student["email_body"], student["gmail_helper"], student["admin_status"]],
    )

    def admin_autofill(submission_id: float):
        sub = store.admin_get(int(submission_id))
        if not sub:
            return "", "", "❌ Not found."
        sub_u = store.unpack(sub)
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
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)
