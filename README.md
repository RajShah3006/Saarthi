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

## 🧠 Core Algorithms

### Multi-Factor Program Scoring

The `ProgramSearchService` class implements a **weighted linear combination** scoring system:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Relevance Score** | 35% | `_calculate_relevance_score()` - Keyword matching against `FIELD_KEYWORDS` dictionary with **quadratic suppression** for irrelevant programs |
| **Embedding Similarity** | 25% | `_calculate_embedding_scores()` - Cosine similarity via **normalized dot product** against embedding matrix |
| **Grade Fit** | 20% | `_calculate_grade_score()` - **Sigmoid transformation** (`_sigmoid()` with k=0.25) of grade delta |
| **Prerequisites** | 15% | `_calculate_prerequisite_score()` - Course pattern matching for Ontario curriculum codes (MCV4U, MHF4U, etc.) |
| **Location** | 5% | `_calculate_location_score()` - GTA region detection and Ontario-wide matching |

**Key Technical Terms:**
- **FIELD_KEYWORDS**: Dictionary mapping 25+ academic fields (robotics, AI, business, medicine, etc.) to related keywords
- **GARBAGE_STRINGS**: List of common scraping artifacts removed via `_clean_prerequisites()`
- **Quadratic Suppression**: Programs with relevance < 30% receive `score *= relevance` penalty
- **Competitive Bonus**: Programs marked competitive where student qualifies get `score * 1.1`

### Semantic Search via Embeddings

The system uses **retrieval_query** task type for query embedding and **retrieval_document** for corpus:

- **Model:** `models/text-embedding-004` (Google Gemini)
- **Embedding Matrix:** NumPy array of shape `(num_programs, 768)` built at startup
- **Normalization:** Query and program vectors normalized to unit length before dot product
- **Similarity Formula:** `max(0, dot(query_norm, prog_norm))` with final normalization

### Grade Scoring Algorithm

The `_parse_admission_average()` method handles various admission formats:

| Input Pattern | Parsing Logic |
|--------------|---------------|
| "Below 75%" / "Under 75%" | Extract number, subtract 5 (easy admission) |
| "85-90%" (range) | Calculate average of low and high |
| "85%" (single) | Direct extraction |
| "Competitive" / "High" | Default to 90% |
| "Mid 80s" / "Low 80s" | Mapped to 85% / 80% |

**Assessment Labels:**
| Grade Delta | Assessment |
|-------------|------------|
| ≥ +10% | Safe 🟢 |
| ≥ +5% | Good 🟢 |
| ≥ 0% | Target 🟡 |
| ≥ -5% | Reach 🟠 |
| < -5% | Long Shot 🔴 |

### Typo Tolerance & Field Detection

- **FIELD_KEYWORDS Dictionary:** Maps fields like "robotics" → ["robotics", "mechatronics", "automation", "mechanical", "electrical", "control", "embedded"]
- **Fuzzy Matching:** SequenceMatcher with 0.75 threshold
- **Interest Word Bonus:** Direct matches of interest words in program name add +0.5 to score

### RAG Pipeline (Retrieval-Augmented Generation)

The `RoadmapService` orchestrates the RAG pipeline:

1. **Retrieval:** `search_with_profile()` returns top-K programs with breakdown dictionaries
2. **Context Assembly:** `PromptTemplates.roadmap_prompt()` formats profile + programs
3. **System Prompt:** `roadmap_system_prompt()` sets rules (no fabrication, verify on link, etc.)
4. **Generation:** `LLMClient.generate()` with `@retry_with_backoff` decorator (3 attempts, exponential delay)
5. **Formatting:** `_format_output()` generates styled markdown with match icons

### LLM Client Architecture

The `LLMClient` class implements **graceful degradation**:

- **API Detection:** Tries `google-genai` (new API) first, falls back to `google-generativeai` (legacy)
- **Retry Logic:** `@retry_with_backoff(max_retries=3, base_delay=1.0)` decorator with exponential backoff
- **Demo Mode:** Static responses when `GEMINI_API_KEY` not configured

### Timeline Generation

- Anchors all milestones to **OUAC equal consideration deadline** (January 15)
- Generates date-specific action items working backwards from deadline
- Interest-specific project checklists (robotics portfolio, CS app, research brief)

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
- **Class:** `LLMClient` with `@retry_with_backoff` decorator
- **API Detection:** Auto-detects `google-genai` vs `google-generativeai`
- **Retry Logic:** Exponential backoff (base_delay=1.0, max_retries=3)
- **Fallback:** `_demo_response()` provides static responses in demo mode

### Program Search (`services/program_search.py`)
- **Class:** `ProgramSearchService`
- **Data Structures:**
  - `FIELD_KEYWORDS`: Dict mapping 25+ fields to keyword lists
  - `GARBAGE_STRINGS`: List of scraping artifacts to remove
  - `embedding_matrix`: NumPy array shape `(n_programs, 768)`
- **Key Methods:**
  - `_calculate_relevance_score()`: Keyword matching with field detection
  - `_calculate_grade_score()`: Sigmoid transformation + assessment labels
  - `_calculate_prerequisite_score()`: Ontario course pattern matching
  - `_calculate_embedding_scores()`: Vectorized cosine similarity
  - `_calculate_final_score()`: Weighted combination with filtering

### Roadmap Service (`services/roadmap.py`)
- **Class:** `RoadmapService`
- **Orchestration:** search → context assembly → LLM generation → formatting
- **Output Format:** Styled markdown with match icons (🌟, ✅, 🔶, ⚪)
- **Timeline:** OUAC-anchored milestones with date-specific actions

### Domain Models (`models.py`)
- **Program:** Dataclass with `embedding: List[float]`, `search_text`, `co_op_available`
- **StudentProfile:** Validated profile with `to_context_string()` for prompts
- **Session:** UUID-based with TTL validation via `is_valid(timeout_minutes)`
- **ServiceResult:** Result wrapper with `ok`, `message`, `data`, `error_id`

### Prompt Templates (`prompts/templates.py`)
- **Class:** `PromptTemplates`
- **System Prompts:** `roadmap_system_prompt()`, `followup_system_prompt()`
- **Rules:** No fabrication, verify on link, 6-12 bullets max
- **Formatting:** `_format_programs()` for RAG context injection

### Submissions Store (`services/submissions_store.py`)
- SQLite database with auto-migration for schema changes
- Tables: `submissions` (profile + outputs), `submission_actions` (audit log)
- Status workflow: NEW → GENERATED → IN_REVIEW → SENT

### GitHub Issues (`services/github_issues.py`)
- Creates tracking issues for email requests (public-repo safe, no PII)
- Round-robin assignee selection
- Status label management and issue closing

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
