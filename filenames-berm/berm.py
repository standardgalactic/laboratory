#!/usr/bin/env python3
"""berm: a status board for a directory whose filenames carry admissibility.

Filenames follow  STATUS - Title.ext , for example
    OPEN - Build Proof of Concept Reknotting Model.md
The first line of the body may restate the status and name dependencies:
    Status: BLOCKED; depends: Build Proof of Concept Reknotting Model

Commands
    board   [DIR]            group files by status
    next    [DIR]            files whose status licenses work now, not blocked
    stale   [DIR]            names whose status disagrees with the body header
    check   [DIR] [--staged] validate the namespace (or only staged changes)
    audit   [DIR]            flag promotions past VERIFY made by the producer
    move    FILE STATUS      rename to a new status (uses git mv when in a repo)
    history [DIR]            status transitions recorded by git renames

Header fields after the status are free-form  key: value  pairs. Recognized:
    depends: Title, Title    owner: name    lease: YYYY-MM-DD
The current user for leases is $BERM_USER, else git config user.name.
"""
import datetime
import os
import re
import subprocess
import sys

VOCAB = {
    "OPEN": "problem posed, approach not fixed: propose or attempt",
    "TODO": "task specified: execute it",
    "EXPERIMENT": "claim is testable: run the test, record the result",
    "VERIFY": "result exists, unchecked: check it, do not build on it",
    "EXTEND": "result checked: build on it",
    "SYNTHESIZE": "parts exist: combine them",
    "REVIEW": "draft complete: critique it, do not rewrite it",
    "META": "about the corpus itself: inspect other files",
    "BLOCKED": "waiting on a dependency: resolve that first",
    "ARCHIVE": "settled: read only",
}
ACTIONABLE = {"OPEN", "TODO", "EXPERIMENT", "VERIFY", "EXTEND",
              "SYNTHESIZE", "REVIEW", "META"}
# Statuses at which a dependency counts as satisfied.
SATISFIES = {"EXTEND", "REVIEW", "ARCHIVE"}
NAME_RE = re.compile(r"^([A-Z]+) - (.+?)(\.[A-Za-z0-9]+)?$")
HEAD_RE = re.compile(r"^Status:\s*([A-Z]+)\s*(?:;\s*(.*))?$")


def parse_name(fn):
    m = NAME_RE.match(fn)
    if not m or m.group(1) not in VOCAB:
        return None
    return m.group(1), m.group(2)


def read_fields(path):
    """Return (status, fields) from the header line, or (None, {})."""
    try:
        with open(path, encoding="utf-8") as f:
            line = f.readline().strip()
    except (OSError, UnicodeDecodeError):
        return None, {}
    m = HEAD_RE.match(line)
    if not m:
        return None, {}
    fields = {}
    for part in (m.group(2) or "").split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            fields[key.strip().lower()] = value.strip()
    return m.group(1), fields


def read_head(path):
    status, fields = read_fields(path)
    deps = [d.strip() for d in fields.get("depends", "").split(",")
            if d.strip()]
    return status, deps


def current_user(d):
    user = os.environ.get("BERM_USER")
    if user:
        return user
    r = subprocess.run(["git", "-C", d, "config", "user.name"],
                       capture_output=True, text=True)
    return r.stdout.strip() or None


def lease_state(fields, user, today=None):
    """None if unleased; 'mine', 'held', or 'expired' otherwise."""
    owner, lease = fields.get("owner"), fields.get("lease")
    if not owner:
        return None
    if lease:
        try:
            until = datetime.date.fromisoformat(lease)
        except ValueError:
            return "held"
        if until < (today or datetime.date.today()):
            return "expired"
    return "mine" if owner == user else "held"


def scan(d):
    items = []
    for fn in sorted(os.listdir(d)):
        p = parse_name(fn)
        if p:
            items.append({"file": fn, "status": p[0], "title": p[1],
                          "path": os.path.join(d, fn)})
    return items


def board(d):
    items = scan(d)
    for st in VOCAB:
        group = [i for i in items if i["status"] == st]
        if group:
            print(f"{st}  ({VOCAB[st]})")
            for i in group:
                print(f"    {i['title']}")


def next_items(d, verify=True):
    """Name-indexed, body-verified: read the listing, open only candidates."""
    items = scan(d)
    by_title = {i["title"]: i for i in items}
    user = current_user(d)
    opened, out, unblock = 0, [], []
    for i in items:
        if i["status"] == "BLOCKED" and verify:
            opened += 1
            _, deps = read_head(i["path"])
            if deps and all(by_title.get(dp, {}).get("status") in SATISFIES
                            for dp in deps):
                unblock.append(i)
            continue
        if i["status"] not in ACTIONABLE:
            continue
        if verify:
            opened += 1
            head, fields = read_fields(i["path"])
            deps = [x.strip() for x in fields.get("depends", "").split(",")
                    if x.strip()]
            status = head or i["status"]
            if status not in ACTIONABLE:
                continue
            ls = lease_state(fields, user)
            if ls == "held":
                continue
            if ls:
                i = dict(i, lease=f"{ls}: {fields.get('owner')}")
            unmet = [dp for dp in deps
                     if by_title.get(dp, {}).get("status") not in SATISFIES]
            if unmet:
                continue
            i = dict(i, effective=status)
        out.append(i)
    return out, unblock, opened


def stale(d):
    bad = []
    for i in scan(d):
        head, _ = read_head(i["path"])
        if head and head != i["status"]:
            bad.append((i["file"], head))
    return bad


def integrity(d):
    """Return corpus-level defects that a name-indexed query cannot detect."""
    items = scan(d)
    by_title = {}
    problems = []
    for i in items:
        by_title.setdefault(i["title"], []).append(i)
        head, deps = read_head(i["path"])
        if head is None:
            problems.append(f"NO HEADER: {i['file']}")
        elif head != i["status"]:
            problems.append(
                f"STALE: {i['file']} (body says {head})")
        for dep in deps:
            if dep == i["title"]:
                problems.append(f"SELF DEPENDENCY: {i['file']}")
    for title, group in by_title.items():
        if len(group) > 1:
            problems.append(
                f"DUPLICATE TITLE: {title} ({', '.join(x['file'] for x in group)})")
    titles = set(by_title)
    graph = {}
    for i in items:
        _, deps = read_head(i["path"])
        graph[i["title"]] = [x for x in deps if x in titles and x != i["title"]]
        for dep in deps:
            if dep not in titles:
                problems.append(f"MISSING DEPENDENCY: {i['file']} -> {dep}")
    for cycle in find_cycles(graph):
        problems.append("DEPENDENCY CYCLE: " + " -> ".join(cycle))
    return problems


def find_cycles(graph):
    """Each elementary cycle reported once, rotated to its least title."""
    seen, cycles = set(), []

    def walk(node, path, onpath):
        for nxt in graph.get(node, []):
            if nxt in onpath:
                cyc = path[path.index(nxt):]
                k = cyc.index(min(cyc))
                key = tuple(cyc[k:] + cyc[:k])
                if key not in seen:
                    seen.add(key)
                    cycles.append(list(key) + [key[0]])
            elif len(path) < len(graph):
                walk(nxt, path + [nxt], onpath | {nxt})

    for start in sorted(graph):
        walk(start, [start], {start})
    return cycles


def staged_files(d):
    r = subprocess.run(["git", "-C", d, "diff", "--cached", "--name-only",
                        "--relative", "--diff-filter=ACMR"],
                       capture_output=True, text=True)
    return {os.path.basename(x) for x in r.stdout.splitlines() if x}


def integrity_staged(d):
    """Incremental check at commit time: split representations among
    staged files, and dependencies they name that do not exist."""
    names = staged_files(d)
    titles = {i["title"] for i in scan(d)}
    problems = []
    for i in scan(d):
        if i["file"] not in names:
            continue
        head, deps = read_head(i["path"])
        if head is None:
            problems.append(f"NO HEADER: {i['file']}")
        elif head != i["status"]:
            problems.append(f"STALE: {i['file']} (body says {head})")
        for dep in deps:
            if dep not in titles:
                problems.append(f"MISSING DEPENDENCY: {i['file']} -> {dep}")
    return problems


def transitions(d):
    """(date, author, title, old, new) for every status rename in git."""
    out = subprocess.run(
        ["git", "-C", d, "log", "--reverse", "--format=@%ad|%an",
         "--date=short", "--name-status", "-M"],
        capture_output=True, text=True).stdout
    date = author = None
    rows = []
    for line in out.splitlines():
        if line.startswith("@"):
            date, author = line[1:].split("|", 1)
        elif line.startswith("R"):
            _, old, new = line.split("\t")
            a = parse_name(os.path.basename(old))
            b = parse_name(os.path.basename(new))
            if a and b and a[1] == b[1]:
                rows.append((date, author, a[1], a[0], b[0]))
    return rows


def audit(d):
    """Flag promotions out of VERIFY made by whoever moved the item into it."""
    into_verify, flags = {}, []
    for date, author, title, old, new in transitions(d):
        if new == "VERIFY":
            into_verify[title] = author
        elif old == "VERIFY" and new in {"EXTEND", "SYNTHESIZE", "REVIEW",
                                         "ARCHIVE"}:
            if into_verify.get(title) == author:
                flags.append(f"SELF-PROMOTION: {title}: VERIFY -> {new} "
                             f"by {author} on {date}")
    return flags


def in_git(d):
    return subprocess.run(["git", "-C", d, "rev-parse"],
                          capture_output=True).returncode == 0


def move(path, new):
    d, fn = os.path.split(path)
    d = d or "."
    p = parse_name(fn)
    if not p or new not in VOCAB:
        sys.exit(f"cannot move {fn!r} to {new!r}")
    ext = os.path.splitext(fn)[1]
    target = os.path.join(d, f"{new} - {p[1]}{ext}")
    # keep the body header in step with the name
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    m = HEAD_RE.match(lines[0].strip()) if lines else None
    if m:
        fields = m.group(2)
        lines[0] = f"Status: {new}" + (f"; {fields}" if fields else "")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    if in_git(d):
        subprocess.run(["git", "-C", d, "mv", fn, os.path.basename(target)],
                       check=True)
    else:
        os.rename(path, target)
    return target


def history(d):
    for date, author, title, old, new in transitions(d):
        print(f"{date}  {title}: {old} -> {new}  ({author})")


def main(argv):
    if not argv or argv[0] not in {"board", "next", "stale", "check", "audit",
                                   "move", "history"}:
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    if cmd == "board":
        board(rest[0] if rest else ".")
    elif cmd == "next":
        items, unblock, opened = next_items(rest[0] if rest else ".")
        for i in items:
            st = i.get("effective", i["status"])
            note = f"   (name says {i['status']})" if st != i["status"] else ""
            if i.get("lease"):
                note += f"   [{i['lease']}]"
            print(f"{st:10s} {i['title']}{note}")
        for i in unblock:
            print(f"UNBLOCK    {i['title']}   (every dependency satisfied)")
        print(f"({opened} of {len(scan(rest[0] if rest else '.'))} files opened)")
    elif cmd == "stale":
        for fn, head in stale(rest[0] if rest else "."):
            print(f"{fn}  body says {head}")
    elif cmd == "check":
        staged = "--staged" in rest
        rest = [x for x in rest if x != "--staged"]
        d = rest[0] if rest else "."
        problems = integrity_staged(d) if staged else integrity(d)
        if problems:
            print("\n".join(problems))
            raise SystemExit(1)
        n = len(staged_files(d)) if staged else len(scan(d))
        print(f"OK: {n} {'staged' if staged else 'status-bearing'} files")
    elif cmd == "audit":
        flags = audit(rest[0] if rest else ".")
        print("\n".join(flags) if flags else "OK: no self-promotions")
        if flags:
            raise SystemExit(1)
    elif cmd == "move":
        print(move(rest[0], rest[1]))
    elif cmd == "history":
        history(rest[0] if rest else ".")


if __name__ == "__main__":
    main(sys.argv[1:])
