"""WhatsMyJob: a free, offline career guide for fresh graduates (Streamlit edition).

Run:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import html
import io
import json
import re

import streamlit as st
import streamlit.components.v1 as components

import engine as E
import visuals as V

try:
    from pypdf import PdfReader
except ImportError:  # the PDF tab explains how to install it
    PdfReader = None

st.set_page_config(page_title="WhatsMyJob", page_icon="📊", layout="wide")

DEGREES = ["B.Sc", "B.Com", "BA", "BCA", "B.Tech", "BBA", "Other"]
STATUSES = ["Wishlist", "Applied", "Interview", "Offer", "Rejected"]
NOT_SURE = "Not sure, suggest one for me"

CSS = """
<style>
.eyebrow{font-family:ui-monospace,Menlo,Consolas,monospace;letter-spacing:.14em;color:#2dd4bf;font-size:.8rem;margin:0 0 .4rem}
.big{font-size:4.2rem;line-height:1.02;font-weight:800;margin:.1rem 0 1rem}
.big .light{font-weight:300;color:#94a3b8}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;background:#fb8f68;color:#111;font-size:.72rem;font-weight:700;letter-spacing:.06em}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.78rem;color:#94a3b8}
@media (max-width:800px){.big{font-size:3rem}}
</style>
"""


# ------------------------------------------------------------------ state
def new_state() -> dict:
    return {"profile": None, "plan": None, "start": None, "tasks": [], "chat": [], "jobs": [], "docs": [], "next_id": 1}


def _clear_widget_state() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith(("task_", "jobstatus_", "pdf_result", "mentor_q")):
            del st.session_state[key]


def _replace_state(state: dict) -> None:
    st.session_state.app = state
    _clear_widget_state()


if "app" not in st.session_state:
    st.session_state.app = new_state()


def day_no(a: dict) -> int:
    return max(1, (dt.date.today() - dt.date.fromisoformat(a["start"])).days + 1)


def streak(a: dict) -> int:
    done = lambda d: any(t["day"] == d and t["done"] for t in a["tasks"])  # noqa: E731
    n, d = 0, day_no(a)
    if not done(d):
        d -= 1
    while d >= 1 and done(d):
        n += 1
        d -= 1
    return n


def stats(a: dict) -> dict:
    return {"done": sum(1 for t in a["tasks"] if t["done"]), "total": len(a["tasks"])}


def add_days(a: dict, start_day: int, days: list, done: bool = False) -> None:
    for i, day in enumerate(days):
        for t in day["tasks"]:
            a["tasks"].append({"id": a["next_id"], "day": start_day + i, "title": t["t"], "mins": t["mins"], "done": done})
            a["next_id"] += 1


def create_plan(profile: dict) -> None:
    plan = E.build_plan(profile)
    days = plan.pop("days")
    a = new_state()
    a.update(profile=profile, plan=plan, start=dt.date.today().isoformat())
    add_days(a, 1, days)
    _replace_state(a)


def start_demo() -> None:
    p = {"degree": "B.Com", "skills": "Excel, English", "interests": "data", "goal": "Data Analyst", "hours": 2, "months": 4}
    plan = E.build_plan(p)
    days = plan.pop("days")
    a = new_state()
    a.update(profile=p, plan=plan, start=(dt.date.today() - dt.timedelta(days=35)).isoformat(),
             jobs=[{"id": 900, "company": "Acme Analytics", "role": "Junior Data Analyst", "status": "Applied"},
                   {"id": 901, "company": "BrightMart", "role": "MIS Executive", "status": "Wishlist"}])
    add_days(a, 1, days, done=True)
    add_days(a, 33, E.make_days(plan, p, 33, [], 3), done=True)
    add_days(a, 36, E.next_days(plan, p, 36, []))
    next(t for t in a["tasks"] if t["day"] == 36)["done"] = True
    q = "What should I do this week?"
    a["chat"] = [{"role": "user", "content": q},
                 {"role": "assistant", "content": E.reply(q, "", p, plan, 36, {"done": 21, "total": 34})}]
    _replace_state(a)
    st.toast("Demo loaded: day 36 of the journey")


# ------------------------------------------------------------------ callbacks
def _toggle_task(task_id: int) -> None:
    a = st.session_state.app
    for t in a["tasks"]:
        if t["id"] == task_id:
            t["done"] = bool(st.session_state[f"task_{task_id}"])


def _plan_more() -> None:
    a = st.session_state.app
    day = day_no(a)
    start = max(max((t["day"] for t in a["tasks"]), default=0) + 1, day)
    recent = list(reversed(a["tasks"]))[:14]
    add_days(a, start, E.next_days(a["plan"], a["profile"], start, recent))
    st.toast("Next 7 days planned")


def _send(text: str) -> None:
    a = st.session_state.app
    prev = next((m["content"] for m in reversed(a["chat"]) if m["role"] == "assistant"), "")
    a["chat"].append({"role": "user", "content": text})
    a["chat"].append({"role": "assistant",
                      "content": E.reply(text, prev, a["profile"], a["plan"], day_no(a), stats(a))})


def _send_from_form() -> None:
    text = st.session_state.get("mentor_q", "").strip()
    if text:
        _send(text)
        st.session_state["mentor_q"] = ""


def _set_status(job_id: int) -> None:
    for j in st.session_state.app["jobs"]:
        if j["id"] == job_id:
            j["status"] = st.session_state[f"jobstatus_{job_id}"]


def _delete_job(job_id: int) -> None:
    a = st.session_state.app
    a["jobs"] = [j for j in a["jobs"] if j["id"] != job_id]


def _ask_pdf(doc_index: int) -> None:
    a = st.session_state.app
    question = st.session_state.get("pdf_q", "").strip()
    if question and 0 <= doc_index < len(a["docs"]):
        st.session_state["pdf_result"] = E.search_doc(a["docs"][doc_index]["pages"], question)


# ------------------------------------------------------------------ helpers
def show_scene(page_html: str, height: int) -> None:
    """Embed an animated Three.js scene (see visuals.py)."""
    components.html(page_html, height=height + 4)


def md_escape(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]<>#+!|~$])", r"\\\1", text)


def make_ics(at: dt.time) -> str:
    today = dt.date.today().strftime("%Y%m%d")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//WhatsMyJob//EN", "BEGIN:VEVENT", "UID:whatsmyjob-daily@local",
             f"DTSTAMP:{stamp}", f"DTSTART:{today}T{at:%H%M}00", "DURATION:PT30M", "RRULE:FREQ=DAILY",
             "SUMMARY:WhatsMyJob: finish today's tasks", "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines)


def export_progress(a: dict) -> str:
    return json.dumps({k: v for k, v in a.items() if k != "docs"}, indent=2)  # PDFs stay out of the file


def load_progress(raw: bytes) -> None:
    data = json.loads(raw)
    if not isinstance(data, dict) or not {"profile", "plan", "start", "tasks"} <= data.keys():
        raise ValueError("This does not look like a WhatsMyJob progress file.")
    dt.date.fromisoformat(data["start"])
    state = new_state()
    state.update({k: data[k] for k in state if k in data and k != "docs"})
    _replace_state(state)


# ------------------------------------------------------------------ welcome screen
def welcome() -> None:
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown('<p class="eyebrow">FOR FRESH GRADUATES</p>'
                    '<div class="big">Find your<br><span class="light">first job.</span></div>', unsafe_allow_html=True)
        st.write("Tell us about your degree. We choose a career, build your roadmap, and give you small daily tasks until you are job-ready.")
        if st.button("See a live demo"):
            start_demo()
            st.rerun()
        st.caption("No sign-up. No tracking. Your data stays in this browser session.")
    with right:
        show_scene(V.globe_html(list(E.CAREERS), 420), 420)

    st.divider()
    st.subheader("Build my roadmap")
    with st.form("profile"):
        c1, c2 = st.columns(2)
        degree = c1.selectbox("Your degree", DEGREES, index=1)
        other = c2.text_input("Other degree (only if you chose Other)")
        c3, c4 = st.columns(2)
        skills = c3.text_input("Skills you have", placeholder="Excel, English, Canva")
        interests = c4.text_input("Interests", placeholder="data, design, writing")
        goal = st.selectbox("Target career", [NOT_SURE] + list(E.CAREERS))
        c5, c6 = st.columns(2)
        hours = c5.select_slider("Study hours per day", options=[1, 2, 3], value=2)
        months = c6.select_slider("Months until you want a job", options=[2, 3, 4, 5, 6], value=4)
        submitted = st.form_submit_button("Build my roadmap", type="primary")
    if submitted:
        chosen = other.strip() if degree == "Other" and other.strip() else degree
        create_plan({"degree": chosen, "skills": skills.strip() or "none yet", "interests": interests.strip() or "not sure",
                     "goal": "not sure" if goal == NOT_SURE else goal, "hours": int(hours), "months": int(months)})
        st.rerun()


# ------------------------------------------------------------------ tabs
def tab_today(a: dict) -> None:
    plan, day = a["plan"], day_no(a)
    cur = E.phase_of(plan, day)
    hour = dt.datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    left, right = st.columns([1, 1.1])
    with left:
        st.markdown(f'<p class="eyebrow">{greeting.upper()}</p><div class="big">Day {day}</div>', unsafe_allow_html=True)
        st.markdown(f"Heading to **{plan['role']}**  \nNow: {plan['phases'][cur]['title']}")
    with right:
        show_scene(V.staircase_html(plan["phases"], cur, 380), 380)

    s = stats(a)
    today = [t for t in a["tasks"] if t["day"] == day]
    pct = round(100 * s["done"] / s["total"]) if s["total"] else 0
    m1, m2, m3 = st.columns(3)
    m1.metric("Progress", f"{pct}%")
    m2.metric("Day streak", streak(a))
    m3.metric("Done today", f"{sum(1 for t in today if t['done'])}/{len(today)}")
    st.progress(pct / 100)

    st.subheader("Today's tasks")
    st.caption(dt.date.today().strftime("%a %b %d %Y"))
    if not today:
        st.info("No tasks are planned for today yet.")
    for t in today:
        st.checkbox(f"{t['title']}  ·  {t['mins']} min", value=t["done"], key=f"task_{t['id']}",
                    on_change=_toggle_task, args=(t["id"],))
    if any(t["day"] == day + 1 for t in a["tasks"]):
        st.caption("Tomorrow's tasks are ready.")
    else:
        st.button("Plan the next 7 days", on_click=_plan_more,
                  help="Builds a new week and carries one unfinished task forward.")

    st.subheader("Progress by phase")
    for i, ph in enumerate(plan["phases"]):
        mark = "✅" if i < cur else "▶️" if i == cur else "⚪"
        st.markdown(f"{mark} **{ph['title']}** <span class='mono'>{ph['weeks']}</span>", unsafe_allow_html=True)


def tab_roadmap(a: dict) -> None:
    plan, day = a["plan"], day_no(a)
    cur = E.phase_of(plan, day)
    left, right = st.columns([1, 1.1])
    with left:
        st.markdown('<p class="eyebrow">YOUR ROADMAP</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="big">{html.escape(plan["role"])}</div>', unsafe_allow_html=True)
        st.write(plan["why"])
    with right:
        show_scene(V.staircase_html(plan["phases"], cur, 380), 380)
    st.subheader("Phases")
    for col, (i, ph) in zip(st.columns(4), enumerate(plan["phases"])):
        with col, st.container(border=True):
            st.markdown(f"### {i + 1:02d}")
            st.markdown(f"<span class='pill'>{ph['weeks'].upper()}{' · YOU ARE HERE' if i == cur else ''}</span>", unsafe_allow_html=True)
            st.markdown(f"**{ph['title']}**")
            st.caption(ph["goal"])
            st.markdown("\n".join(f"- {s}" for s in ph["steps"]))
            st.markdown("**Free:** " + " · ".join(ph["resources"]))
    st.subheader("Job-hunt tips")
    st.markdown("\n".join(f"- {t}" for t in plan["jobTips"]))


def tab_mentor(a: dict) -> None:
    st.subheader("Mentor")
    st.caption("Offline, rule-based guidance for freshers. Ask about your plan, skills, projects, resume, interviews, jobs or motivation.")
    if not a["chat"]:
        st.info("Try one of the quick questions below, or start a mock interview.")
    for m in a["chat"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"].replace("\n", "  \n"))
    quick = ["Start a mock interview for my target role.", "What should I do this week?", "Which skills should I learn?", "I feel stuck."]
    for col, (i, q) in zip(st.columns(len(quick)), enumerate(quick)):
        col.button(q, key=f"quick_{i}", on_click=_send, args=(q,))
    with st.form("mentor_form"):
        st.text_input("Type your question or interview answer…", key="mentor_q")
        st.form_submit_button("Send", type="primary", on_click=_send_from_form)


def tab_resume(a: dict) -> None:
    st.subheader("Resume builder")
    st.caption("Built from your profile. It never invents facts: anything missing becomes an [ADD: ...] placeholder.")
    left, right = st.columns(2)
    with left:
        name = st.text_input("Full name", key="resume_name")
        details = st.text_area("Your details, one per line", key="resume_details", height=220,
                               placeholder="Project: Sales dashboard in Power BI, cut reporting time by 40%\nCertificate: Excel basics, Coursera, 2026\nInternship: data intern at a local cafe")
    draft = E.build_resume(name, details, a["profile"], a["plan"])
    with right:
        with st.container(border=True):
            st.markdown(draft)
    st.download_button("Download resume draft (.md)", draft, file_name="resume-draft.md", mime="text/markdown")


def tab_pdf(a: dict) -> None:
    st.subheader("Ask your PDF")
    st.caption("Upload a text-based PDF (resume, job description, notes). Every answer shows the page and the exact quote.")
    if PdfReader is None:
        st.error("PDF support needs the pypdf package: pip install pypdf")
        return
    up = st.file_uploader("Drop a PDF here", type="pdf")
    if up is not None:
        key = f"{up.name}:{up.size}"
        if not any(d["key"] == key for d in a["docs"]):
            try:
                pages = [(p.extract_text() or "") for p in PdfReader(io.BytesIO(up.getvalue())).pages]
            except Exception as exc:  # corrupt or encrypted file
                st.error(f"Could not read this PDF: {exc}")
                pages = []
            if pages and not any(p.strip() for p in pages):
                st.error("This PDF has no selectable text (it may be a scan). Please use a text-based PDF.")
            elif pages:
                a["docs"].append({"key": key, "name": up.name, "pages": pages})
    if not a["docs"]:
        return
    idx = st.selectbox("Document", range(len(a["docs"])),
                       format_func=lambda i: f"{a['docs'][i]['name']} · {len(a['docs'][i]['pages'])} pages")
    with st.form("pdf_form"):
        st.text_input("Your question", key="pdf_q", placeholder="e.g. What skills are listed?")
        st.form_submit_button("Ask", type="primary", on_click=_ask_pdf, args=(idx,))
    res = st.session_state.get("pdf_result")
    if res:
        with st.container(border=True):
            st.write(res["answer"])
            for c in res["citations"]:
                st.caption(f"PAGE {c['pages']}")
                st.markdown(f"> “{md_escape(c['quote'])}”")


def tab_jobs(a: dict) -> None:
    st.subheader("Job tracker")
    with st.form("addjob", clear_on_submit=True):
        c1, c2 = st.columns(2)
        company, role = c1.text_input("Company"), c2.text_input("Role")
        if st.form_submit_button("Add application") and company.strip() and role.strip():
            a["jobs"].insert(0, {"id": a["next_id"], "company": company.strip(), "role": role.strip(), "status": "Wishlist"})
            a["next_id"] += 1
            st.rerun()
    for col, status in zip(st.columns(len(STATUSES)), STATUSES):
        col.metric(status, sum(1 for j in a["jobs"] if j["status"] == status))
    if not a["jobs"]:
        st.info("No applications yet. Add the first one above.")
    for j in a["jobs"]:
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        c1.markdown(f"**{j['company']}**")
        c2.write(j["role"])
        c3.selectbox("Status", STATUSES, index=STATUSES.index(j["status"]), key=f"jobstatus_{j['id']}",
                     label_visibility="collapsed", on_change=_set_status, args=(j["id"],))
        c4.button("Delete", key=f"jobdel_{j['id']}", on_click=_delete_job, args=(j["id"],))


def tab_more(a: dict) -> None:
    st.subheader("Daily reminder")
    st.caption("Download a calendar reminder and open it with Google Calendar, Outlook or your phone's calendar.")
    at = st.time_input("Time", dt.time(19, 0))
    st.download_button("Download reminder (.ics)", make_ics(at), file_name="whatsmyjob-daily-reminder.ics", mime="text/calendar")

    st.subheader("Save and restore progress")
    st.caption("Progress lives in this browser session. Download it to keep it, and load it later or on another device.")
    st.download_button("Download my progress (.json)", export_progress(a), file_name="whatsmyjob-progress.json", mime="application/json")
    up = st.file_uploader("Load a progress file", type="json", key="progress_upload")
    if up is not None and st.button("Load this progress"):
        try:
            load_progress(up.getvalue())
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            st.error(f"Could not load that file: {exc}")
        else:
            st.rerun()

    st.subheader("Demo tools")
    st.caption("Jump one day ahead to see how tasks and the staircase progress, or erase everything.")
    c1, c2 = st.columns(2)
    if c1.button("Skip to next day"):
        a["start"] = (dt.date.fromisoformat(a["start"]) - dt.timedelta(days=1)).isoformat()
        st.rerun()
    if c2.button("Erase everything and start over"):
        _replace_state(new_state())
        st.rerun()


# ------------------------------------------------------------------ main
def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    a = st.session_state.app
    head, badge = st.columns([4, 1])
    head.markdown("#### 📊 WhatsMyJob")
    badge.markdown("<div class='mono' style='text-align:right;padding-top:12px'>● OFFLINE · FREE</div>", unsafe_allow_html=True)
    if not a["plan"]:
        welcome()
        return
    names = ["Today", "Roadmap", "Mentor", "Resume", "PDF", "Jobs", "More"]
    for tab, fn in zip(st.tabs(names), (tab_today, tab_roadmap, tab_mentor, tab_resume, tab_pdf, tab_jobs, tab_more)):
        with tab:
            fn(a)
    st.caption("Rule-based and offline: no AI model, no tracking. Built with Python and Streamlit.")


main()
