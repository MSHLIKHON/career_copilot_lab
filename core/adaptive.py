import re
from core.catalog import GOALS, SKILLS
from core.tasks import TASKS, TASK_BY_ID, TOPICS


def extract_claims(text):
    text = text[:50000].lower()
    return [skill for skill in SKILLS if re.search(r"(?<![a-z])" + re.escape(skill.lower()) + r"(?![a-z])", text)]


def summarize(attempts):
    rows = []
    for topic in TOPICS:
        items = [a for a in attempts if TASK_BY_ID[a["task_id"]]["topic"] == topic]
        passed = {a["task_id"] for a in items if a["result"]["status"] == "passed"}
        independent = {a["task_id"] for a in items if a["result"]["status"] == "passed" and not a["hints"] and not a["solution_seen"]}
        best = max([TASK_BY_ID[k]["level"] for k in independent], default=0)
        rows.append({"Topic": topic, "Attempts": len(items), "Tasks passed": len(passed),
                     "Independent passes": len(independent), "Highest evidenced level": best,
                     "Status": "Not assessed" if not items else "Task evidence recorded" if independent else "Practice needed"})
    return rows


def recommend(attempts, target="Python foundations"):
    done = {a["task_id"] for a in attempts if a["result"]["status"] == "passed"}
    if attempts:
        last = attempts[-1]
        current = TASK_BY_ID[last["task_id"]]
        if last["result"]["status"] != "passed":
            easier = [t for t in TASKS if t["topic"] == current["topic"] and t["level"] < current["level"] and t["id"] not in done]
            if easier:
                return easier[-1], "The latest attempt failed. Review an easier task in the same topic first."
            related = [t for t in TASKS if t["topic"] == current["topic"] and t["level"] <= current["level"] and t["id"] not in done and t["id"] != current["id"]]
            if related:
                return related[0], "Try a different task at this level to practise the same topic."
            return current, "Review the failed tests and hint, then retry this task."
    for row in sorted(summarize(attempts), key=lambda r: (r["Highest evidenced level"], r["Tasks passed"])):
        options = [t for t in TASKS if t["topic"] == row["Topic"] and t["id"] not in done and t["level"] <= GOALS[target][row["Topic"]]]
        if options:
            return options[0], f"Build evidence in {row['Topic']} for your selected learning goal."
    options = [t for t in TASKS if t["id"] not in done]
    if options:
        return options[0], "Your goal-level tasks are complete. Try the next extension task."
    return TASKS[0], "All 20 tasks have a passing attempt. Revisit topics; assisted passes are not independent evidence."


def roadmap(attempts, target):
    rows = []
    for row in summarize(attempts):
        required = GOALS[target][row["Topic"]]
        rows.append({"Topic": row["Topic"], "Goal level": required,
                     "Independent evidence level": row["Highest evidenced level"],
                     "Next action": "Try a new task without hints" if row["Highest evidenced level"] < required else "Maintain practice; task evidence only"})
    return rows
