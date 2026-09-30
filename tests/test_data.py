"""Every data file is accounted for: where it came from, when, and the SHA-256 of its bytes."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NOT_DATA = {"README.md", "sources.json"}


def manifest() -> dict[str, dict]:
    entries = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    return {entry["file"]: entry for entry in entries}


def test_every_data_file_is_listed_with_its_source_and_checksum():
    listed = manifest()
    for path in sorted(DATA.rglob("*")):
        if not path.is_file() or path.name in NOT_DATA:
            continue
        name = path.relative_to(DATA).as_posix()
        assert name in listed, f"data/{name} isn't in data/sources.json"
        entry = listed[name]
        assert entry["source"].startswith("https://"), f"data/{name}: where did it come from?"
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["retrieved"]), f"data/{name}: when?"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], (
            f"data/{name} has changed since it was recorded"
        )


def test_every_listed_file_is_there():
    for name in manifest():
        assert (DATA / name).is_file(), f"data/sources.json lists data/{name}, which is missing"
