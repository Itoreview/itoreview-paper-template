"""Publishes the reproducibility check's result (CI only).

    python3 tools/status.py SITE

Writes SITE/status.json, which a paper's page on itoreview.org reads for its "Reproducible"
badge; a copy of the committed figures; and SITE/index.html, a plain page for people who follow
the badge's link. The checks' outcomes arrive in TESTS, FIGURES and BROWSER ("success",
"failure", "skipped"...), and GitHub's own variables name the commit and the run. It uses the
standard library alone, so it still runs when installing the project failed.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {  # outcome variable: what it proves when it succeeds
    "TESTS": "the tests pass",
    "FIGURES": "every figure redraws to match the committed files",
    "BROWSER": "every figure draws exactly the same in Pyodide, the Python in readers' browsers",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status() -> dict:
    checks = {name.lower(): os.environ.get(name, "not run") for name in CHECKS}
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    return {
        "schema": 1,
        "reproducible": all(outcome == "success" for outcome in checks.values()),
        "checked": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository": repository,
        "commit": os.environ.get("GITHUB_SHA", ""),
        "run": f"{server}/{repository}/actions/runs/{run_id}" if run_id else "",
        "checks": checks,
        "lockfile_sha256": sha256(ROOT / "uv.lock"),
        "figures": [
            {"file": path.name, "sha256": sha256(path)}
            for path in sorted((ROOT / "figures").glob("*"))
        ],
    }


def when(checked: str) -> str:
    """2026-09-30T09:52:21Z, as people write it: 30 September 2026 at 09:52 UTC."""
    moment = datetime.strptime(checked, "%Y-%m-%dT%H:%M:%SZ")
    return f"{moment.day} {moment:%B %Y} at {moment:%H:%M} UTC"


def verdict(result: dict) -> str:
    if result["reproducible"]:
        return "Reproducible ✓"
    failed = [name for name, outcome in result["checks"].items() if outcome != "success"]
    return f"Not reproducible ✗ (failed or didn't run: {', '.join(failed)})"


def page(result: dict) -> str:
    """A plain page for people who follow the badge's link."""
    name = html.escape(result["repository"] or "This paper's code")
    proofs = "".join(
        f"<li>{html.escape(proof)}: "
        f"<strong>{html.escape(result['checks'][key.lower()])}</strong></li>"
        for key, proof in CHECKS.items()
    )
    links = [f'<a href="{html.escape(result["run"])}">the run</a>'] if result["run"] else []
    if result["repository"] and result["commit"]:
        code = f"https://github.com/{result['repository']}/tree/{result['commit']}"
        links.append(f'<a href="{html.escape(code)}">the code at {result["commit"][:7]}</a>')
    links.append('<a href="status.json">status.json</a>')
    figures = "".join(
        f'<figure><img src="figures/{html.escape(entry["file"])}" alt=""><figcaption>'
        f"{html.escape(entry['file'])}</figcaption></figure>"
        for entry in result["figures"]
        if entry["file"].endswith(".svg")
    )
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}: reproducibility</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ margin: 2rem auto; padding: 0 1rem; max-width: 46rem; color: #1b2a41;
    background: #fff; font: 1rem/1.55 system-ui, sans-serif; }}
  img {{ max-width: 100%; height: auto; }}
  figure {{ margin: 2rem 0; }}
  figcaption {{ font-size: 0.875rem; color: #4a5a70; }}
</style>
<h1>{name}</h1>
<p><strong>{html.escape(verdict(result))}</strong>, checked
<time datetime="{html.escape(result["checked"])}">{html.escape(when(result["checked"]))}</time>
on a fresh machine, with the versions locked in <code>uv.lock</code>:</p>
<ul>{proofs}</ul>
<p>{" · ".join(links)}</p>
<h2>Figures</h2>
{figures}
</html>
"""


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    site = Path(sys.argv[1])
    result = status()
    (site / "figures").mkdir(parents=True, exist_ok=True)
    for path in sorted((ROOT / "figures").glob("*")):
        shutil.copy2(path, site / "figures" / path.name)
    (site / "status.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (site / "index.html").write_text(page(result), encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"## {verdict(result)}\n\n")
            for key, proof in CHECKS.items():
                file.write(f"- {proof}: **{result['checks'][key.lower()]}**\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
