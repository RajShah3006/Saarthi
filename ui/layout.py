# ui/layout.py - Two-page flow: Inputs Wizard -> Fullscreen Outputs Dashboard

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
    session_state = gr.State("")
    status_text = "✅ AI enabled" if config.GEMINI_API_KEY else "Under Maintenance"

    # =====================
    # LOGIN SECTION
    # =====================
    with gr.Column(visible=True, elem_classes="glass-panel") as login_section:
        gr.Markdown("### Welcome!")
        gr.Markdown("Enter your name to get started with personalized university guidance.")

        name_input = gr.Textbox(
            label="Your Name",
            placeholder="Enter your name",
            elem_classes="glass-input",
        )
        start_btn = gr.Button(
            "Start Session →",
            variant="primary",
            elem_classes="primary-btn",
        )
        gr.Markdown(
            "*No account needed - your session data stays in your browser only.*",
            elem_classes="hint-text",
        )

    # =====================
    # STUDENT SECTION (2 pages)
    # =====================
    with gr.Column(visible=False, elem_classes="glass-panel") as student_section:
        # Page state
        wizard_step = gr.State(1)

        # -------------------------
        # PAGE 1: INPUTS (visible initially)
        # -------------------------
        with gr.Column(visible=True, elem_id="inputs_view") as inputs_view:
            gr.HTML(f"<div class='status-badge'>{status_text}</div>")
            step_label = gr.Markdown("**Step 1 of 4**")

            # STEP 1: Basics
            with gr.Column(visible=True, elem_id="step1") as step1:
                gr.Markdown("### 1) Basics")
                with gr.Row():
                    average_input = gr.Slider(50, 100, value=85, step=1, label="Current Average %")
                    grade_input = gr.Dropdown(choices=config.GRADE_OPTIONS, value="Grade 12", label="Grade Level")
                location_input = gr.Textbox(
                    label="Location",
                    placeholder="e.g., Toronto, ON",
                    elem_classes="glass-input",
                )

            # STEP 2: Academics
            with gr.Column(visible=False, elem_id="step2") as step2:
                gr.Markdown("### 2) Academics")
                subjects_input = gr.Dropdown(
                    choices=COURSES,
                    multiselect=True,
                    label="Current/Planned Subjects",
                    info="Select courses you're taking or plan to take",
                    elem_classes="glass-input",
                )

            # STEP 3: Interests & Extras
            with gr.Column(visible=False, elem_id="step3") as step3:
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
                    lines=2,
                )
                extracurriculars_input = gr.Textbox(
                    label="Extracurricular Activities",
                    placeholder="e.g., Robotics Club, Debate Team, Volunteering",
                    elem_classes="glass-input",
                    lines=2,
                )
                preferences_input = gr.Textbox(
                    label="Preferences (optional)",
                    placeholder="e.g., close to home, scholarships, smaller campus",
                    elem_classes="glass-input",
                    lines=2,
                )

                with gr.Row():
                    preset_eng = gr.Button("Engineering", elem_classes="chip-btn")
                    preset_cs = gr.Button("Computer Science", elem_classes="chip-btn")
                with gr.Row():
                    preset_bus = gr.Button("Business", elem_classes="chip-btn")
                    preset_hs = gr.Button("Health Sci", elem_classes="chip-btn")

            # STEP 4: Review
            with gr.Column(visible=False, elem_id="step4") as step4:
                gr.Markdown("### 4) Review")
                review_box = gr.Markdown("Fill earlier steps to preview here.", elem_classes="output-box")

            # Nav buttons
            with gr.Row():
                back_btn = gr.Button("← Back", elem_classes="secondary-btn", visible=False)
                next_btn = gr.Button("Next →", elem_classes="secondary-btn", visible=True)

            # Actions
            generate_btn = gr.Button(
                "Generate Roadmap",
                variant="primary",
                elem_classes="primary-btn",
                interactive=False,  # enabled at Step 4 in app.py
            )
            clear_btn = gr.Button("Clear", elem_classes="secondary-btn")

        # -------------------------
        # PAGE 2: OUTPUTS (hidden until Generate)
        # -------------------------
        with gr.Column(visible=False, elem_id="outputs_view") as outputs_view:
            with gr.Row():
                edit_inputs_btn = gr.Button("← Edit Inputs", elem_classes="secondary-btn")
                # optional: you can add a "Regenerate" button here later if you want

            gr.Markdown("### Your Roadmap Dashboard")

            with gr.Tabs(elem_id="roadmap_tabs"):
                with gr.Tab("Roadmap (Timeline)"):
                    timeline_display = gr.HTML(
                        "<div class='card-empty'>Generate a roadmap to see your timeline.</div>",
                        elem_id="timeline_display",
                    )

                with gr.Tab("Programs"):
                    programs_display = gr.HTML(
                        "<div class='card-empty'>Your recommended programs will appear here as cards.</div>",
                        elem_id="programs_display",
                    )

                with gr.Tab("Checklist"):
                    checklist_display = gr.HTML(
                        "<div class='card-empty'>Your action checklist will appear here.</div>",
                        elem_id="checklist_display",
                    )

                with gr.Tab("Full Plan"):
                    output_display = gr.Markdown(
                        "Generate a roadmap to see the full plan.",
                        elem_classes="output-box",
                        elem_id="roadmap_md",
                    )

                with gr.Tab("Q&A"):
                    gr.Markdown("Ask follow-up questions and refine your roadmap.")
                    with gr.Row():
                        followup_input = gr.Textbox(
                            label="Your Question",
                            placeholder="e.g., Which programs fit my marks best?",
                            scale=4,
                            elem_classes="glass-input",
                        )
                        send_btn = gr.Button("Send", scale=1, elem_classes="secondary-btn")

        # Admin (hidden)
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

            # page containers (important)
            "inputs_view": inputs_view,
            "outputs_view": outputs_view,
            "edit_inputs_btn": edit_inputs_btn,

            # inputs
            "subjects_input": subjects_input,
            "interest_tags_input": interest_tags_input,
            "interest_details_input": interest_details_input,
            "extracurriculars_input": extracurriculars_input,
            "average_input": average_input,
            "grade_input": grade_input,
            "location_input": location_input,
            "preferences_input": preferences_input,

            # presets
            "preset_eng": preset_eng,
            "preset_cs": preset_cs,
            "preset_bus": preset_bus,
            "preset_hs": preset_hs,

            # actions
            "clear_btn": clear_btn,
            "generate_btn": generate_btn,

            # outputs
            "timeline_display": timeline_display,
            "programs_display": programs_display,
            "checklist_display": checklist_display,
            "output_display": output_display,

            # q&a
            "followup_input": followup_input,
            "send_btn": send_btn,

            # wizard
            "wizard_step": wizard_step,
            "step_label": step_label,
            "step1": step1, "step2": step2, "step3": step3, "step4": step4,
            "review_box": review_box,
            "back_btn": back_btn,
            "next_btn": next_btn,
        },
        "admin": {
            "section": admin_section,
            "admin_info": admin_info,
        },
    }
