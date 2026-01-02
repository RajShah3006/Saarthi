# ui/layout.py - UI components (Roadmap Dashboard)

import gradio as gr
from config import Config

COURSES = sorted([
    "Advanced Functions (MHF4U)", "Calculus & Vectors (MCV4U)",
    "Data Management (MDM4U)", "English (ENG4U)",
    "Biology (SBI4U)", "Chemistry (SCH4U)", "Physics (SPH4U)",
    "Computer Science (ICS4U)", "Business Leadership (BOH4M)",
    "Functions (MCR3U)", "English (ENG3U)", "Biology (SBI3U)",
    "Chemistry (SCH3U)", "Physics (SPH3U)", "Computer Science (ICS3U)",
    "World History (CHW3M)", "Law (CLU3M)", "Accounting (BAF3M)",
])


def create_ui_layout(config: Config) -> dict:
    """Create the complete UI layout and return component references"""

    session_state = gr.State("")
    status_text = "" if config.GEMINI_API_KEY else ""

    # === LOGIN SECTION ===
    with gr.Column(visible=True, elem_classes="glass-panel") as login_section:
        gr.Markdown("### Welcome!")
        gr.Markdown("Enter your name to get started with personalized university guidance.")

        name_input = gr.Textbox(
            label="Your Name",
            placeholder="Enter your name",
            elem_classes="glass-input"
        )
        start_btn = gr.Button(
            "Start Session →",
            variant="primary",
            elem_classes="primary-btn"
        )
        gr.Markdown("*No account needed - your session data stays in your browser only.*",
                    elem_classes="hint-text")

    # === STUDENT DASHBOARD ===
    with gr.Column(visible=False, elem_classes="glass-panel") as student_section:
        with gr.Row():
            # Left: Form
            with gr.Column(scale=1, min_width=320):
                gr.Markdown(f"**Status:** {status_text}")

                subjects_input = gr.Dropdown(
                    choices=COURSES,
                    multiselect=True,
                    label="Current/Planned Subjects",
                    info="Select courses you're taking or plan to take",
                    elem_classes="glass-input"
                )

                interests_input = gr.Textbox(
                    label="Academic Interests *",
                    placeholder="e.g., Computer Science, Medicine, Business",
                    info="What fields interest you?",
                    elem_classes="glass-input",
                    lines=2
                )

                extracurriculars_input = gr.Textbox(
                    label="Extracurricular Activities",
                    placeholder="e.g., Robotics Club, Debate Team, Volunteering",
                    elem_classes="glass-input",
                    lines=2
                )

                with gr.Row():
                    average_input = gr.Slider(
                        minimum=50, maximum=100, value=85, step=1,
                        label="Current Average %"
                    )
                    grade_input = gr.Dropdown(
                        choices=config.GRADE_OPTIONS,
                        value="Grade 12",
                        label="Grade Level"
                    )

                location_input = gr.Textbox(
                    label="Location",
                    placeholder="e.g., Toronto, ON",
                    elem_classes="glass-input"
                )

                # ✅ Preferences (optional): pick from suggestions OR type your own
                PREFERENCE_SUGGESTIONS = [
                    "Co-op / internships",
                    "Scholarships / financial aid",
                    "Hands-on / lab-heavy learning",
                    "Robotics / competitions / clubs",
                    "Strong job outcomes",
                    "Research opportunities",
                    "Small class sizes",
                    "Big-city campus",
                    "Closer to home",
                    "Lower tuition / cost",
                    "Flexible / hybrid options",
                ]

                preferences_input = gr.Dropdown(
                    choices=PREFERENCE_SUGGESTIONS,
                    value=[],
                    multiselect=True,
                    allow_custom_value=True,  # type custom preference, press Enter
                    label="Preferences (optional)",
                    info="Pick a few or type your own (press Enter).",
                    elem_classes="glass-input",
                )

                preferences_free_text = gr.Textbox(
                    label="Anything else? (optional)",
                    placeholder="e.g., Only Ontario, close to Toronto, guaranteed co-op, strong mechatronics focus…",
                    lines=2,
                    elem_classes="glass-input",
                )

                with gr.Row():
                    clear_btn = gr.Button("Clear", elem_classes="secondary-btn")
                    generate_btn = gr.Button(
                        "Generate Roadmap",
                        variant="primary",
                        elem_classes="primary-btn"
                    )

            # Right: Roadmap Dashboard
            with gr.Column(scale=2, min_width=520):
                gr.Markdown("### Your Roadmap Dashboard")

                with gr.Tabs(elem_id="roadmap_tabs"):
                    with gr.Tab("Roadmap (Timeline)"):
                        timeline_display = gr.HTML(
                            "<div class='card-empty'>Fill in your profile and click <b>Generate Roadmap</b>.</div>",
                            elem_id="timeline_display"
                        )

                    with gr.Tab("Programs"):
                        programs_display = gr.HTML(
                            "<div class='card-empty'>Your recommended programs will appear here as cards.</div>",
                            elem_id="programs_display"
                        )

                    with gr.Tab("Checklist"):
                        checklist_display = gr.HTML(
                            "<div class='card-empty'>Your action checklist will appear here.</div>",
                            elem_id="checklist_display"
                        )

                    with gr.Tab("Full Plan"):
                        output_display = gr.Markdown(
                            "Fill in your profile and click **Generate Roadmap** to get started.",
                            elem_classes="output-box",
                            elem_id="roadmap_md"
                        )

                    with gr.Tab("Q&A"):
                        gr.Markdown("Ask follow-up questions and refine your roadmap.")
                        with gr.Row():
                            followup_input = gr.Textbox(
                                label="Your Question",
                                placeholder="e.g., Which programs fit my marks best?",
                                scale=4,
                                elem_classes="glass-input"
                            )
                            send_btn = gr.Button("Send", scale=1, elem_classes="secondary-btn")

                # Hidden admin section (unchanged)
                with gr.Column(visible=False) as admin_section:
                    admin_info = gr.Markdown("")

    return {
        "session_state": session_state,
        "login": {
            "section": login_section,
            "name_input": name_input,
            "start_btn": start_btn
        },
        "student": {
            "section": student_section,
            "subjects_input": subjects_input,
            "interests_input": interests_input,
            "extracurriculars_input": extracurriculars_input,
            "average_input": average_input,
            "grade_input": grade_input,
            "location_input": location_input,

            # ✅ new
            "preferences_input": preferences_input,
            "preferences_free_text": preferences_free_text,

            "clear_btn": clear_btn,
            "generate_btn": generate_btn,

            "timeline_display": timeline_display,
            "programs_display": programs_display,
            "checklist_display": checklist_display,
            "output_display": output_display,

            "followup_input": followup_input,
            "send_btn": send_btn
        },
        "admin": {
            "section": admin_section,
            "admin_info": admin_info
        }
    }
