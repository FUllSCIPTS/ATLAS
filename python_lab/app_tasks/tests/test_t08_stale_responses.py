"""T08 - Ignore out-of-order search responses (8 points). See TICKETS.md#t08.

The server is slowed down (or broken) per search text, so the outcome never depends on
which request happens to reach the server first.
"""
import time

import pytest
from conftest import ai, book


class Unavailable(ai.AppError):
    status = 503


def network(app, delays=None, failures=()):
    """Delay GET /api/rides by search text (seconds) and/or answer 503 for some texts."""
    delays = delays or {}

    def hook(request):
        if request.method == "GET" and request.path == "/api/rides":
            text = request.query.get("q", [""])[0]
            time.sleep(delays.get(text, 0))
            if text in failures:
                raise Unavailable("search is down")

    app.server.before_request.append(hook)


@pytest.fixture
def app(make_app, impl):
    app = make_app(drivers=1)
    for name in ("Annie Air", "Andy Air", "Kate Kent"):
        book(app, passenger=name, destination="Douglas")
    impl.install_t08(app)
    return app


def ids_for(app, text):
    return [r["id"] for r in app.client.get(f"/api/rides?q={text}&limit=100").body["items"]]


def test_ac1_click_returns_immediately_with_a_future(app):
    network(app, {"Air": 0.2})
    future = app.screen.live_search_button.click("Air")
    assert hasattr(future, "result") and not future.done()
    assert app.screen.search_status == "Searching..."
    app.screen.wait()
    assert app.screen.search_status == "2 results"


def test_ac2_slow_old_response_never_overwrites_newer_one(app):
    s = app.screen
    network(app, {"Air": 0.3})                                         # the FIRST search is slow
    s.live_search_button.click("Air")
    s.live_search_button.click("Kent")
    s.wait()
    assert [r["id"] for r in s.table] == ids_for(app, "Kent")
    assert s.stale_responses_ignored == 1 and s.search_status == "1 results"


def test_ac3_in_order_responses_are_all_applied(app):
    s = app.screen
    s.live_search_button.click("Air"); s.wait()
    assert [r["id"] for r in s.table] == ids_for(app, "Air")
    s.live_search_button.click("Kent"); s.wait()
    assert [r["id"] for r in s.table] == ids_for(app, "Kent") and s.stale_responses_ignored == 0


def test_ac4_errors_only_count_for_the_newest_request(app):
    s = app.screen
    network(app, {"Air": 0.3}, failures={"Air"})                       # slow AND failing, but stale
    s.live_search_button.click("Air")
    s.live_search_button.click("Kent")
    s.wait()
    assert s.banner == "" and [r["id"] for r in s.table] == ids_for(app, "Kent")
    network(app, failures={"Andy"})                                    # the newest one fails
    s.live_search_button.click("Andy"); s.wait()
    assert s.banner.startswith("Something went wrong") and s.search_status == ""
    assert s.stale_responses_ignored == 1


def test_ac5_many_quick_searches_end_on_the_last(app):
    s = app.screen
    network(app, {"A": 0.3, "Ai": 0.2, "Air": 0.1})
    for text in ("A", "Ai", "Air", "Kent"):
        s.live_search_button.click(text)
    s.wait()
    assert [r["id"] for r in s.table] == ids_for(app, "Kent")
    assert s.stale_responses_ignored == 3
