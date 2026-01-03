import logging
import os

import gradio as gr

from config import Config
from controllers import Controllers
from session import SessionManager
from services.llm_client import LLMClient
from services.program_search import ProgramSearchService
from services.roadmap import RoadmapService
from ui.layout import create_ui_layout
from ui.roadmap_renderer import RoadmapRenderer
from ui.styles import SAARTHI_CSS


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger("saarthi")


def create_app():
    setup_logging()

    logger.info("=" * 50)
    logger.info(" Initializing Saarthi AI")
    logger.info("=" * 50)

    # Load configuration
    config = Config()

    # Initialize services
    session_manager = SessionManager()
    llm_client = LLMClient(config)
    program_search = ProgramSearchService(config)
    roadmap_service = RoadmapService(config, llm_client, program_search)

    # Initialize controllers
    controllers = Controllers(session_manager, program_search, roadmap_service)

    # UI renderer (turns roadmap markdown into the styled HTML/blocks)
    renderer = RoadmapRenderer()

    # Create UI
    with gr.Blocks(
        title="Saarthi AI 🏹 | Your Personal Guide",
        theme=gr.themes.Soft(),
        css=SAARTHI_CSS,
    ) as app:

        components = create_ui_layout()

        # Wire events
        def generate_and_render(
            subjects,
            interests,
            extracurriculars,
            average,
            grade,
            location,
            preferences,
            preferences_free_text,
            session_id,
        ):
            status, roadmap_md, new_session = controllers.handle_generate_roadmap(
                subjects,
                interests,
                extracurriculars,
                average,
                grade,
                location,
                preferences,
                preferences_free_text,
                session_id,
            )
            rendered = renderer.render(roadmap_md) if roadmap_md else ""
            return status, rendered, new_session

        components["generate_btn"].click(
            fn=generate_and_render,
            inputs=[
                components["subjects_input"],
                components["interests_input"],
                components["extracurriculars_input"],
                components["average_input"],
                components["grade_input"],
                components["location_input"],
                components["preferences_input"],
                components["preferences_free_text"],
                components["session_id"],
            ],
            outputs=[
                components["status_output"],
                components["roadmap_output"],
                components["session_id"],
            ],
        )

        components["clear_btn"].click(
            fn=controllers.handle_clear_form,
            inputs=[],
            outputs=[
                components["subjects_input"],
                components["interests_input"],
                components["extracurriculars_input"],
                components["average_input"],
                components["grade_input"],
                components["location_input"],
                components["preferences_input"],
                components["preferences_free_text"],
            ],
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
    )
