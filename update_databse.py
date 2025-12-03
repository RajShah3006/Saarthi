import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai
import json
import os
import time
import concurrent.futures
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("⚠️ Error: GOOGLE_API_KEY not found in .env file.")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# --- SCRAPING FUNCTIONS ---
def list_all_programs(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        programs_list = []
        for el in soup.select('h2.result-heading'):
            link = el.find('a', href=True)
            if link:
                programs_list.append({'name': el.get_text(strip=True), 'url': link['href']})
        return programs_list
    except: return []

def scrape_university_info(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}
        prereqs = []
        for h in soup.find_all(string=re.compile(r'Prerequisites|Admission Requirements', re.IGNORECASE)):
            lst = h.find_next(['ul', 'ol'])
            if lst: prereqs.extend([li.get_text(strip=True) for li in lst.select('li')])
        
        data['prerequisites'] = ", ".join(list(set(prereqs))) if prereqs else "Not listed"
        
        avg = soup.find(string=re.compile(r'\d+%', re.IGNORECASE))
        data['admission_average'] = avg.strip() if avg else "Not listed"
        return data
    except: return {}

def get_batch_embeddings(text_list):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004", 
            content=text_list, 
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Batch Error: {e}")
        return [[0]*768 for _ in range(len(text_list))]

# --- MAIN EXECUTION ---
def main():
    print("🚀 Starting Database Update...")
    programs_with_urls = []
    # FULL ALPHABET SCAN
    alphabet = ['a', 'b', 'c', 'd-e', 'f-g', 'h', 'i', 'j-l', 'm', 'n-p', 'q-s', 't-z']
    
    for group in alphabet:
        print(f"Scanning Group: {group.upper()}...")
        res = list_all_programs(f"https://www.ouinfo.ca/programs/search/?search=&group={group}")
        if res: programs_with_urls.extend(res)
    
    print(f"✅ Found {len(programs_with_urls)} programs. Deep scraping details...")
    
    scraped_results = []
    
    def process_program(entry):
        url = f"https://www.ouinfo.ca{entry['url']}"
        data = scrape_university_info(url)
        return {'program_name': entry['name'], 'program_url': url, **data}

    # Parallel Scrape (Fast)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_program, p): p for p in programs_with_urls}
        completed = 0
        total = len(futures)
        for future in concurrent.futures.as_completed(futures):
            if future.result(): scraped_results.append(future.result())
            completed += 1
            if completed % 50 == 0: print(f"Scraped {completed}/{total}...")

    print("\n🧠 Generating AI Embeddings...")
    texts = [f"{item['program_name']} {item.get('prerequisites','')}"[:2000] for item in scraped_results]
    all_vectors = []
    
    # Batch Embeddings
    for i in range(0, len(texts), 50):
        batch = texts[i : i + 50]
        print(f"Embedding batch {i}...", end="\r")
        if batch:
            all_vectors.extend(get_batch_embeddings(batch))
            time.sleep(1)

    # Combine Data
    final_database = []
    for i, item in enumerate(scraped_results):
        if i < len(all_vectors):
            item['embedding'] = all_vectors[i]
            final_database.append(item)
    
    # SAVE TO FILE
    with open("university_data_cached.json", 'w', encoding='utf-8') as f:
        json.dump(final_database, f)
        
    print(f"\n✅ SUCCESS! New database saved with {len(final_database)} programs.")
    print("👉 Now upload 'university_data_cached.json' to Hugging Face.")

if __name__ == "__main__":
    main()
