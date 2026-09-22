#!/usr/bin/env python3
"""
generate_callgraph.py

Parses every COBOL file's FUNCTION-ID declarations and REPOSITORY
dependencies under SRC/, exactly as compile_check.py does, and emits
the resulting call graph as Graphviz DOT files: one master graph
covering the whole project, and one focused subgraph per SRC/ domain
folder, since a single graph across thousands of functions stops being
readable well before that scale.

If Graphviz's own `dot` command is available, this script also renders
each .dot file to .svg. If it is not installed, the .dot files are
still written, and a message explains how to render them.

This script intentionally re-implements its own small COBOL parser
rather than importing one from compile_check.py. With two scripts, that
duplication is a reasonable, deliberate choice for independence; the
project's own fan-in rule says that the moment a third script needs the
same parsing logic, it should be promoted into a shared
TOOLS/cobol_parser.py module instead of copied a second time.

Usage:
    python3 TOOLS/generate_callgraph.py
"""

import re
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "SRC"
DIAGRAMS_DIR = REPO_ROOT / "DOCS" / "DIAGRAMS"

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

# One stable color per domain, so the same domain always renders the
# same color across the master graph and its own subgraph.
DOMAIN_COLORS = {
    "TIME-VALUE-MONEY": "#a6cee3",
    "AMORTIZATION": "#b2df8a",
    "DEPRECIATION": "#fdbf6f",
    "BONDS-FIXED-INCOME": "#cab2d6",
    "CURRENCY-ROUNDING": "#fb9a99",
    "STATISTICS-SUPPORT": "#ffff99",
    "STATISTICS-RISK": "#e31a1c",
    "ACTUARIAL-LIFE-CONTINGENCIES": "#6a3d9a",
    "MATH-SUPPORT": "#1f78b4",
    "FORTRAN-MODULES": "#33a02c",
}
DEFAULT_COLOR = "#cccccc"


def find_cobol_files():
    return sorted(SRC_ROOT.rglob("*.cbl"))


def domain_of(path):
    """The SRC/ subfolder a file lives in, e.g. TIME-VALUE-MONEY."""
    relative = path.relative_to(SRC_ROOT)
    return relative.parts[0] if relative.parts else "UNKNOWN"


def parse_file(path):
    text = path.read_text(errors="ignore")
    declared = FUNCTION_ID_RE.findall(text)
    repo_match = REPOSITORY_BLOCK_RE.search(text)
    dependencies = set()
    if repo_match:
        dependencies = set(FUNCTION_NAME_RE.findall(repo_match.group(1)))
    dependencies -= set(declared)
    return declared, dependencies


def build_edges(files):
    """Return [set of (caller_function, callee_function) edges] and
    [function name -> domain]."""
    owner_domain = {}
    file_functions = {}
    for path in files:
        declared, _ = parse_file(path)
        file_functions[path] = declared
        for name in declared:
            owner_domain[name.upper()] = domain_of(path)

    edges = set()
    for path in files:
        declared, dependencies = parse_file(path)
        for caller in declared:
            for callee in dependencies:
                if callee.upper() in owner_domain:
                    edges.add((caller, callee))
    return edges, owner_domain


def node_line(name, domain):
    color = DOMAIN_COLORS.get(domain, DEFAULT_COLOR)
    return f'    "{name}" [fillcolor="{color}"];'


def render_dot(title, nodes_by_domain, edges):
    lines = [f"digraph {title} {{", '    node [shape=box, style=filled, fontname="Helvetica"];']
    for domain, names in sorted(nodes_by_domain.items()):
        lines.append(f'    subgraph "cluster_{domain}" {{')
        lines.append(f'        label="{domain}";')
        for name in sorted(names):
            lines.append(node_line(name, domain))
        lines.append("    }")
    for caller, callee in sorted(edges):
        lines.append(f'    "{caller}" -> "{callee}";')
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_and_render(dot_text, out_path):
    out_path.write_text(dot_text)
    if shutil.which("dot") is None:
        print(f"Wrote {out_path.name}. Graphviz 'dot' not found on PATH, "
              f"skipping SVG render. Install Graphviz to render locally.")
        return
    svg_path = out_path.with_suffix(".svg")
    result = subprocess.run(
        ["dot", "-Tsvg", str(out_path), "-o", str(svg_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"Wrote {out_path.name} and {svg_path.name}")
    else:
        print(f"Wrote {out_path.name}. Rendering to SVG failed:")
        print(result.stderr)


def main():
    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    files = find_cobol_files()
    if not files:
        print("No .cbl files found under SRC/. Nothing to graph yet.")
        return

    edges, owner_domain = build_edges(files)

    nodes_by_domain = {}
    for name, domain in owner_domain.items():
        nodes_by_domain.setdefault(domain, set()).add(name)

    # Master graph: every domain, every edge.
    master_dot = render_dot("COBOLFinancialFunctions", nodes_by_domain, edges)
    write_and_render(master_dot, DIAGRAMS_DIR / "callgraph.dot")

    # One focused subgraph per domain: that domain's own functions,
    # plus any edge touching one of them, so a cross-domain dependency
    # [e.g. BONDS-FIXED-INCOME calling into MATH-SUPPORT] is still
    # visible from either domain's own diagram.
    for domain, names in nodes_by_domain.items():
        relevant_edges = {
            (a, b) for a, b in edges if a in names or b in names
        }
        touched_names = set(names)
        for a, b in relevant_edges:
            touched_names.add(a)
            touched_names.add(b)
        touched_by_domain = {}
        for name in touched_names:
            d = owner_domain.get(name, "UNKNOWN")
            touched_by_domain.setdefault(d, set()).add(name)

        domain_dot = render_dot(domain.replace("-", "_"), touched_by_domain, relevant_edges)
        safe_name = domain.lower()
        write_and_render(domain_dot, DIAGRAMS_DIR / f"{safe_name}.dot")


if __name__ == "__main__":
    main()
