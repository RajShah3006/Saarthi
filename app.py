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

_APP_CSS = None
_APP_THEME = None


def create_app() -> gr.Blocks:
    global _APP_CSS, _APP_THEME

    config = Config()
    controllers = Controllers(config)
    _APP_CSS = get_css(config)
    _APP_THEME = gr.themes.Soft(primary_hue="blue", secondary_hue="purple", neutral_hue="slate")

    with gr.Blocks(title="Saarthi AI - University Guidance") as app:
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
    def safe_plan_dict(plan: Any, fallback_profile: Dict[str, Any]) -> Dict[str, Any]:
        # preferred: dict
        if isinstance(plan, dict):
            out = dict(plan)
            out.setdefault("profile", fallback_profile)
            out.setdefault("programs", [])
            out.setdefault("timeline_events", [])
            out.setdefault("projects", [])
            out.setdefault("md", out.get("message", "") or out.get("md", "") or "")
            return out

        # ServiceResult-like
        if hasattr(plan, "data") and isinstance(getattr(plan, "data", None), dict):
            d = plan.data
            md = getattr(plan, "message", "") or d.get("md", "") or ""
            out = {
                "md": md,
                "profile": d.get("profile") or fallback_profile,
                "programs": d.get("programs") or [],
                "timeline_events": d.get("timeline_events") or [],
                "projects": d.get("projects") or d.get("checklist") or [],
            }
            return out

        # legacy tuple: (md, programs, phases, profile)
        if isinstance(plan, (list, tuple)) and len(plan) == 4:
            md, programs, phases, prof = plan
            return {
                "md": md or "",
                "profile": prof or fallback_profile,
                "programs": programs or [],
                "timeline_events": phases or [],
                "projects": [],
            }

        return {"md": str(plan or ""), "profile": fallback_profile, "programs": [], "timeline_events": [], "projects": []}

    def parse_resume_code(code: str) -> Tuple[int, str]:
        code = (code or "").strip()
        if ":" not in code:
            return (0, "")
        a, b = code.split(":", 1)
        try:
            return (int(a.strip()), b.strip())
        except Exception:
            return (0, "")

    def build_review(grade, average, location, tags, details, subjects, wants_email, email) -> str:
        tags_str = ", ".join(tags or []) or "—"
        subjects_str = ", ".join(subjects or []) or "—"
        details = (details or "").strip() or "—"
        location = (location or "").strip() or "—"
        email_line = "No"
        if wants_email:
            email_line = f"Yes ({email.strip()})" if (email or "").strip() else "Yes (missing email!)"

        return (
            f"**Grade:** {grade}  \n"
            f"**Average:** {average}%  \n"
            f"**Location:** {location}  \n\n"
            f"**Interests:** {tags_str}  \n"
            f"**Details:** {details}  \n\n"
            f"**Subjects:** {subjects_str}  \n\n"
            f"**Email response:** {email_line}"
        )

    # ---------------- Login ----------------
    def on_start(name: str):
        hide_login, show_student, welcome_md, session_id = controllers.handle_start_session(name)
        return (
            hide_login,
            show_student,
            welcome_md,
            session_id,
            (name or "Student"),
            gr.update(visible=True),
            gr.update(visible=False),
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

    def on_next(step, grade, average, location, tags, details, subjects, wants_email, email):
        new_step = min(4, int(step) + 1)
        base = set_step(new_step)
        review = gr.update()
        if new_step == 4:
            review = gr.update(value=build_review(grade, average, location, tags, details, subjects, wants_email, email))
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
            student["interest_tags_input"],
            student["interest_details_input"],
            student["subjects_input"],
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
            return gr.update(value="❌ Invalid code. Use format: `id:token`"), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

        sub = store.get_by_resume_code(sid, token)
        if not sub:
            return gr.update(value="❌ Not found. Check the code again."), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

        sub_u = store.unpack(sub)

        profile = {
            "interest": sub_u.get("interests", ""),
            "grade": sub_u.get("grade", ""),
            "avg": sub_u.get("average", ""),
            "subjects": ", ".join((sub_u.get("subjects") or [])[:6]),
        }

        timeline_events = sub_u.get("ui_timeline") or []
        projects = sub_u.get("ui_projects") or []   # ✅ this is the checklist source
        programs = sub_u.get("ui_programs") or []
        full_md = sub_u.get("roadmap_md") or ""

        timeline_html = render_timeline(profile, timeline_events)
        programs_html = render_program_cards(programs)
        checklist_html = render_checklist(projects)  # ✅ now renders correctly

        note = f"**Resume code:** `{sid}:{token}`"
        return (
            gr.update(value="✅ Loaded saved roadmap."),
            gr.update(value=note),
            gr.update(visible=False),
            gr.update(visible=True),
            "outputs",
            timeline_html,
            programs_html,
            checklist_html,
            full_md,
        )

    login["resume_btn"].click(
        fn=on_resume,
        inputs=[login["resume_code_input"]],
        outputs=[
            login["resume_status"],
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
    def generate_and_show(
        grade, average, location,
        tags, details,
        subjects,
        extracurriculars, preferences,
        wants_email, student_email,
        session_id, student_name
    ):
        tags_clean = [t.strip() for t in (tags or []) if t and t.strip()]
        details_clean = (details or "").strip()
        interests = ", ".join(tags_clean) if tags_clean else ""
        if details_clean:
            interests = (interests + f"; Details: {details_clean}").strip("; ").strip()

        if wants_email and not (student_email or "").strip():
            return (
                gr.update(value="❌ Email is required if you request an email response."),
                gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
            )

        created = store.create_submission({
            "student_name": student_name or "Student",
            "student_email": (student_email or "").strip(),
            "wants_email": bool(wants_email),
            "grade": grade,
            "average": float(average),
            "subjects": subjects or [],
            "interests": interests,
            "interest_details": details_clean,
            "extracurriculars": extracurriculars or "",
            "location": location or "",
            "preferences": preferences or "",
        })

        fallback_profile = {
            "interest": interests,
            "grade": grade,
            "avg": average,
            "subjects": ", ".join((subjects or [])[:6]),
        }

        plan_raw = controllers.handle_generate_roadmap(
            subjects, interests, extracurriculars, average, grade, location, preferences, session_id
        )
        plan = safe_plan_dict(plan_raw, fallback_profile)

        programs = plan.get("programs") or []
        timeline_events = plan.get("timeline_events") or []
        projects = plan.get("projects") or []
        full_md = plan.get("md") or ""

        # store: ✅ projects saved separately so checklist tab works after resume too
        store.save_generated_plan(
            created["id"],
            full_md,
            programs,
            timeline_events,
            projects,
        )

        resume_code = f"{created['id']}:{created['resume_token']}"
        note = f"**Resume code:** `{resume_code}`"

        # If email requested: DON'T show roadmap, show confirmation only.
        if wants_email:
            msg = (
                "✅ **Request received.**\n\n"
                "A team member will review your roadmap and send you a personalized email.\n\n"
                "Save this resume code in case you want to come back later:\n\n"
                f"`{resume_code}`"
            )
            return (
                gr.update(value=""),
                gr.update(value=note),
                gr.update(visible=False),
                gr.update(visible=True),
                "outputs",
                "<div class='card-empty'>Email requested — timeline will arrive by email after review.</div>",
                "<div class='card-empty'>Email requested — program details will arrive by email after review.</div>",
                "<div class='card-empty'>Email requested — checklist will arrive by email after review.</div>",
                msg,
            )

        # Otherwise show results
        timeline_html = render_timeline(plan.get("profile") or fallback_profile, timeline_events)
        programs_html = render_program_cards(programs)
        checklist_html = render_checklist(projects)  # ✅ fix
        return (
            gr.update(value=""),
            gr.update(value=note),
            gr.update(visible=False),
            gr.update(visible=True),
            "outputs",
            timeline_html,
            programs_html,
            checklist_html,
            full_md,
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
            login["resume_status"],
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

    # Clear form
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

    # Follow-up (updates markdown only)
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

    # Exports (use markdown as plain text)
    def export_txt(md: str) -> str:
        import os, tempfile
        p = os.path.join(tempfile.gettempdir(), "saarthi_roadmap.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(md or "")
        return p

    student["export_pdf_btn"].click(
        fn=lambda md: export_txt(md),  # safe default (no dependency risk)
        inputs=[student["output_display"]],
        outputs=[student["download_file"]],
    )

    student["export_docx_btn"].click(
        fn=lambda md: export_txt(md),  # safe default (no dependency risk)
        inputs=[student["output_display"]],
        outputs=[student["download_file"]],
    )

    # Feedback
    def submit_feedback(rating: str, text: str, code_md: str):
        # extract id from submission_code_out: **Resume code:** `id:token`
        import re
        m = re.search(r"`(\d+):", code_md or "")
        if not m:
            return "⚠️ Feedback saved locally (no submission id found)."
        sid = int(m.group(1))
        store.save_feedback(sid, int(rating), text or "")
        return "✅ Thanks — feedback received."

    student["feedback_btn"].click(
        fn=submit_feedback,
        inputs=[student["feedback_rating"], student["feedback_text"], student["submission_code_out"]],
        outputs=[student["feedback_status"]],
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
        table = [[r["id"], r["created_at"], r["student_name"], r["student_email"], r["status"], (r.get("assigned_to") or "")] for r in rows]
        return table

    student["refresh_queue_btn"].click(fn=refresh_queue, inputs=[], outputs=[student["queue_table"]])

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

        email = (sub_u.get("student_email") or "").strip()
        mailto = ""
        if email:
            import urllib.parse
            mailto = (
                "<div class='hint-text'>"
                + f"<a target='_blank' href='mailto:{urllib.parse.quote(email)}"
                + f"?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(body)}'>"
                + "Open draft in mail client</a></div>"
            )

        return plan_md, subj, body, mailto, "✅ Loaded."

    student["load_btn"].click(
        fn=admin_load,
        inputs=[student["review_id"]],
        outputs=[student["admin_plan_md"], student["email_subject"], student["email_body"], student["gmail_helper"], student["admin_status"]],
    )

    def admin_assign(submission_id: float, assigned_to: str, notes: str):
        if submission_id is None:
            return "❌ Pick a submission ID first."
        store.admin_assign(int(submission_id), assigned_to or "", notes or "")
        return "✅ Assigned."

    student["assign_btn"].click(
        fn=admin_assign,
        inputs=[student["review_id"], student["assigned_to"], student["review_notes"]],
        outputs=[student["admin_status"]],
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
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=_APP_CSS,
        theme=_APP_THEME,
    )
