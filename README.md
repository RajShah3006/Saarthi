# 🏹 Saarthi AI: Intelligent University Guidance Counselor

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/gradio-4.0+-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Saarthi** (Sanskrit: सारथी, "Charioteer") is a production-grade AI application implementing **Retrieval-Augmented Generation (RAG)** with **semantic vector search** to provide Ontario high school students with personalized university program recommendations. The system combines Google Gemini's LLM capabilities with a custom multi-factor scoring algorithm operating on 768-dimensional embedding vectors.

🔗 **Live Demo:** [saarthi.me](https://saarthi.me) | **Backend:** [Hugging Face Space](https://huggingface.co/spaces/rajshah13/saarthi)

---

## 📑 Table of Contents

- [System Architecture](#-system-architecture)
- [Core Algorithms](#-core-algorithms)
- [Project Structure](#-project-structure)
- [Module Documentation](#-module-documentation)
- [Data Pipeline](#-data-pipeline)
- [Installation & Setup](#-installation--setup)
- [Configuration Reference](#-configuration-reference)
- [REST API Specification](#-rest-api-specification)
- [Deployment Guide](#-deployment-guide)
- [Performance Considerations](#-performance-considerations)
- [Future Roadmap](#-future-roadmap)

---

## 🏗 System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  index.html (Static - GitHub Pages)     │  Gradio Blocks (HF Spaces)        │
│  ├── CSS: Glassmorphism + animations    │  ├── gr.State() session mgmt      │
│  ├── JS: Typewriter, localStorage       │  ├── 4-step wizard UI             │
│  └── iframe → HF Space embedding        │  └── Real-time event binding      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    HTTP/WebSocket (Gradio protocol)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             APPLICATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  app.py                              │  api_server.py                       │
│  ├── create_app() → gr.Blocks        │  ├── FastAPI application             │
│  ├── wire_events() → event handlers  │  ├── Pydantic request validation     │
│  ├── Admin workflow integration      │  └── RESTful CRUD endpoints          │
│  └── Startup diagnostics             │                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                           Method invocations
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CONTROLLER LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  controllers.py                                                             │
│  ├── handle_start_session() → Session creation + validation                 │
│  ├── handle_generate_roadmap() → Orchestrates RAG pipeline                  │
│  ├── handle_followup() → Contextual Q&A with session state                  │
│  └── Returns Dict[str, Any] with: md, profile, programs, timeline, projects │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                           Service delegation
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               SERVICE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  llm_client.py          │  program_search.py       │  roadmap.py            │
│  ├── Gemini API wrapper │  ├── Vector search       │  ├── RAG orchestration │
│  ├── Retry w/ backoff   │  ├── Multi-factor score  │  ├── Timeline builder  │
│  ├── API version detect │  ├── Fuzzy matching      │  ├── Project checklist │
│  └── Demo mode fallback │  └── Embedding cache     │  └── MD/HTML output    │
├─────────────────────────┼──────────────────────────┼────────────────────────┤
│  session.py             │  submissions_store.py    │  github_issues.py      │
│  ├── UUID-based IDs     │  ├── SQLite persistence  │  ├── Issue CRUD        │
│  ├── TTL management     │  ├── JSON serialization  │  ├── Label management  │
│  └── Profile caching    │  └── Action audit log    │  └── Error handling    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                            Data access
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                DATA LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  programs.json / university_data_cached.json                                │
│  ├── ~2000+ Program objects with schema:                                    │
│  │   { program_name, program_url, prerequisites, admission_average,         │
│  │     university_name, location, embedding[768] }                          │
│  └── Pre-computed embeddings via text-embedding-004                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  data/submissions.db (SQLite3)                                              │
│  ├── submissions table: student data, roadmap_md, ui_*_json blobs           │
│  ├── submission_actions table: audit trail with actor, action, timestamp    │
│  └── Indexes: idx_status, idx_token, idx_wants_email                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow Diagram

```
User Input (interests, grade, subjects)
         │
         ▼
┌─────────────────────────────┐
│   Input Validation          │  validators.py: sanitize_text(), validate_profile_inputs()
│   - Length limits           │
│   - XSS prevention          │
│   - Type coercion           │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Semantic Search           │  program_search.py: search_with_profile()
│   1. Typo correction        │  _correct_typos() → TYPO_CORRECTIONS dict
│   2. Field detection        │  _detect_user_fields() → FIELD_KEYWORDS mapping
│   3. Query embedding        │  _get_query_embedding() → Gemini API
│   4. Cosine similarity      │  np.dot(query_emb, program_matrix)
│   5. Multi-factor scoring   │  _calculate_final_score()
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   RAG Context Assembly      │  roadmap.py: generate()
│   - Top-K programs (k=10)   │
│   - Student profile string  │
│   - Prompt template         │  prompts/templates.py
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   LLM Generation            │  llm_client.py: generate()
│   - Model: gemini-2.5-flash │
│   - Retry: 3x exponential   │
│   - Timeout: configurable   │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   Response Assembly         │  roadmap.py: _format_full_plan_ai()
│   - Timeline events         │  _build_timeline() → OUAC deadline anchor
│   - Project checklist       │  _build_projects() → interest-specific
│   - Program cards           │  _program_to_payload()
│   - Full markdown plan      │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   UI Rendering              │  utils/dashboard_renderer.py
│   - render_timeline()       │  HTML with .t-item, .t-card classes
│   - render_program_cards()  │  .prog-card grid layout
│   - render_checklist()      │  Interactive checkboxes
└─────────────────────────────┘
```

---

## 🧠 Core Algorithms

### 1. Multi-Factor Program Scoring (`services/program_search.py`)

The scoring engine implements a weighted linear combination with non-linear transformations:

```python
# Final score calculation (lines 1436-1524)
final_score = (
    w_relevance * relevance_score +      # 35% - keyword/field alignment
    w_embedding * embedding_score +       # 25% - cosine similarity
    w_grade * grade_score +               # 20% - sigmoid admission fit
    w_prereq * prereq_score +             # 15% - course requirement match
    w_location * location_score           # 5%  - geographic preference
)

# Double penalty for low relevance (filters irrelevant programs)
if relevance_score < 0.3:
    final_score *= relevance_score  # Quadratic suppression
```

#### Relevance Score Algorithm

```python
def _calculate_relevance_score(program, interests, user_fields, is_stem):
    score = 0.0
    
    # Direct keyword match in program name: +1.0
    for keyword in FIELD_KEYWORDS[field]:
        if keyword in program.program_name.lower():
            score += 1.0
            break
    
    # Fuzzy match (SequenceMatcher > 0.7): +0.7
    # Prerequisite mention: +0.3
    
    # STEM irrelevance penalty (Sport Management for robotics): ×0.05
    if is_stem and program in IRRELEVANT_FOR_STEM:
        score *= 0.05
    
    return min(1.0, score / max_score)
```

#### Grade Fit Scoring (Sigmoid-based)

```python
def _calculate_grade_score(student_avg, program):
    program_avg = _parse_admission_average(program.admission_average)
    delta = student_avg - program_avg
    
    # Sigmoid transformation: S(x) = 1 / (1 + e^(-kx)), k=0.25
    score = 1.0 / (1.0 + math.exp(-0.25 * delta))
    
    # Assessment labels based on delta:
    # delta >= 10: "Safe"    | delta >= 5: "Good"
    # delta >= 0:  "Target"  | delta >= -5: "Reach"
    # delta < -5:  "Long Shot"
    
    return score, assessment
```

### 2. Semantic Embedding Pipeline

```python
# Embedding generation (update_databse.py lines 53-63)
def get_batch_embeddings(text_list):
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text_list,
        task_type="retrieval_document"  # Optimized for corpus
    )
    return result['embedding']  # List[List[float]] - 768 dims each

# Query-time embedding (program_search.py lines 1366-1407)
def _get_query_embedding(query):
    response = genai.embed_content(
        model="models/text-embedding-004",
        content=query[:2000],
        task_type="retrieval_query"  # Optimized for queries
    )
    embedding = np.array(response["embedding"], dtype=np.float32)
    return embedding / np.linalg.norm(embedding)  # L2 normalize

# Vectorized similarity (program_search.py lines 1409-1432)
def _calculate_embedding_scores(query):
    query_emb = _get_query_embedding(query)
    # Pre-normalized matrix multiplication
    scores = np.dot(self.embedding_matrix, query_emb)  # O(n×d)
    return np.maximum(scores, 0) / scores.max()  # Normalize to [0,1]
```

### 3. Typo Correction & Fuzzy Matching

```python
# Typo correction dictionary (program_search.py lines 711-749)
TYPO_CORRECTIONS = {
    "enginering": "engineering",
    "computor": "computer",
    "robtics": "robotics",
    "aersospace": "aerospace",
    # ... 40+ common misspellings
}

# Fuzzy matching using SequenceMatcher (lines 856-888)
def _fuzzy_match(word, target):
    return SequenceMatcher(None, word.lower(), target.lower()).ratio()

def _find_best_field_match(word):
    for field, keywords in FIELD_KEYWORDS.items():
        for keyword in keywords:
            if _fuzzy_match(word, keyword) >= 0.75:  # Threshold
                return field, confidence
    return None, 0.0
```

### 4. LLM Client with Retry Logic

```python
# Exponential backoff decorator (llm_client.py lines 12-30)
def retry_with_backoff(max_retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

# API version detection (lines 49-78)
def _initialize_client(self):
    try:
        from google import genai  # New API (google-genai)
        self.client = genai.Client(api_key=self.config.GEMINI_API_KEY)
        self.use_new_api = True
    except ImportError:
        import google.generativeai as genai  # Legacy API
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        self.use_new_api = False
```

---

## 📁 Project Structure

```
Saarthi/
├── app.py                      # Gradio application (1056 lines)
│                               # - create_app(): gr.Blocks factory
│                               # - wire_events(): 800+ lines of event handlers
│                               # - Admin workflow with GitHub sync
│
├── api_server.py               # FastAPI REST API (148 lines)
│                               # - Pydantic models: SubmitRequest, SubmitResponse
│                               # - CRUD endpoints for submissions
│                               # - Admin endpoints with auth bypass
│
├── config.py                   # Configuration dataclass (79 lines)
│                               # - Environment variable loading
│                               # - Path resolution for programs.json
│                               # - Startup diagnostics logging
│
├── controllers.py              # Controller layer (276 lines)
│                               # - Input validation orchestration
│                               # - Service method delegation
│                               # - Response DTO assembly
│
├── models.py                   # Domain models (174 lines)
│                               # - Program: with embedding[768] field
│                               # - StudentProfile: validated student data
│                               # - Session: UUID + TTL + cached state
│                               # - ServiceResult: ok/fail pattern
│
├── update_databse.py           # Data pipeline script (141 lines)
│                               # - OUInfo.ca web scraper
│                               # - ThreadPoolExecutor (10 workers)
│                               # - Batch embedding generation
│                               # - HuggingFace upload
│
├── requirements.txt            # Dependencies (10 packages)
│
├── index.html                  # Landing page (845 lines)
│                               # - CSS: glassmorphism, animations
│                               # - JS: typewriter, preloader
│
├── services/                   # Business logic layer
│   ├── llm_client.py           # Gemini client (174 lines)
│   │                           # - Retry decorator with backoff
│   │                           # - API version auto-detection
│   │                           # - Demo mode fallback responses
│   │
│   ├── program_search.py       # Search engine (1720 lines)
│   │                           # - ProgramSearchService class
│   │                           # - Multi-factor scoring algorithm
│   │                           # - Embedding matrix operations
│   │                           # - Typo correction + fuzzy matching
│   │
│   ├── roadmap.py              # RAG service (585 lines)
│   │                           # - RoadmapService class
│   │                           # - Timeline builder (OUAC anchored)
│   │                           # - Project checklist generator
│   │                           # - LLM prompt formatting
│   │
│   ├── session.py              # Session management
│   │                           # - SessionManager: dict-based store
│   │                           # - TTL enforcement
│   │                           # - Profile caching
│   │
│   ├── submissions_store.py    # SQLite persistence (744 lines)
│   │                           # - Schema with auto-migration
│   │                           # - JSON blob serialization
│   │                           # - Admin queue management
│   │                           # - Action audit logging
│   │
│   ├── github_issues.py        # GitHub API client (418 lines)
│   │                           # - GitHubIssuesClient class
│   │                           # - Issue CRUD with httpx
│   │                           # - Error categorization enum
│   │                           # - Diagnostics function
│   │
│   └── email_builder.py        # Email template generation
│
├── prompts/
│   └── templates.py            # LLM prompts (70 lines)
│                               # - roadmap_system_prompt()
│                               # - roadmap_prompt(profile, programs)
│                               # - followup_system_prompt()
│
├── ui/
│   ├── layout.py               # Gradio layout (354 lines)
│   │                           # - COURSES: 300+ Ontario course codes
│   │                           # - INTEREST_AREAS: 12 categories
│   │                           # - create_ui_layout() → component dict
│   │
│   └── styles.py               # CSS styling
│
└── utils/
    ├── dashboard_renderer.py   # HTML generators (138 lines)
    │                           # - render_program_cards()
    │                           # - render_checklist()
    │                           # - render_timeline()
    │
    ├── roadmap_renderer.py     # Markdown utilities
    │
    └── validators.py           # Input validation
                                # - sanitize_text(): XSS prevention
                                # - validate_profile_inputs()
```

---

## 📖 Module Documentation

### `services/program_search.py` - Semantic Search Engine

**Class:** `ProgramSearchService`

| Method | Signature | Description |
|--------|-----------|-------------|
| `search_with_profile` | `(profile: StudentProfile, top_k: int) → List[Tuple[Program, float, Dict]]` | Main search entry point. Returns top-K programs with scores and breakdowns. |
| `_detect_user_fields` | `(interests: str) → Tuple[List[str], bool, str]` | Extracts academic fields from free-text interests. Returns (fields, is_stem, corrected_text). |
| `_calculate_relevance_score` | `(program, interests, user_fields, is_stem) → Tuple[float, List, List]` | Computes keyword alignment score with penalty/bonus tracking. |
| `_calculate_grade_score` | `(student_avg: float, program: Program) → Tuple[float, str]` | Sigmoid-based admission probability with assessment label. |
| `_calculate_embedding_scores` | `(query: str) → np.ndarray` | Batch cosine similarity against all program embeddings. |
| `_get_query_embedding` | `(query: str) → Optional[np.ndarray]` | Generates normalized embedding with LRU cache. |

**Configuration Constants:**

```python
MIN_RELEVANCE_THRESHOLD = 0.1      # Filter threshold
FUZZY_MATCH_THRESHOLD = 0.75       # SequenceMatcher cutoff
FIELD_KEYWORDS: Dict[str, List[str]]  # 25+ field → keyword mappings
TYPO_CORRECTIONS: Dict[str, str]      # 40+ common misspellings
```

### `services/roadmap.py` - RAG Orchestration

**Class:** `RoadmapService`

| Method | Signature | Description |
|--------|-----------|-------------|
| `generate` | `(profile: StudentProfile, session: Session) → ServiceResult` | Full RAG pipeline: search → context → LLM → format. |
| `_build_timeline` | `(profile) → List[Dict]` | Generates date-anchored milestones to OUAC deadline. |
| `_build_projects` | `(profile) → List[Dict]` | Interest-specific checklist (robotics, CS, health, etc.). |
| `_format_full_plan_ai` | `(profile, programs, analysis, timeline, projects) → str` | LLM-polished markdown with template constraints. |
| `followup` | `(question: str, session: Session) → ServiceResult` | Contextual Q&A using session's cached profile. |

### `services/submissions_store.py` - Persistence Layer

**Class:** `SubmissionStore`

**Schema:**

```sql
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,           -- ISO8601
    updated_at TEXT NOT NULL,
    student_name TEXT NOT NULL,
    student_email TEXT,
    wants_email INTEGER DEFAULT 0,      -- Boolean
    grade TEXT NOT NULL,
    average REAL NOT NULL,
    subjects_json TEXT NOT NULL,        -- JSON array
    interests TEXT NOT NULL,
    extracurriculars TEXT,
    location TEXT,
    preferences TEXT,
    status TEXT DEFAULT 'NEW',          -- NEW|GENERATED|IN_REVIEW|SENT
    resume_token TEXT NOT NULL,         -- secrets.token_urlsafe(16)
    roadmap_md TEXT,                    -- Generated markdown
    ui_programs_json TEXT,              -- JSON array of program cards
    ui_timeline_json TEXT,              -- JSON array of timeline events
    ui_projects_json TEXT,              -- JSON array of checklist items
    email_subject TEXT,
    email_body_text TEXT,
    github_issue_number INTEGER,
    github_issue_url TEXT,
    github_status TEXT
);

CREATE TABLE submission_actions (
    id INTEGER PRIMARY KEY,
    submission_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,               -- SUBMITTED|GENERATED|SAVED_EMAIL|MARKED_SENT
    details TEXT
);
```

---

## 🔄 Data Pipeline

### Web Scraping (`update_databse.py`)

```python
# Concurrent scraping with ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(process_program, p): p for p in programs}
    for future in concurrent.futures.as_completed(futures):
        scraped_results.append(future.result())

# Batch embedding generation (50 items per API call)
for i in range(0, len(texts), 50):
    batch = texts[i:i+50]
    embeddings = genai.embed_content(
        model="models/text-embedding-004",
        content=batch,
        task_type="retrieval_document"
    )['embedding']
    all_vectors.extend(embeddings)
    time.sleep(1)  # Rate limiting
```

### Data Format (`programs.json`)

```json
[
  {
    "program_name": "Computer Science (Co-op)",
    "program_url": "https://ouinfo.ca/programs/waterloo/computer-science",
    "prerequisites": "MCV4U, MHF4U, ENG4U",
    "admission_average": "90-95%",
    "university_name": "University of Waterloo",
    "location": "Waterloo, ON",
    "embedding": [0.0234, -0.0891, 0.0456, ...]  // 768 floats
  }
]
```

---

## 📦 Installation & Setup

### Prerequisites

- Python 3.10+ (tested on 3.11)
- 4GB RAM minimum (embedding matrix: ~50MB for 2000 programs)
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Local Development

```bash
# Clone and setup
git clone https://github.com/RajShah3006/Saarthi.git
cd Saarthi
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Required environment variables
export GEMINI_API_KEY="your-api-key"

# Optional configuration
export ADMIN_PIN="custom-pin"           # Default: saarthi-admin
export GITHUB_TOKEN="ghp_..."           # For issue tracking
export GITHUB_OWNER="username"
export GITHUB_REPO="repo-name"

# Run Gradio app (port 7860)
python app.py

# OR run FastAPI server (port 8000)
pip install uvicorn
uvicorn api_server:app --reload --port 8000
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["python", "app.py"]
```

---

## ⚙️ Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GEMINI_API_KEY` | ✅ | - | Google Gemini API key for LLM (`gemini-2.5-flash`) and embeddings (`text-embedding-004`) |
| `ADMIN_PIN` | ❌ | `saarthi-admin` | PIN for admin panel authentication |
| `GITHUB_TOKEN` | ❌ | - | GitHub Personal Access Token (requires `repo` or `public_repo` scope) |
| `GITHUB_OWNER` | ❌ | - | GitHub username or organization |
| `GITHUB_REPO` | ❌ | - | Repository name for issue tracking |
| `GITHUB_ASSIGNEES` | ❌ | - | Comma-separated usernames for round-robin assignment |
| `GITHUB_API_BASE` | ❌ | `https://api.github.com` | GitHub API base URL (for GitHub Enterprise) |
| `PUBLIC_STATUS_URL` | ❌ | - | Public URL displayed in GitHub issues |

### Config Class Properties

```python
@dataclass
class Config:
    GEMINI_API_KEY: str               # From env
    GEMINI_MODEL: str = "gemini-2.5-flash"
    PROGRAMS_FILE: Path               # Auto-detected
    DATA_DIR: Path                    # Parent of PROGRAMS_FILE
    
    # Limits
    TOP_K_PROGRAMS: int = 10
    MAX_INTERESTS_LENGTH: int = 500
    MAX_LOCATION_LENGTH: int = 100
    MAX_FOLLOWUP_LENGTH: int = 1000
    SESSION_TIMEOUT_MINUTES: int = 60
    
    # UI theming
    THEME_PRIMARY: str = "#3b82f6"
    THEME_SECONDARY: str = "#8b5cf6"
    
    # Grade options
    GRADE_OPTIONS: List[str] = [
        "Grade 9", "Grade 10", "Grade 11",
        "Grade 12", "Gap Year", "University Transfer"
    ]
```

---

## 📡 REST API Specification

### Base URL
- Local: `http://localhost:8000`
- Production: Deployed on Hugging Face Spaces

### Endpoints

#### `POST /api/submit`

Submit student profile and generate roadmap.

**Request Body:**
```typescript
interface SubmitRequest {
  student_name: string;
  student_email?: string;        // EmailStr validation
  wants_email: boolean;          // Default: false
  grade: string;                 // e.g., "Grade 12"
  average: number;               // 0-100
  subjects: string[];            // Ontario course codes
  interests: string;
  extracurriculars?: string;
  location?: string;
  preferences?: string;
}
```

**Response:**
```typescript
interface SubmitResponse {
  id: number;
  resume_token: string;          // 22-char URL-safe token
  status: "GENERATED";
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Alex",
    "grade": "Grade 12",
    "average": 92,
    "subjects": ["Advanced Functions (MHF4U)", "Calculus & Vectors (MCV4U)"],
    "interests": "Computer Science, AI, Robotics"
  }'
```

#### `GET /api/submission/{id}?token={token}`

Retrieve submission by ID with resume token authentication.

#### `GET /api/admin/submissions`

List submissions in admin queue.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | string | `null` | Filter by status: `NEW`, `GENERATED`, `IN_REVIEW`, `SENT` |
| `limit` | int | `50` | Maximum results (1-200) |

#### `POST /api/admin/generate_email/{id}`

Auto-generate email draft from submission data.

---

## 🚀 Deployment Guide

### Hugging Face Spaces

1. Create Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select SDK: **Gradio**
3. Upload files:
   ```
   app.py, config.py, controllers.py, models.py, requirements.txt
   services/, prompts/, ui/, utils/
   programs.json (or university_data_cached.json)
   ```
4. Configure Secrets (Settings → Repository Secrets):
   - `GEMINI_API_KEY` (required)
   - `ADMIN_PIN` (optional)
   - `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO` (optional)

### GitHub Pages (Landing Page)

1. Repository Settings → Pages → Source: Deploy from branch
2. Select branch: `main`, folder: `/ (root)`
3. Custom domain: Add CNAME file with domain name
4. Update `index.html` line 778:
   ```html
   <iframe src="https://YOUR-USERNAME-YOUR-SPACE.hf.space"></iframe>
   ```

### Database Refresh

```bash
# Set credentials
export GOOGLE_API_KEY="your-gemini-key"  # Used by update_databse.py
export HF_TOKEN="your-huggingface-token"

# Run pipeline (scrape → embed → upload)
python update_databse.py

# Output:
# 🚀 Starting Database Update...
# Scanning Group: A... Found 150 programs
# ...
# ✅ SUCCESS! New database saved with 2000 programs.
# 🚀 Uploading database to Hugging Face...
# ✅ Upload Complete!
```

---

## ⚡ Performance Considerations

### Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Embedding matrix | ~50MB | 2000 programs × 768 dims × 4 bytes |
| SQLite DB | ~10MB | Depends on submission volume |
| Gradio state | ~5MB | Per-session profile caching |

### Latency Breakdown

| Operation | Time | Optimization |
|-----------|------|--------------|
| Query embedding | ~200ms | LRU cache (`_embedding_cache`) |
| Cosine similarity | ~5ms | Vectorized NumPy, pre-normalized |
| LLM generation | ~2-5s | Retry with backoff |
| Total roadmap | ~3-6s | Dominated by LLM latency |

### Scaling Considerations

- **Embedding cache**: Limited to ~1000 entries (memory bound)
- **Session store**: In-memory dict, not horizontally scalable
- **SQLite**: Single-writer limitation, suitable for ~100 concurrent users
- **Rate limiting**: Gemini API quota (varies by tier)

---

## 🔮 Future Roadmap

| Priority | Feature | Technical Approach |
|----------|---------|-------------------|
| High | Real-time transit | Google Maps Distance Matrix API integration |
| High | Scholarship matching | Secondary vector store with financial aid data |
| Medium | Transcript OCR | Gemini Vision API for PDF parsing |
| Medium | Multi-province support | Extended scraper for BC, Alberta, Quebec |
| Low | Mobile app | React Native with REST API backend |
| Low | Comparison charts | Chart.js/Plotly visualizations |

---

## 👨‍💻 Author

**Raj Shah** - [GitHub](https://github.com/RajShah3006)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with Python, Gradio, and Google Gemini for Ontario students navigating university admissions.</sub>
</p>
