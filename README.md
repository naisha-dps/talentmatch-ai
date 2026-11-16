# 🎯 TalentMatch AI

An **AI-powered recruitment platform** that helps both candidates and recruiters using
**Llama 3.3 70B** (via Groq API), **LangChain**, **LangGraph**, and **Streamlit**.

Built as an internship-worthy project by a Computer Science student.

Every user creates an account and logs in through a role-based authentication system
(Candidate or Recruiter, SQLite-backed, hashed passwords) before entering the platform.

---

## 📸 Features

### 🔐 Authentication
| Feature | Description |
|---|---|
| Sign Up / Login | Email + password accounts stored in a local SQLite database |
| Role Selection | Every account is either a Candidate or a Recruiter |
| Role-Based Access | Candidates only see the Candidate Portal; Recruiters only see the Recruiter Portal |
| Password Hashing | PBKDF2-HMAC-SHA256 with a per-user salt (Python stdlib `hashlib`/`secrets`) |
| Session Persistence | Login state held in Streamlit session state for the duration of the browser session |

### 👤 Candidate Portal
| Feature | Description |
|---|---|
| 📎 Resume Upload | Upload PDF resume and extract text automatically |
| 🔍 Resume Analyzer | Get strengths, weaknesses, missing sections, ATS score |
| ❓ Interview Prep | Auto-generate technical, HR & behavioral questions |
| 🎤 Voice Interview | Live adaptive multi-turn voice interview with scored feedback |
| 🗺️ Career Guidance | Skills to learn, certifications, projects, roadmap |
| ✍️ Resume Generation | AI-tailored resume rewrite for a target role/job description |

### 💼 Recruiter Portal
| Feature | Description |
|---|---|
| 📎 Batch Resume Upload | Upload multiple candidate PDF resumes at once |
| 📋 Job Description Matching | Paste job description text to score every candidate against it |
| 🎯 Resume Ranking | AI-generated % match with explanation, per candidate |
| 🏆 Candidate Leaderboard | Sortable, filterable leaderboard with a live score threshold |

---

## 🏗️ Architecture

```
talentmatch-ai/
│
├── app.py                    # Thin entry point: config, auth gate, role-based routing
├── requirements.txt          # Python dependencies
├── .env                      # API keys (never commit this!)
├── README.md
│
├── auth/                      # Authentication logic (no UI, no DB access to SQL directly)
│   ├── security.py            # Password hashing (PBKDF2-HMAC-SHA256, stdlib only)
│   ├── validators.py          # Signup/login input validation
│   ├── service.py              # register_user / authenticate_user orchestration
│   └── session.py              # Streamlit session_state login/logout/current user
│
├── database/                  # SQLite persistence layer
│   ├── db.py                   # Connection + schema bootstrap
│   └── user_repository.py     # users table CRUD
│
├── models/                    # Domain models
│   └── user.py                 # User dataclass
│
├── ui/                         # Streamlit rendering layer
│   ├── styles.py                # Global CSS design system (dark theme + glassmorphism)
│   ├── landing.py                # Landing page + Sign Up / Login auth card
│   ├── sidebar.py                 # Authenticated sidebar (identity + logout)
│   ├── candidate_portal.py        # Candidate workspace (moved from app.py, logic unchanged)
│   ├── recruiter_portal.py        # Recruiter workspace (moved from app.py, logic unchanged)
│   └── workspace_helpers.py       # Shared helpers used by both portals
│
├── agents/                   # LangChain AI agents
│   ├── candidate_agents.py   # Resume analyzer, interview gen, mock, career
│   └── recruiter_agents.py   # Matcher, skill gap, hiring recommendation
│
├── graph/                    # LangGraph workflow orchestration
│   ├── candidate_graph.py    # 5-node candidate pipeline
│   └── recruiter_graph.py    # 5-node recruiter pipeline
│
├── prompts/                  # All LLM prompt templates
│   ├── candidate_prompts.py  # Prompts for candidate agents
│   └── recruiter_prompts.py  # Prompts for recruiter agents
│
├── utils/                    # Utility modules
│   ├── pdf_parser.py         # pypdf-based PDF text extraction
│   ├── llm_config.py         # Groq LLM configuration
│   └── voice_utils.py        # Groq Whisper transcription + Edge TTS speech synthesis
│
├── data/                      # SQLite database (talentmatch.db, gitignored) + uploads
└── assets/                   # (Optional) Images, icons
```

### LangGraph Flows

**Candidate Flow:**
```
Resume Upload → Resume Analyzer → Interview Generator → Mock Evaluator → Career Guidance
```

**Recruiter Flow:**
```
Resume Upload → Job Description → Candidate Matcher → Skill Gap → Hiring Recommendation
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Llama 3.3 70B Versatile (Groq — Free) |
| **LLM Framework** | LangChain |
| **Workflow** | LangGraph |
| **Frontend** | Streamlit |
| **PDF Parsing** | pypdf |
| **Config** | python-dotenv |
| **Language** | Python 3.10+ |

---

## 🚀 Setup & Installation

### 1. Clone or Download the Project
```bash
git clone https://github.com/yourusername/talentmatch-ai.git
cd talentmatch-ai
```

### 2. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Get Your FREE Groq API Key
1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key

### 5. Configure Environment Variables
Open the `.env` file and replace the placeholder:
```env
GROQ_API_KEY=gsk_your_actual_key_here
```

### 6. Run the App
```bash
streamlit run app.py
```

The app will open at **http://localhost:8501** 🎉

---

## 💡 Usage Guide

### First Time: Create an Account
1. Open the app — you'll land on the TalentMatch AI landing page
2. On the auth card, stay on the **Sign Up** tab
3. Choose your role — **Candidate** or **Recruiter**
4. Enter your Full Name, Email, Password, and Confirm Password, then submit
5. You'll be redirected to the **Login** tab with a success message

### Candidate Portal (Candidate accounts only)
1. Log in — you're taken straight to the Candidate workspace
2. Upload your **PDF resume**
3. Run **Resume Analysis** for a full ATS-style report
4. Generate **Interview Preparation** questions
5. Try the **Voice Interview** — a live, adaptive multi-turn spoken interview
6. Generate a **Career Roadmap**
7. Generate an AI-tailored, **Resume-Optimized** rewrite

### Recruiter Portal (Recruiter accounts only)
1. Log in — you're taken straight to the Recruiter workspace
2. Upload **multiple candidate PDF resumes** (batch processing)
3. Paste the **job description** to match against
4. Click **"Execute Batch Talent Assessment Process"**
5. Review the ranked **Candidate Leaderboard** and per-candidate diagnostic reports

Logout is available at any time from the sidebar.

---

## 🔒 Security Notes

- ✅ API key stored in `.env` (never hardcoded)
- ✅ `.env` is listed in `.gitignore`
- ✅ Passwords are never stored in plaintext — PBKDF2-HMAC-SHA256 with a per-user salt
- ✅ The local SQLite database (`data/talentmatch.db`) is gitignored, never committed
- ✅ Resume/report data stays in-memory for the session; only account records persist

---

## 🔮 Future Enhancements

1. **Multi-Resume Comparison** — Compare multiple candidates for one JD
2. **ATS Score Optimizer** — Automatically rewrite resume for ATS
3. **Interview Video Analysis** — Analyze tone, filler words via audio
4. **Job Board Integration** — Scrape LinkedIn/Indeed job postings
5. **Email Report Export** — Send PDF hiring reports via email
6. **Password Reset** — Self-service "forgot password" flow
7. **Candidate Profile History** — Persist past reports per account, not just per session
8. **Batch Processing at Scale** — Screen hundreds of resumes at once
9. **Multilingual Support** — Support resumes in multiple languages

---

## 🙋 Built By

A first-year CS student learning AI engineering.
Powered by open-source tools — no paid APIs required!

---

## 📄 License

MIT License — free to use, modify, and distribute.
