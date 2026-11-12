# App-building tasks — graded, like real tickets

[Tickets (the specification)](TICKETS.md) · [Your file: `starter.py`](starter.py) · [Acceptance tests](tests/) · [Autograder](grade.py) · [Guide, Part IV](../../docs/PYTHON_PROGRAMMING.md#part-iv--graded-app-building-tasks)

Part III's labs *show* how a button click travels to the database and back. This part asks you to **build** features into the same running app, the way a developer on a team would. You get a ticket, implement it, and an autograder runs the acceptance tests.

```
python_lab/app_tasks/
├── TICKETS.md     10 tickets: user story, contract, numbered acceptance criteria, definition of done
├── starter.py     your work: install_t01 ... install_t10 (all raise NotImplementedError)
├── solution.py    reference solution (instructors; compare after you finish)
├── grade.py       autograder: score per ticket, failing criteria, --check for the suite itself
└── tests/         123 acceptance tests, one file per ticket, test_acN_... = criterion N
```

## For students

~~~bash
python -m pip install pytest matplotlib
python python_lab/app_tasks/grade.py --task 1         # start with T01
python python_lab/app_tasks/grade.py                  # all tickets -> score / 100
python python_lab/app_tasks/grade.py --impl my_copy.py --json report.json
~~~

Sample output:

~~~text
T01 Delete a cancelled ride                            5/9     4.4/8    todo
      x test_ac1_delete_cancelled_ride_returns_204_and_removes_row_and_audit: AssertionError: assert (500 == 204)
      x test_ac4_second_delete_is_404: AssertionError: assert 500 == 204
      x test_ac5_screen_removes_row_only_after_204: AssertionError: assert (500 == 204)
      x test_ac7_delete_is_atomic_and_never_500: AssertionError: assert 500 == 204
~~~

Every cancelled ride has an audit row, so a 500 on every delete means the delete broke the foreign key: the audit rows have to be deleted first, in the same transaction. Reading failing acceptance tests like this is the core skill.

**Order.** T01, T02, T06 and T09 are a good warm-up. T03 then T04 (authentication, then authorisation). T05, T07, T08 and T10 involve concurrency, schema changes, asynchronous UI and reliable messaging. Expect 10–20 hours in total.

**Rules.** Don't edit `app_integration.py` or the tests. Use bound parameters for every SQL value. Writes that belong together go in one transaction. Never trust the client.

## For instructors

~~~bash
python python_lab/app_tasks/grade.py --check          # about 1 minute
~~~

`--check` validates the grading itself:

1. The reference solution scores **100/100** on repeated runs (no flaky tests).
2. The untouched starter scores **0/100**.
3. **21 mutants** are each caught by their ticket's tests. A mutant is the solution with one realistic bug: plaintext passwords, an error message that reveals whether a user exists, trusting a role sent by the client, sessions that never expire, CSV formula injection, a sort column pasted into SQL, an out-of-order search response being applied, a migration re-run on start-up, a webhook retried forever, and so on.

Tests use injected clocks and per-request delays instead of real waiting or arrival order, so results are deterministic. The full suite takes about 6 seconds.

**Assessment.** Score = Σ weight × passed/total per ticket (see `grade.py --json`). For a viva, ask the student to explain one design decision per ticket (for example: why 401 and not 403, why a conditional `UPDATE` for ratings, why the outbox row shares the transaction).
