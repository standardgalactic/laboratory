"""Inspection cost and error for status-bearing filenames.

A corpus of N items, each with a true status (in the body) and a name status.
A fraction p of names is stale, either lagging (the name still shows the
previous lifecycle state) or leading (renamed before the work was done).

Strategies for the query "what may be worked on now, and how":
  opaque   names carry no status; open every file
  trust    act on names alone; open nothing
  indexed  read names, open only candidates to confirm (berm next)

Reported per strategy: files opened, recall of the truly actionable set,
and premature licenses acted on (the name licenses building on a result
that the body says is not yet checked).
"""
import random

NEXT = {"OPEN": ["TODO", "EXPERIMENT"], "TODO": ["VERIFY"],
        "EXPERIMENT": ["VERIFY"], "VERIFY": ["EXTEND"],
        "EXTEND": ["SYNTHESIZE", "REVIEW"], "SYNTHESIZE": ["REVIEW"],
        "REVIEW": ["ARCHIVE"], "ARCHIVE": [], "BLOCKED": ["OPEN"],
        "META": []}
PREV = {s: [p for p, ns in NEXT.items() if s in ns] for s in NEXT}
ORDER = ["BLOCKED", "OPEN", "TODO", "EXPERIMENT", "VERIFY", "EXTEND",
         "SYNTHESIZE", "REVIEW", "ARCHIVE"]
RANK = {s: i for i, s in enumerate(ORDER)}
ACTIONABLE = {"OPEN", "TODO", "EXPERIMENT", "VERIFY", "EXTEND",
              "SYNTHESIZE", "REVIEW", "META"}
BUILD_ON = {"EXTEND", "SYNTHESIZE"}          # licenses building on a result
UNCHECKED = {"OPEN", "TODO", "EXPERIMENT", "VERIFY"}
WEIGHTS = {"OPEN": 12, "TODO": 8, "EXPERIMENT": 6, "VERIFY": 6, "EXTEND": 6,
           "SYNTHESIZE": 3, "REVIEW": 4, "META": 3, "BLOCKED": 6,
           "ARCHIVE": 6}


def corpus(n, p, mode, rng):
    pop = list(WEIGHTS)
    w = [WEIGHTS[s] for s in pop]
    items = []
    for _ in range(n):
        true = rng.choices(pop, w)[0]
        name = true
        if rng.random() < p:
            cand = PREV[true] if mode == "lag" else NEXT[true]
            if cand:
                name = rng.choice(cand)
        items.append((name, true))
    return items


QUERIES = {"next": ACTIONABLE, "check": {"VERIFY"}, "build": BUILD_ON}


def evaluate(items, strategy, target):
    truth = {i for i, (_, t) in enumerate(items) if t in target}
    if strategy == "opaque":
        return len(items), 1.0, 0
    cands = {i for i, (nm, _) in enumerate(items) if nm in target}
    if strategy == "trust":
        got = cands
        premature = sum(1 for i in got
                        if items[i][0] in BUILD_ON and items[i][1] in UNCHECKED)
        opened = 0
    else:  # indexed: open candidates, keep those the body confirms
        got = {i for i in cands if items[i][1] in target}
        premature = 0
        opened = len(cands)
    recall = len(got & truth) / len(truth) if truth else 1.0
    return opened, recall, premature


def run(n=60, trials=2000, seed=7):
    rng = random.Random(seed)
    rows = []
    for q, target in QUERIES.items():
        for mode in ("lag", "lead"):
            for p in (0.0, 0.2):
                acc = {s: [0, 0, 0] for s in ("opaque", "trust", "indexed")}
                for _ in range(trials):
                    items = corpus(n, p, mode, rng)
                    for s in acc:
                        o, r, pm = evaluate(items, s, target)
                        acc[s][0] += o; acc[s][1] += r; acc[s][2] += pm
                for s, (o, r, pm) in acc.items():
                    rows.append((q, mode, p, s, o / trials, r / trials,
                                 pm / trials))
    return rows


if __name__ == "__main__":
    print(f"{'query':6s} {'stale':5s} {'p':>5s} {'strategy':9s} "
          f"{'opened':>7s} {'recall':>7s} {'premature':>10s}")
    for q, mode, p, s, o, r, pm in run():
        if p == 0.0 and mode == "lead":
            continue
        tag = "none" if p == 0.0 else mode
        print(f"{q:6s} {tag:5s} {p:5.2f} {s:9s} {o:7.1f} {r:7.3f} "
              f"{pm:10.2f}")
