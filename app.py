# app.py
import gradio as gr
import logging
import sys

from config import Config
from controllers import Controllers
from ui.layout import create_ui_layout
from ui.styles import get_css

from utils.dashboard_renderer import render_program_cards, render_checklist, render_timeline

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

    # =====================
    # SIDEBAR TOGGLE (must be inside wire_events)
    # =====================
    def toggle_sidebar(collapsed: bool):
        collapsed = bool(collapsed)
        new_collapsed = not collapsed
        label = "Show Inputs ▶" if new_collapsed else "Hide Inputs ◀"
        return (
            gr.update(visible=not new_collapsed),  # sidebar column visibility
            new_collapsed,                         # sidebar state
            gr.update(value=label),                # button text
        )

    # These keys MUST exist in create_ui_layout():
    # student["sidebar_col"], student["sidebar_state"], student["sidebar_toggle_btn"]
    student["sidebar_toggle_btn"].click(
        fn=toggle_sidebar,
        inputs=[student["sidebar_state"]],
        outputs=[student["sidebar_col"], student["sidebar_state"], student["sidebar_toggle_btn"]],
    )

    # =====================
    # PRESETS (inside wire_events)
    # =====================
    student["preset_eng"].click(fn=lambda: ["Engineering"], inputs=[], outputs=[student["interest_tags_input"]])
    student["preset_cs"].click(fn=lambda: ["Computer Science"], inputs=[], outputs=[student["interest_tags_input"]])
    student["preset_bus"].click(fn=lambda: ["Business/Commerce"], inputs=[], outputs=[student["interest_tags_input"]])
    student["preset_hs"].click(fn=lambda: ["Health Sciences"], inputs=[], outputs=[student["interest_tags_input"]])

    # =====================
    # LOGIN
    # =====================
    login["start_btn"].click(
        fn=controllers.handle_start_session,
        inputs=[login["name_input"]],
        outputs=[
            login["section"],
            student["section"],
            student["output_display"],  # Full plan markdown
            session_state,
        ],
    )

    # =====================
    # Generate Roadmap
    # =====================
    def generate_and_render(subjects, interest_tags, interest_details, extracurriculars, average, grade, location, preferences, session_id):
        tags = [t.strip() for t in (interest_tags or []) if t and t.strip()]
        details = (interest_details or "").strip()

        if tags and details:
            interests = f"{', '.join(tags)}; Details: {details}"
        elif tags:
            interests = ", ".join(tags)
        else:
            interests = details

        plan = controllers.handle_generate_roadmap(
            subjects,
            interests,
            extracurriculars,
            average,
            grade,
            location,
            preferences,
            session_id,
        )

        # EXPECTED (recommended) plan dict:
        # { "md": "...", "profile": {...}, "programs": [...], "phases": [...] }
        if isinstance(plan, dict):
            timeline_html = render_timeline(plan.get("profile", {}), plan.get("phases", []))
            programs_html = render_program_cards(plan.get("programs", []))
            checklist_html = render_checklist(plan.get("phases", []))
            full_md = plan.get("md", "") or ""
            return timeline_html, programs_html, checklist_html, full_md

        # fallback if controller still returns markdown string
        full_md = plan or ""
        return (
            "<div class='card-empty'>Timeline unavailable (controller returned markdown only).</div>",
            "<div class='card-empty'>Programs unavailable (controller returned markdown only).</div>",
            "<div class='card-empty'>Checklist unavailable (controller returned markdown only).</div>",
            full_md,
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
        ],
    )

    # =====================
    # Clear form
    # =====================
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

    # =====================
    # Follow-up
    # =====================
    # IMPORTANT:
    # - If your controller followup still expects (question, current_md, session_id),
    #   keep current_md in inputs.
    # - If you refactored it to (question, session_id) and it returns a plan dict,
    #   then this matches.

    def followup_and_render(question, session_id):
        plan = controllers.handle_followup(question, session_id)

        if isinstance(plan, dict):
            timeline_html = render_timeline(plan.get("profile", {}), plan.get("phases", []))
            programs_html = render_program_cards(plan.get("programs", []))
            checklist_html = render_checklist(plan.get("phases", []))
            full_md = plan.get("md", "") or ""
            return "", timeline_html, programs_html, checklist_html, full_md

        # fallback
        return "", gr.update(), gr.update(), gr.update(), (plan or "")

    student["send_btn"].click(
        fn=followup_and_render,
        inputs=[student["followup_input"], session_state],
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
        inputs=[student["followup_input"], session_state],
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
