# Resume Analyzer

An AI-powered resume analyzer that compares resumes with job descriptions, identifies skill gaps, and suggests improvements with user approval.

Built with **LangGraph, FastAPI, React, and TypeScript**.

## What It Does

- **Resume Analysis:** Extracts skills, experience, projects, and education.
- **Job Matching:** Compares the resume against individual job requirements.
- **Match Scoring:** Calculates a weighted score using deterministic Python logic.
- **Gap Detection:** Identifies missing required and preferred qualifications.
- **Human Review:** Lets users correct AI-generated assessments.
- **AI Suggestions:** Recommends improvements based on the job description.
- **Resume Editing:** Users accept, edit, or reject proposed changes.
- **Export:** Preview and download the tailored resume as a TXT file.

## Tech Stack

| Frontend | Backend | AI |
|---|---|---|
| React | Python | LangGraph |
| TypeScript | FastAPI | LangChain |
| Tailwind CSS | Pydantic | Groq API |
| Vite | | |

## How It Works

```text
Resume + Job Description
          |
          v
   Structured Extraction
          |
          v
   Requirement Matching
          |
          v
   Evidence Verification
          |
          v
   Deterministic Scoring
          |
          v
      Human Review
          |
          v
    AI Suggestions
          |
          v
   Proposed Resume Edits
          |
          v
   Accept / Edit / Reject
          |
          v
      Tailored Resume
```

AI handles extraction, matching, and suggestions. Python handles scoring and applies only user-approved edits.

## Getting Started

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

**2. Set up the backend**

Requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r resume_analyzer/requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_api_key
```

Start the API:

```bash
python -m uvicorn resume_analyzer.api:app --reload
```

**3. Set up the frontend**

Requires Node.js and npm.

```bash
cd resume-analyzer-frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

## Testing

Backend tests are located in `resume_analyzer/tests/`.

Example:

```bash
python -m resume_analyzer.tests.evaluate --all
```

The project includes tests for requirement matching, scoring, human review, and resume-edit application.

## Current Status

**Working MVP:** Resume analysis, scoring, human review, AI suggestions, edit approval, and TXT export.

**Planned:** PDF/DOCX support, improved suggestion validation, persistent storage, and deployment.

## Design Principles

- LLMs provide recommendations, not final scores.
- Resume matches include supporting evidence.
- Users control which changes are applied.
- Unchanged resume content is preserved during editing.
- Unsupported experience should not be added to resumes.

---

*Built to make resume optimization more transparent, explainable, and user-controlled.*