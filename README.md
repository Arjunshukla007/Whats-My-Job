# WhatsMyJob (Python / Streamlit)

**A free career guide for fresh graduates.** Pick a target career, follow a phase-by-phase roadmap, get adaptive daily tasks,
practise mock interviews, build a resume and ask questions about a PDF with page-level citations.
No API keys, no database, no tracking.

**Live demo:** [Visit GitHub](https://whats-my-job-manu8baqberxgfhq6nqkeu.streamlit.app/) ·  Click **"See a live demo"** to explore a populated account.

<!-- Add 3-4 screenshots of YOUR running app here, e.g. docs/today.png -->

## Features
- **Career matching:** recommends one of 8 career paths from degree, skills and interests.
- **Roadmap:** four phases (foundations, core skills, projects, job-ready) scaled to your timeline, with free resources.
- **Adaptive daily tasks:** sized to your study hours; unfinished work carries into the next 7-day plan.
- **Mentor and mock interview:** answers common fresher questions; a 5-question interview with feedback on length, results and reasoning.
- **Resume builder:** never invents facts; missing details appear as `[ADD: ...]`.
- **PDF Q&A with citations:** reads PDFs (pypdf) and returns the exact matching sentences with page numbers.
- **Job tracker**, a downloadable **daily calendar reminder** (.ics), and **save/restore progress** (.json).
- **Animated 3D visuals** (Three.js/WebGL): a slowly rotating roadmap staircase with a bobbing orb and waving flag, and a rotating globe of career paths with pulsing nodes. Drag either one to spin it yourself.

## Run it
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```
Or run it from anywhere by giving the file path:
```bash
streamlit run C:\path\to\whatsmyjob_streamlit\app.py
```

## Deploy for free (Streamlit Community Cloud)
1. Push this folder to a public GitHub repo (`app.py` and `requirements.txt` at the top level).
2. Go to share.streamlit.io, sign in with GitHub, click **Create app**, pick the repo, branch `main`, main file `app.py`.
3. Click **Deploy**. You get a public `*.streamlit.app` link for your resume.

## How it works
| File | Role |
|---|---|
| `engine.py` | All logic: career matching, roadmap, task planning, mentor, mock interview, resume, PDF search. Pure Python, no Streamlit. |
| `app.py` | Streamlit UI: tabs, state, callbacks, file upload/download. |
| `visuals.py` | Animated Three.js scenes (staircase and globe) embedded with `st.components.v1.html`. Needs internet for the three.js CDN. |
| `test_engine.py` | Unit tests for the engine. |

The engine is **rule-based, not generative AI**: career matching is keyword scoring, task plans come from per-career task pools,
and PDF search is TF-IDF-style ranking over sentences. Because search only returns sentences that exist in the PDF,
every quote is verbatim and the page number is where it was found.

State lives in `st.session_state` (per visitor, so deployed users never see each other's data).
Use **More > Download my progress** to keep it between sessions.

## Tests
```bash
python -m unittest -v
```
Covers roadmap generation, task sizing, career matching, re-planning, the mock interview, resume honesty, PDF citation accuracy,
every career path, and far-future day planning.

## Limitations and next steps
Keyword-based answers rather than an LLM, text-based PDFs only (no OCR), progress is per session unless exported.
Next: optional LLM mode via an API key, user accounts with a database, more careers.

## License
MIT.
