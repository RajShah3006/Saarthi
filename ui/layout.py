# ui/layout.py
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
    name_state = gr.State("")
    view_state = gr.State("inputs")  # "inputs" or "outputs"
    programs_state = gr.State([])    # used for Compare tab

    status_text = "✅ AI enabled" if config.GEMINI_API_KEY else "Under Maintenance"

    # ---------- LOGIN ----------
    with gr.Column(visible=True, elem_classes="glass-panel") as login_section:
        gr.Markdown("### Welcome!")
        gr.Markdown("Enter your name to get started.")
        name_input = gr.Textbox(label="Your Name", placeholder="Enter your name", elem_classes="glass-input")
        start_btn = gr.Button("Start Session →", variant="primary", elem_classes="primary-btn")
        gr.Markdown("*No account needed - session stays in your browser.*", elem_classes="hint-text")

    # ---------- STUDENT ----------
    with gr.Column(visible=False, elem_classes="glass-panel") as student_section:

        # ---------------- Inputs View ----------------
        with gr.Column(visible=True, elem_id="inputs_view") as inputs_view:
            gr.HTML(f"<div class='status-badge'>{status_text}</div>")
            gr.Markdown("## Student Wizard (Step-by-step)")

            gr.Markdown("### Resume existing plan (optional)")
            resume_code_input = gr.Textbox(
                label="Resume code",
                placeholder="Paste code like: 12:AbCdEf...",
                elem_classes="glass-input",
            )
            resume_btn = gr.Button("Resume", elem_classes="secondary-btn")
            resume_status = gr.Markdown("", elem_classes="hint-text")
            gr.Markdown("---")

            wizard_step = gr.State(1)
            step_label = gr.Markdown("**Step 1 of 4**")

            # STEP 1: Basics + Delivery
            with gr.Column(visible=True) as step1:
                gr.Markdown("### 1) Basics + Delivery")
                with gr.Row():
                    average_input = gr.Slider(50, 100, value=85, step=1, label="Current Average %")
                    grade_input = gr.Dropdown(choices=config.GRADE_OPTIONS, value="Grade 12", label="Grade Level")
                location_input = gr.Textbox(label="Location", placeholder="e.g., Toronto, ON", elem_classes="glass-input")

                gr.Markdown("#### Delivery")
                wants_email = gr.Checkbox(label="Email me the results (requires admin approval)", value=False)
                student_email = gr.Textbox(
                    label="Student Email (only if emailing)",
                    placeholder="name@email.com",
                    elem_classes="glass-input",
                )

            # STEP 2: Academics
            with gr.Column(visible=False) as step2:
                gr.Markdown("### 2) Academics")
                subjects_input = gr.Dropdown(
                    choices=COURSES,
                    multiselect=True,
                    label="Current/Planned Subjects",
                    elem_classes="glass-input",
                )

            # STEP 3: Interests & extras
            with gr.Column(visible=False) as step3:
                gr.Markdown("### 3) Interests & Extras")
                interest_tags_input = gr.CheckboxGroup(
                    choices=INTEREST_AREAS,
                    label="Interest Areas *",
                    info="Pick 2–4.",
                )
                interest_details_input = gr.Textbox(
                    label="Interest Details (optional)",
                    placeholder="e.g., AI + robotics",
                    elem_classes="glass-input",
                    lines=2,
                )
                extracurriculars_input = gr.Textbox(
                    label="Extracurricular Activities",
                    placeholder="e.g., Robotics club, volunteering",
                    elem_classes="glass-input",
                    lines=2,
                )
                preferences_input = gr.Textbox(
                    label="Preferences (optional)",
                    placeholder="e.g., scholarships, co-op, close to home",
                    elem_classes="glass-input",
                    lines=2,
                )

            # STEP 4: Review + Generate (Generate only here)
            with gr.Column(visible=False) as step4:
                gr.Markdown("### 4) Review + Generate")
                review_box = gr.Markdown("Fill earlier steps to preview here.", elem_classes="output-box")
                generate_btn = gr.Button("Generate Roadmap", variant="primary", elem_classes="primary-btn")

            with gr.Row():
                back_btn = gr.Button("← Back", elem_classes="secondary-btn", visible=False)
                next_btn = gr.Button("Next →", elem_classes="secondary-btn", visible=True)

            clear_btn = gr.Button("Clear", elem_classes="secondary-btn")

        # ---------------- Outputs View ----------------
        with gr.Column(visible=False, elem_id="outputs_view") as outputs_view:
            with gr.Row():
                edit_inputs_btn = gr.Button("← Edit Inputs", elem_classes="secondary-btn")
                submission_code_out = gr.Markdown("")

            # Email notice (shown when wants_email=True)
            email_notice = gr.Markdown(
                "",
                visible=False,
                elem_classes="output-box",
            )

            dashboard_tabs = gr.Tabs(elem_id="roadmap_tabs", visible=True)

            with dashboard_tabs:
                with gr.Tab("Roadmap (Timeline)"):
                    timeline_display = gr.HTML("<div class='card-empty'>No timeline yet.</div>")

                with gr.Tab("Programs"):
                    programs_display = gr.HTML("<div class='card-empty'>No programs yet.</div>")

                with gr.Tab("Checklist"):
                    checklist_display = gr.HTML("<div class='card-empty'>No checklist yet.</div>")

                with gr.Tab("Compare"):
                    compare_select = gr.CheckboxGroup(
                        choices=[],
                        label="Select up to 4 programs",
                        info="Pick programs, then the compare table will update automatically.",
                    )
                    compare_table = gr.HTML("<div class='card-empty'>Pick programs to compare.</div>")

                with gr.Tab("Full Plan"):
                    output_display = gr.Markdown("", elem_classes="output-box")

                with gr.Tab("Q&A"):
                    with gr.Row():
                        followup_input = gr.Textbox(
                            label="Your Question",
                            placeholder="Ask a follow-up…",
                            elem_classes="glass-input",
                        )
                        send_btn = gr.Button("Send", elem_classes="secondary-btn")

    return {
        "session_state": session_state,
        "name_state": name_state,
        "view_state": view_state,
        "programs_state": programs_state,
        "login": {"section": login_section, "name_input": name_input, "start_btn": start_btn},
        "student": {
            "section": student_section,

            # views
            "inputs_view": inputs_view,
            "outputs_view": outputs_view,
            "edit_inputs_btn": edit_inputs_btn,
            "submission_code_out": submission_code_out,

            # resume
            "resume_code_input": resume_code_input,
            "resume_btn": resume_btn,
            "resume_status": resume_status,

            # wizard
            "wizard_step": wizard_step,
            "step_label": step_label,
            "step1": step1, "step2": step2, "step3": step3, "step4": step4,
            "review_box": review_box,
            "back_btn": back_btn,
            "next_btn": next_btn,

            # inputs
            "average_input": average_input,
            "grade_input": grade_input,
            "location_input": location_input,
            "subjects_input": subjects_input,
            "interest_tags_input": interest_tags_input,
            "interest_details_input": interest_details_input,
            "extracurriculars_input": extracurriculars_input,
            "preferences_input": preferences_input,

            # delivery
            "wants_email": wants_email,
            "student_email": student_email,

            # actions
            "generate_btn": generate_btn,
            "clear_btn": clear_btn,

            # outputs
            "email_notice": email_notice,
            "dashboard_tabs": dashboard_tabs,
            "timeline_display": timeline_display,
            "programs_display": programs_display,
            "checklist_display": checklist_display,
            "output_display": output_display,

            # compare
            "compare_select": compare_select,
            "compare_table": compare_table,

            # q&a
            "followup_input": followup_input,
            "send_btn": send_btn,
        }
    }
