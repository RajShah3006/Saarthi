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

INTEREST_AREAS = [
    "Engineering", "Computer Science", "Health Sciences", "Business/Commerce",
    "Life Sciences", "Physical Sciences", "Math/Statistics", "Social Sciences",
    "Arts & Design", "Law/Criminology", "Education", "Environment",
]

def create_ui_layout(config: Config) -> dict:
    """Create the complete UI layout and return component references"""

    session_state = gr.State("")
    status_text = "✅ AI enabled" if config.GEMINI_API_KEY else "Under Maintenance"

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
        sidebar_collapsed = gr.State(False)  # False = expanded, True = hidden
        with gr.Row(elem_id="dash_row"):
            # Left: Form
            with gr.Column(elem_id="sidebar_col", scale=1, min_width=320) as sidebar_col:
                gr.HTML(f"<div class='status-badge'>{status_text}</div>")

                                # --- Wizard state ---
                wizard_step = gr.State(1)
                
                with gr.Column(scale=1, min_width=320) as sidebar_col:
                    gr.Markdown(f"**Status:** {status_text}")
                
                    step_label = gr.Markdown("**Step 1 of 4**")
                
                    # STEP 1: Basics
                    with gr.Column(visible=True) as step1:
                        gr.Markdown("### 1) Basics")
                        with gr.Row():
                            average_input = gr.Slider(50, 100, value=85, step=1, label="Current Average %")
                            grade_input = gr.Dropdown(choices=config.GRADE_OPTIONS, value="Grade 12", label="Grade Level")
                        location_input = gr.Textbox(label="Location", placeholder="e.g., Toronto, ON", elem_classes="glass-input")
                
                    # STEP 2: Academics
                    with gr.Column(visible=False) as step2:
                        gr.Markdown("### 2) Academics")
                        subjects_input = gr.Dropdown(
                            choices=COURSES,
                            multiselect=True,
                            label="Current/Planned Subjects",
                            info="Select courses you're taking or plan to take",
                            elem_classes="glass-input"
                        )
                
                    # STEP 3: Interests & Extras
                    with gr.Column(visible=False) as step3:
                        gr.Markdown("### 3) Interests & Extras")
                        interest_tags_input = gr.CheckboxGroup(
                            choices=INTEREST_AREAS,
                            label="Interest Areas *",
                            info="Pick a few (2–4). If unsure, pick your best guess.",
                        )
                        interest_details_input = gr.Textbox(
                            label="Interest Details (optional)",
                            placeholder="e.g., AI + robotics, neuroscience, entrepreneurship",
                            elem_classes="glass-input",
                            lines=2
                        )
                        extracurriculars_input = gr.Textbox(
                            label="Extracurricular Activities",
                            placeholder="e.g., Robotics Club, Debate Team, Volunteering",
                            elem_classes="glass-input",
                            lines=2
                        )
                        preferences_input = gr.Textbox(
                            label="Preferences (optional)",
                            placeholder="e.g., close to home, scholarships, smaller campus",
                            elem_classes="glass-input",
                            lines=2
                        )
                
                    # STEP 4: Review
                    with gr.Column(visible=False) as step4:
                        gr.Markdown("### 4) Review")
                        review_box = gr.Markdown("Fill earlier steps to preview here.", elem_classes="output-box")
                
                    # Nav buttons
                    with gr.Row():
                        back_btn = gr.Button("← Back", elem_classes="secondary-btn", visible=False)
                        next_btn = gr.Button("Next →", elem_classes="secondary-btn", visible=True)
                
                    # Generate
                    generate_btn = gr.Button("Generate Roadmap", variant="primary", elem_classes="primary-btn")
                
                    clear_btn = gr.Button("Clear", elem_classes="secondary-btn")

            # Right: Roadmap Dashboard
            with gr.Column(elem_id="main_col", scale=3, min_width=700) as main_col:
                sidebar_toggle_btn = gr.Button(
                "Hide Inputs ◀",
                elem_id="sidebar_toggle_btn",
                elem_classes="sidebar-toggle"
            )
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

                with gr.Column(visible=False) as admin_section:
                    admin_info = gr.Markdown("")

    return {
        "session_state": session_state,
        "login": {
            "section": login_section,
            "name_input": name_input,
            "start_btn": start_btn,
        },
        "student": {
            "section": student_section,
            "sidebar_col": sidebar_col,
            "sidebar_state": sidebar_collapsed,
            "sidebar_toggle_btn": sidebar_toggle_btn,

            "subjects_input": subjects_input,
            "interest_tags_input": interest_tags_input,
            "interest_details_input": interest_details_input,
            "extracurriculars_input": extracurriculars_input,
            "average_input": average_input,
            "grade_input": grade_input,
            "location_input": location_input,
            "preferences_input": preferences_input,

            "preset_eng": preset_eng,
            "preset_cs": preset_cs,
            "preset_bus": preset_bus,
            "preset_hs": preset_hs,

            "clear_btn": clear_btn,
            "generate_btn": generate_btn,

            "timeline_display": timeline_display,
            "programs_display": programs_display,
            "checklist_display": checklist_display,
            "output_display": output_display,

            "followup_input": followup_input,
            "send_btn": send_btn,

            "wizard_step": wizard_step,
            "step_label": step_label,
            "step1": step1, "step2": step2, "step3": step3, "step4": step4,
            "review_box": review_box,
            "back_btn": back_btn,
            "next_btn": next_btn,
            "sidebar_col": sidebar_col,

        },
        "admin": {
            "section": admin_section,
            "admin_info": admin_info,
        }
    }
