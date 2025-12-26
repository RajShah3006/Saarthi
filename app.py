import re
import json
import os
import csv
import datetime
import time

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import gradio as gr
import google.generativeai as genai

# ========== CONFIG ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY missing in environment.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

GEMINI_MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(GEMINI_MODEL_NAME)
chat = model.start_chat()

ADMIN_PASSWORD = "saarthi-admin-rs"

CACHE_FILE = "university_data_cached.json"
LOG_FILE = "user_traffic_logs.csv"
USER_FILE = "users.json"
CHAT_FILE = "chats.json"

GRADE_OPTIONS = ["Grade 11", "Grade 12", "Gap Year"]

ALL_COURSES = [
    "Dramatic Arts (ADA4M1)", "Drama Film/Video (ADV4M1)", "Exploring and Creating in the Arts (AEA4O1)",
    "Guitar Music (AMG4M1)", "Music (AMU4M1)", "Visual Arts (AVI4M1)",
    "Visual Arts - Info/Consumer (AWE4M1)", "Visual Arts - Fashion (AWI4M1)",
    "Visual Arts - Drawing (AWM4M1)", "Visual Arts - Photography (AWQ4M1)",
    "Visual Arts - Film/Video (AWR4M1)", "Visual Arts - Computer (AWS4M1)",
    "Visual Arts - Non-Traditional (AWT4M1)", "Entrepreneurship: Venture Planning (BDV4C1)",
    "Environment & Resource Mgmt (CGR4M1)", "World Issues (CGW4U1)",
    "Canada: History, Identity, Culture (CHI4U1)", "World History (CHY4U1)",
    "Canadian & International Law (CLN4U1)", "Canadian & World Politics (CPW4U1)",
    "English (University) (ENG4U1)", "English (College) (ENG4C1)", "Studies in Literature (ETS4U1)",
    "The Writer's Craft (EWC4U1)", "Nutr. & Health (HFA4U1)", "Personal Life Mgmt (HIP4O1)",
    "Challenge & Change (HSB4U1)", "Equity & Social Justice (HSE4M1)", "Philosophy (HZT4U1)",
    "Interdisciplinary Studies (IDC4U1)", "College Math (MAP4C1)", "Calculus/Vectors (MCV4U1)",
    "Data Management (MDM4U1)", "Advanced Functions (MHF4U1)", "Literacy (OLC4O1)",
    "Personal Fitness (PAF4O1)", "Recreation (PLF4M1)", "Active Living (PPL4O1)",
    "Kinesiology (PSK4U1)", "Biology (SBI4U1)", "Chemistry (SCH4U1)", "Physics (SPH4U1)",
    "Dramatic Arts (ADA3M1)", "Drama Film (ADV3M1)", "Guitar Music (AMG3M1)",
    "Media Arts (ASM3M1)", "Visual Arts (AVI3M1)", "Arts & Crafts (AWA3M1)",
    "Fashion Arts (AWI3M1)", "Photography (AWQ3M1)", "Accounting (BAF3M1)",
    "Entrepreneurship (BDI3C1)", "Marketing (BMI3C1)", "Forces of Nature (CGF3M1)",
    "Travel/Tourism (CGG3O1)", "Genocide Studies (CHG381)", "World History (CHW3M1)",
    "Canadian Law (CLU3M1)", "Media Studies (EMS3O1)", "Food & Culture (HFC3M1)",
    "World Religions (HRT3M1)", "Anth/Psych/Soc (HSP3U1)", "Philosophy (HZB3M1)",
    "Functions (MCR3U1)", "Functions & Apps (MCF3M1)", "First Nations Voices (NBE3U1)",
    "Biology (SBI3U1)", "Chemistry (SCH3U1)", "Physics (SPH3U1)", "Environmental Sci (SVN3M1)",
    "Tech Design (TDJ3M1)", "Hairstyling (TXJ3E1)"
]

ghost_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body, .gradio-container {
    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1729 100%);
    font-family: "Inter", sans-serif;
    color: #e8f1ff;
    position: relative;
}

/* Animated gradient orbs background */
.gradio-container:before {
    content: "";
    position: fixed;
    inset: 0;
    background: 
        radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 40% 80%, rgba(236, 72, 153, 0.1) 0%, transparent 50%);
    animation: floatOrbs 20s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
}

@keyframes floatOrbs {
    0%, 100% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.1); }
}

/* Grid overlay */
.gradio-container:after {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
}

/* Make all children above background */
.gradio-container > * {
    position: relative;
    z-index: 1;
}

/* Translucent glass panels */
.gr-panel, .gr-box, .gr-form, .gr-input {
    background: rgba(15, 23, 42, 0.3) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.05),
        0 0 0 1px rgba(59, 130, 246, 0.1);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.gr-panel:hover, .gr-box:hover {
    background: rgba(15, 23, 42, 0.4) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    box-shadow: 
        0 12px 48px rgba(59, 130, 246, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.1),
        0 0 0 1px rgba(59, 130, 246, 0.2);
    transform: translateY(-2px);
}

/* Translucent input fields */
textarea, input, .gr-textbox, .gr-text-input, select {
    background: rgba(15, 23, 42, 0.4) !important;
    border: 2px solid rgba(59, 130, 246, 0.25) !important;
    border-radius: 14px !important;
    color: #e8f1ff !important;
    padding: 14px !important;
    font-size: 15px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    transition: all 0.3s ease;
}

textarea:focus, input:focus, .gr-textbox:focus, select:focus {
    background: rgba(15, 23, 42, 0.5) !important;
    border-color: rgba(59, 130, 246, 0.6) !important;
    box-shadow: 
        0 0 0 4px rgba(59, 130, 246, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    outline: none !important;
}

textarea::placeholder, input::placeholder {
    color: rgba(203, 213, 225, 0.5) !important;
}

/* Glass buttons */
button {
    background: rgba(59, 130, 246, 0.2) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(59, 130, 246, 0.4) !important;
    color: #93c5fd !important;
    border-radius: 14px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    cursor: pointer !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 4px 16px rgba(59, 130, 246, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

button:hover {
    background: rgba(59, 130, 246, 0.35) !important;
    border-color: rgba(59, 130, 246, 0.6) !important;
    color: #dbeafe !important;
    transform: translateY(-2px);
    box-shadow: 
        0 8px 24px rgba(59, 130, 246, 0.35),
        inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
}

button:active {
    transform: translateY(0px);
}

/* Primary button - Golden glass */
.primary {
    background: rgba(245, 158, 11, 0.25) !important;
    border: 1px solid rgba(245, 158, 11, 0.5) !important;
    color: #fcd34d !important;
    box-shadow: 
        0 4px 20px rgba(245, 158, 11, 0.25),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.primary:hover {
    background: rgba(245, 158, 11, 0.4) !important;
    border-color: rgba(245, 158, 11, 0.7) !important;
    color: #fef3c7 !important;
    box-shadow: 
        0 8px 32px rgba(245, 158, 11, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

/* Translucent markdown */
.gr-markdown, .gr-html {
    background: rgba(15, 23, 42, 0.25) !important;
    border: 1px solid rgba(59, 130, 246, 0.15) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    color: #e8f1ff !important;
    line-height: 1.8 !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
    color: #93c5fd !important;
    font-weight: 700 !important;
    margin-top: 28px !important;
    margin-bottom: 14px !important;
    text-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.gr-markdown h2 {
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
}

.gr-markdown strong {
    color: #fbbf24 !important;
    font-weight: 600 !important;
}

.gr-markdown a {
    color: #60a5fa !important;
    text-decoration: none !important;
    border-bottom: 1px solid rgba(96, 165, 250, 0.4);
    transition: all 0.2s;
    padding-bottom: 2px;
}

.gr-markdown a:hover {
    color: #93c5fd !important;
    border-bottom-color: rgba(147, 197, 253, 0.8);
    text-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

.gr-markdown code {
    background: rgba(59, 130, 246, 0.15) !important;
    padding: 2px 6px !important;
    border-radius: 6px !important;
    border: 1px solid rgba(59, 130, 246, 0.2);
    font-family: 'Fira Code', monospace !important;
}

.gr-markdown hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, 
        transparent, 
        rgba(59, 130, 246, 0.4), 
        transparent) !important;
    margin: 24px 0 !important;
}

/* Glass scrollbar */
::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.2);
    border-radius: 10px;
    backdrop-filter: blur(8px);
}

::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.3);
    border-radius: 10px;
    border: 2px solid rgba(15, 23, 42, 0.2);
    backdrop-filter: blur(8px);
    transition: all 0.3s;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.5);
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
}

/* Labels with glow */
label {
    color: #cbd5e1 !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    margin-bottom: 8px !important;
    text-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
}

/* Dropdown translucent */
.gr-dropdown {
    background: rgba(15, 23, 42, 0.4) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

/* Group containers */
.gr-group {
    background: rgba(15, 23, 42, 0.2) !important;
    border: 1px solid rgba(59, 130, 246, 0.1) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(16px) !important;
}

/* Loading spinner glow */
.loading {
    filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.6));
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Shimmer effect on hover */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.gr-panel:hover::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(59, 130, 246, 0.1),
        transparent
    );
    background-size: 1000px 100%;
    animation: shimmer 2s infinite;
    border-radius: 20px;
    pointer-events: none;
}

/* Hide Gradio footer */
footer {
    display: none !important;
}

/* Alternative: Hide specific footer elements */
.gradio-container footer,
.gradio-container .footer {
    display: none !important;
}

/* Hide the Built with Gradio link */
.built-with-gradio {
    display: none !important;
}

/* Remove Gradio loading bar */
.progress-bar,
.progress-bar-wrap,
.loading,
.eta-bar,
.block-label-loading,
.wrap.pending {
    display: none !important;
}

/* Hide the orange/gold border animation */
.pending {
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    animation: none !important;
}

/* Remove any pulsing/loading effects */
@keyframes pulse {
    0%, 100% { border-color: rgba(59, 130, 246, 0.3); }
}

/* Hide status indicator */
.loading-spinner,
.loader {
    display: none !important;
}
</style>
"""


# ========== DATA LOADERS ==========

def load_programs():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[DATA] Loaded {len(data)} programs from {CACHE_FILE}")
                return data
        except Exception as e:
            print(f"[DATA] Failed to load {CACHE_FILE}: {e}")
    else:
        print(f"[DATA] Cache file {CACHE_FILE} not found.")
    return []

all_programs_detailed_data = load_programs()

def log_interaction(grade, location, interests, subjects):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_needed = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header_needed:
            writer.writerow(["Timestamp", "Grade", "Location", "Interests", "Subjects"])
        writer.writerow([ts, grade, location, interests, subjects])

# ========== EMBEDDING MATCHING ==========

def get_single_embedding(text):
    try:
        resp = genai.embed_content(
            model="models/text-embedding-004",
            content=str(text)[:2000],
            task_type="retrieval_query",
        )
        return resp["embedding"]
    except Exception as e:
        print("[EMBED] Error:", e)
        return [0.0] * 768

def find_best_matches(query, data, top_k=10):
    if not data:
        return []
    q_vec = get_single_embedding(query)
    valid = [p for p in data if p.get("embedding")]
    if not valid:
        return data[:top_k]
    db_vecs = [p["embedding"] for p in valid]
    try:
        sims = cosine_similarity([q_vec], db_vecs)[0]
    except Exception as e:
        print("[SIM] Error:", e)
        sims = np.zeros(len(db_vecs))
    top_indices = np.argsort(sims)[-top_k:][::-1]
    return [valid[i] for i in top_indices]

def generate_chatbot_response(user_data, relevant_programs):
    context = ""
    for p in relevant_programs:
        context += f"- {p.get('program_name','Unknown')} (Avg: {p.get('admission_average','Not listed')})\n"
        context += f"  Prereqs: {p.get('prerequisites','Not listed')}\n"
        context += f"  Link: {p.get('program_url','#')}\n\n"

    prompt = f"""
Act as 'Saarthi', a wise university guidance counselor.
STUDENT:
- Interests: {user_data['interests']}
- Grade: {user_data['grade']}
- Avg: {user_data['overall_average']}
- Courses: {user_data['subjects']}
- Location: {user_data['location']}
- Extracurriculars: {user_data['extracurriculars']}
OPTIONS:
{context}
TASK:
1. **Rank & Recommend:** Recommend the top 10 programs.
2. **Prerequisite Check:** Compare "Subjects" vs "Prereqs". Warn if missing.
3. **Fit Analysis:** Explain fit.
4. **Extracurriculars:** Suggest side projects.
5. **COMMUTE ANALYSIS:**
   - Estimate travel time from '{user_data['location']}' to each university.
   - If > 1 hour, suggest RESIDENCE.
   - Briefly mention GO Train / gas cost ballpark.
6. **Tone:** Warm and supportive. Use emojis.
"""
    try:
        return chat.send_message(prompt).text
    except Exception as e:
        return f"Error generating response: {e}"

# ========== USER & CHAT STORAGE ==========

def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(USER_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        print(f"[WARNING] Corrupted {USER_FILE}, resetting...")
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
        return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_chats():
    if not os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(CHAT_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        print(f"[WARNING] Corrupted {CHAT_FILE}, resetting...")
        with open(CHAT_FILE, "w") as f:
            json.dump({}, f)
        return {}

def save_chats(chats):
    with open(CHAT_FILE, "w") as f:
        json.dump(chats, f, indent=2)

def register_user(email, password, role):
    users = load_users()
    if role != "Student":
        return "Only students can register."
    if not email or not password:
        return "Please provide both email and password."
    if email in users:
        return "Email already registered. Please login."
    users[email] = {"password": password, "role": role}
    save_users(users)
    chats = load_chats()
    chats[email] = []
    save_chats(chats)
    return "Registration successful! You can now log in."

def login_user(email, password, role):
    users = load_users()

    # Admin login
    if role == "Admin":
        if password == ADMIN_PASSWORD:
            student_list = [u for u, v in users.items() if v.get("role") == "Student"]
            if student_list:
                student_str = "\n".join(f"- {u}" for u in student_list)
            else:
                student_str = "No registered students."
            admin_content = f"**Registered Students:**\n{student_str}"
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                "",
                "",
                "Admin logged in.",
                admin_content,
            )
        else:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                "",
                "",
                "Invalid admin password.",
                "",
            )

    # Student login
    if role == "Student":
        if email in users and users[email]["password"] == password:
            chats = load_chats()
            chat_history = chats.get(email, [])
            # Build display from chat history
            display = "Welcome! Generate a roadmap to start."
            if chat_history:
                for user_msg, bot_msg in chat_history:
                    display += f"\n\n---\n\n**You:** {user_msg}\n\n**Saarthi:** {bot_msg}"
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                display,
                email,
                f"Welcome, {email}!",
                "",
            )
        else:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                "",
                "",
                "Invalid email or password.",
                "",
            )

# ========== STUDENT CHAT LOGIC ==========
def student_generate(subjects, interests, extracurriculars, average, grade, location, current_output, user_email):
    if not user_email:
        return "Please log in first."

    subjects_str = ", ".join(subjects) if subjects else "None"
    log_interaction(grade, location, f"{interests} | ECs: {extracurriculars}", subjects_str)

    user_data = {
        "subjects": subjects_str,
        "interests": interests,
        "extracurriculars": extracurriculars,
        "overall_average": average,
        "grade": grade,
        "location": location,
    }

    matches = find_best_matches(interests or "", all_programs_detailed_data, top_k=10)
    response = generate_chatbot_response(user_data, matches)

    prompt_summary = (
        f"Subjects: {subjects_str}\n"
        f"Interests: {interests}\n"
        f"Extracurriculars: {extracurriculars}\n"
        f"Avg: {average}\n"
        f"Grade: {grade}\n"
        f"Location: {location}"
    )

    # Save to chat history
    chats = load_chats()
    if user_email not in chats:
        chats[user_email] = []
    chats[user_email].append([prompt_summary, response])
    save_chats(chats)

    # Update display
    display_text = f"**Your Roadmap Request:**\n{prompt_summary}\n\n**Saarthi Response:**\n{response}"
    return display_text

def student_followup(message, user_email, current_output):
    if not message or not user_email:
        return "", current_output

    # Call Gemini for response
    try:
        response = chat.send_message(message).text
    except Exception as e:
        response = f"Error: {e}"

    # Save to chat history
    chats = load_chats()
    if user_email not in chats:
        chats[user_email] = []
    chats[user_email].append([message, response])
    save_chats(chats)

    # Append to output
    new_output = f"{current_output}\n\n---\n\n**You:** {message}\n\n**Saarthi:** {response}"
    return "", new_output

# ========== UI DEFINITION ==========
with gr.Blocks(title="Saarthi AI") as app:
    gr.HTML(ghost_css)
    current_user = gr.State("")

    # Login section
    with gr.Column() as login_section:
        gr.Markdown("## Saarthi AI - Login")
        role_dropdown = gr.Dropdown(choices=["Student", "Admin"], value="Student", label="Select Role")
        email_input = gr.Textbox(placeholder="Enter your email", label="Email")
        password_input = gr.Textbox(placeholder="Enter your password", label="Password", type="password")
        login_msg = gr.Textbox(label="Status", interactive=False)
        with gr.Row():
            register_button = gr.Button("Register")
            login_button = gr.Button("Login")

    # Student section
    with gr.Column(visible=False) as student_column:
        gr.Markdown("## Student Guidance")
        
        with gr.Row():
            # Left: Input form
            with gr.Column(scale=1):
                gr.Markdown("### Your Profile")
                inp_subjects = gr.Dropdown(
                    choices=ALL_COURSES,
                    multiselect=True,
                    label="Current Subjects",
                    info="Search e.g. 'Math', 'SCH4U1'",
                    allow_custom_value=True,
                )
                inp_interests = gr.Textbox(label="Interests", placeholder="e.g. Robotics, Law")
                inp_extra = gr.Textbox(
                    label="Extracurriculars",
                    placeholder="e.g. DECA, Robotics Club, Volunteering",
                )
                inp_avg = gr.Textbox(label="Average %")
                inp_grade = gr.Dropdown(GRADE_OPTIONS, label="Grade")
                inp_loc = gr.Textbox(label="Location", placeholder="City, ON")
                gen_button = gr.Button("Generate Roadmap 🚀", variant="primary")
            
            # Right: Output
            with gr.Column(scale=2):
                output_display = gr.Markdown(value="Chat will appear here...")
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask a follow-up question...", label="Follow-up", scale=4
                    )
                    send_button = gr.Button("Send Follow-up", scale=1)

    # Admin section
    with gr.Column(visible=False) as admin_column:
        gr.Markdown("## Admin Dashboard")
        admin_info = gr.Markdown("")

    # Event handlers
    def toggle_register(role):
        return gr.update(visible=(role == "Student"))

    role_dropdown.change(toggle_register, [role_dropdown], [register_button])

    register_button.click(
        register_user, 
        [email_input, password_input, role_dropdown], 
        [login_msg]
    )

    login_button.click(
        login_user,
        [email_input, password_input, role_dropdown],
        [login_section, student_column, admin_column, output_display, current_user, login_msg, admin_info],
    )

    gen_button.click(
        student_generate,
        [inp_subjects, inp_interests, inp_extra, inp_avg, inp_grade, inp_loc, output_display, current_user],
        [output_display],
    )
    
    msg_input.submit(
        student_followup,
        [msg_input, current_user, output_display],
        [msg_input, output_display],
    )
    send_button.click(
        student_followup,
        [msg_input, current_user, output_display],
        [msg_input, output_display],
    )

if __name__ == "__main__":
    app.launch()
