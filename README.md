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

### Layer Overview

The application follows a 5-layer architecture:

1. **Presentation Layer** - Static landing page (GitHub Pages) with iframe embedding to Gradio app (Hugging Face Spaces)
2. **Application Layer** - Gradio Blocks UI with event handlers and FastAPI REST endpoints
3. **Controller Layer** - Input validation, service orchestration, and response assembly
4. **Service Layer** - Business logic including LLM client, semantic search, roadmap generation, and persistence
5. **Data Layer** - Program database with pre-computed embeddings and SQLite for submissions

### Request Flow

1. User submits profile through 4-step wizard (interests, academics, extracurriculars, review)
2. Input validation sanitizes and checks all fields
3. Semantic search engine finds top-10 matching programs using multi-factor scoring
4. RAG pipeline assembles context from matched programs + student profile
5. LLM generates personalized analysis based on retrieved facts only
6. Timeline and checklist are generated based on interest area and OUAC deadlines
7. Dashboard renders program cards, timeline, checklist, and full markdown plan

---

## 🧠 Core Algorithms

### Multi-Factor Program Scoring

The search engine combines five scoring factors with configurable weights:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Relevance** | 35% | Keyword matching and academic field alignment with penalty for irrelevant programs |
| **Embedding Similarity** | 25% | Cosine similarity between query and program embeddings (768 dimensions) |
| **Grade Fit** | 20% | Sigmoid-based probability of admission acceptance |
| **Prerequisites** | 15% | Match rate between student's courses and program requirements |
| **Location** | 5% | Geographic preference matching (GTA, regional, Ontario-wide) |

Programs with relevance below 10% are filtered out. Low-relevance programs (below 30%) receive additional quadratic suppression.

### Semantic Search via Embeddings

- **Model:** Google Gemini text-embedding-004 (768 dimensions)
- **Corpus:** 2000+ Ontario university programs with pre-computed embeddings
- **Query Processing:** Student interests and extracurriculars are embedded at runtime
- **Similarity:** Vectorized dot product against normalized embedding matrix
- **Caching:** LRU cache for query embeddings to reduce API calls

### Typo Tolerance & Fuzzy Matching

- Dictionary of 40+ common misspellings with corrections
- Fuzzy string matching using SequenceMatcher (threshold: 0.75)
- Expanded keyword dictionaries for 25+ academic fields including space, robotics, and health sciences

### Grade Scoring

- Parses admission averages from text (ranges, "below X%", "competitive", etc.)
- Sigmoid transformation converts grade delta to probability score
- Assessment labels: Safe (+10%), Good (+5%), Target (0%), Reach (-5%), Long Shot (below -5%)

### Timeline Generation

- Anchors all milestones to OUAC equal consideration deadline (January 15)
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
- Wraps Google Gemini API with automatic retry (3 attempts, exponential backoff)
- Auto-detects API version (google-genai vs google-generativeai)
- Demo mode fallback when API key is not configured

### Program Search (`services/program_search.py`)
- Main class: `ProgramSearchService`
- Loads program database and builds embedding matrix at startup
- Implements relevance scoring, grade fitting, prerequisite matching, and location preferences
- Filters and ranks programs using weighted linear combination

### Roadmap Service (`services/roadmap.py`)
- Main class: `RoadmapService`
- Orchestrates RAG pipeline: search → context assembly → LLM generation → formatting
- Builds timeline events anchored to OUAC deadline
- Generates interest-specific project checklists

### Submissions Store (`services/submissions_store.py`)
- SQLite database with auto-migration for schema changes
- Tables: submissions (profile + generated outputs), submission_actions (audit log)
- Supports email workflow with status tracking (NEW → GENERATED → IN_REVIEW → SENT)

### GitHub Issues (`services/github_issues.py`)
- Creates tracking issues for email requests (public-repo safe, no PII in issue body)
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
