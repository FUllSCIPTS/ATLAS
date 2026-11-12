"""Autograder for the app-building tickets (T01-T10, 100 points).

    python python_lab/app_tasks/grade.py                     # grade starter.py (your work)
    python python_lab/app_tasks/grade.py --task 3 --task 4   # only some tickets
    python python_lab/app_tasks/grade.py --impl my_copy.py   # grade another file
    python python_lab/app_tasks/grade.py --json report.json  # machine-readable report
    python python_lab/app_tasks/grade.py --check             # instructors: validate the test suite itself

Points per ticket = weight x (passed acceptance tests / all acceptance tests); a ticket is
DONE only when every test passes.

--check proves the grading is trustworthy:
  1. the reference solution scores 100/100 (run --repeat times to catch flaky tests);
  2. the untouched starter scores 0/100;
  3. every "mutant" - a copy of the solution with one realistic bug - is caught by its
     ticket's tests (a test suite that cannot see a bug cannot grade it).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE / "tests"
TICKETS = {
    1: ("Delete a cancelled ride", 8), 2: ("Available-drivers dropdown", 8),
    3: ("Accounts, login and sessions", 15), 4: ("Protect the API with roles", 12),
    5: ("Rate-limit bookings", 10), 6: ("CSV export", 10), 7: ("Schema migration and ratings", 12),
    8: ("Ignore out-of-order search responses", 8), 9: ("Sorting and filtering without SQL injection", 8),
    10: ("Transactional outbox and delivery worker", 9),
}
assert sum(w for _, w in TICKETS.values()) == 100

# (ticket, bug description, [(text in solution.py, replacement), ...])
MUTANTS = [
    (1, "forgets the audit rows (FOREIGN KEY error -> 500)",
     [('            db.execute("DELETE FROM audit WHERE ride_id = ?", (ride_id,))   # children first (FOREIGN KEY)\n', "")]),
    (1, "removes the row from the screen before the server answers",
     [("        if resp.status == 204:\n            screen.table", "        if True:\n            screen.table")]),
    (2, "offers busy drivers", [("WHERE online = 1 AND busy = 0", "WHERE online = 1")]),
    (2, "does not refresh the dropdown after assigning",
     [("            on_available()                                     # that driver is busy now\n", "")]),
    (3, "stores the password in plain text",
     [("(username, salt, _hash_password(password, salt), role)", "(username, salt, password.encode(), role)")]),
    (3, "error message reveals whether the user exists",
     [('raise Unauthorized("invalid username or password")             # same message either way',
       'raise Unauthorized("unknown user" if not rows else "invalid username or password")')]),
    (3, "trusts the role sent by the client",
     [('create_user(app, b.get("username"), b.get("password"))', 'create_user(app, b.get("username"), b.get("password"), b.get("role", "passenger"))')]),
    (3, "sessions never expire", [(' or rows[0]["expires_at"] <= app.auth_clock()', "")]),
    (4, "lets passengers book in someone else's name",
     [('            request.body["passenger"] = user["username"]           # passengers book in their own name\n', "            pass\n")]),
    (4, "forgets that statistics are dispatcher-only", [('("GET", r"/api/stats"),', "")]),
    (5, "limits by IP only (one office shares an IP)",
     [('key = "token:" + auth if auth.startswith("Bearer ") else "ip:" + request.client', 'key = "ip:" + request.client')]),
    (5, "always says Retry-After: 60", [("math.ceil(q[0] + window - now)", "window")]),
    (6, "no protection against formula injection",
     [('return "\'" + text if text[:1] in ("=", "+", "-", "@", "\\t", "\\r") else text', "return text")]),
    (6, "Unix line endings instead of RFC 4180", [('lineterminator="\\r\\n"', 'lineterminator="\\n"')]),
    (7, "re-runs every migration on start-up",
     [("enumerate(migrations[version:], start=version + 1)", "enumerate(migrations, start=1)")]),
    (7, "accepts True as a star rating", [("if isinstance(stars, bool) or not isinstance(stars, int)", "if not isinstance(stars, int)")]),
    (8, "applies whichever response arrives last", [("if seq != screen.search_seq:", "if False:")]),
    (9, "pastes the sort column into SQL",
     [("if sort not in SORT_COLUMNS:", "if not sort:"), ("ORDER BY {SORT_COLUMNS[sort]} {direction}", "ORDER BY {sort} {direction}")]),
    (9, "no id tie-break, so equal values come back in any order", [("{direction}, id {direction} ", "{direction} ")]),
    (10, "never gives up on a broken webhook", [('"dead" if attempts >= max_attempts else "pending"', '"pending"')]),
    (10, "registers the hook again on every start-up",
     [('    if getattr(app, "outbox_installed", False):        # idempotent: never register the hook twice\n        return\n', "")]),
]


def test_file(ticket: int) -> Path:
    return next(TESTS.glob(f"test_t{ticket:02}_*.py"))


def run_ticket(ticket: int, impl: str) -> dict:
    """Run one ticket's tests against `impl`; return passed/failed test names and failure messages."""
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "junit.xml"
        env = {**os.environ, "APP_TASKS_IMPL": impl, "PYTHONDONTWRITEBYTECODE": "1"}
        subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--color=no",
                        f"--junitxml={xml_path}", "-o", "junit_family=xunit1", str(test_file(ticket))],
                       env=env, cwd=HERE.parents[1], capture_output=True, text=True, timeout=600)
        if not xml_path.exists():
            return {"passed": [], "failed": [("collection", "the test file could not be collected")]}
        passed, failed = [], []
        for case in ET.parse(xml_path).getroot().iter("testcase"):
            name = case.get("name")
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            if problem is None and case.find("skipped") is None:
                passed.append(name)
            elif problem is not None:
                failed.append((name, (problem.get("message") or "").splitlines()[0][:160]))
    return {"passed": passed, "failed": failed}


def grade(impl: str, tickets, verbose=True) -> dict:
    report, total = {}, 0.0
    if verbose:
        print(f"Grading {impl}\n")
        print(f"{'ticket':<52} {'tests':>7} {'points':>9}  status")
    for t in tickets:
        title, weight = TICKETS[t]
        res = run_ticket(t, impl)
        n = len(res["passed"]) + len(res["failed"])
        points = round(weight * len(res["passed"]) / n, 1) if n else 0.0
        total += points
        done = not res["failed"] and n > 0
        report[f"T{t:02}"] = {"title": title, "weight": weight, "points": points, "done": done, **res}
        if verbose:
            print(f"T{t:02} {title:<48} {len(res['passed']):>3}/{n:<3} {points:>5}/{weight:<3}  "
                  f"{'DONE' if done else 'todo'}")
            for name, message in res["failed"][:6]:
                print(f"      x {name}: {message}")
            if len(res["failed"]) > 6:
                print(f"      ... and {len(res['failed']) - 6} more")
    possible = sum(TICKETS[t][1] for t in tickets)
    if verbose:
        print(f"\nScore: {round(total, 1)} / {possible}")
    return {"impl": impl, "score": round(total, 1), "possible": possible, "tickets": report}


def check(repeat: int) -> bool:
    ok = True
    print("1) Reference solution must score 100 on every run")
    for i in range(repeat):
        rep = grade("solution", TICKETS, verbose=False)
        flaky = {k: v["failed"] for k, v in rep["tickets"].items() if v["failed"]}
        print(f"   run {i + 1}: {rep['score']}/100" + (f"  FAILED {flaky}" if flaky else ""))
        ok &= rep["score"] == 100
    print("2) Untouched starter must score 0")
    rep = grade("starter", TICKETS, verbose=False)
    print(f"   {rep['score']}/100")
    ok &= rep["score"] == 0
    print(f"3) Every mutant must be caught ({len(MUTANTS)} realistic bugs)")
    source = (HERE / "solution.py").read_text()
    with tempfile.TemporaryDirectory() as tmp:
        for i, (ticket, bug, edits) in enumerate(MUTANTS, 1):
            text = source
            for old, new in edits:
                if text.count(old) != 1:
                    raise SystemExit(f"mutant {i} ({bug}): text not found exactly once in solution.py: {old!r}")
                text = text.replace(old, new)
            path = Path(tmp) / f"mutant_{i:02}.py"
            path.write_text(text)
            res = run_ticket(ticket, str(path))
            caught = bool(res["failed"])
            ok &= caught
            first = res["failed"][0][0] if caught else "-"
            print(f"   {'caught ' if caught else 'MISSED '} T{ticket:02} {bug:<58} by {first}")
    print("\nTest suite is trustworthy." if ok else "\nTest suite check FAILED.")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--impl", default="starter", help="starter (default), solution, or a path to a .py file")
    parser.add_argument("--task", type=int, action="append", choices=sorted(TICKETS))
    parser.add_argument("--json", help="also write the report to this file")
    parser.add_argument("--check", action="store_true", help="validate the tests (instructors)")
    parser.add_argument("--repeat", type=int, default=3, help="solution runs in --check (flakiness)")
    args = parser.parse_args()
    if args.check:
        sys.exit(0 if check(args.repeat) else 1)
    impl = args.impl if args.impl in ("starter", "solution") else str(Path(args.impl).resolve())
    report = grade(impl, args.task or list(TICKETS))
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
    sys.exit(0 if report["score"] == report["possible"] else 1)


if __name__ == "__main__":
    main()
