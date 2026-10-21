"""WhatsMyJob engine: career matching, roadmap, daily tasks, mentor chat,
mock interview, resume draft and PDF search.

Rule-based and fully offline (no API keys). It is a Python port of the engine
that powers the original browser version, and it has no Streamlit dependency,
so it can be unit-tested on its own.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

Profile = dict[str, Any]
Plan = dict[str, Any]


@dataclass(frozen=True)
class Career:
    keywords: str
    why: str
    foundations: list[str]
    core: list[str]
    projects: list[str]
    resources: list[str]
    questions: list[str]


CAREERS: dict[str, Career] = {
    "Data Analyst": Career(
        "data analyst analytics excel sql powerbi tableau statistics maths economics bcom",
        "Every company needs people who turn numbers into decisions. Entry-level roles are common, the tools are free to learn, and Excel + SQL + one dashboard project already puts you ahead of many applicants.",
        ["Excel (formulas, pivot tables)", "SQL basics", "Statistics basics"],
        ["Power BI or Tableau", "Python with Pandas", "Data cleaning", "Data storytelling"],
        ["Sales dashboard from a public dataset", "Customer churn analysis", "IPL or cricket data insights"],
        ["Kaggle Learn", "freeCodeCamp", "Google Data Analytics (audit free)", "YouTube: Alex The Analyst"],
        ["What is the difference between WHERE and HAVING in SQL?", "How would you handle missing values in a dataset?",
         "Explain a pivot table to a non-technical person.", "Walk me through a data project you built.", "What makes a good dashboard?"],
    ),
    "Web Developer": Career(
        "web developer html css javascript react frontend website bca btech it computer coding",
        "Every business needs websites and web apps, and live projects let you prove your skills even without experience.",
        ["HTML & CSS", "JavaScript basics", "Git & GitHub"],
        ["Responsive design", "JavaScript DOM & APIs", "React basics", "Backend basics (Node or Python)"],
        ["Personal portfolio website", "To-do app that saves data", "Weather app using a public API"],
        ["freeCodeCamp", "MDN Web Docs", "The Odin Project", "CS50 Web (Harvard, free)"],
        ["What is the difference between let, const and var?", "Explain the CSS box model.", "What happens when you type a URL in the browser?",
         "How do you make a page responsive?", "Walk me through a website you built."],
    ),
    "Software Developer": Career(
        "software developer programming coding java python dsa btech cs computer engineer algorithms",
        "Software teams hire freshers who can solve problems and write clean code. Strong basics plus a few projects matter more than fancy certificates.",
        ["Python or Java basics", "Data structures (arrays, strings, hashmaps)", "Git & GitHub"],
        ["Recursion & sorting", "Object-oriented programming", "SQL & databases", "Problem solving (easy to medium level)"],
        ["Library or inventory management app", "URL shortener", "Quiz app with a database"],
        ["CS50 (Harvard, free)", "NPTEL", "LeetCode", "GeeksforGeeks"],
        ["Explain the four pillars of OOP with examples.", "Difference between an array and a linked list?", "What is time complexity? Give an example.",
         "How would you reverse a string?", "Tell me about a bug you fixed."],
    ),
    "Digital Marketer": Career(
        "digital marketing marketer seo social media ads instagram bba mba brand",
        "Small and big businesses all need online customers. You can learn the tools for free and show real results with your own practice campaigns.",
        ["Marketing basics (funnel, 4Ps)", "Social media marketing", "Canva design basics"],
        ["SEO basics", "Google Ads & Meta Ads basics", "Google Analytics", "Email marketing"],
        ["Grow a niche Instagram page for 30 days", "SEO blog with 5 optimised posts", "Mock ad campaign with budget and results plan"],
        ["Google Digital Garage", "HubSpot Academy", "Meta Blueprint", "Semrush Academy"],
        ["Explain the marketing funnel.", "How do you measure a campaign's success?", "What is SEO and how does it work?",
         "Difference between organic and paid reach?", "How would you promote a new local business?"],
    ),
    "UI/UX Designer": Career(
        "ui ux designer design figma creative drawing graphic wireframe",
        "Good design makes products easy to use, and companies hire designers based on portfolios, not only degrees.",
        ["Design principles (layout, colour, typography)", "Figma basics", "UX basics (users, research)"],
        ["Wireframing & prototyping", "User research & testing", "Design systems", "Case-study writing"],
        ["Redesign a popular app screen", "Mobile app design for a local problem", "Portfolio website with 2 case studies"],
        ["Figma Learn", "Google UX Design (audit free)", "Behance & Dribbble for inspiration", "YouTube Figma tutorials"],
        ["What is the difference between UI and UX?", "Walk me through your design process.", "How do you test whether a design works?",
         "What makes a design accessible?", "Present one of your case studies."],
    ),
    "Content Writer": Career(
        "content writer writing blog english journalism copywriting mass communication ba",
        "Brands need clear writing for websites, blogs and social media. A small portfolio of published samples can open doors quickly.",
        ["Grammar & clear writing", "Research & outlining", "Basic SEO writing"],
        ["Blog & article writing", "Copywriting (headlines, CTAs)", "Editing & proofreading", "Writing for social media"],
        ["Personal blog with 5 posts", "Rewrite 3 product descriptions", "LinkedIn or newsletter series (10 posts)"],
        ["HubSpot Academy (content marketing)", "Grammarly blog", "Medium & Substack for practice", "Google Digital Garage"],
        ["How do you research a topic you do not know?", "What makes a good headline?", "How do you edit your own writing?",
         "Explain SEO writing in simple words.", "Show me an article you are proud of."],
    ),
    "HR Executive": Career(
        "hr human resources recruiter recruitment people psychology talent communication",
        "Every growing company needs people to hire, onboard and support employees. Communication and organisation matter more than technical skills here.",
        ["HR basics (hiring cycle, policies)", "Business communication", "MS Excel & Word basics"],
        ["Recruitment & sourcing", "Interviewing & screening", "Onboarding & payroll basics", "Indian labour law basics"],
        ["Write 3 job descriptions", "Design a screening questionnaire and hiring process", "Mock onboarding plan for a new joiner"],
        ["Alison (free HR courses)", "Coursera (audit free)", "LinkedIn Learning (free trial)", "YouTube HR channels"],
        ["Describe the full recruitment process.", "How would you screen 100 CVs quickly?", "How do you handle a conflict between two employees?",
         "What does an onboarding plan include?", "Why HR?"],
    ),
    "Accounts & Finance Executive": Career(
        "accounts accounting finance tally gst bcom commerce taxation bookkeeping",
        "Every business needs accurate books, GST filing and reports. Tally and Excel skills are in steady demand for freshers.",
        ["Accounting basics (debit/credit, ledgers)", "MS Excel", "Tally Prime basics"],
        ["GST basics", "Financial statements", "Excel for finance (VLOOKUP, pivots)", "Bank reconciliation & invoicing"],
        ["Books of a small shop in Tally", "Monthly budget and expense tracker in Excel", "Analyse a listed company's annual report"],
        ["Tally Education (free learning)", "Khan Academy (accounting)", "NPTEL", "YouTube accounting channels"],
        ["Explain debit and credit with an example.", "What is a bank reconciliation?", "What is GST and who must register?",
         "Difference between balance sheet and P&L?", "What Excel functions do you use most?"],
    ),
}

JOB_TASKS = [
    "Write your resume with the Resume tab and ask 2 people to review it",
    "Set up a complete LinkedIn profile with a clear headline",
    "Apply to 5 jobs or internships and log them in the Jobs tab",
    "Practise 5 interview questions out loud (Mentor tab, mock interview)",
    "Message 3 people in your field for advice or referrals",
    "Put your best project online and add the link to your resume",
    "Prepare a 60-second 'Tell me about yourself' answer",
    "List 10 companies that hire freshers for this role",
    "Follow up on applications you sent last week",
    "Do a full mock interview and note 3 things to improve",
]
JOB_TIPS = [
    "Apply to at least 5 roles every week and track them in the Jobs tab.",
    "Put 2-3 projects with links on your resume; projects beat marks for freshers.",
    "Ask friends, seniors and alumni for referrals; many jobs are filled this way.",
    "Practise your self-introduction until it is clear and under one minute.",
]
PHASE_TITLES = ["Foundations", "Core skills", "Portfolio projects", "Job-ready & applications"]
PHASE_GOALS = [
    "Understand the basics and build a daily study habit.",
    "Learn the skills employers ask for in job descriptions.",
    "Prove your skills with real projects you can show.",
    "Polish your profile and apply, practise and follow up.",
]
GENERIC_QUESTIONS = ["Tell me about yourself.", "Why do you want to work in this field, and why should we hire you?"]


# ---------------------------------------------------------------- helpers
def _round(x: float) -> int:
    """Round half up (Python's round() rounds half to even)."""
    return math.floor(x + 0.5)


def norm(s: str | None) -> str:
    return re.sub(r"[.\-/]", "", (s or "").lower())


def _words(s: str | None) -> set[str]:
    return set(re.findall(r"[a-z0-9+#]+", norm(s)))


def _overlap(a: set[str], b: set[str]) -> int:
    return len(a & b)


# ---------------------------------------------------------------- career matching
def pick_role(p: Profile) -> str:
    """Use the stated goal if it names a career, else score keywords."""
    g = norm(p.get("goal"))
    for name in CAREERS:
        nk = norm(name)
        if (g and nk in g) or (len(g) > 3 and g in nk):
            return name
    best, best_score = "Data Analyst", -1
    for name, c in CAREERS.items():
        kw = set(c.keywords.split())
        score = (3 * _overlap(kw, _words(p.get("goal")))
                 + 2 * _overlap(kw, _words(p.get("interests")))
                 + _overlap(kw, _words(p.get("degree")))
                 + _overlap(kw, _words(p.get("skills"))))
        if score > best_score:
            best, best_score = name, score
    return best


# ---------------------------------------------------------------- roadmap and daily tasks
def build_phases(role: str, months: int | str) -> list[dict[str, Any]]:
    c = CAREERS[role]
    total_weeks = max(8, int(months) * 4)
    widths = [max(1, _round(total_weeks * x)) for x in (0.25, 0.30, 0.25)]
    widths.append(max(1, total_weeks - sum(widths)))
    steps = [
        ["Learn " + s for s in c.foundations],
        ["Learn " + s for s in c.core],
        ["Build: " + s for s in c.projects],
        ["Polish resume and LinkedIn", "Apply to 5+ jobs every week", "Practise interview questions", "Ask for referrals and network"],
    ]
    resources = [
        c.resources[:3], c.resources[1:],
        ["Your own portfolio (GitHub, Behance or a personal site)"],
        ["LinkedIn Jobs", "Naukri", "Indeed", "Internshala", "Company career pages"],
    ]
    phases, start = [], 1
    for i in range(4):
        end = start + widths[i] - 1
        phases.append({
            "title": PHASE_TITLES[i],
            "weeks": f"Week {start}" if start == end else f"Weeks {start}-{end}",
            "frm": start, "to": end, "goal": PHASE_GOALS[i],
            "steps": steps[i], "resources": resources[i],
        })
        start = end + 1
    return phases


def _task_pool(role: str, phase: int) -> list[str]:
    c = CAREERS[role]
    if phase == 0:
        return [t for s in c.foundations for t in (
            f"Learn the basics of {s}: watch one tutorial and take notes",
            f"Practise {s}: complete 5 small exercises",
            f"Revise {s}: explain it in 5 sentences without looking")]
    if phase == 1:
        return [t for s in c.core for t in (
            f"Go deeper in {s}: follow a tutorial step by step",
            f"Mini-challenge: use {s} to solve one small problem",
            f"Revise {s} and write down what is still unclear")]
    if phase == 2:
        return [t for x in c.projects for t in (
            f"Plan your project: {x}",
            f"Build the first version of: {x}",
            f"Improve and test: {x}",
            f"Write a short explanation of '{x}' and publish it online")]
    return JOB_TASKS


def phase_of(plan: Plan, day: int) -> int:
    week = (day - 1) // 7 + 1
    for i, ph in enumerate(plan["phases"]):
        if ph["frm"] <= week <= ph["to"]:
            return i
    return len(plan["phases"]) - 1


def make_days(plan: Plan, p: Profile, start: int, carry: list[str] | None = None, count: int = 7) -> list[dict[str, Any]]:
    carry = carry or []
    hours = int(p.get("hours") or 2)
    n = 2 if hours <= 2 else 3
    mins = max(20, _round(hours * 60 / n / 5) * 5)
    days = []
    for k in range(count):
        d = start + k
        i = phase_of(plan, d)
        pool = _task_pool(plan["role"], i)
        offset = (d - ((plan["phases"][i]["frm"] - 1) * 7 + 1)) * n
        tasks = [carry[0]] if (k == 0 and carry) else []
        j = 0
        while len(tasks) < n:
            t = pool[(offset + j) % len(pool)]
            j += 1
            if t not in tasks:
                tasks.append(t)
        days.append({"tasks": [{"t": t, "mins": mins} for t in tasks]})
    return days


def build_plan(p: Profile) -> Plan:
    role = pick_role(p)
    plan: Plan = {"role": role, "why": CAREERS[role].why,
                  "phases": build_phases(role, p.get("months") or 4), "jobTips": JOB_TIPS}
    plan["days"] = make_days(plan, p, 1)
    return plan


def next_days(plan: Plan, p: Profile, from_day: int, recent: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Plan the next 7 days; `recent` is newest first. One unfinished task is carried over."""
    carry: list[str] = []
    for t in recent:
        if not t.get("done") and t["title"] not in carry:
            carry.append(t["title"])
    return make_days(plan, p, from_day, carry)


# ---------------------------------------------------------------- mentor and mock interview
def mock_question(role: str, n: int) -> str:
    return (GENERIC_QUESTIONS + CAREERS[role].questions[:3])[n]


def interview_feedback(answer: str) -> str:
    words = len(answer.strip().split())
    tips = [
        "✅ Good length." if 25 <= words <= 150
        else "⚠️ Too short: aim for 4-6 sentences with one example." if words < 25
        else "⚠️ A little long: keep it under about a minute (~120 words).",
        "✅ You used a number or result." if re.search(r"\d", answer)
        else "💡 Add a number or result (for example 'finished in 2 weeks').",
        "✅ You explained your reasoning." if re.search(r"because|so that|therefore|result|learn", answer, re.I)
        else "💡 Say WHY: use 'because...' or what you learned.",
    ]
    return "Feedback:\n" + "\n".join(tips)


def reply(msg: str, prev: str, p: Profile, plan: Plan, day: int, stats: dict[str, int]) -> str:
    m = msg.lower()
    role = plan["role"]
    c = CAREERS.get(role, CAREERS["Data Analyst"])
    ph = plan["phases"][phase_of(plan, day)]
    asked = re.findall(r"🎤 Q(\d)/5", prev or "")

    if "mock interview" in m and "start" in m:
        return (f"🎤 Q1/5: {mock_question(role, 0)}\n\nAnswer in your own words. "
                "I will give feedback after each answer. Type 'stop' to end.")
    if m.strip() == "stop":
        return "Okay, mock interview stopped. Come back any time and press 'Start a mock interview'."
    if asked:
        n = int(asked[-1])
        if n >= 5:
            return f"{interview_feedback(msg)}\n\n🎉 Mock interview finished! Repeat it weekly and try recording yourself."
        return f"{interview_feedback(msg)}\n\n🎤 Q{n + 1}/5: {mock_question(role, n)}"

    def has(*keys: str) -> bool:
        return any(k in m for k in keys)

    if has("stuck", "demotiv", "tired", "give up", "lazy", "bored", "hopeless", "scared", "anxious", "worried"):
        return (f"It is normal to feel like this, almost every fresher does. Today, do just 15 minutes of ONE task from the Today tab; "
                f"starting is the hardest part. You have already completed {stats['done']} tasks, which is real progress. "
                "Small steps every day beat big plans you never start.")
    if has("resume", "cv"):
        return ("Use the Resume tab: it builds a draft from your profile. Keep it to 1 page, put Projects above Skills, use real numbers "
                "(e.g. 'built a dashboard with 5,000 rows'), and never list skills you cannot explain in an interview.")
    if has("linkedin"):
        return (f"LinkedIn checklist: clear photo, headline like '{role} | Fresher | {c.foundations[0]}', a 3-line About section, "
                "your projects with links, and connect with 5 new people in your field every week.")
    if has("project"):
        return f"Project ideas for {role}: {'; '.join(c.projects)}. Pick one, finish a simple version, and publish it online."
    if has("course", "certif", "resource", "learn", "youtube"):
        return f"Free resources for {role}: {', '.join(c.resources)}. Pick one main course and finish it instead of starting many."
    if has("skill"):
        return f"Skills for {role}: Basics: {', '.join(c.foundations)}. Core: {', '.join(c.core)}."
    if has("salary", "pay", "package", "lpa"):
        return (f"Fresher salaries depend heavily on city, company and skills, so I will not guess a number. Check current ranges for {role} "
                "on job portals and Glassdoor for your city, and negotiate based on your projects.")
    if has("job", "apply", "application", "hiring", "naukri"):
        return ("Job hunting plan: apply to 5 roles a week (LinkedIn, Naukri, Internshala, company career pages), tailor your resume to each "
                "job description, and log everything in the Jobs tab. Follow up after 7 days.")
    if has("week", "today", "next", "what should", "what to do", "plan"):
        return (f"You are on day {day}, in phase '{ph['title']}' ({ph['weeks']}): {ph['goal']} Open the Today tab and finish your tasks. "
                f"You have done {stats['done']} of {stats['total']} planned tasks so far.")
    if has("interview", "question"):
        return ("Press 'Start a mock interview' below for 5 practice questions with feedback. Tip: answer using Situation, Task, Action, "
                "Result (STAR) and always include one example.")
    if has("hello", "hi ", "hey", "namaste") or m.strip() in ("hi", "hey"):
        return f"Hi! I am your offline mentor for your {role} goal. Ask me about your plan, skills, projects, resume, interviews, jobs or motivation."
    return ("I am running in free offline mode, so I answer from built-in guidance. Try asking about: this week's plan, skills, projects, "
            "free courses, resume, LinkedIn, job applications, interviews, or motivation.")


# ---------------------------------------------------------------- resume
def build_resume(name: str, details: str, p: Profile, plan: Plan) -> str:
    """Markdown resume draft. Never invents facts: gaps become [ADD: ...] placeholders."""
    role = plan["role"]
    c = CAREERS.get(role, CAREERS["Data Analyst"])
    lines = [re.sub(r"^[\s\-•\t]+|[\s\-•\t]+$", "", l) for l in (details or "").split("\n")]
    lines = [l for l in lines if l]
    projects = [l for l in lines if re.match(r"projects?\b", l, re.I)]
    certs = [l for l in lines if re.match(r"(certificat|course)", l, re.I)]
    other = [l for l in lines if l not in projects and l not in certs]
    skills = [s.strip() for s in re.split(r"[,;]", p.get("skills") or "") if s.strip() and s.strip().lower() != "none yet"]

    def bullets(items: list[str], default: str) -> str:
        return "\n".join("- " + i for i in items) if items else default

    degree = p.get("degree") or "graduate"
    focus = ", ".join(c.foundations[:2] + c.core[:1])
    return (
        f"# {name or '[ADD: Full name]'}\n[ADD: phone] | [ADD: email] | [ADD: LinkedIn / GitHub link] | [ADD: city]\n\n"
        f"## Objective\nFresh {degree} seeking an entry-level {role} position. Actively building skills in {focus} "
        f"through a structured {p.get('months') or 4}-month learning plan.\n\n"
        f"## Education\n- {p.get('degree') or '[ADD: degree]'}: [ADD: college, year, CGPA/percentage]\n\n"
        f"## Skills\n- {', '.join(skills) if skills else '[ADD: skills you can really do]'}\n"
        f"- Currently learning: {', '.join(c.foundations + c.core[:2])}\n\n"
        f"## Projects\n{bullets(projects, f'- [ADD: project name, what you built, tools used, result]{chr(10)}  (Idea: {c.projects[0]})')}\n\n"
        f"## Certifications / Courses\n{bullets(certs, '- [ADD: course name, platform, year]')}\n\n"
        f"## Other\n{bullets(other, '- [ADD: achievements, internships, volunteering]')}\n\n"
        "_Tip: replace every [ADD: ...] with true details and keep it to one page._"
    )


# ---------------------------------------------------------------- PDF search
_STOP = set("a an the is are was were of to in on for and or with what which who how do does did i my me your you it this that be as at by "
            "from can she he her his they have has tell about".split())


def _tokens(s: str) -> list[str]:
    words = [w for w in re.findall(r"[a-z0-9+#]+", s.lower()) if w not in _STOP and len(w) > 1]
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]


def search_doc(pages: list[str], question: str, k: int = 3) -> dict[str, Any]:
    """TF-IDF-style ranking over sentences. Quotes are verbatim, page numbers are where they were found."""
    chunks: list[tuple[int, str]] = []
    for page_no, text in enumerate(pages, start=1):
        for line in re.split(r"\n+", text):
            marked = re.sub(r"([.!?])\s+(?=[A-Z])", "\\1\x01", line)
            for part in marked.split("\x01"):
                if len(part.strip()) > 3:
                    chunks.append((page_no, part.strip()))
    q = list(dict.fromkeys(_tokens(question)))
    toks = [_tokens(c[1]) for c in chunks]
    if not q or not chunks:
        return {"answer": "Please ask a more specific question.", "citations": [], "unverified": 0}
    n_chunks = len(chunks)
    df = {w: sum(1 for t in toks if w in t) for w in q}
    scored = []
    for i, (page_no, text) in enumerate(chunks):
        score = 0.0
        for w in q:
            n = toks[i].count(w)
            if n:
                score += math.log(1 + n_chunks / (1 + df[w])) * (1 + math.log(n))
        if score > 0:
            scored.append((score, page_no, text))
    scored.sort(key=lambda x: -x[0])  # stable, like the original
    cites, seen = [], set()
    for _, page_no, text in scored:
        if text in seen:
            continue
        seen.add(text)
        cites.append({"pages": str(page_no), "quote": text[:300]})
        if len(cites) == k:
            break
    if not cites:
        return {"answer": "I could not find that in your document. Try different keywords from the PDF.", "citations": [], "unverified": 0}
    return {"answer": f"I found {len(cites)} matching passage(s) in your PDF. These are exact quotes from your document (offline search, not AI-written):",
            "citations": cites, "unverified": 0}
