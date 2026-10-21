"""Engine tests. Run with:  python -m unittest -v   (or: pytest)"""
import unittest

import engine as E

P = {"degree": "B.Com", "skills": "Excel", "interests": "data", "goal": "Data Analyst", "hours": 2, "months": 4}


class EngineTests(unittest.TestCase):
    def test_roadmap_has_4_phases_covering_whole_timeline(self):
        plan = E.build_plan(P)
        ph = plan["phases"]
        self.assertEqual(plan["role"], "Data Analyst")
        self.assertEqual(len(ph), 4)
        self.assertEqual((ph[0]["frm"], ph[3]["to"]), (1, 16))
        for i in range(3):
            self.assertEqual(ph[i]["to"] + 1, ph[i + 1]["frm"])

    def test_task_sizing_follows_study_hours(self):
        a = E.build_plan(P)
        self.assertEqual(len(a["days"]), 7)
        self.assertTrue(all(len(d["tasks"]) == 2 and all(t["mins"] == 60 for t in d["tasks"]) for d in a["days"]))
        b = E.build_plan({**P, "hours": 3})
        self.assertTrue(all(len(d["tasks"]) == 3 and all(t["mins"] == 60 for t in d["tasks"]) for d in b["days"]))

    def test_suggests_career_when_user_is_not_sure(self):
        self.assertEqual(E.pick_role({"degree": "BCA", "goal": "not sure", "interests": "websites html", "skills": ""}), "Web Developer")
        self.assertEqual(E.pick_role({"degree": "BA English", "goal": "not sure", "interests": "writing blogs", "skills": ""}), "Content Writer")
        self.assertEqual(E.pick_role({"degree": "B.Com", "goal": "not sure", "interests": "tally gst", "skills": ""}), "Accounts & Finance Executive")

    def test_replanning_carries_one_unfinished_task(self):
        plan = E.build_plan(P)
        rec = [{"title": "Unfinished thing", "done": False}, {"title": "Finished", "done": True}]
        days = E.next_days(plan, P, 8, rec)
        self.assertEqual(len(days), 7)
        self.assertEqual(days[0]["tasks"][0]["t"], "Unfinished thing")

    def test_mock_interview_runs_5_questions_then_finishes(self):
        plan, st, prev = E.build_plan(P), {"done": 3, "total": 14}, ""
        r = E.reply("Start a mock interview for my target role.", prev, P, plan, 1, st)
        self.assertRegex(r, r"^🎤 Q1/5")
        answer = "I built a dashboard because I wanted to learn SQL and it saved 30 percent of reporting time for a small shop"
        for n in range(2, 6):
            prev = r
            r = E.reply(answer, prev, P, plan, 1, st)
            self.assertRegex(r, rf"Feedback[\s\S]*Q{n}/5")
        r = E.reply("I solved it step by step because accuracy matters and I learned from 2 mistakes", r, P, plan, 1, st)
        self.assertIn("finished", r)

    def test_resume_never_invents_facts(self):
        plan = E.build_plan(P)
        r = E.build_resume("Asha Rao", "Project: Sales dashboard\nCertificate: Excel basics", P, plan)
        self.assertIn("# Asha Rao", r)
        self.assertIn("Sales dashboard", r)
        self.assertIn("[ADD:", r)
        for fake in ("Google", "Infosys", "TCS"):
            self.assertNotIn(fake, r)

    def test_pdf_search_returns_verbatim_quotes_with_correct_pages(self):
        pages = ["Name: Asha Rao. B.Sc Maths 2025.", "Skills: Python, SQL, Excel.", "Project: Sales dashboard in Power BI."]
        self.assertEqual(E.search_doc(pages, "What skills does she have?")["citations"][0],
                         {"pages": "2", "quote": "Skills: Python, SQL, Excel."})
        self.assertEqual(E.search_doc(pages, "Which dashboard project did she build?")["citations"][0]["pages"], "3")
        self.assertEqual(E.search_doc(pages, "quantum physics experiments")["citations"], [])
        for c in E.search_doc(pages, "skills python")["citations"]:
            self.assertIn(E.norm(c["quote"]), E.norm(pages[int(c["pages"]) - 1]))

    def test_every_career_builds_a_plan(self):
        for role in E.CAREERS:
            plan = E.build_plan({**P, "goal": role})
            self.assertEqual(plan["role"], role)
            self.assertTrue(all(len(d["tasks"]) >= 2 for d in plan["days"]))

    def test_far_future_days_use_job_phase(self):
        plan = E.build_plan(P)
        self.assertEqual(E.phase_of(plan, 500), 3)
        self.assertEqual(len(E.make_days(plan, P, 100)), 7)


if __name__ == "__main__":
    unittest.main()
