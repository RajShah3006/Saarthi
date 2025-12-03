import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai
import time
import concurrent.futures
import json
import os
import csv
import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import gradio as gr

# --- 1. SETUP ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("⚠️ API Key missing.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
chat = model.start_chat(history=[])

# --- 2. DATA CONFIG ---
CACHE_FILE = "university_data_cached.json"
LOG_FILE = "user_traffic_logs.csv"
GRADE_OPTIONS = ["Grade 11", "Grade 12", "Gap Year"]

# --- COMPLETE COURSE DATABASE (From your PDFs) ---
ALL_COURSES = [
    # GRADE 12
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
    "The Writer's Craft (EWC4U1)", "Nutrition and Health (HFA4U1)",
    "Personal Life Management (HIP4O1)", "Challenge and Change in Society (HSB4U1)",
    "Equity and Social Justice (HSE4M1)", "Philosophy (HZT4U1)",
    "Interdisciplinary Studies (IDC4U1)", "Foundations for College Math (MAP4C1)",
    "Calculus and Vectors (MCV4U1)", "Data Management (MDM4U1)",
    "Advanced Functions (MHF4U1)", "Literacy Course (OLC4O1)",
    "Personal Fitness (PAF4O1)", "Recreation Leadership (PLF4M1)",
    "Healthy Active Living (PPL4O1)", "Kinesiology (PSK4U1)",
    "Biology (SBI4U1)", "Chemistry (SCH4U1)", "Physics (SPH4U1)",

    # GRADE 11
    "Dramatic Arts (ADA3M1)", "Drama Film/Video (ADV3M1)", "Guitar Music (AMG3M1)",
    "Media Arts (ASM3M1)", "Visual Arts (AVI3M1)", "Visual Arts - Crafts (AWA3M1)",
    "Visual Arts - Fashion (AWI3M1)", "Photography (AWQ3M1)",
    "Financial Accounting (BAF3M1)", "Entrepreneurship (BDI3C1)",
    "Marketing (BMI3C1)", "Forces of Nature (CGF3M1)", "Travel and Tourism (CGG3O1)",
    "Genocide and Crimes Against Humanity (CHG381)", "World History to 16th Century (CHW3M1)",
    "Understanding Canadian Law (CLU3M1)", "Media Studies (EMS3O1)",
    "Food and Culture (HFC3M1)", "World Religions (HRT3M1)",
    "Intro to Anthropology/Psych/Soc (HSP3U1)", "Philosophy: Big Questions (HZB3M1)",
    "Functions (MCR3U1)", "Functions & Applications (MCF3M1)",
    "First Nations, Métis, Inuit Voices (NBE3U1)", "Biology (SBI3U1)",
    "Chemistry (SCH3U1)", "Physics (SPH3U1)", "Environmental Science (SVN3M1)",
    "Technological Design (TDJ3M1)", "Hairstyling and Aesthetics (TXJ3E1)"
]

# --- 3. CSS (Invisible Theme) ---
ghost_css = """
opacity:0.1;
body, .gradio-container, .dark { background-color: rgba(255, 255, 255, 0.5); opacity: 0.1; }
footer { display: none !important; }
#component-0 { border: none !important; box-shadow: none !important; }

/* Glass Inputs */
.group, .input_area, .dropdown-container {
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(4px);
    border-radius: 12px !important;
}
/* Text Colors */
label span, textarea, input, .prose, span {
    color: #e2e8f0 !important;
}
input, textarea { background-color: transparent !important; }

/* Buttons & Chat */
.message.user { background: linear-gradient(90deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; }
.message.bot { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #e2e8f0 !important; }
button.primary { background: #6366f1 !important; border: none !important; }
"""

# --- 4. LOGIC ---
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def save_data(data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(data, f)

def load_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return None

def get_single_embedding(text):
    try:
        result = genai.embed_content(model="models/text-embedding-004", content=str(text)[:2000], task_type="retrieval_query")
        return result['embedding']
    except: return [0] * 768

def log_interaction(grade, location, interests, subjects):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode = 'a' if os.path.exists(LOG_FILE) else 'w'
    with open(LOG_FILE, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w': writer.writerow(["Timestamp", "Grade", "Location", "Interests", "Subjects"])
        writer.writerow([timestamp, grade, location, interests, subjects])

all_programs_detailed_data = load_data() or []

def find_best_matches(query, data, top_k=5):
    if not data: return []
    q_vec = get_single_embedding(query)
    valid_data = [x for x in data if 'embedding' in x]
    if not valid_data: return data[:5]
    db_vecs = [x['embedding'] for x in valid_data]
    scores = cosine_similarity([q_vec], db_vecs)[0]
    top_indices = scores.argsort()[-top_k:][::-1]
    return [valid_data[i] for i in top_indices]

def initial_report(subjects, interests, average, grade, location):
    subjects_str = ", ".join(subjects) if subjects else "None"
    log_interaction(grade, location, interests, subjects_str)
    
    matches = find_best_matches(interests, all_programs_detailed_data)
    
    context_data = {
        "profile": f"Grade: {grade}, Avg: {average}, Loc: {location}, Subj: {subjects_str}, Int: {interests}",
        "matches": matches
    }
    
    context_str = ""
    for p in matches:
        name = p.get('program_name', p.get('name', 'Unknown'))
        context_str += f"- {name} (Avg: {p.get('admission_average', 'N/A')})\n  Prereqs: {p.get('prerequisites', 'N/A')}\n  Link: {p.get('program_url', '#')}\n\n"

    # FIX: Used direct variables instead of user_data dict
    prompt = f"""
    Act as 'Saarthi', a futuristic AI guidance counselor.
    
    STUDENT: {context_data['profile']}
    OPTIONS: {context_str}
    
    MISSION:
    1. **Rank & Recommend:** Recommend the top 10 programs.
    2. **Prerequsite Check:** Compare "Subjects" vs "Prereqs". Warn if missing.
    3. **Fit Analysis:** Explain fit.
    4. **Extracurriculars:** Suggest side projects.
    5. **COMMUTE ANALYSIS:** - Calculate estimated travel time from '{location}' to the university.
       - If > 1 hour, recommend RESIDENCE.
       - Estimate Cost (GO Train/Gas).
    6. **Tone:** Warm and supportive. Use emojis.
    """
    
    try: 
        response = chat.send_message(prompt).text
    except Exception as e: 
        response = f"Error: {e}"
    
    return [(None, response)], context_data, gr.update(visible=True), gr.update(visible=True)

def follow_up_chat(user_message, history, context_data):
    if not context_data: return history + [(user_message, "Generate a roadmap first!")], ""
    context_str = "\n".join([f"- {p.get('program_name', 'Program')}" for p in context_data['matches']])
    prompt = f"CONTEXT: {context_data['profile']}\nOPTIONS: {context_str}\nUSER: {user_message}"
    try: response = chat.send_message(prompt).text
    except: response = "Connection error."
    history.append((user_message, response))
    return history, ""

# --- ADMIN LOGIC ---
def get_admin_logs(password):
    # REPLACE "1234" WITH YOUR OWN SECRET PASSWORD
    if password != "saarthi-admin-rs": 
        return None, "❌ Access Denied: Wrong Password"
    
    if os.path.exists(LOG_FILE):
        return LOG_FILE, "✅ Access Granted: Logs Ready"
    else:
        return None, "⚠️ No logs found yet."
        
# --- 5. UI ---
with gr.Blocks(theme="dark", css=ghost_css, title="Saarthi AI") as app:
    session_state = gr.State()
    
    with gr.Row():
        with gr.Column(scale=1):
            # THIS IS THE FIXED DROPDOWN
            inp_subjects = gr.Dropdown(
                choices=ALL_COURSES, 
                multiselect=True, 
                label="Current Subjects", 
                info="Type to search (e.g. 'Math', 'SCH4U1')",
                allow_custom_value=True
            )
            inp_interests = gr.Textbox(label="Interests", placeholder="e.g. Robotics, Law")
            inp_avg = gr.Textbox(label="Average %")
            inp_grade = gr.Dropdown(GRADE_OPTIONS, label="Grade")
            inp_loc = gr.Textbox(label="Location", placeholder="City, ON")
            
            btn_generate = gr.Button("Generate Roadmap 🚀", variant="primary")
            
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Saarthi's Guidance", height=600, bubble_full_width=False, type="tuples")
            with gr.Row():
                txt_followup = gr.Textbox(label="Follow-up", placeholder="Ask anything...", visible=False, scale=4)
                btn_ask = gr.Button("Send", visible=False, scale=1)

    btn_generate.click(fn=initial_report, inputs=[inp_subjects, inp_interests, inp_avg, inp_grade, inp_loc], outputs=[chatbot, session_state, txt_followup, btn_ask])
    txt_followup.submit(fn=follow_up_chat, inputs=[txt_followup, chatbot, session_state], outputs=[chatbot, txt_followup])
    btn_ask.click(fn=follow_up_chat, inputs=[txt_followup, chatbot, session_state], outputs=[chatbot, txt_followup])
    
# --- ADMIN TAB (Locked) ---
    with gr.Tab("🔐 Admin Panel"):
        gr.Markdown("### Administrator Access Only")
        gr.Markdown("Enter the master password to download user traffic logs.")
        
        with gr.Row():
            admin_pass = gr.Textbox(label="Enter Admin Password", type="password", placeholder="••••••••")
            btn_admin = gr.Button("Unlock Logs 🔓", variant="primary")
        
        # These are hidden until you unlock them
        admin_status = gr.Textbox(label="Status", interactive=False)
        admin_file = gr.File(label="Download Log CSV", interactive=False)

        # The Button Logic
        btn_admin.click(
            fn=get_admin_logs, 
            inputs=[admin_pass], 
            outputs=[admin_file, admin_status]
        )
if __name__ == "__main__":
    app.launch()