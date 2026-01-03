# app.py
import gradio as gr

from controllers import Controllers
from config import Config
from ui.layout import create_ui_layout
from utils.roadmap_renderer import render_roadmap_bundle
from templates import get_system_prompt


def create_app():
    config = Config()
    controllers = Controllers(config=config)

    demo, components = create_ui_layout()
    wire_events(components, controllers)

    return demo


def wire_events(components, controllers: Controllers):
    student = components["inputs"]
    outputs = components["outputs"]
    session_state = components["session_state"]

    # --- Events ---
    def start_session():
        return controllers.session_manager.create_session()

    def generate_and_render(
        subjects,
        interests,
        extracurriculars,
        average,
        grade,
        location,
        preferences,
        preferences_other,
        session_id,
    ):
        # Ensure session exists
        if not session_id:
            session_id = start_session()

        result = controllers.handle_generate_roadmap(
            subjects=subjects,
            interests=interests,
            extracurriculars=extracurriculars,
            average=average,
            grade=grade,
            location=location,
            preferences=preferences,
            preferences_other=preferences_other,
            session_id=session_id,
        )

        if not result.ok:
            html_error = f"""
            <div class="glass-card">
                <h3>⚠️ Something went wrong</h3>
                <p>{result.error}</p>
            </div>
            """
            return (
                session_id,
                html_error,
                "",
                "",
                "",
                "",
            )

        # Render bundle
        rendered = render_roadmap_bundle(result.data)

        return (
            session_id,
            rendered["roadmap_html"],
            rendered["programs_html"],
            rendered["checklist_html"],
            rendered["full_plan_html"],
            rendered["qa_html"],
        )

    # Start session on load (optional, but helps)
    components["outputs"]["roadmap_output"].change(
        fn=lambda x: x,
        inputs=components["outputs"]["roadmap_output"],
        outputs=components["outputs"]["roadmap_output"],
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
            student["preferences_input"],
            student["preferences_other_input"],
            session_state,
        ],
        outputs=[
            session_state,
            outputs["roadmap_output"],
            outputs["programs_output"],
            outputs["checklist_output"],
            outputs["full_plan_output"],
            outputs["qa_output"],
        ],
    )

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
            student["preferences_input"],
            student["preferences_other_input"],
        ],
    )


if __name__ == "__main__":
    demo = create_app()
    demo.launch()
