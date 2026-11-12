"""T06 - CSV export (10 points). See TICKETS.md#t06."""
import csv
import io
from urllib.parse import quote

import pytest
from conftest import book

HEADER = ["id", "passenger", "pickup", "destination", "distance_km", "fare_eur", "status", "driver"]


@pytest.fixture
def app(make_app, impl):
    app = make_app(drivers=2, rides=4)
    impl.install_t06(app)
    return app


def rows(resp):
    return list(csv.reader(io.StringIO(resp.body, newline="")))


def test_ac1_download_headers(app):
    resp = app.client.get("/api/rides/export.csv")
    assert resp.status == 200
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert resp.headers["Content-Disposition"] == 'attachment; filename="rides.csv"'


def test_ac2_one_row_per_ride_in_id_order_with_exact_columns(app):
    table = rows(app.client.get("/api/rides/export.csv"))
    assert table[0] == HEADER
    db_rows = app.db.query("SELECT * FROM rides ORDER BY id")
    assert [int(r[0]) for r in table[1:]] == [r["id"] for r in db_rows]
    first = db_rows[0]
    assert table[1][5] == f"{first['fare_cents'] / 100:.2f}" and table[1][6] == first["status"]


def test_ac3_rfc4180_line_endings_and_quoting(app):
    book(app, passenger='Smith, "Jo"')
    resp = app.client.get("/api/rides/export.csv")
    assert resp.body.endswith("\r\n") and "\r\n" in resp.body and "\n\n" not in resp.body
    assert '"Smith, ""Jo"""' in resp.body
    assert rows(resp)[-1][1] == 'Smith, "Jo"'


def test_ac4_driver_name_via_join_and_one_query(app):
    app.client.post("/api/rides/2/assign", {"driver_id": 2})
    mark = len(app.db.statements)
    table = rows(app.client.get("/api/rides/export.csv"))
    assert app.db.selects_since(mark) == 1
    by_id = {int(r[0]): r for r in table[1:]}
    assert by_id[2][7] == "Oisin" and by_id[1][7] == ""


@pytest.mark.parametrize("name", ["=HYPERLINK(\"http://x\")", "+1+1", "-2+3", "@SUM(A1)"])
def test_ac5_formula_injection_is_neutralised(app, name):
    book(app, passenger=name)
    cell = rows(app.client.get("/api/rides/export.csv"))[-1][1]
    assert cell == "'" + name


def test_ac6_status_filter_and_validation(app):
    app.client.post("/api/rides/3/cancel")
    table = rows(app.client.get("/api/rides/export.csv?status=cancelled"))
    assert [r[6] for r in table[1:]] == ["cancelled"]
    assert rows(app.client.get("/api/rides/export.csv?status=completed")) == [HEADER]
    bad = app.client.get("/api/rides/export.csv?status=" + quote("' OR 1=1 --"))
    assert bad.status == 422 and bad.body["field"] == "status"


def test_ac7_screen_receives_a_named_download(app):
    resp = app.screen.export_button.click()
    assert resp.status == 200
    filename, text = app.screen.download
    assert filename == "rides.csv" and text.startswith(",".join(HEADER))
