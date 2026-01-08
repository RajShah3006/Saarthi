# app.py - Two-page flow (Inputs Wizard -> Fullscreen Outputs) + Thin wiring

import gradio as gr
import logging
import sys
from typing import Any, Dict

from config import Config
from controllers import Controllers
from ui.layout import create_ui_layout
from ui.styles import get_css

from utils.dashboard_renderer import render_program_cards, render_checklist, render_timeline


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("saarthi")


def create_app():
    logger.info("=" * 50)
    logger.info(" Initializing Saarthi AI")
    logger.info("=" * 50)

    config = Config()
    controllers = Controllers(config)

    logger.info(f" Data directory: {config.DATA_DIR}")
    logger.info(f" AI Service: {'Enabled' if config.GEMINI_API_KEY else 'Demo Mode'}")
    logger.info(f" Programs loaded: {len(controllers.program_search.programs)}")

    css = get_css(config)
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="purple",
        neutral_hue="slate",
    )

    # Gradio 6+: pass css/theme to launch() (not Blocks) to avoid warning
    with gr.Blocks(title="Saarthi AI - University Guidance") as app:
        components = create_ui_layout(config)
        wire_events(components, controllers)
        logger.info("✅ App initialized successfully")

    launch_kwargs = dict(css=css, theme=theme)
    return app, launch_kwargs


def wire_events(components: dict, controllers: Controllers):
    session_state = components["session_state"]
    login = components["login"]
    student = components["student"]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def build_review(subjects, tags, details, extracurriculars, average, grade, location, preferences):
        subjects_str = ", ".join(subjects or []) or "—"
        tags_str = ", ".join(tags or []) or "—"
        details = (details or "").strip() or "—"
        extracurriculars = (extracurriculars or "").strip() or "—"
        location = (location or "").strip() or "—"
        preferences = (preferences or "").strip() or "—"
        return (
            f"**Grade:** {grade}  \n"
            f"**Average:** {average}%  \n"
            f"**Location:** {location}  \n\n"
            f"**Subjects:** {subjects_str}  \n\n"
            f"**Interests:** {tags_str}  \n"
            f"**Details:** {details}  \n\n"
            f"**Extracurriculars:** {extracurriculars}  \n"
            f"**Preferences:** {preferences}"
        )

    def safe_plan_dict(plan_raw: Any) -> Dict[str, Any]:
        """
        Normalize controller output into:
        { "md": str, "profile": dict, "programs": list, "phases": list }

        Supports:
        - dict (preferred)
        - markdown string (legacy)
        - tuple/list (md, programs, phases, profile) from earlier refactors
        """
        if isinstance(plan_raw, dict):
            return {
                "md": plan_raw.get("md", "") or "",
                "profile": plan_raw.get("profile", {}) or {},
                "programs": plan_raw.get("programs", []) or [],
                "phases": plan_raw.get("phases", []) or [],
            }

        if isinstance(plan_raw, (tuple, list)) and len(plan_raw) == 4:
            md, programs, phases, profile = plan_raw
            return {
                "md": md or "",
                "profile": profile or {},
                "programs": programs or [],
                "phases": phases or [],
            }

        # fallback: treat as markdown string
        return {"md": plan_raw or "", "profile": {}, "programs": [], "phases": []}

    # ------------------------------------------------------------------
    # Wizard step navigation
    # ------------------------------------------------------------------
    def set_step(step: int):
        step = max(1, min(4, int(step)))
        return (
            step,
            gr.update(value=f"**Step {step} of 4**"),
            gr.update(visible=(step == 1)),
            gr.update(visible=(step == 2)),
            gr.update(visible=(step == 3)),
            gr.update(visible=(step == 4)),
            gr.update(visible=(step > 1)),          # back visible
            gr.update(visible=(step < 4)),          # next visible
            gr.update(interactive=(step == 4)),     # generate enabled only on step 4
        )

    def on_next(step, subjects, tags, details, extracurriculars, average, grade, location, preferences):
        new_step = min(4, int(step) + 1)
        base = set_step(new_step)

        review = gr.update()
        if new_step == 4:
            review = gr.update(
                value=build_review(subjects, tags, details, extracurriculars, average, grade, location, preferences)
            )

        # base returns 9 outputs; review_box is 10th
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

    # ------------------------------------------------------------------
    # Preset buttons (optional)
    # ------------------------------------------------------------------
    if "preset_eng" in student:
        student["preset_eng"].click(fn=lambda: ["Engineering"], inputs=[], outputs=[student["interest_tags_input"]])
    if "preset_cs" in student:
        student["preset_cs"].click(fn=lambda: ["Computer Science"], inputs=[], outputs=[student["interest_tags_input"]])
    if "preset_bus" in student:
        student["preset_bus"].click(fn=lambda: ["Business/Commerce"], inputs=[], outputs=[student["interest_tags_input"]])
    if "preset_hs" in student:
        student["preset_hs"].click(fn=lambda: ["Health Sciences"], inputs=[], outputs=[student["interest_tags_input"]])

    # ------------------------------------------------------------------
    # Login -> show student section and reset to INPUTS view
    # ------------------------------------------------------------------
    def start_and_reset(name: str):
        login_update, student_update, welcome_md, sid = controllers.handle_start_session(name)

        # force: show inputs page, hide outputs page, reset wizard to step 1
        step = 1
        step_updates = set_step(step)

        return (
            login_update,
            student_update,
            welcome_md,
            sid,
            gr.update(visible=True),     # inputs_view
            gr.update(visible=False),    # outputs_view
            *step_updates,               # wizard_step..generate_btn updates
            gr.update(value="Fill earlier steps to preview here."),  # review_box
        )

    login["start_btn"].click(
        fn=start_and_reset,
        inputs=[login["name_input"]],
        outputs=[
            login["section"],
            student["section"],
            student["output_display"],   # welcome text goes into Full Plan (hidden until outputs view, but ok)
            session_state,

            student["inputs_view"],
            student["outputs_view"],

            student["wizard_step"],
            student["step_label"],
            student["step1"], student["step2"], student["step3"], student["step4"],
            student["back_btn"], student["next_btn"],
            student["generate_btn"],

            student["review_box"],
        ],
    )

    # ------------------------------------------------------------------
    # Generate Roadmap -> render + switch to OUTPUTS fullscreen
    # ------------------------------------------------------------------
    def generate_and_render(subjects, interest_tags, interest_details, extracurriculars, average, grade, location, preferences, session_id):
        tags = [t.strip() for t in (interest_tags or []) if t and t.strip()]
        details = (interest_details or "").strip()

        if tags and details:
            interests = f"{', '.join(tags)}; Details: {details}"
        elif tags:
            interests = ", ".join(tags)
        else:
            interests = details

        plan_raw = controllers.handle_generate_roadmap(
            subjects,
            interests,
            extracurriculars,
            average,
            grade,
            location,
            preferences,
            session_id,
        )

        plan = safe_plan_dict(plan_raw)

        timeline_html = render_timeline(plan.get("profile", {}) or {}, plan.get("phases", []) or [])
        programs_html = render_program_cards(plan.get("programs", []) or [])
        checklist_html = render_checklist(plan.get("phases", []) or [])
        full_md = plan.get("md", "") or ""

        return (
            timeline_html,
            programs_html,
            checklist_html,
            full_md,
            gr.update(visible=False),  # inputs_view OFF
            gr.update(visible=True),   # outputs_view ON
        )

    student["generate_btn"].click(
        fn=generate_and_render,
        inputs=[
            student["subjects_input"],
            student["interest_tags_input"],
            student["interest_details_input"],
            student["extracurriculars_input"],
            student["average_input"],
            student["grade_input"],
            student["location_input"],
            student["preferences_input"],
            session_state,
        ],
        outputs=[
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
            student["inputs_view"],
            student["outputs_view"],
        ],
    )

    # ------------------------------------------------------------------
    # "Edit Inputs" button -> switch back to INPUTS fullscreen
    # ------------------------------------------------------------------
    def show_inputs():
        return gr.update(visible=True), gr.update(visible=False)

    student["edit_inputs_btn"].click(
        fn=show_inputs,
        inputs=[],
        outputs=[student["inputs_view"], student["outputs_view"]],
    )

    # ------------------------------------------------------------------
    # Clear form (optional: also bring them back to step 1)
    # ------------------------------------------------------------------
    def clear_and_reset():
        cleared = controllers.handle_clear_form()
        step_updates = set_step(1)
        return (
            *cleared,
            *step_updates,
            gr.update(value="Fill earlier steps to preview here."),
        )

    student["clear_btn"].click(
        fn=clear_and_reset,
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

            student["wizard_step"],
            student["step_label"],
            student["step1"], student["step2"], student["step3"], student["step4"],
            student["back_btn"], student["next_btn"],
            student["generate_btn"],

            student["review_box"],
        ],
    )

    # ------------------------------------------------------------------
    # Follow-up -> update outputs (keep outputs view visible)
    # Controller signature assumed: (question, current_md, session_id)
    # ------------------------------------------------------------------
    def followup_and_render(question, current_md, session_id):
        plan_raw = controllers.handle_followup(question, current_md, session_id)
        plan = safe_plan_dict(plan_raw)

        timeline_html = render_timeline(plan.get("profile", {}) or {}, plan.get("phases", []) or [])
        programs_html = render_program_cards(plan.get("programs", []) or [])
        checklist_html = render_checklist(plan.get("phases", []) or [])
        full_md = plan.get("md", "") or ""

        return "", timeline_html, programs_html, checklist_html, full_md

    student["send_btn"].click(
        fn=followup_and_render,
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
        fn=followup_and_render,
        inputs=[student["followup_input"], student["output_display"], session_state],
        outputs=[
            student["followup_input"],
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
        ],
    )


if __name__ == "__main__":
    app, launch_kwargs = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        **launch_kwargs,
    )
