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
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("saarthi")


def create_app() -> gr.Blocks:
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
        title="Saarthi AI 🏹",
        css=css,
        analytics_enabled=False
    ) as app:
        components = create_ui_layout(config)

        # Wire events
        controllers.wire_events(components, render_roadmap_bundle)

    logger.info("✅ App initialized successfully")
    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
