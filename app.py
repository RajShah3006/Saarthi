# app.py - Gradio wiring only (thin) + Wizard + Collapsible Sidebar (right column expands)

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


def create_app() -> gr.Blocks:
    logger.info("=" * 50)
    logger.info(" Initializing Saarthi AI")
    logger.info("=" * 50)

    config = Config()
    controllers = Controllers(config)

    logger.info(f" Data directory: {config.DATA_DIR}")
    logger.info(f" AI Service: {'Enabled' if config.GEMINI_API_KEY else 'Demo Mode'}")
    logger.info(f" Programs loaded: {len(controllers.program_search.programs)}")

    css = get_css(config)

    with gr.Blocks(
        title="Saarthi AI - University Guidance",
        css=css,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="purple",
            neutral_hue="slate",
        ),
    ) as app:
        components = create_ui_layout(config)
        wire_events(components, controllers)
        logger.info("✅ App initialized successfully")

    return app


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

    def safe_plan_dict(plan: Any) -> Dict[str, Any]:
        """
        Controllers should ideally return a dict:
        { "md": "...", "profile": {...}, "programs": [...], "phases": [...] }
        If not, we degrade gracefully.
        """
        if isinstance(plan, dict):
            return plan
        # fallback: treat as markdown string
        return {"md": plan or "", "profile": {}, "programs": [], "phases": []}

    # ------------------------------------------------------------------
    # Wizard (Step-by-step inputs)
    # IMPORTANT: This avoids relying on State.change (can be flaky)
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
            gr.update(interactive=(step == 4)),     # ✅ generate enabled only on step 4
        )

    def on_next(step, subjects, tags, details, extracurriculars, average, grade, location, preferences):
        new_step = min(4, int(step) + 1)
        base = set_step(new_step)

        review = gr.update()
        if new_step == 4:
            review = gr.update(
                value=build_review(subjects, tags, details, extracurriculars, average, grade, location, preferences)
            )

        # base returns 9 outputs, then add review_box as 10th
        return (*base, review)

    def on_back(step):
        # set_step returns 9 outputs (no review update here)
        return set_step(max(1, int(step) - 1))

    # These keys MUST exist in create_ui_layout(config) -> student dict:
    # wizard_step, step_label, step1..step4, back_btn, next_btn, generate_btn, review_box
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
    # Sidebar Toggle (hide left inputs + make right take full width)
    # ------------------------------------------------------------------
    def toggle_sidebar(collapsed: bool):
        collapsed = bool(collapsed)
        new_collapsed = not collapsed
        label = "Show Inputs ▶" if new_collapsed else "Hide Inputs ◀"

        # dashboard_col must exist in layout and be returned in student dict
        # scale: 3 when expanded, 2 when normal (adjust as you like)
        return (
            gr.update(visible=not new_collapsed),                 # sidebar column visibility
            new_collapsed,                                        # sidebar state
            gr.update(value=label),                               # button text
            gr.update(scale=3 if new_collapsed else 2),           # ✅ dashboard expands
        )

    # These keys MUST exist in create_ui_layout():
    # student["sidebar_col"], student["sidebar_state"], student["sidebar_toggle_btn"], student["dashboard_col"]
    student["sidebar_toggle_btn"].click(
        fn=toggle_sidebar,
        inputs=[student["sidebar_state"]],
        outputs=[
            student["sidebar_col"],
            student["sidebar_state"],
            student["sidebar_toggle_btn"],
            student["dashboard_col"],
        ],
    )

    # ------------------------------------------------------------------
    # Preset buttons (optional)
    # ------------------------------------------------------------------
    # These keys must exist only if you created these buttons in the layout.
    if "preset_eng" in student:
        student["preset_eng"].click(fn=lambda: ["Engineering"], inputs=[], outputs=[student["interest_tags_input"]])
    if "preset_cs" in student:
        student["preset_cs"].click(fn=lambda: ["Computer Science"], inputs=[], outputs=[student["interest_tags_input"]])
    if "preset_bus" in student:
        student["preset_bus"].click(fn=lambda: ["Business/Commerce"], inputs=[], outputs=[student["interest_tags_input"]])
    if "preset_hs" in student:
        student["preset_hs"].click(fn=lambda: ["Health Sciences"], inputs=[], outputs=[student["interest_tags_input"]])

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    login["start_btn"].click(
        fn=controllers.handle_start_session,
        inputs=[login["name_input"]],
        outputs=[
            login["section"],
            student["section"],
            student["output_display"],  # Full plan markdown tab
            session_state,
        ],
    )

    # ------------------------------------------------------------------
    # Generate Roadmap (renders dashboard blocks + full markdown)
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

        return timeline_html, programs_html, checklist_html, full_md

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
        ],
    )

    # ------------------------------------------------------------------
    # Clear form
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Follow-up
    # NOTE:
    # - If your controller signature is still (question, current_md, session_id),
    #   you must pass current_md in inputs.
    # - If you refactored it to (question, session_id) and return a plan dict, keep as is.
    # ------------------------------------------------------------------
    def followup_and_render(question, current_md, session_id):
        # If your controller expects 3 args:
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
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )

