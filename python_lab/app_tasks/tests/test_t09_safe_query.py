"""T09 - Sorting and filtering without SQL injection (8 points). See TICKETS.md#t09."""
from urllib.parse import quote

import pytest


@pytest.fixture
def app(make_app, impl):
    app = make_app(drivers=3, rides=40)
    for ride_id in range(1, 11):
        app.client.post(f"/api/rides/{ride_id}/cancel")
    impl.install_t09(app)
    return app


def reference(app, statuses=None, lo=None, hi=None, sort="id", order="asc", limit=20):
    rows = app.db.query("SELECT * FROM rides")
    rows = [r for r in rows if (not statuses or r["status"] in statuses)
            and (lo is None or r["fare_cents"] >= lo) and (hi is None or r["fare_cents"] <= hi)]
    rows.sort(key=lambda r: (r[sort], r["id"]), reverse=order == "desc")
    return [r["id"] for r in rows[:limit]], len(rows)


def get(app, query):
    return app.client.get("/api/rides/query?" + quote(query, safe="=&,"))


def test_ac1_defaults_id_ascending_limit_20(app):
    resp = get(app, "")
    ids, total = reference(app)
    assert resp.status == 200 and [r["id"] for r in resp.body["items"]] == ids and resp.body["total"] == total == 40


@pytest.mark.parametrize("sort", ["id", "fare_cents", "distance_km", "passenger"])
@pytest.mark.parametrize("order", ["asc", "desc"])
def test_ac2_sorting_matches_reference_with_id_tiebreak(app, sort, order):
    resp = get(app, f"sort={sort}&order={order}&limit=100")
    assert [r["id"] for r in resp.body["items"]] == reference(app, sort=sort, order=order, limit=100)[0]


def test_ac3_status_and_fare_filters_combine(app):
    resp = get(app, "status=requested,cancelled&min_fare=800&max_fare=2000&sort=fare_cents&limit=100")
    ids, total = reference(app, {"requested", "cancelled"}, 800, 2000, "fare_cents", limit=100)
    assert [r["id"] for r in resp.body["items"]] == ids and resp.body["total"] == total


def test_ac4_total_counts_all_matches_not_just_the_page(app):
    resp = get(app, "status=requested&limit=5")
    assert len(resp.body["items"]) == 5 and resp.body["total"] == 30


@pytest.mark.parametrize("query, field", [
    ("sort=id;DROP TABLE rides", "sort"), ("sort=(SELECT 1)", "sort"), ("sort=fare_cents&order=sideways", "order"),
    ("order=desc,id", "order"), ("status=requested,' OR 1=1--", "status"), ("status=", "status"),
    ("min_fare=abc", "min_fare"), ("min_fare=-1", "min_fare"), ("min_fare=900&max_fare=100", "min_fare"),
    ("limit=0", "limit"), ("limit=101", "limit")])
def test_ac5_bad_parameters_are_422_and_change_nothing(app, query, field):
    resp = get(app, query)
    assert resp.status == 422 and resp.body["field"] == field
    assert app.db.count("rides") == 40


def test_ac6_values_are_bound_parameters_not_sql_text(app, monkeypatch):
    calls, real_query = [], app.db.query

    def recording_query(sql, params=()):
        calls.append((sql, tuple(params)))
        return real_query(sql, params)

    monkeypatch.setattr(app.db, "query", recording_query)
    assert get(app, "sort=fare_cents&order=desc&status=requested&min_fare=1&max_fare=99999").status == 200
    assert calls, "use app.db.query(sql, params)"
    for sql, params in calls:
        assert "requested" not in sql and "99999" not in sql            # values never pasted into SQL
    assert any("requested" in params and 99999 in params for _, params in calls)
