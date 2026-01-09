# app.py
import gradio as gr
import logging
import sys
from typing import Any, Dict, Tuple, List

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("saarthi")

store = SubmissionStore()


def make_compare_choices(programs: List[Dict[str, Any]]) -> List[str]:
    choices = []
    for i, p in enumerate((programs or [])[:12], start=1):
        prog = (p.get("program_name") or "").strip()
        uni = (p.get("university_name") or "").strip()
        pct = int(p.get("match_percent") or 0)
        choices.append(f"{i}. [{pct}%] {prog} — {uni}".strip(" —"))
    return choices


def create_app() -> gr.Blocks:
    config = Config()
    controllers = Controllers(config)
    css = get_css(config)

    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="purple",
        neutral_hue="slate",
    )

    with gr.Blocks(title="Saarthi AI - University Guidance") as app:
        components = create_ui_layout(config)
        wire_events(components, controllers, config)

    # ✅ Gradio 6+ wants css/theme in launch()
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

    # ---------------- Helpers ----------------
    def safe_plan_dict(plan: Any) -> Dict[str, Any]:
        # preferred dict
        if isinstance(plan, dict):
            return plan

        # ServiceResult-like
        if hasattr(plan, "data") and hasattr(plan, "message"):
            data = getattr(plan, "data") or {}
            return data if isinstance(data, dict) else {"md": getattr(plan, "message") or ""}

        # legacy tuple
        if isinstance(plan, (list, tuple)) and len(plan) == 4:
            md, programs, phases, profile = plan
            return {"md": md or "", "programs": programs or [], "projects": phases or [], "profile": profile or {}}

        return {"md": plan or "", "profile": {}, "programs": [], "timeline_events": [], "projects": []}

    def build_review(subjects, tags, details, extracurriculars, average, grade, location, preferences, wants_email, email):
        subjects_str = ", ".join(subjects or []) or "—"
        tags_str = ", ".join(tags or []) or "—"
        details = (details or "").strip() or "—"
        extracurriculars = (extracurriculars or "").strip() or "—"
        location = (location or "").strip() or "—"
        preferences = (preferences or "").strip() or "—"
        email_line = (
            f"Yes ({email.strip()})" if wants_email and (email or "").strip()
            else ("Yes (missing email!)" if wants_email else "No")
        )

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
        code = (code or "").strip()
        if ":" not in code:
            return (0, "")
        a, b = code.split(":", 1)
        try:
            return (int(a.strip()), b.strip())
        except Exception:
            return (0, "")

    # ---------------- Compare live update ----------------
    student["compare_select"].change(
        fn=render_compare,
        inputs=[student["compare_select"], programs_state],
        outputs=[student["compare_table"]],
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
        ],
    )

    # ---------------- Resume ----------------
    def on_resume(code: str):
        sid, token = parse_resume_code(code)
        if not sid or not token:
            return (
                gr.update(value="❌ Invalid code. Use format: `id:token`"),
                gr.update(),
                gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
            )

        sub = store.get_by_resume_code(sid, token)
        if not sub:
            return (
                gr.update(value="❌ Not found. Check the code again."),
                gr.update(),
                gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
            )

        sub_u = store.unpack(sub)

        programs = sub_u.get("ui_programs", []) or []
        timeline_events = sub_u.get("ui_timeline", []) or []
        projects = sub_u.get("ui_projects", []) or []
        full_md = sub_u.get("roadmap_md", "") or ""

        profile = {
            "interest": sub_u.get("interests", ""),
            "grade": sub_u.get("grade", ""),
            "avg": sub_u.get("average", ""),
            "subjects": ", ".join((sub_u.get("subjects") or [])[:6]),
        }

        # render
        timeline_html = render_timeline(profile, timeline_events)
        programs_html = render_program_cards(programs)
        checklist_html = render_checklist(projects)

        choices = make_compare_choices(programs)

        return (
            gr.update(value="✅ Loaded saved roadmap."),
            gr.update(value=f"**Resume code:** `{sid}:{token}`"),
            gr.update(visible=False),   # inputs_view
            gr.update(visible=True),    # outputs_view
            "outputs",

            gr.update(value=""),        # email_notice
            gr.update(visible=True),    # tabs visible

            timeline_html,
            programs_html,
            checklist_html,
            full_md,

            programs,                   # programs_state
            gr.update(choices=choices, value=[]),
            gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
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

            student["email_notice"],
            student["dashboard_tabs"],

            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],

            programs_state,
            student["compare_select"],
            student["compare_table"],
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

        if wants_email and not (student_email or "").strip():
            return (
                gr.update(value="❌ Please enter an email address (Step 1)."),
                gr.update(),
                gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(),
            )

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

        plan_raw = controllers.handle_generate_roadmap(
            subjects, interests, extracurriculars, average, grade, location, preferences, session_id
        )
        plan = safe_plan_dict(plan_raw)

        programs = plan.get("programs", []) or []
        timeline_events = plan.get("timeline_events", []) or []
        projects = plan.get("projects", []) or []
        profile = plan.get("profile", {}) or {
            "interest": interests,
            "grade": grade,
            "avg": average,
            "subjects": ", ".join((subjects or [])[:6]),
        }
        full_md = plan.get("md", "") or ""

        # store generated outputs
        store.save_generated_plan(
            created["id"],
            full_md,
            programs,
            timeline_events,
            projects,
        )

        resume_code = f"{created['id']}:{created['resume_token']}"
        note = f"**Resume code:** `{resume_code}`"

        # If wants_email: don’t show roadmap; show email confirmation
        if wants_email:
            email_msg = (
                "## ✅ Submission received\n\n"
                "A team member will review your results and email you a personalized response.\n\n"
                f"{note}\n\n"
                "Keep this code to resume later."
            )
            return (
                gr.update(value=""),
                gr.update(value=note),
                gr.update(visible=False),
                gr.update(visible=True),
                "outputs",

                gr.update(value=email_msg, visible=True),   # email_notice
                gr.update(visible=False),                  # tabs hidden

                "<div class='card-empty'>Results will be emailed after approval.</div>",
                "<div class='card-empty'>Results will be emailed after approval.</div>",
                "<div class='card-empty'>Results will be emailed after approval.</div>",
                "",

                programs,                                   # programs_state stored anyway
                gr.update(choices=make_compare_choices(programs), value=[]),
                gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
            )

        # Otherwise: show dashboard normally
        timeline_html = render_timeline(profile, timeline_events)
        programs_html = render_program_cards(programs)
        checklist_html = render_checklist(projects)
        choices = make_compare_choices(programs)

        return (
            gr.update(value=""),
            gr.update(value=note),
            gr.update(visible=False),
            gr.update(visible=True),
            "outputs",

            gr.update(value="", visible=False),  # email_notice hidden
            gr.update(visible=True),             # tabs visible

            timeline_html,
            programs_html,
            checklist_html,
            full_md,

            programs,
            gr.update(choices=choices, value=[]),
            gr.update(value="<div class='card-empty'>Pick programs to compare.</div>"),
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

            student["email_notice"],
            student["dashboard_tabs"],

            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],

            programs_state,
            student["compare_select"],
            student["compare_table"],
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

    # Follow-up (only updates Full Plan markdown)
    def followup(question, current_md, session_id):
        cleared_q, new_md = controllers.handle_followup(question, current_md, session_id)
        return cleared_q, new_md

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


if __name__ == "__main__":
    app = create_app()
    # css/theme stored on app in create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=getattr(app, "_saarthi_css", None),
        theme=getattr(app, "_saarthi_theme", None),
    )
