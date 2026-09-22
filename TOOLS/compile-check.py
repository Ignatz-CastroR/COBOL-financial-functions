#!/usr/bin/env python3
"""
compile_check.py

Walks SRC/, extracts each COBOL file's FUNCTION-ID declarations and its
REPOSITORY paragraph's declared dependencies, builds the resulting
call graph, topologically sorts it, and compiles every file with
GnuCOBOL in dependency order: leaves first, composites after the
functions they call have already been proven to compile.

If a file fails to compile, every file that transitively depends on it
is reported as SKIPPED rather than attempted, since it would fail to
link regardless. This keeps the failure report focused on the actual
root cause instead of a wall of downstream noise.

Usage:
    python3 TOOLS/compile_check.py
"""

import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "SRC"

FUNCTION_ID_RE = re.compile(
    r"FUNCTION-ID\.\s+([A-Za-z0-9\-]+)", re.IGNORECASE
)
REPOSITORY_BLOCK_RE = re.compile(
    r"REPOSITORY\.(.*?)(?:\.\s*\n\s*\n|PROCEDURE\s+DIVISION)",
    re.IGNORECASE | re.DOTALL,
)
FUNCTION_NAME_RE = re.compile(
    r"FUNCTION\s+([A-Za-z0-9\-]+)", re.IGNORECASE
)


def find_cobol_files():
    return sorted(SRC_ROOT.rglob("*.cbl"))


def parse_file(path):
    """Return [list of function names declared in this file],
    [set of function names this file's REPOSITORY paragraph declares
    as callable dependencies]."""
    text = path.read_text(errors="ignore")
    declared = FUNCTION_ID_RE.findall(text)
    repo_match = REPOSITORY_BLOCK_RE.search(text)
    dependencies = set()
    if repo_match:
        dependencies = set(FUNCTION_NAME_RE.findall(repo_match.group(1)))
    # A file never depends on the functions it declares itself.
    dependencies -= set(declared)
    return declared, dependencies


def build_graph(files):
    """Return [function name -> owning file] and
    [file -> set of files it depends on]."""
    owner_of = {}
    file_functions = {}
    for path in files:
        declared, _ = parse_file(path)
        file_functions[path] = declared
        for name in declared:
            owner_of[name.upper()] = path

    file_deps = defaultdict(set)
    for path in files:
        _, dependencies = parse_file(path)
        for dep_name in dependencies:
            owner = owner_of.get(dep_name.upper())
            if owner is not None and owner != path:
                file_deps[path].add(owner)
    return owner_of, file_deps


def topological_order(files, file_deps):
    """Kahn's algorithm. Raises on a cycle, since a cycle here is a
    design error, not a modeling quirk, per this project's conventions."""
    in_degree = {f: 0 for f in files}
    dependents = defaultdict(set)
    for f in files:
        for dep in file_deps.get(f, ()):
            in_degree[f] += 1
            dependents[dep].add(f)

    queue = deque(f for f in files if in_degree[f] == 0)
    order = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for dependent in dependents[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(files):
        remaining = [f for f in files if f not in order]
        raise RuntimeError(
            "Dependency cycle detected. This is a design error, not a "
            "modeling quirk: extract the shared logic into a new leaf "
            "function both sides call, instead of calling each other. "
            "Files still involved in the cycle:\n"
            + "\n".join(f"  {f.relative_to(REPO_ROOT)}" for f in remaining)
        )
    return order


def compile_file(path):
    """Compile one file as a callable GnuCOBOL module. Returns
    [True, ''] on success or [False, compiler output] on failure."""
    result = subprocess.run(
        ["cobc", "-m", "-std=ibm", str(path)],
        cwd=path.parent,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def main():
    files = find_cobol_files()
    if not files:
        print("No .cbl files found under SRC/. Nothing to compile yet.")
        return 0

    _, file_deps = build_graph(files)
    try:
        order = topological_order(files, file_deps)
    except RuntimeError as error:
        print(str(error))
        return 1

    skipped = set()
    failures = []
    passed = []

    for path in order:
        rel = path.relative_to(REPO_ROOT)
        if path in skipped:
            print(f"SKIP    {rel}  [depends on a file that failed]")
            continue

        ok, output = compile_file(path)
        if ok:
            print(f"OK      {rel}")
            passed.append(path)
        else:
            print(f"FAIL    {rel}")
            print(output)
            failures.append(path)
            # Every file depending on this one, directly or
            # transitively, cannot meaningfully be compiled either.
            to_skip = deque([path])
            while to_skip:
                current = to_skip.popleft()
                for other in order:
                    if current in file_deps.get(other, ()) and other not in skipped:
                        skipped.add(other)
                        to_skip.append(other)

    print()
    print(f"Passed:  {len(passed)}")
    print(f"Failed:  {len(failures)}")
    print(f"Skipped: {len(skipped)}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
