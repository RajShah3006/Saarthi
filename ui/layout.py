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

    # Used to populate compare UI
    programs_state = gr.State([])

    status_text = "✅ AI enabled" if config.GEMINI_API_KEY else "Under Maintenance"

    # ---------- LOGIN ----------
    with gr.Column(visible=True, elem_classes="glass-panel") as login_section:
        gr.Markdown("### Welcome!")
        gr.Markdown("Enter your name to get started — or resume with a code.")

        name_input = gr.Textbox(label="Your Name", placeholder="Enter your name", elem_classes="glass-input")
        start_btn = gr.Button("Start Session →", variant="primary", elem_classes="primary-btn")

        gr.Markdown("#### Resume")
        resume_code_input = gr.Textbox(
            label="Resume Code",
            placeholder="example: 12:AbCdEf...",
            elem_classes="glass-input",
            elem_id="resume_code_input",
        )
        resume_btn = gr.Button("Resume", elem_classes="secondary-btn")
        resume_login_status = gr.Markdown("", elem_classes="hint-text")

        # JS: auto-fill resume_code_input from localStorage, and store new codes later
        gr.HTML("""
<script>
(() => {
  const KEY = "saarthi_last_resume_code";
  function getInputById(id){
    const root = document.getElementById(id);
    if(!root) return null;
    return root.querySelector("textarea, input");
  }
  function setVal(id, val){
    const el = getInputById(id);
    if(!el) return;
    el.value = val;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }
  window.addEventListener("load", () => {
    const saved = localStorage.getItem(KEY) || "";
    if(saved) setVal("resume_code_input", saved);
  });

  // Store whenever hidden field changes
  function readAndStore(){
    const el = getInputById("resume_code_store");
    if(!el) return;
    const v = (el.value || "").trim();
    if(v) localStorage.setItem(KEY, v);
  }
  setInterval(readAndStore, 1200);
})();
</script>
        """)

        gr.Markdown("*No account needed — session stays in your browser.*", elem_classes="hint-text")

    # ---------- STUDENT ----------
    with gr.Column(visible=False, elem_classes="glass-panel") as student_section:

        # ---------------- INPUTS VIEW ----------------
        with gr.Column(visible=True, elem_id="inputs_view") as inputs_view:
            gr.HTML(f"<div class='status-badge'>{status_text}</div>")
            gr.Markdown("## Student Wizard (Step-by-step)")

            wizard_error = gr.Markdown("", elem_classes="hint-text")

            wizard_step = gr.State(1)
            step_label = gr.Markdown("**Step 1 of 4**")

            # STEP 1: Most important first
            with gr.Column(visible=True) as step1:
                gr.Markdown("### 1) Basics + Interests + Delivery")

                with gr.Row():
                    grade_input = gr.Dropdown(choices=config.GRADE_OPTIONS, value="Grade 12", label="Grade Level")
                    average_input = gr.Slider(50, 100, value=85, step=1, label="Current Average %")

                location_input = gr.Textbox(label="Location", placeholder="e.g., Toronto, ON", elem_classes="glass-input")

                interest_tags_input = gr.CheckboxGroup(
                    choices=INTEREST_AREAS,
                    label="Interest Areas *",
                    info="Pick at least 2.",
                )
                interest_details_input = gr.Textbox(
                    label="Interest Details (optional)",
                    placeholder="e.g., AI + robotics, biomedical, entrepreneurship",
                    elem_classes="glass-input",
                    lines=2,
                )

                interest_hint = gr.Markdown("", elem_classes="hint-text")

                gr.Markdown("#### Delivery")
                wants_email = gr.Checkbox(label="Email me the results (requires admin approval)", value=False)
                student_email = gr.Textbox(
                    label="Student Email (only if emailing)",
                    placeholder="name@email.com",
                    elem_classes="glass-input",
                    visible=False,
                )
                email_hint = gr.Markdown("", elem_classes="hint-text")

            # STEP 2: Academics
            with gr.Column(visible=False) as step2:
                gr.Markdown("### 2) Academics")
                subjects_input = gr.Dropdown(
                    choices=COURSES,
                    multiselect=True,
                    label="Current/Planned Subjects",
                    elem_classes="glass-input",
                )
                prereq_hint = gr.Markdown("", elem_classes="hint-text")

            # STEP 3: Extras
            with gr.Column(visible=False) as step3:
                gr.Markdown("### 3) Activities + Preferences")
                extracurriculars_input = gr.Textbox(
                    label="Extracurricular Activities",
                    placeholder="e.g., robotics club, volunteering, sports, part-time job",
                    elem_classes="glass-input",
                    lines=3,
                )
                preferences_input = gr.Textbox(
                    label="Preferences (optional)",
                    placeholder="e.g., co-op, scholarships, close to home, smaller campus",
                    elem_classes="glass-input",
                    lines=3,
                )

            # STEP 4: Review + Generate (Generate ONLY here)
            with gr.Column(visible=False) as step4:
                gr.Markdown("### 4) Review + Generate")
                review_box = gr.Markdown("Fill earlier steps to preview here.", elem_classes="output-box")
                generate_btn = gr.Button("Generate Roadmap", variant="primary", elem_classes="primary-btn", interactive=False)

            with gr.Row():
                back_btn = gr.Button("← Back", elem_classes="secondary-btn", visible=False)
                next_btn = gr.Button("Next →", elem_classes="secondary-btn", visible=True)

            clear_btn = gr.Button("Clear", elem_classes="secondary-btn")

        # ---------------- OUTPUTS VIEW ----------------
        with gr.Column(visible=False, elem_id="outputs_view") as outputs_view:
            with gr.Row():
                edit_inputs_btn = gr.Button("← Edit Inputs", elem_classes="secondary-btn")
                submission_code_out = gr.Markdown("")
                # hidden: used for localStorage persistence
                resume_code_store = gr.Textbox(value="", visible=False, elem_id="resume_code_store")

            # Notice shown ONLY when email is requested
            email_only_notice = gr.Markdown("", visible=False, elem_classes="output-box")

            # Normal dashboard (hidden when email-only flow)
            with gr.Column(visible=True) as dashboard_wrap:
                gr.Markdown("## Your Roadmap Dashboard")

                with gr.Tabs(elem_id="roadmap_tabs"):
                    with gr.Tab("Roadmap (Timeline)"):
                        timeline_display = gr.HTML("<div class='card-empty'>No timeline yet.</div>")
                    with gr.Tab("Programs"):
                        programs_display = gr.HTML("<div class='card-empty'>No programs yet.</div>")
                    with gr.Tab("Checklist"):
                        checklist_display = gr.HTML("<div class='card-empty'>No checklist yet.</div>")
                    with gr.Tab("Full Plan"):
                        output_display = gr.Markdown("", elem_classes="output-box")
                    with gr.Tab("Compare"):
                        compare_select = gr.CheckboxGroup(
                            choices=[],
                            label="Select up to 4 programs to compare",
                        )
                        compare_table = gr.HTML("<div class='card-empty'>Pick programs to compare.</div>")
                    with gr.Tab("Q&A"):
                        with gr.Row():
                            followup_input = gr.Textbox(
                                label="Your Question",
                                placeholder="Ask a follow-up…",
                                elem_classes="glass-input",
                            )
                            send_btn = gr.Button("Send", elem_classes="secondary-btn")

        # ---------------- ADMIN PANEL ----------------
        with gr.Accordion("Admin Panel", open=False):
            with gr.Row():
                admin_pin = gr.Textbox(label="Admin PIN", type="password", placeholder="Enter PIN", elem_classes="glass-input")
                admin_name = gr.Textbox(label="Admin name", placeholder="e.g., Raj / Teammate 1", elem_classes="glass-input")
                admin_login_btn = gr.Button("Unlock Admin", elem_classes="secondary-btn")
            admin_status = gr.Markdown("", elem_classes="hint-text")

            with gr.Column(visible=False) as admin_section:
                gr.Markdown("### Review Queue (Email Requests)")

                with gr.Row():
                    status_filter = gr.Dropdown(
                        choices=["ALL", "GENERATED", "IN_REVIEW", "SENT", "ERROR"],
                        value="ALL",
                        label="Status filter",
                    )
                    search_query = gr.Textbox(label="Search", placeholder="name or email", elem_classes="glass-input")
                    refresh_queue_btn = gr.Button("Refresh", elem_classes="secondary-btn")
                    open_next_btn = gr.Button("Open Next Pending", elem_classes="secondary-btn")

                queue_table = gr.Dataframe(
                    headers=["id", "created_at", "student_name", "student_email", "status"],
                    datatype=["number", "str", "str", "str", "str"],
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### Review + Edit Email")
                with gr.Row():
                    review_id = gr.Number(label="Submission ID", value=None)
                    load_btn = gr.Button("Load", elem_classes="secondary-btn")

                admin_plan_md = gr.Markdown("", elem_classes="output-box")
                email_subject = gr.Textbox(label="Email Subject", elem_classes="glass-input")
                email_body = gr.Textbox(label="Email Body (plain text)", lines=14, elem_classes="glass-input")

                with gr.Row():
                    autofill_email_btn = gr.Button("Auto-fill Email", elem_classes="secondary-btn")
                    save_email_btn = gr.Button("Save Draft", variant="primary", elem_classes="primary-btn")
                    mark_sent_btn = gr.Button("Mark Sent", elem_classes="secondary-btn")

                gmail_helper = gr.HTML("")

                gr.Markdown("### Action Log")
                actions_table = gr.Dataframe(
                    headers=["created_at", "actor", "action", "details"],
                    datatype=["str", "str", "str", "str"],
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### GitHub Diagnostics")
                github_diag_btn = gr.Button("Run GitHub Diagnostics", elem_classes="secondary-btn")
                github_diag_output = gr.Markdown("", elem_classes="output-box")

    return {
        "session_state": session_state,
        "name_state": name_state,
        "view_state": view_state,
        "programs_state": programs_state,

        "login": {
            "section": login_section,
            "name_input": name_input,
            "start_btn": start_btn,
            "resume_code_input": resume_code_input,
            "resume_btn": resume_btn,
            "resume_login_status": resume_login_status,
        },

        "student": {
            "section": student_section,

            "inputs_view": inputs_view,
            "outputs_view": outputs_view,
            "edit_inputs_btn": edit_inputs_btn,
            "submission_code_out": submission_code_out,
            "resume_code_store": resume_code_store,

            "email_only_notice": email_only_notice,
            "dashboard_wrap": dashboard_wrap,

            "wizard_step": wizard_step,
            "step_label": step_label,
            "wizard_error": wizard_error,
            "step1": step1, "step2": step2, "step3": step3, "step4": step4,

            "grade_input": grade_input,
            "average_input": average_input,
            "location_input": location_input,
            "interest_tags_input": interest_tags_input,
            "interest_details_input": interest_details_input,
            "interest_hint": interest_hint,

            "wants_email": wants_email,
            "student_email": student_email,
            "email_hint": email_hint,

            "subjects_input": subjects_input,
            "prereq_hint": prereq_hint,

            "extracurriculars_input": extracurriculars_input,
            "preferences_input": preferences_input,

            "review_box": review_box,
            "generate_btn": generate_btn,

            "back_btn": back_btn,
            "next_btn": next_btn,
            "clear_btn": clear_btn,

            "timeline_display": timeline_display,
            "programs_display": programs_display,
            "checklist_display": checklist_display,
            "output_display": output_display,

            "compare_select": compare_select,
            "compare_table": compare_table,

            "followup_input": followup_input,
            "send_btn": send_btn,

            # Admin
            "admin_pin": admin_pin,
            "admin_name": admin_name,
            "admin_login_btn": admin_login_btn,
            "admin_status": admin_status,
            "admin_section": admin_section,

            "status_filter": status_filter,
            "search_query": search_query,
            "refresh_queue_btn": refresh_queue_btn,
            "open_next_btn": open_next_btn,
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
            "actions_table": actions_table,
            "github_diag_btn": github_diag_btn,
            "github_diag_output": github_diag_output,
        }
    }