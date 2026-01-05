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
    student["preset_eng"].click(fn=lambda: ["Engineering"], inputs=[], outputs=[student["interest_tags_input"]])
    student["preset_cs"].click(fn=lambda: ["Computer Science"], inputs=[], outputs=[student["interest_tags_input"]])
    student["preset_bus"].click(fn=lambda: ["Business/Commerce"], inputs=[], outputs=[student["interest_tags_input"]])
    student["preset_hs"].click(fn=lambda: ["Health Sciences"], inputs=[], outputs=[student["interest_tags_input"]])

    # LOGIN
    login["start_btn"].click(
        fn=controllers.handle_start_session,
        inputs=[login["name_input"]],
        outputs=[
            login["section"],
            student["section"],
            student["output_display"],
            session_state,
        ],
    )

    # Generate Roadmap
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

        timeline_html = render_timeline(plan.get("profile", {}), plan.get("phases", []))
        programs_html = render_program_cards(plan.get("programs", []))
        checklist_html = render_checklist(plan.get("phases", []))
        full_md = plan.get("md", "")

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

    # Follow-up (structured render from session-stored plan)
    def followup_and_render(question, session_id):
        plan = controllers.handle_followup(question, session_id)

        timeline_html = render_timeline(plan.get("profile", {}), plan.get("phases", []))
        programs_html = render_program_cards(plan.get("programs", []))
        checklist_html = render_checklist(plan.get("phases", []))
        full_md = plan.get("md", "")

        return "", timeline_html, programs_html, checklist_html, full_md

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
