import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "explorer/static/five-decisions/five-decisions-project.schema.json"
MANIFEST = ROOT / "portfolio.project.json"


def test_portfolio_manifest_matches_vendored_five_decisions_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda error: error.json_path)

    assert not errors, "\n".join(f"{error.json_path}: {error.message}" for error in errors)
