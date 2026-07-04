import sys
from pathlib import Path

# Ensure the repo root (containing the `qcheck` package) is importable when
# tests run without an editable install.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Make the leaderboard scripts importable for leaderboard tests.
LEADERBOARD = ROOT / "leaderboard"
_SCRIPTS = LEADERBOARD / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

FIXTURES = ROOT / "fixtures"
