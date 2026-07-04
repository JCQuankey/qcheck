import ast
import glob
import json

from qcheck import rules as rc
from qcheck.cli import main, EXIT_PASS
from qcheck.sarif import build_sarif
from qcheck.report import Report, Finding


def _emitted_rule_ids():
    """Every rule id constructed via Finding("ID", ...) in the source."""
    ids = set()
    for f in glob.glob("qcheck/*.py"):
        for node in ast.walk(ast.parse(open(f, encoding="utf-8").read())):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Finding":
                if node.args and isinstance(node.args[0], ast.Constant):
                    ids.add(node.args[0].value)
    return ids


# --- Drift guards ---

def test_every_emitted_id_has_catalog_metadata():
    missing = _emitted_rule_ids() - set(rc.RULES)
    assert not missing, f"rule ids emitted but missing from catalog: {sorted(missing)}"


def test_catalog_ids_unique_and_match_dict():
    ids = [r.id for r in rc.catalog()]
    assert len(ids) == len(set(ids))              # unique
    assert set(ids) == set(rc.RULES)              # dict and list agree


def test_every_rule_has_required_nonempty_fields():
    required = ("id", "title", "category", "default_level",
                "applies_to", "summary", "why_it_matters", "recommended_action")
    for r in rc.catalog():
        d = r.to_dict()
        for field in required:
            assert d.get(field), f"{r.id} missing/empty field {field}"


def test_levels_and_categories_valid():
    for r in rc.catalog():
        assert r.default_level in rc.VALID_LEVELS, f"{r.id} bad level {r.default_level}"
        assert r.category in rc.CATEGORIES, f"{r.id} bad category {r.category}"
        assert r.applies_to in rc.SURFACES, f"{r.id} bad surface {r.applies_to}"


def test_catalog_order_deterministic():
    a = [r.id for r in rc.catalog()]
    assert a == sorted(a)


# --- `qcheck rules` command ---

def test_rules_command_human_exits_pass(capsys):
    rc_code = main(["rules"])
    out = capsys.readouterr().out
    assert rc_code == EXIT_PASS
    assert "RULE" in out and "CATEGORY" in out
    for rid in rc.RULES:
        assert rid in out                          # lists every rule


def test_rules_command_json(capsys):
    rc_code = main(["rules", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert rc_code == EXIT_PASS
    ids = [r["id"] for r in data["rules"]]
    assert ids == sorted(ids)
    assert set(ids) == set(rc.RULES)
    # no private content leaks into catalog output
    blob = json.dumps(data).lower()
    for bad in ("cainmani", "docs/plan", ".env", "jcano@", "claude", "anthropic"):
        assert bad not in blob


# --- SARIF enrichment from catalog ---

def test_sarif_rules_enriched_from_catalog():
    rep = Report(framework="qiskit", syntax_valid=True, findings=[
        Finding("QISKIT-EXECUTE", "error", "execute() removed", 3),
    ])
    doc = build_sarif([("x.py", rep)])
    rules = doc["runs"][0]["tool"]["driver"]["rules"]
    assert len(rules) == 1
    r = rules[0]
    assert r["id"] == "QISKIT-EXECUTE"
    assert r["shortDescription"]["text"]
    assert r["fullDescription"]["text"]
    assert r["help"]["text"]
    assert r["defaultConfiguration"]["level"] == "error"
    assert r["properties"]["category"] == "api-compatibility"
    # SARIF core structure preserved
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["results"][0]["ruleId"] == "QISKIT-EXECUTE"


def test_sarif_only_observed_rules_listed():
    rep = Report(framework="qiskit", syntax_valid=True, findings=[
        Finding("QISKIT-EXECUTE", "error", "x", 1),
    ])
    doc = build_sarif([("x.py", rep)])
    listed = {r["id"] for r in doc["runs"][0]["tool"]["driver"]["rules"]}
    assert listed == {"QISKIT-EXECUTE"}            # not the whole catalog
