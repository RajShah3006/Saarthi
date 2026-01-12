# ui/layout.py
import gradio as gr
from config import Config

COURSES = sorted([
    " Dance (ATC1O)", " Dance (ATC2O)", " Dance (ATC3M)", " Dance (ATC3O)", " Dance (ATC4M)", " Dance (ATC4E)", " Drama (ADA1O)", " Drama (ADA2O)", " Drama (ADA3M)", " Drama (ADA3O)", " Drama (ADA4M)", " Drama (ADA4E)", " Integrated Arts (ALC1O)", " Integrated Arts (ALC2O)", " Exploring and Creating in the Arts (AEA3O)", " Exploring and Creating in the Arts (AEA4O)", " Media Arts (ASM2O)", " Media Arts (ASM3M)", " Media Arts (ASM3O)", " Media Arts (ASM4M)", " Media Arts (ASM4E)", " Music (AMU1O)", " Music (AMU2O)", " Music (AMU3M)", " Music (AMU3O)", " Music (AMU4M)", " Music (AMU4E)", " Visual Arts (AVI1O)", " Visual Arts (AVI2O)", " Visual Arts (AVI3M)", " Visual Arts (AVI3O)", " Visual Arts (AVI4M)", " Visual Arts (AVI4E)", " Information and Communication Technology in Business (BTT1O)", " Introduction to Business (BBI1O)", " Information and Communication Technology in Business (BTT2O)", " Introduction to Business (BBI2O)", " Financial Accounting Fundamentals (BAF3M)", " Accounting Essentials (BAI3E)", " Financial Accounting Principles (BAT4M)", " Accounting for a Small Business (BAN4E)", " Entrepreneurship: The Venture (BDI3C)", " Entrepreneurship: The Enterprising Person (BDP3O)", " Entrepreneurship: Venture Planning in an Electronic Age (BDV4C)", " Information and Communication Technology: The Digital Environment (BTA3O)", " Information and Communication Technology: Multimedia Solutions (BTX4C)", " Information and Communication Technology in the Workplace (BTX4E)", " International Business Fundamentals (BBB4M)", " International Business Essentials (BBB4E)", " Marketing: Goods, Services, Events (BMI3C)", " Marketing: Retail and Service (BMX3E)", " Business Leadership: Management Fundamentals (BOH4M)", " Business Leadership: Becoming a Manager (BOG4E)", " Issues in Canadian Geography (CGC1D)", " Issues in Canadian Geography (CGC1P)", " Regional Geography (CGD3M)", " Forces of Nature: Physical Processes and Disasters (CGF3M)", " Travel and Tourism: A Geographic Perspective (CGG3O)", " Introduction to Spatial Technologies (CGT3O)", " World Issues: A Geographic Analysis (CGW4U)", " World Issues: A Geographic Analysis (CGW4C)", " World Geography: Urban Patterns and Population Issues (CGU4M)", " Spatial Technologies in Action (CGO4M)", " The Environment and Resource Management (CGR4M)", " Living in a Sustainable World (CGR4E)", " Canadian History since World War I (CHC2D)", " Canadian History since World War I (CHC2P)", " Origins and Citizenship: The History of a Canadian Ethnic Group (CHE3O)", " American History (CHA3U)", " World History to the End of the Fifteenth Century (CHW3M)", " World History since 1900: Global and Regional Interactions (CHT3O)", " Canada: History, Identity, and Culture (CHI4U)", " World History since the Fifteenth Century (CHY4U)", " World History since the Fifteenth Century (CHY4C)", " Adventures in World History (CHM4E)", " Understanding Canadian Law (CLU3M)", " Understanding Canadian Law in Everyday Life (CLU3E)", " Canadian and International Law (CLN4U)", " Legal Studies (CLN4C)", " Civics and Citizenship (CHV2O)", " Politics in Action: Making Change (CPC3O)", " Canadian and International Politics (CPW4U)", " Classical Languages (Ancient Greek/Latin) Level 1 (LVGBD/LVLBD)", " Classical Languages (Ancient Greek/Latin) Level 2 (LVGCU/LVLCU)", " Classical Languages (Ancient Greek/Latin) Level 3 (LVGDU/LVLDU)", " Classical Civilization (LVV4U)", " International Languages Level 1 Academic (LBABD–LDYBD)", " International Languages Level 1 Open (LBABO–LDYBO)", " International Languages Level 2 University (LBACU–LDYCU)", " International Languages Level 2 Open (LBACO–LDYCO)", " International Languages Level 3 University (LBADU–LDYDU)", " International Languages Level 3 Open (LBADO–LDYDO)", " Introduction to Computer Studies (ICS2O)", " Introduction to Computer Science (ICS3U)", " Introduction to Computer Programming (ICS3C)", " Computer Science (ICS4U)", " Computer Programming (ICS4C)", " Creating Opportunities through Co-op (DCO3O)", " English (ENG1D)", " English (ENG1P)", " English (ENG2D)", " English (ENG2P)", " Literacy Skills: Reading and Writing (ELS2O)", " English (ENG3U)", " English (ENG3C)", " English (ENG3E)", " Canadian Literature (ETC3M)", " Media Studies (EMS3O)", " Presentation and Speaking Skills (EPS3O)", " English (ENG4U)", " English (ENG4C)", " English (ENG4E)", " Studies in Literature (ETS4U)", " The Writer’s Craft (EWC4U)", " Studies in Literature (ETS4C)", " The Writer’s Craft (EWC4C)", " Business and Technological Communication (EBT4O)", " Ontario Secondary School Literacy Course (OLC3O/OLC4O)", " ESL Level 1 (ESLAO)", " ESL Level 2 (ESLBO)", " ESL Level 3 (ESLCO)", " ESL Level 4 (ESLDO)", " ESL Level 5 (ESLEO)", " ELD Level 1 (ELDAO)", " ELD Level 2 (ELDBO)", " ELD Level 3 (ELDCO)", " ELD Level 4 (ELDDO)", " ELD Level 5 (ELDEO)", " Expressions of First Nations, Métis, and Inuit Cultures (NAC1O)", " First Nations, Métis, and Inuit in Canada (NAC2O)", " English: Understanding Contemporary First Nations, Métis, and Inuit Voices (NBE3U)", " English: Understanding Contemporary First Nations, Métis, and Inuit Voices (NBE3C)", " English: Understanding Contemporary First Nations, Métis, and Inuit Voices (NBE3E)", " Contemporary First Nations, Métis, and Inuit Issues and Perspectives (NDA3M)", " World Views and Aspirations of First Nations, Métis, and Inuit Communities in Canada (NBV3C)", " World Views and Aspirations of First Nations, Métis, and Inuit Communities in Canada (NBV3E)", " Contemporary Indigenous Issues and Perspectives in a Global Context (NDW4M)", " First Nations, Métis, and Inuit Governance in Canada (NDG4M)", " Core French (FSF1D)", " Core French (FSF1P)", " Core French (FSF1O)", " Extended French (FEF1D)", " French Immersion (FIF1D)", " French Immersion (FIF1P)", " Core French (FSF2D)", " Core French (FSF2P)", " Core French (FSF2O)", " Extended French (FEF2D)", " French Immersion (FIF2D)", " French Immersion (FIF2P)", " Core French (FSF3U)", " Core French (FSF3O)", " Extended French (FEF3U)", " French Immersion (FIF3U)", " French Immersion (FIF3O)", " Core French (FSF4U)", " Core French (FSF4O)", " Extended French (FEF4U)", " French Immersion (FIF4U)", " French Immersion (FIF4O)", " Learning Strategies 1: Skills for Success in Secondary School (GLS1O)", " Learning Strategies 1: Skills for Success in Secondary School (GLE1O)", " Career Studies (GLC2O)", " Learning Strategies 1: Skills for Success in Secondary School (GLE2O)", " Discovering the Workplace (GLD2O)", " Designing Your Future (GWL3O)", " Leadership and Peer Support (GPP3O)", " Advanced Learning Strategies: Skills for Success After Secondary School (GLE3O)", " Advanced Learning Strategies: Skills for Success After Secondary School (GLS4O)", " Advanced Learning Strategies: Skills for Success After Secondary School (GLE4O)", " Navigating the Workplace (GLN4O)", " Healthy Active Living Education (PPL1O)", " Healthy Active Living Education (PPL2O)", " Healthy Active Living Education (PPL3O)", " Health for Life (PPZ3C)", " Healthy Active Living Education (PPL4O)", " Introductory Kinesiology (PSK4U)", " Recreation and Healthy Active Living Leadership (PLF4M)", " Interdisciplinary Studies (IDC3O)", " Interdisciplinary Studies (IDP3O)", " Interdisciplinary Studies (IDC4U)", " Interdisciplinary Studies (IDP4U)", " Interdisciplinary Studies (IDC4O)", " Interdisciplinary Studies (IDP4O)", " Principles of Mathematics (MPM1D)", " Foundations of Mathematics (MFM1P)", " Mathematics Transfer (MPM1H)", " Principles of Mathematics (MPM2D)", " Foundations of Mathematics (MFM2P)", " Functions (MCR3U)", " Functions and Applications (MCF3M)", " Foundations for College Mathematics (MBF3C)", " Mathematics for Work and Everyday Life (MEL3E)", " Advanced Functions (MHF4U)", " Calculus and Vectors (MCV4U)", " Mathematics of Data Management (MDM4U)", " Mathematics for College Technology (MCT4C)", " Foundations for College Mathematics (MAP4C)", " Mathematics for Work and Everyday Life (MEL4E)", " Science (SNC1D)", " Science (SNC1P)", " Science (SNC2D)", " Science (SNC2P)", " Science (SNC4M)", " Science (SNC4E)", " Biology (SBI3U)", " Biology (SBI3C)", " Biology (SBI4U)", " Chemistry (SCH3U)", " Chemistry (SCH4U)", " Chemistry (SCH4C)", " Earth and Space Science (SES4U)", " Environmental Science (SVN3M)", " Environmental Science (SVN3E)", " Physics (SPH3U)", " Physics (SPH4U)", " Physics (SPH4C)", " Gender Studies (HSG3M)", " Equity, Diversity, and Social Justice (HSE3E)", " Equity and Social Justice: From Theory to Practice (HSE4M)", " World Cultures (HSC4M)", " Exploring Family Studies (HIF1O)", " Food and Nutrition (HFN1O)", " Exploring Family Studies (HIF2O)", " Food and Nutrition (HFN2O)", " Clothing (HNL2O)", " Understanding Fashion (HNC3C)", " Housing and Home Design (HLS3O)", " Food and Culture (HFC3M)", " Food and Culture (HFC3E)", " Dynamics of Human Relationships (HHD3O)", " Working with Infants and Young Children (HPW3C)", " Raising Healthy Children (HPC3O)", " The World of Fashion (HNB4M)", " Nutrition and Health (HFA4U)", " Nutrition and Health (HFA4C)", " Food and Healthy Living (HFL4E)", " Families in Canada (HHS4U)", " Families in Canada (HHS4C)", " Human Development throughout the Lifespan (HHG4M)", " Personal Life Management (HIP4O)", " Working with School-Age Children and Adolescents (HPD4C)", " Introduction to Anthropology, Psychology, and Sociology (HSP3U)", " Introduction to Anthropology, Psychology, and Sociology (HSP3C)", " Challenge and Change in Society (HSB4U)", " Philosophy: The Big Questions (HZB3M)", " Philosophy: Questions and Theories (HZT4U)", " World Religions and Belief Traditions: Perspectives, Issues, and Challenges (HRT3M)", " World Religions and Belief Traditions in Daily Life (HRF3O)", " Exploring Technologies (TIJ1O)", " Communications Technology (TGJ2O)", " Construction Technology (TCJ2O)", " Construction Engineering Technology (TCJ3C)", " Construction Technology (TCJ3E)", " Custom Woodworking (TWJ3E)", " Construction Engineering Technology (TCJ4C)", " Construction Technology (TCJ4E)", " Custom Woodworking (TWJ4E)", " Green Industries (THJ2O)", " Green Industries (THJ3M)", " Green Industries (THJ3E)", " Green Industries (THJ4M)", " Green Industries (THJ4E)", " Hairstyling and Aesthetics (TXJ2O)", " Hairstyling and Aesthetics (TXJ3E)", " Hairstyling and Aesthetics (TXJ4E)", " Health Care (TPJ2O)", " Health Care (TPJ3M)", " Health Care (TPJ3C)", " Health Care (TPJ4M)", " Health Care (TPJ4C)", " Child Development and Gerontology (TOJ4C)", " Health Care: Support Services (TPJ4E)", " Hospitality and Tourism (TFJ2O)", " Hospitality and Tourism (TFJ3C)", " Hospitality and Tourism (TFJ3E)", " Hospitality and Tourism (TFJ4C)", " Hospitality and Tourism (TFJ4E)", " Manufacturing Technology (TMJ2O)", " Manufacturing Engineering Technology (TMJ3M)", " Manufacturing Technology (TMJ3C)", " Manufacturing Technology (TMJ3E)", " Manufacturing Engineering Technology (TMJ4M)", " Manufacturing Technology (TMJ4C)", " Manufacturing Technology (TMJ4E)", " Technological Design (TDJ2O)", " Technological Design (TDJ3M)", " Technological Design and the Environment (TDJ3O)", " Technological Design (TDJ4M)", " Technological Design in the Twenty-first Century (TDJ4O)", " Transportation Technology (TTJ2O)", " Transportation Technology (TTJ3C)", " Transportation Technology: Vehicle Ownership (TTJ3O)", " Transportation Technology (TTJ4C)", " Transportation Technology: Vehicle Maintenance (TTJ4E)", " Creative Arts for Enjoyment and Expression (KAL)", " Money Management and Personal Banking (KBB)", " Transit Training and Community Exploration (KCC)", " Exploring Our World (KCW)", " Language and Communication Development (KEN)", " Personal Life Skills (KGL)", " Exploring the World of Work (KGW)", " Social Skills Development (KHD)", " Culinary Skills (KHI)", " Numeracy and Numbers (KMM)", " First Canadians (KNA)", " Personal Health and Fitness (KPF)", " Choice Making for Healthy Living (KPH)", " Self Help and Self Care (KPP)", " Exploring Our Environment (KSN)", " Computer Skills (KTT)",
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

        gr.Markdown("#### Resume previous session")
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
                    info="Pick at least 1.",
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
                loading_indicator = gr.HTML(value="",visible=False, elem_id="loading_indicator")
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
            "loading_indicator": loading_indicator,
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