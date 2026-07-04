#!/usr/bin/env python3
"""Example: turn `qcheck rules --json` into a rule-id -> guidance lookup.

    qcheck rules --json | python examples/consume_rules_json.py
    qcheck rules --json | python examples/consume_rules_json.py QISKIT-EXECUTE

An agent that receives a finding with a rule id can look up why it matters and
the recommended action, so it can act without guessing. Stdlib only; no external
dependencies. See docs/CONTRACTS.md for the catalog shape.
"""
import json
import sys


def build_index(catalog):
    """Map rule id -> rule metadata dict."""
    return {r["id"]: r for r in catalog["rules"]}


def main():
    index = build_index(json.load(sys.stdin))
    if len(sys.argv) > 1:
        rid = sys.argv[1]
        r = index.get(rid)
        if not r:
            print(f"unknown rule: {rid}")
            return 1
        print(f"{r['id']}: {r['title']}")
        print(f"  why: {r['why_it_matters']}")
        print(f"  action: {r['recommended_action']}")
    else:
        for rid in sorted(index):
            print(f"{rid}: {index[rid]['recommended_action']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
