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

    status_text = "✅ AI enabled" if config.GEMINI_API_KEY else "Under Maintenance"

    # ---------- LOGIN ----------
    with gr.Column(visible=True, elem_classes="glass-panel") as login_section:
        gr.Markdown("### Welcome!")
        gr.Markdown("Enter your name to get started.")
        name_input = gr.Textbox(label="Your Name", placeholder="Enter your name", elem_classes="glass-input")
        start_btn = gr.Button("Start Session →", variant="primary", elem_classes="primary-btn")
        gr.Markdown("*No account needed - session stays in browser.*", elem_classes="hint-text")

    # ---------- STUDENT ----------
    with gr.Column(visible=False, elem_classes="glass-panel") as student_section:

        # =========================
        # INPUTS VIEW (wizard)
        # =========================
        with gr.Column(visible=True, elem_id="inputs_view") as inputs_view:
            gr.HTML(f"<div class='status-badge'>{status_text}</div>")
            gr.Markdown("## Student Wizard (Step-by-step)")

            # ---- Resume (optional) ----
            gr.Markdown("### Resume (optional)")
            resume_code_input = gr.Textbox(
                label="Resume code",
                placeholder="Paste code like: 12:AbCdEf...",
                elem_classes="glass-input",
            )
            with gr.Row():
                resume_btn = gr.Button("Resume", elem_classes="secondary-btn")
                resume_status = gr.Markdown("", elem_classes="hint-text")
            gr.Markdown("---")

            wizard_step = gr.State(1)
            step_label = gr.Markdown("**Step 1 of 4**")

            # STEP 1: Basics + Delivery
            with gr.Column(visible=True) as step1:
                gr.Markdown("### 1) Basics + Delivery")
                with gr.Row():
                    grade_input = gr.Dropdown(
                        choices=config.GRADE_OPTIONS,
                        value="Grade 12",
                        label="Grade Level",
                    )
                    average_input = gr.Slider(50, 100, value=85, step=1, label="Current Average %")

                location_input = gr.Textbox(
                    label="Location",
                    placeholder="e.g., Toronto, ON",
                    elem_classes="glass-input",
                )

                gr.Markdown("#### Delivery")
                wants_email = gr.Checkbox(
                    label="Email me the results (requires admin approval)",
                    value=False
                )
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

            # STEP 4: Review + Generate (button only exists here)
            with gr.Column(visible=False) as step4:
                gr.Markdown("### 4) Review + Generate")
                review_box = gr.Markdown("Fill earlier steps to preview here.", elem_classes="output-box")
                generate_btn = gr.Button("Generate Roadmap", variant="primary", elem_classes="primary-btn")

            with gr.Row():
                back_btn = gr.Button("← Back", elem_classes="secondary-btn", visible=False)
                next_btn = gr.Button("Next →", elem_classes="secondary-btn", visible=True)

            clear_btn = gr.Button("Clear", elem_classes="secondary-btn")

        # =========================
        # OUTPUTS VIEW (dashboard)
        # =========================
        with gr.Column(visible=False, elem_id="outputs_view") as outputs_view:
            with gr.Row():
                with gr.Column(scale=1, min_width=180):
                    edit_inputs_btn = gr.Button("← Edit Inputs", elem_classes="secondary-btn")
                with gr.Column(scale=3, min_width=320):
                    submission_code_out = gr.Markdown("")

            gr.Markdown("## Your Roadmap Dashboard")
            with gr.Tabs(elem_id="roadmap_tabs"):
                with gr.Tab("Roadmap (Timeline)"):
                    timeline_display = gr.HTML("<div class='card-empty'>No timeline yet.</div>", elem_id="timeline_display")

                with gr.Tab("Programs"):
                    programs_display = gr.HTML("<div class='card-empty'>No programs yet.</div>", elem_id="programs_display")

                with gr.Tab("Checklist"):
                    checklist_display = gr.HTML("<div class='card-empty'>No checklist yet.</div>", elem_id="checklist_display")

                with gr.Tab("Full Plan"):
                    output_display = gr.Markdown("", elem_classes="output-box", elem_id="roadmap_md")

                with gr.Tab("Q&A"):
                    with gr.Row():
                        followup_input = gr.Textbox(
                            label="Your Question",
                            placeholder="Ask a follow-up…",
                            elem_classes="glass-input",
                            scale=4
                        )
                        send_btn = gr.Button("Send", elem_classes="secondary-btn", scale=1)

        # =========================
        # ADMIN PANEL (approval)
        # =========================
        with gr.Accordion("Admin Panel", open=False) as admin_panel:
            admin_pin = gr.Textbox(label="Admin PIN", type="password", placeholder="Enter PIN")
            admin_login_btn = gr.Button("Unlock Admin", elem_classes="secondary-btn")
            admin_status = gr.Markdown("", elem_classes="hint-text")

            with gr.Column(visible=False) as admin_section:
                gr.Markdown("### Review Queue (Email Requests)")
                refresh_queue_btn = gr.Button("Refresh Queue", elem_classes="secondary-btn")
                queue_table = gr.Dataframe(
                    headers=["id", "created_at", "student_name", "student_email", "status"],
                    datatype=["number", "str", "str", "str", "str"],
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### Review + Edit Email")
                review_id = gr.Number(label="Submission ID", value=None)
                load_btn = gr.Button("Load Submission", elem_classes="secondary-btn")

                admin_plan_md = gr.Markdown("", elem_classes="output-box")
                email_subject = gr.Textbox(label="Email Subject", elem_classes="glass-input")
                email_body = gr.Textbox(label="Email Body (plain text)", lines=14, elem_classes="glass-input")

                with gr.Row():
                    autofill_email_btn = gr.Button("Auto-fill Email", elem_classes="secondary-btn")
                    save_email_btn = gr.Button("Save Draft", variant="primary", elem_classes="primary-btn")
                    mark_sent_btn = gr.Button("Mark Sent", elem_classes="secondary-btn")

                gmail_helper = gr.HTML("")

    return {
        "session_state": session_state,
        "name_state": name_state,
        "view_state": view_state,
        "login": {
            "section": login_section,
            "name_input": name_input,
            "start_btn": start_btn,
        },
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
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "step4": step4,
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
            "timeline_display": timeline_display,
            "programs_display": programs_display,
            "checklist_display": checklist_display,
            "output_display": output_display,

            # q&a
            "followup_input": followup_input,
            "send_btn": send_btn,

            # admin
            "admin_pin": admin_pin,
            "admin_login_btn": admin_login_btn,
            "admin_status": admin_status,
            "admin_section": admin_section,
            "refresh_queue_btn": refresh_queue_btn,
            "queue_table": queue_table,
            "review_id": review_id,
            "load_btn": load_btn,
            "admin_plan_md": admin_plan_md,
            "email_subject": email_subject,
            "email_body": email_body,
            "autofill_email_btn": autofill_email_btn,
            "save_email_btn": save_email_btn,
            "mark_sent_btn": mark_sent_btn,
            "gmail_helper": gmail_helper,
        },
    }