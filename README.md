# 🏹 Saarthi AI: Intelligent University Guidance Counselor

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/gradio-4.0+-orange.svg)](https://gradio.app)

**Saarthi** (Sanskrit: सारथी, "Charioteer") is a production-grade AI application that helps Ontario high school students find personalized university program recommendations. The system implements **Retrieval-Augmented Generation (RAG)** with **semantic vector search** to match students with programs based on their interests, grades, and course selections.

🔗 **Live Demo:** [saarthi.me](https://saarthi.me) | **Backend:** [Hugging Face Space](https://huggingface.co/spaces/rajshah13/saarthi)

---

## 📑 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Core Algorithms](#-core-algorithms)
- [Project Structure](#-project-structure)
- [Services & Modules](#-services--modules)
- [Data Pipeline](#-data-pipeline)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [Deployment](#-deployment)
- [Future Roadmap](#-future-roadmap)

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **Smart Roadmap Generation** | Multi-step wizard collecting grade, average, subjects, interests, extracurriculars, and location to generate personalized program recommendations |
| **Semantic Program Search** | Uses 768-dimensional vector embeddings and cosine similarity to find programs matching student interests—even with typos or synonyms |
| **Prerequisite Auditing** | Automatically checks the user's Grade 11/12 courses against university requirements and warns of missing prerequisites |
| **Timeline & Checklist** | Auto-generated application timeline anchored to OUAC deadlines (Jan 15) with customized project checklists |
| **Program Comparison** | Side-by-side comparison of up to 4 programs with match scores, co-op availability, and admission requirements |
| **Follow-up Q&A** | Conversational interface to ask follow-up questions about recommended programs |
| **Email Request Workflow** | Students can request roadmaps via email; admin panel manages queue with GitHub Issues integration |
| **Resume Sessions** | Resume previous sessions using a unique code stored in localStorage |
| **Glassmorphism UI** | Space-themed interface with animated backgrounds, shooting stars, and responsive design |

---

## 🏗 System Architecture

### High-Level Overview

```
┌────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│         index.html (GitHub Pages) + Gradio (HF Spaces)         │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│              app.py (Gradio) + api_server.py (FastAPI)         │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                       CONTROLLER LAYER                          │
│                        controllers.py                           │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                        SERVICE LAYER                            │
│   llm_client │ program_search │ roadmap │ session │ storage    │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                              │
│            programs.json (embeddings) + SQLite DB              │
└────────────────────────────────────────────────────────────────┘
```

### Layer Details

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Presentation** | `index.html`, Gradio Blocks | Static landing page (GitHub Pages) + Interactive wizard UI (HF Spaces) |
| **Application** | `app.py`, `api_server.py` | Gradio event wiring, FastAPI REST endpoints |
| **Controller** | `controllers.py` | Input validation, service orchestration, response assembly |
| **Service** | `services/` directory | LLM client, semantic search, roadmap generation, persistence |
| **Data** | `programs.json`, SQLite | Program database with embeddings, submission storage |

### Request Flow

| Step | Action | Component |
|------|--------|-----------|
| 1 | User submits profile through 4-step wizard | Gradio UI |
| 2 | Input validation sanitizes all fields | `validators.py` |
| 3 | Semantic search finds top-10 matching programs | `program_search.py` |
| 4 | RAG assembles context from programs + profile | `roadmap.py` |
| 5 | LLM generates personalized analysis | `llm_client.py` |
| 6 | Timeline and checklist generated | `roadmap.py` |
| 7 | Dashboard renders all components | `dashboard_renderer.py` |

---

## 🧠 Core Algorithms & AI Concepts

### Key Technical Terms

| Term | Description |
|------|-------------|
| **RAG (Retrieval-Augmented Generation)** | AI architecture that retrieves relevant documents before generating responses, reducing hallucinations by grounding LLM output in real data |
| **Vector Embeddings** | 768-dimensional numerical representations of text that capture semantic meaning, enabling similarity comparisons |
| **Cosine Similarity** | Mathematical measure of similarity between two vectors, calculated as the dot product of normalized vectors |
| **Semantic Search** | Search method that understands meaning rather than just keywords, finding related content even with different wording |
| **LLM (Large Language Model)** | AI model (Google Gemini) used for natural language understanding and generation |
| **Context Window** | The text provided to the LLM containing retrieved documents and user profile for generating responses |
| **Prompt Engineering** | Designing system prompts and user prompts to guide LLM behavior and output format |
| **Sigmoid Function** | S-shaped mathematical function used to convert grade differences into probability scores |
| **Weighted Linear Combination** | Scoring method that combines multiple factors with configurable weights |
| **Fuzzy Matching** | String comparison technique that finds similar text even with typos or variations |
| **Top-K Retrieval** | Selecting the K most relevant items from a larger corpus |
| **Exponential Backoff** | Retry strategy that increases wait time between attempts (1s, 2s, 4s...) |
| **TTL (Time To Live)** | Session expiration mechanism based on elapsed time |
| **Graceful Degradation** | System design that provides reduced functionality rather than failing completely |

### Multi-Factor Program Scoring

The search engine implements a **weighted linear combination** of five scoring factors:

| Factor | Weight | AI/ML Technique |
|--------|--------|-----------------|
| **Relevance** | 35% | Keyword matching with **quadratic suppression** for irrelevant results |
| **Embedding Similarity** | 25% | **Cosine similarity** between query and program **vector embeddings** |
| **Grade Fit** | 20% | **Sigmoid transformation** of admission average delta |
| **Prerequisites** | 15% | Pattern matching for Ontario course codes |
| **Location** | 5% | Geographic region detection |

### RAG Pipeline (Retrieval-Augmented Generation)

The system implements a complete **RAG architecture**:

1. **Retrieval Phase:** **Semantic search** finds top-10 programs using **vector embeddings** and **cosine similarity**
2. **Augmentation Phase:** Retrieved programs are formatted into the **context window** along with student profile
3. **Generation Phase:** **LLM** generates personalized analysis using only the provided context (no hallucination)
4. **Post-processing:** Output is formatted with match scores, icons, and structured markdown

### Semantic Search via Vector Embeddings

- **Embedding Model:** Google Gemini text-embedding-004 produces **768-dimensional vectors**
- **Corpus Embeddings:** All 2000+ programs are pre-embedded and stored in a **vector database** (JSON)
- **Query Embedding:** Student interests are converted to vectors at runtime using **retrieval_query** task type
- **Similarity Calculation:** **Cosine similarity** computed via **normalized dot product**
- **Ranking:** Programs sorted by similarity score with **top-K retrieval**

### Grade Fit Scoring

Uses **sigmoid function** to convert grade differences into probability-based assessments:

| Grade Delta | Assessment | Interpretation |
|-------------|------------|----------------|
| ≥ +10% | Safe 🟢 | High admission probability |
| ≥ +5% | Good 🟢 | Strong chances |
| ≥ 0% | Target 🟡 | Competitive fit |
| ≥ -5% | Reach 🟠 | Aspirational choice |
| < -5% | Long Shot 🔴 | Low probability |

### LLM Integration

- **Model:** Google Gemini (gemini-2.5-flash)
- **Prompt Engineering:** Structured system prompts prevent hallucination and enforce output format
- **Retry Strategy:** **Exponential backoff** (3 attempts with 1s, 2s, 4s delays)
- **Graceful Degradation:** Demo mode with static responses when API unavailable

### Fuzzy Matching & Typo Tolerance

- **Fuzzy String Matching:** SequenceMatcher algorithm with 0.75 similarity threshold
- **Field Keywords:** 25+ academic fields mapped to related terms for **semantic expansion**
- **Typo Correction:** Common misspellings automatically corrected before search

---

## 📁 Project Structure

```
Saarthi/
├── app.py                      # Gradio application entry point with event wiring
├── api_server.py               # FastAPI REST API for programmatic access
├── config.py                   # Configuration management and path resolution
├── controllers.py              # Controller layer with validation and orchestration
├── models.py                   # Domain models (Program, StudentProfile, Session)
├── update_databse.py           # Web scraper and embedding generator
├── requirements.txt            # Python dependencies
├── index.html                  # Static landing page with glassmorphism design
├── CNAME                       # Custom domain configuration
│
├── services/                   # Business logic layer
│   ├── llm_client.py           # Gemini API wrapper with retry logic
│   ├── program_search.py       # Semantic search engine with multi-factor scoring
│   ├── roadmap.py              # RAG orchestration and output formatting
│   ├── session.py              # In-memory session management with TTL
│   ├── submissions_store.py    # SQLite persistence for submissions
│   ├── github_issues.py        # GitHub Issues API integration
│   └── email_builder.py        # Email template generation
│
├── prompts/                    # LLM prompt templates
│   └── templates.py            # System prompts and user prompt builders
│
├── ui/                         # Gradio UI components
│   ├── layout.py               # UI layout with 300+ Ontario course codes
│   └── styles.py               # Custom CSS styling
│
└── utils/                      # Utility functions
    ├── dashboard_renderer.py   # HTML generators for timeline, cards, checklist
    ├── roadmap_renderer.py     # Markdown formatting utilities
    └── validators.py           # Input sanitization and validation
```

---

## 🔧 Services & Modules

### LLM Client (`services/llm_client.py`)
- Wrapper for Google Gemini API with **exponential backoff** retry logic
- Automatic API version detection with **graceful degradation**
- Demo mode fallback when API key not configured

### Program Search (`services/program_search.py`)
- **Semantic search** engine using **vector embeddings** and **cosine similarity**
- **Multi-factor scoring** with **weighted linear combination**
- **Fuzzy matching** for typo tolerance
- **Quadratic suppression** for irrelevant results filtering

### Roadmap Service (`services/roadmap.py`)
- **RAG pipeline** orchestrator: retrieval → augmentation → generation
- **Prompt engineering** for structured LLM output
- Timeline generation anchored to OUAC deadlines

### Domain Models (`models.py`)
- **Program:** Contains **768-dim embedding vector** and metadata
- **StudentProfile:** Validated profile for **context window** injection
- **Session:** **TTL-based** session management
- **ServiceResult:** Standard response wrapper pattern

### Prompt Templates (`prompts/templates.py`)
- **System prompts** for **prompt engineering** (rules, format constraints)
- **Context assembly** templates for **RAG augmentation**
- Anti-hallucination rules (verify on link, no fabrication)

### Submissions Store (`services/submissions_store.py`)
- SQLite persistence for student submissions
- Status workflow: NEW → GENERATED → IN_REVIEW → SENT
- Audit trail for compliance

### GitHub Issues (`services/github_issues.py`)
- Issue tracking integration for email workflow
- Round-robin assignee selection
- Status label automation

---

## 🔄 Data Pipeline

### Program Database

The program database is generated by `update_databse.py`:

1. **Scraping:** Fetches all programs from OUInfo.ca using parallel requests (10 workers)
2. **Data Extraction:** Parses program name, prerequisites, admission average, and URL
3. **Embedding Generation:** Batch embeds all programs (50 per API call) using Gemini
4. **Storage:** Saves to JSON with ~2000 programs, each with 768-dimension embedding
5. **Deployment:** Uploads to Hugging Face Space for production use

### Database Schema

**submissions table:**
- Student info: name, email, grade, average, subjects (JSON), interests, location, preferences
- Generated outputs: roadmap markdown, program cards (JSON), timeline (JSON), checklist (JSON)
- Workflow: status, resume token, email fields, GitHub issue tracking

**submission_actions table:**
- Audit trail with timestamp, actor, action type, and details

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Google Gemini API key

### Local Development

1. Clone the repository
2. Create virtual environment and activate it
3. Install dependencies from requirements.txt
4. Set environment variable GEMINI_API_KEY
5. Run app.py (Gradio on port 7860) or api_server.py with uvicorn (port 8000)

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GEMINI_API_KEY` | ✅ | - | Google Gemini API key for LLM and embeddings |
| `ADMIN_PIN` | ❌ | saarthi-admin | PIN for admin panel authentication |
| `GITHUB_TOKEN` | ❌ | - | GitHub PAT for issue tracking (requires repo scope) |
| `GITHUB_OWNER` | ❌ | - | GitHub username or organization |
| `GITHUB_REPO` | ❌ | - | Repository name for issue tracking |
| `GITHUB_ASSIGNEES` | ❌ | - | Comma-separated usernames for round-robin assignment |

### Configuration Options

- **TOP_K_PROGRAMS:** Number of programs to return (default: 10)
- **SESSION_TIMEOUT_MINUTES:** Session expiry time (default: 60)
- **MAX_INTERESTS_LENGTH:** Input length limit for interests field (default: 500)
- **GEMINI_MODEL:** LLM model name (default: gemini-2.5-flash)

---

## 📡 API Endpoints

### REST API (api_server.py)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/submit | Submit student profile and generate roadmap |
| GET | /api/submission/{id} | Retrieve submission by ID with resume token |
| GET | /api/admin/submissions | List submissions in admin queue |
| GET | /api/admin/submission/{id} | Get full submission details (admin) |
| POST | /api/admin/generate_email/{id} | Auto-generate email draft |
| POST | /api/admin/update_email/{id} | Save edited email draft |
| POST | /api/admin/mark_sent/{id} | Mark email as sent |

---

## 🚀 Deployment

### Hugging Face Spaces

1. Create a new Space with Gradio SDK
2. Upload Python files, services/, prompts/, ui/, utils/, and requirements.txt
3. Upload programs.json (or generate with update_databse.py)
4. Add GEMINI_API_KEY to Space secrets
5. Optionally add ADMIN_PIN and GitHub integration secrets

### GitHub Pages (Landing Page)

1. Enable GitHub Pages in repository settings
2. Point to root directory on main branch
3. Add CNAME file for custom domain
4. Update iframe source in index.html to your HF Space URL

---

## 🔮 Future Roadmap

- [ ] **Real-time Transit API:** Integrate Google Maps API for exact commute times
- [ ] **Scholarship Database:** Create a secondary vector store for financial aid matching
- [ ] **Transcript OCR:** Upload PDF report cards for automatic grade parsing via Gemini Vision
- [ ] **Multi-Province Support:** Expand beyond Ontario to other Canadian provinces
- [ ] **Comparison Charts:** Visual charts for program comparison
- [ ] **Mobile App:** React Native mobile application

---

## 👨‍💻 Author

**Raj Shah** - [GitHub](https://github.com/RajShah3006)

---

## 📄 License

MIT License - See LICENSE for details.

---

<p align="center">
  <sub>Built with Python, Gradio, and Google Gemini for Ontario students navigating university admissions.</sub>
</p>
