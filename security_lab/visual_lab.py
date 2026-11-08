#!/usr/bin/env python3
"""Colab-ready visual companion for the existing ATLAS security/cryptography labs.

Calls the ACTUAL numbered experiments, captures outcome/time, and generates:
1. observed execution chart + log for every experiment;
2. a separately labeled illustrative concept chart (NOT measured output).
Theoretical illustrations do not claim to measure security or benchmark the app.
Python 3.10+; pip install matplotlib.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    "crypto": ROOT / "security_lab" / "crypto_lab.py",
    "security": ROOT / "security_lab" / "password_storage_demo.py",
}
# Each diagram is a conceptual model: explicit axes and units; never presented as lab measurement.
# x (numeric), y (numeric) and optional z are teaching examples, not program outputs.
CONCEPTS = {
 "crypto": [
 ("SHA-256: digest bytes for varied message lengths", "Input bytes", "Digest bytes", [0,8,64,128,512], [32]*5, None),
 ("Avalanche: expected changed digest bits", "Changed input bits", "Expected changed output bits", [1,2,4,8,16], [128]*5, None),
 ("Brute force and birthday work (bits)", "Truncated hash bits", "log2 trial count", [8,16,24,32,40], [8,16,24,32,40], [4,8,12,16,20]),
 ("Toy additive checksum collisions", "Added value", "Possible offset cancel", [0,1,2,3,4], [0,1,2,3,4], [4,3,2,1,0]),
 ("CRC32: fixed checksum width", "Message bytes", "CRC32 bits", [1,8,32,128,512], [32]*5, None),
 ("SHA-256 integrity verification", "Altered payload bytes", "Expected integrity match (0/1)", [0,1,2,3,4], [1,0,0,0,0], None),
 ("Pinning: expected digest comparisons", "Dependencies checked", "SHA-256 comparisons", [1,2,3,4,5], [1,2,3,4,5], None),
 ("Prefix-MAC flaw vs HMAC", "Message variant", "Toy accepting verifiers (0/1)", [0,1,2,3,4], [1,1,1,1,1], [1,0,0,0,0]),
 ("PBKDF2: work relative to iteration count", "Iterations (thousands)", "Relative cost units", [10,50,100,200,400], [10,50,100,200,400], None),
 ("CSPRNG vs PRNG: predictability model", "Known outputs", "Toy PRNG predictability indicator", [0,156,312,468,624], [0,0,0,0,1], [0,0,0,0,0]),
 ("Certificate fingerprint size", "Certificate bytes", "SHA-256 fingerprint bits", [512,1024,2048,4096,8192], [256]*5, None),
 ("DER: nested encoded fields", "Illustrative nesting level", "Fields to inspect", [1,2,3,4,5], [1,3,5,7,9], None),
 ("RSA signature: verification condition", "Signature tampering (toy steps)", "Expected acceptance (0/1)", [0,1,2,3,4], [1,0,0,0,0], None),
 ("PKI validity criteria", "Passed required checks", "Checks still missing (of 5)", [0,1,2,3,4,5], [5,4,3,2,1,0], None),
 ("Textbook RSA: toy multiplicativity", "Illustrative factors", "Resulting product factor", [1,2,3,4,5], [1,4,9,16,25], None),
 ("RSA signature padding structure", "RSA modulus bits", "Encoded signature bytes", [1024,2048,3072,4096], [128,256,384,512], None),
 ("JAR signing: integrity checks by stage", "Verified layers", "Checks covered", [0,1,2,3,4], [0,1,2,3,4], None),
 ("Lamport signature: hash count vs digest length", "Digest bits", "Revealed blocks", [32,64,128,192,256], [32,64,128,192,256], None),
 ("One-time signature reuse: revealed secrets", "Distinct messages signed (toy)", "Maximum revealed pairs", [1,2,3,4,5], [1,1.5,1.75,1.875,1.94], None),
 ("Hybrid: two independent toy failure probabilities", "Component failure probability", "Both fail (independent toy)", [0,0.1,0.2,0.3,0.4,0.5], [0,.01,.04,.09,.16,.25], None),
 ],
 "security": [
 ("Credential storage: field lengths", "Credential field", "Illustrative bytes", [1,2,3], [16,32,4], None),
 ("Salt diversity: collision chance (toy model)", "Accounts", "Approx. collision prob × 10^6 (16-bit toy)", [2,4,8,16,32], [0.015,0.092,0.427,1.831,7.568], None),
 ("Password verification outcomes", "Test category", "Accepted (0/1)", [1,2,3,4], [1,0,0,0], None),
 ("PBKDF2 iterations and cost", "Iterations (thousands)", "Relative cost", [10,50,100,200,400], [10,50,100,200,400], None),
 ("Guessing work: toy exhaustive keyspace", "Secret length (base 10)", "log10 candidates", [2,3,4,5,6,7], [2,3,4,5,6,7], None),
 ("Dictionary search: hit position", "Wordlist size", "Worst attempts", [10,20,30,40,50], [10,20,30,40,50], None),
 ("Password policy checks: count", "Applied checks", "Cumulative controls", [1,2,3,4,5], [1,2,3,4,5], None),
 ("Plaintext absent from expected state record", "Field group", "Contains plaintext password (0/1)", [1,2,3], [0,0,0], None),
 ("Input validation outcomes", "Example case", "Accepted (0/1)", [1,2,3,4,5,6], [1,0,1,0,1,0], None),
 ("Uniqueness: duplicate attempts rejected", "Registration attempts, same email", "Expected successful registrations", [1,2,3,4,5], [1,1,1,1,1], None),
 ("RBAC: permitted actions (toy matrix)", "Role", "Allowed action count (illustrative)", [1,2,3], [2,3,2], None),
 ("Login lockout after five failures", "Failure number", "Accept login attempts (0/1)", [0,1,2,3,4,5,6], [1,1,1,1,1,0,0], None),
 ("Account enumeration: error consistency", "Identity type", "Expected distinct error strings", [1,2], [1,1], None),
 ("Login timing: illustrative risk", "Secret-check work units", "Relative work", [0,1,2,3,4,5], [0,1,2,3,4,5], [1,1,1,1,1,1]),
 ("In-memory lockout after restart", "Stage", "Failed-attempt counter (toy)", [1,2,3,4,5], [1,2,3,0,1], None),
 ("Session transitions", "Stage", "Authenticated session indicator", [1,2,3,4,5], [0,1,1,0,0], None),
 ("File tampering: accept/reject", "State file integrity", "Loaded (0/1)", [0,1], [1,0], None),
 ("Atomic write: consistent states", "Storage stage", "Consistent (0/1)", [1,2,3,4], [1,1,1,1], None),
 ("Deletion: personally identifying records (toy)", "Lifecycle stage", "Identifying records", [1,2,3,4], [1,1,0,0], None),
 ("Rehash on login: iteration migration", "Login stage", "Iterations (thousands)", [0,1,2,3], [100,100,200,200], None),
 ]
}
assert all(len(v)==20 for v in CONCEPTS.values())

def concept_chart(domain, number, folder):
    title, xlabel, ylabel, xs, ys, second = CONCEPTS[domain][number-1]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(xs, ys, "o-", label="illustrative series A")
    if second is not None:
        ax.plot(xs, second, "s--", label="illustrative series B")
        ax.legend()
    ax.set(xlabel=xlabel, ylabel=ylabel, title=f"{domain.title()} E{number:02}: {title}")
    ax.grid(alpha=.25)
    fig.text(.5, .005, "CONCEPTUAL MODEL — not measurements from the ATLAS experiment",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0,.035,1,1))
    fig.savefig(folder / f"{number:02}_concept.png", dpi=160)
    plt.close(fig)
    with (folder / f"{number:02}_concept.csv").open("w", newline="", encoding="utf8") as f:
        writer=csv.writer(f)
        writer.writerow([xlabel,"illustrative_A","illustrative_B" if second is not None else ""])
        for k, x in enumerate(xs):
            writer.writerow([x,ys[k],second[k] if second is not None else ""])

def observed_chart(domain, number, seconds, ok, folder):
    fig, axs = plt.subplots(1, 2, figsize=(8, 3.6))
    axs[0].bar(["Real run"], [seconds], color="#2865A7")
    axs[0].set(ylabel="Elapsed seconds (measured)", title="Actual script execution")
    axs[1].bar(["Exit status"], [int(ok)], color="#35845B" if ok else "#BA4444")
    axs[1].set(ylim=(0,1.15),ylabel="Pass=1 / Fail=0",title="Actual process result")
    fig.suptitle(f"{domain.title()} E{number:02} — OBSERVED lab execution")
    fig.tight_layout()
    fig.savefig(folder / f"{number:02}_observed.png", dpi=160)
    plt.close(fig)

def run_one(domain, number, output, timeout=300):
    if domain not in SCRIPTS or not 1 <= number <= 20: raise ValueError("Unknown lab")
    folder = Path(output) / domain
    folder.mkdir(parents=True, exist_ok=True)
    command=[sys.executable,str(SCRIPTS[domain]),"-e",str(number)]
    start=time.perf_counter()
    try:
        p=subprocess.run(command,cwd=str(ROOT),capture_output=True,text=True,
                         encoding="utf8",errors="replace",timeout=timeout)
        code=p.returncode
        transcript=p.stdout + ("\n--- STDERR ---\n"+p.stderr if p.stderr else "")
    except subprocess.TimeoutExpired as error:
        code=124
        transcript=f"Timed out after {timeout}s\n{error}"
    elapsed=time.perf_counter()-start
    ok=code==0
    (folder/f"{number:02}_run.log").write_text(transcript,encoding="utf8")
    observed_chart(domain,number,elapsed,ok,folder)
    concept_chart(domain,number,folder)
    data={"domain":domain,"experiment":number,"success":ok,"exit_code":code,
          "elapsed_seconds":round(elapsed,5),"illustration_is_measurement":False}
    (folder/f"{number:02}_summary.json").write_text(json.dumps(data,indent=2),encoding="utf8")
    return data

def run_many(domains=("crypto","security"), numbers=range(1,21),
             output="security_lab/results", timeout=300):
    output=Path(output)
    records=[]
    for domain in domains:
        for n in numbers:
            data=run_one(domain,n,output,timeout)
            records.append(data)
            print(f"{domain} E{n:02}: {'PASS' if data['success'] else 'FAIL'} "
                  f"({data['elapsed_seconds']:.3f}s)",flush=True)
    output.mkdir(parents=True,exist_ok=True)
    with (output/"summary.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    fig, ax = plt.subplots(figsize=(max(10,len(records)*.29),4.5))
    labels=[f"{r['domain'][0]}{r['experiment']:02}" for r in records]
    ax.bar(labels,[r["elapsed_seconds"] for r in records],
           color=["#35845B" if r["success"] else "#BA4444" for r in records])
    ax.set(ylabel="Measured execution seconds",title="Real ATLAS experiment runtime — green passed / red failed")
    ax.tick_params(axis="x",labelrotation=70)
    fig.tight_layout()
    fig.savefig(output/"all_runtime.png",dpi=160)
    plt.close(fig)
    return records

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--domain",choices=("crypto","security","both"),default="both")
    p.add_argument("--experiment",type=int,action="append",choices=range(1,21))
    p.add_argument("--output",default="security_lab/results")
    p.add_argument("--timeout",type=int,default=300)
    args=p.parse_args()
    domains=("crypto","security") if args.domain=="both" else (args.domain,)
    records=run_many(domains,args.experiment or range(1,21),args.output,args.timeout)
    failed=[f"{r['domain']} {r['experiment']}" for r in records if not r["success"]]
    print(f"Results: {len(records)} run; {len(failed)} failed. Output: {args.output}")
    if failed:
        print("FAILED:",", ".join(failed))
        raise SystemExit(1)

if __name__=="__main__": main()
