# ui/layout.py
import gradio as gr
from config import GRADE_OPTIONS, BUDGET_OPTIONS
from ui.styles import get_css, get_theme


def create_ui_layout():
    css = get_css()
    theme = get_theme()

    with gr.Blocks(theme=theme, css=css) as demo:
        session_state = gr.State("")

        # Header
        gr.HTML(
            """
            <div class="saarthi-header">
                <div class="saarthi-title">Saarthi AI 🏹</div>
                <div class="saarthi-subtitle">Ontario-wide university program roadmap + recommendations</div>
            </div>
            """
        )

        # Main Tabs
        with gr.Tabs(elem_classes="tabs-container"):
            with gr.Tab("🎯 Roadmap", elem_id="tab-roadmap"):
                with gr.Row():
                    # Left panel - Student Profile Form
                    with gr.Column(scale=1, elem_classes="glass-card"):
                        gr.Markdown("## Student Profile")
                        gr.Markdown("Fill this in to get a personalized roadmap and program suggestions.")

                        # Inputs
                        with gr.Group():
                            subjects_input = gr.CheckboxGroup(
                                choices=[
                                    "English (ENG4U)",
                                    "Advanced Functions (MHF4U)",
                                    "Calculus & Vectors (MCV4U)",
                                    "Data Management (MDM4U)",
                                    "Physics (SPH4U)",
                                    "Chemistry (SCH4U)",
                                    "Biology (SBI4U)",
                                    "Computer Science (ICS4U)",
                                    "Business (BBB4M)",
                                    "Other",
                                ],
                                label="Current/Planned Grade 12 Subjects",
                                info="Select all that apply",
                            )

                            interests_input = gr.Textbox(
                                label="What field are you interested in?",
                                placeholder="e.g., Robotics, Nursing, Business, Computer Science, Trades...",
                                elem_classes="glass-input",
                            )

                            extracurriculars_input = gr.Textbox(
                                label="What activities do you enjoy?",
                                placeholder="e.g., coding club, sports, volunteering, design projects...",
                                elem_classes="glass-input",
                            )

                            average_input = gr.Slider(
                                minimum=50,
                                maximum=100,
                                step=1,
                                value=85,
                                label="Current Average (%)",
                                info="Rough estimate is fine",
                            )

                            grade_input = gr.Dropdown(
                                choices=GRADE_OPTIONS,
                                value="Grade 12",
                                label="Current Grade",
                            )

                            location_input = gr.Textbox(
                                label="Preferred Location (optional)",
                                placeholder="e.g., Toronto, GTA, Ottawa, Anywhere in Ontario",
                                elem_classes="glass-input",
                            )

                            # What matters to you? (choose + optional custom)
                            preferences_input = gr.CheckboxGroup(
                                choices=[
                                    "Co-op / internships",
                                    "Hands-on / project-based learning",
                                    "Close to home",
                                    "Top-ranked / prestigious program",
                                    "Easier admission / safer options",
                                    "Scholarships / financial aid",
                                    "Strong campus life",
                                    "Small class sizes",
                                    "Urban campus",
                                    "Research opportunities",
                                ],
                                label="What matters most to you?",
                                info="Pick anything that’s important (you can choose multiple).",
                            )

                            preferences_other_input = gr.Textbox(
                                label="Other preferences (optional)",
                                placeholder="e.g., 'strong robotics club' or 'AI electives' or 'more hands-on labs'",
                                elem_classes="glass-input",
                                lines=2,
                            )

                        # Buttons
                        with gr.Row():
                            generate_btn = gr.Button("🚀 Generate My Roadmap", variant="primary")
                            clear_btn = gr.Button("🧹 Clear", variant="secondary")

                    # Right panel - Output
                    with gr.Column(scale=2):
                        roadmap_output = gr.HTML(
                            value="""
                            <div class="glass-card">
                                <h3>Welcome 👋</h3>
                                <p>Fill out the profile form and click <b>Generate My Roadmap</b> to get:</p>
                                <ul>
                                    <li>✅ A personalized roadmap for your field</li>
                                    <li>🎓 Top Ontario program recommendations</li>
                                    <li>📋 A checklist of next steps</li>
                                </ul>
                            </div>
                            """
                        )

                        # Program recommendations
                        programs_output = gr.HTML()

                        # Checklist
                        checklist_output = gr.HTML()

                        # Full plan (roadmap + programs + checklist)
                        full_plan_output = gr.HTML()

                        # Q&A
                        qa_output = gr.HTML()

        components = {
            "session_state": session_state,
            "inputs": {
                "subjects_input": subjects_input,
                "interests_input": interests_input,
                "extracurriculars_input": extracurriculars_input,
                "average_input": average_input,
                "grade_input": grade_input,
                "location_input": location_input,
                "preferences_input": preferences_input,
                "preferences_other_input": preferences_other_input,
                "generate_btn": generate_btn,
                "clear_btn": clear_btn,
            },
            "outputs": {
                "roadmap_output": roadmap_output,
                "programs_output": programs_output,
                "checklist_output": checklist_output,
                "full_plan_output": full_plan_output,
                "qa_output": qa_output,
            },
        }

    return demo, components
