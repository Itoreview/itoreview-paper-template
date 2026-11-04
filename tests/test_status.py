"""The published result (tools/status.py): schema 1, which itoreview.org reads, with the version
CITATION.cff gives, and a page that says "rerun", never "reproducible", and what a rerun doesn't
prove."""

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("status", ROOT / "tools" / "status.py")
status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(status)


def result(monkeypatch, **outcomes) -> dict:
    for name in status.CHECKS:
        monkeypatch.setenv(name, outcomes.get(name.lower(), "success"))
    monkeypatch.setenv("GITHUB_REPOSITORY", "Itoreview/a-paper")
    monkeypatch.setenv("GITHUB_SHA", "0" * 40)
    monkeypatch.setenv("GITHUB_RUN_ID", "7")
    return status.status()


def cited_version() -> str:
    return str(yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))["version"])


def test_it_names_the_version_citation_cff_gives(monkeypatch):
    assert result(monkeypatch)["version"] == cited_version()


def test_it_keeps_schema_1_which_itoreview_reads(monkeypatch):
    passed = result(monkeypatch)
    assert passed["schema"] == 1
    assert passed["reproducible"] is True
    assert result(monkeypatch, figures="failure")["reproducible"] is False


def test_the_page_says_rerun_never_reproducible(monkeypatch):
    passed = status.page(result(monkeypatch))
    failed = status.page(result(monkeypatch, browser="failure"))
    assert "Rerun passed" in passed
    assert "Rerun failed" in failed
    for page in (passed, failed):
        assert "eproducib" not in page  # neither "Reproducible" nor "reproducibility"
        assert "It does not show that anyone independent has checked the paper" in page
        assert f"for version {cited_version()}," in page
