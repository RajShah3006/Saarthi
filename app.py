# app.py - Gradio wiring only (thin)

import gradio as gr
import logging
import sys

from config import Config
from controllers import Controllers
from ui.layout import create_ui_layout
from ui.styles import get_css

# NEW: renders markdown roadmap into dashboard HTML blocks
from utils.roadmap_renderer import render_roadmap_bundle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("saarthi")


def create_app() -> gr.Blocks:
    """Create and wire the Gradio application"""
    logger.info("=" * 50)
    logger.info(" Initializing Saarthi AI")
    logger.info("=" * 50)

    # Initialize config and controllers
    config = Config()
    controllers = Controllers(config)

    # Log startup info
    logger.info(f" Data directory: {config.DATA_DIR}")
    logger.info(f" AI Service: {'Enabled' if config.GEMINI_API_KEY else 'Demo Mode'}")
    logger.info(f" Programs loaded: {len(controllers.program_search.programs)}")

    # Build UI
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
        # Create UI layout and get component references
        components = create_ui_layout(config)

        # Wire events to controllers
        wire_events(components, controllers)

        logger.info("✅ App initialized successfully")

    return app


def wire_events(components: dict, controllers: Controllers):
    """Wire UI events to controller methods"""
    session_state = components["session_state"]
    login = components["login"]
    student = components["student"]
    admin = components["admin"]  # kept for future use

    # =====================
    # LOGIN EVENTS
    # =====================
    login["start_btn"].click(
        fn=controllers.handle_start_session,
        inputs=[login["name_input"]],
        outputs=[
            login["section"],
            student["section"],
            student["output_display"],  # Full Plan tab markdown
            session_state,
        ],
    )

    # =====================
    # STUDENT EVENTS
    # =====================

    # --- Generate Roadmap: update ALL dashboard views ---
    def generate_and_render(subjects, interests, extracurriculars, average, grade, location, budget, session_id):
        md = controllers.handle_generate_roadmap(
            subjects,
            interests,
            extracurriculars,
            average,
            grade,
            location,
            budget,
            session_id,
        )
        bundle = render_roadmap_bundle(md)
        return (
            bundle["timeline_html"],
            bundle["programs_html"],
            bundle["checklist_html"],
            bundle["full_md"],
        )

    student["generate_btn"].click(
        fn=generate_and_render,
        inputs=[
            student["subjects_input"],
            student["interests_input"],
            student["extracurriculars_input"],
            student["average_input"],
            student["grade_input"],
            student["location_input"],
            student["budget_input"],
            session_state,
        ],
        outputs=[
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
        ],
    )

    # --- Clear form ---
    student["clear_btn"].click(
        fn=controllers.handle_clear_form,
        inputs=[],
        outputs=[
            student["subjects_input"],
            student["interests_input"],
            student["extracurriculars_input"],
            student["average_input"],
            student["grade_input"],
            student["location_input"],
            student["budget_input"],
        ],
    )

    # --- Follow-up: update Q&A + ALL dashboard views ---
    def followup_and_render(question, current_md, session_id):
        cleared_q, new_md = controllers.handle_followup(question, current_md, session_id)
        bundle = render_roadmap_bundle(new_md)
        return (
            cleared_q,
            bundle["timeline_html"],
            bundle["programs_html"],
            bundle["checklist_html"],
            bundle["full_md"],
        )

    student["send_btn"].click(
        fn=followup_and_render,
        inputs=[
            student["followup_input"],
            student["output_display"],
            session_state,
        ],
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
        inputs=[
            student["followup_input"],
            student["output_display"],
            session_state,
        ],
        outputs=[
            student["followup_input"],
            student["timeline_display"],
            student["programs_display"],
            student["checklist_display"],
            student["output_display"],
        ],
    )


# Launch
if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
