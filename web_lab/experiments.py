"""Reproducible 12-part HTTP/database experiments with measured CSV + PNG graphs.

No synthetic measurements are invented: each lab calls FastAPI TestClient and
a temporary SQLite file. Metrics measure actual response codes, rows or timings.
Run python -m web_lab.experiments --all --output web_lab/results
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import tempfile
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi.testclient import TestClient

from web_lab.app import create_app


def payload(i: int):
    return {"passenger": f"Student {i}", "pickup": "UCC", "destination": "Station",
            "distance_km": float(i % 20 + 1), "request_key": f"lab-{i:08}"}


TITLES = {
 1: "HTML form and static assets",
 2: "CSS responsive style served",
 3: "JavaScript fetch code served",
 4: "OpenAPI documentation and health",
 5: "POST creates SQL rows",
 6: "GET list and filter",
 7: "Idempotent repeat request",
 8: "Validation: invalid distance",
 9: "SQL injection string kept as data",
10: "PATCH state transitions",
11: "DELETE and 404 status",
12: "HTTP request latency versus stored rows",
}


def run(number: int, sizes=(1, 2, 4, 8, 16)):
    if number not in TITLES: raise ValueError("Unknown experiment")
    rows = []
    with tempfile.TemporaryDirectory() as td:
        with TestClient(create_app(Path(td)/"rides.sqlite")) as client:
            index = 0
            for n in sizes:
                if number in (1, 2, 3, 4):
                    path = ["/", "/static/style.css", "/static/app.js", "/openapi.json"][number-1]
                    response = client.get(path)
                    assert response.status_code == 200
                    rows.append((n, response.status_code, len(response.content)))
                elif number == 5:
                    for _ in range(n):
                        index += 1
                        response = client.post("/api/rides", json=payload(index))
                        assert response.status_code == 201
                    rows.append((n, len(client.get("/api/rides").json()), 201))
                elif number == 6:
                    for _ in range(n):
                        index += 1
                        client.post("/api/rides", json=payload(index))
                    data = client.get("/api/rides?status=requested").json()
                    rows.append((n, len(data), len(client.get("/api/rides").json())))
                elif number == 7:
                    index += 1
                    data = payload(index)
                    first = client.post("/api/rides", json=data)
                    for _ in range(n):
                        follow = client.post("/api/rides", json=data)
                        assert follow.json()["id"] == first.json()["id"]
                    rows.append((n, n, len(client.get("/api/rides").json())))
                elif number == 8:
                    failures = sum(client.post("/api/rides",json={**payload(index+j+1),"distance_km":-1}).status_code==422 for j in range(n))
                    rows.append((n, failures, len(client.get("/api/rides").json())))
                elif number == 9:
                    for _ in range(n):
                        index += 1
                        data = payload(index)
                        data["pickup"] = "x'); DROP TABLE rides; --"
                        assert client.post("/api/rides",json=data).status_code == 201
                    rows.append((n,len(client.get("/api/rides").json()),200))
                elif number == 10:
                    index += 1
                    ride = client.post("/api/rides",json=payload(index)).json()
                    first = client.patch(f"/api/rides/{ride['id']}",json={"status":"assigned"})
                    second = client.patch(f"/api/rides/{ride['id']}",json={"status":"completed"})
                    failed = client.patch(f"/api/rides/{ride['id']}",json={"status":"requested"})
                    assert (first.status_code,second.status_code,failed.status_code)==(200,200,409)
                    rows.append((n,2,1))
                elif number == 11:
                    index += 1
                    ride = client.post("/api/rides",json=payload(index)).json()
                    deleted = client.delete(f"/api/rides/{ride['id']}")
                    missing = client.get(f"/api/rides/{ride['id']}")
                    assert (deleted.status_code,missing.status_code)==(204,404)
                    rows.append((n,204,404))
                else:
                    for _ in range(n):
                        index += 1
                        client.post("/api/rides",json=payload(index))
                    samples=[]
                    for _ in range(9):
                        start=time.perf_counter()
                        result=client.get("/api/rides")
                        assert result.status_code == 200
                        samples.append((time.perf_counter()-start)*1000)
                    rows.append((len(result.json()),statistics.median(samples),statistics.pstdev(samples)))
    return rows


def draw(number, rows, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    unit = "milliseconds" if number == 12 else "observed values (see legend)"
    labels = ("median HTTP ms", "stdev HTTP ms") if number==12 else ("result A", "result B")
    path=output/f"experiment_{number:02}"
    with path.with_suffix(".csv").open("w",newline="") as f:
        writer=csv.writer(f);writer.writerow(["input_size",*labels]);writer.writerows(rows)
    path.with_suffix(".json").write_text(json.dumps({"title":TITLES[number],"rows":rows,
                                                     "metric":unit},indent=2))
    fig,ax=plt.subplots(figsize=(8,4.5))
    for col,label in enumerate(labels,1):
        ax.plot([r[0] for r in rows],[r[col] for r in rows],marker="o",label=label)
    ax.set(xlabel="Input size / workload",ylabel=unit,title=f"Web lab {number:02}: {TITLES[number]}")
    ax.grid(alpha=.25);ax.legend()
    fig.tight_layout();fig.savefig(path.with_suffix(".png"),dpi=150);plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--all",action="store_true")
    parser.add_argument("--experiment",type=int,choices=range(1,13))
    parser.add_argument("--output",default="web_lab/results")
    args=parser.parse_args()
    targets=list(TITLES) if args.all else [args.experiment] if args.experiment else []
    for n in targets:
        rows=run(n);draw(n,rows,args.output)
        print(f"W{n:02}: {TITLES[n]} -> {args.output}")
    if not targets:parser.print_help()


if __name__=="__main__":main()
