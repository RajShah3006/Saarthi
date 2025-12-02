# 🏹 Saarthi AI: Intelligent University Guidance Counselor

**Saarthi** (meaning "Charioteer" or "Guide") is an AI-powered application designed to help Ontario high school students navigate their post-secondary options. Unlike standard search engines, Saarthi uses **Retrieval-Augmented Generation (RAG)** to provide personalized, data-backed recommendations based on a student's unique profile.

---

## 🧠 Key Technical Methods Used

This project moves beyond simple "if/then" logic by implementing modern AI architecture. Here are the core methods powering the bot:

### 1. Retrieval-Augmented Generation (RAG)
Instead of relying solely on the AI's training data (which might be outdated), Saarthi uses a RAG pipeline:
1.  **Retrieval:** When a user enters their interests (e.g., "Robotics"), the system searches a local database of scraped university programs to find the most relevant matches.
2.  **Augmentation:** The detailed data of the top matches (Prerequisites, Admission Averages, URLs) is injected into the AI's context window.
3.  **Generation:** Google Gemini generates a response using *only* the retrieved facts, ensuring accuracy and reducing hallucinations.



[Image of Retrieval Augmented Generation RAG architecture diagram]


### 2. Semantic Search via Embeddings
The search functionality does not use basic keyword matching. It uses **Vector Embeddings**:
* **Model:** `models/text-embedding-004` (Google Gemini).
* **Method:** Every university program description is converted into a 768-dimensional vector (a list of numbers representing its "meaning").
* **Search:** When a user queries "I like building things," the system calculates the **Cosine Similarity** between the user's query vector and the program vectors. This allows the bot to recommend "Civil Engineering" even if the user never typed the word "Engineering."



[Image of word embedding vector space]


### 3. Parallel Web Scraping & Batch Processing
To build the database, the system includes a high-performance scraper:
* **Concurrency:** Uses `concurrent.futures.ThreadPoolExecutor` to scrape multiple university pages simultaneously, reducing data collection time by ~90%.
* **Batch Embeddings:** Instead of processing items one by one, data is sent to the embedding API in batches (e.g., chunks of 50), significantly reducing API overhead and latency.

### 4. Stateful Conversational Memory
The application uses a **Hybrid UI Architecture** (Gradio Blocks):
* **State Management:** Uses `gr.State()` to persist the user's profile (Grade, Average, Location) across multiple turns of conversation.
* **Context Injection:** Every follow-up question (e.g., "How is the commute?") automatically re-sends the user's profile and the previously retrieved university options to the AI, ensuring the bot never loses context.

---

## 🛠️ Tech Stack & Tools

**Core AI & Logic**
* **[Google Gemini API](https://ai.google.dev/)**: The "Brain" of the application (Model: `gemini-2.5-flash`). Used for generating advice and creating vector embeddings (`text-embedding-004`).
* **[Scikit-Learn](https://scikit-learn.org/)**: Used to perform **Cosine Similarity** calculations for the RAG (Retrieval-Augmented Generation) search engine.
* **[NumPy](https://numpy.org/)**: Handles the vector math and array processing for the embeddings.

**Interface & Frontend**
* **[Gradio](https://www.gradio.app/)**: The Python library used to build the interactive chat interface and dropdown menus.
* **[HTML5 / CSS3](https://developer.mozilla.org/en-US/docs/Web/HTML)**: Used for the custom "Glassmorphism" landing page and responsive design.
* **[JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)**: Connects the custom HTML frontend to the Python backend via API.

**Data Processing**
* **[Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)**: The web scraping library used to extract university program data from OUInfo.
* **[Requests](https://requests.readthedocs.io/)**: Handles HTTP requests to fetch web pages for scraping.
* **[Pandas](https://pandas.pydata.org/)**: (Optional) Used for organizing data during the initial scraping phase.

**Infrastructure & Deployment**
* **[Hugging Face Spaces](https://huggingface.co/spaces)**: Hosts the Python backend server 24/7 for free.
* **[GitHub Pages](https://pages.github.com/)**: Hosts the static HTML frontend website.
* **[Namecheap](https://www.namecheap.com/)**: Provided the free `.me` custom domain (via the [GitHub Student Developer Pack](https://education.github.com/pack)).
* **[Google Colab](https://colab.research.google.com/)**: The development environment used to write, test, and debug the initial code.

---

## 🚀 Features

* **Smart Roadmap Generation:** Takes 5 inputs (Subjects, Interests, Average, Grade, Location) and generates a top-3 program list.
* **Prerequisite Auditing:** Automatically checks the user's selected Grade 11/12 courses against university requirements and warns of missing credits.
* **Commute Analysis:** The AI estimates travel time and cost (GO Train/Gas) from the user's home city to the campus.
* **Glassmorphism UI:** A custom CSS theme featuring a transparent, space-themed interface with animated backgrounds.

---

## 🔮 Future Roadmap

* [ ] **Real-time Transit API:** Integrate Google Maps API for exact commute times.
* [ ] **Scholarship Database:** Create a secondary vector store specifically for financial aid matching.
* [ ] **Transcript OCR:** Allow users to upload a PDF of their report card for automatic grade parsing using Gemini Vision.

---
