"""The paper's metadata agrees with itself across CITATION.cff, .zenodo.json and pyproject.toml,
and a paper made from the template can't be released under the template's name."""

import json
import os
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_REPOSITORY = "Itoreview/itoreview-paper-template"
TEMPLATE_TITLE = "Itoreview paper template"


@pytest.fixture(scope="module")
def citation():
    return yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def zenodo():
    return json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def project():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_zenodo_files_each_release_as_a_working_paper_under_cc_by(zenodo):
    """So the DOI names the paper, and the archive holds its code."""
    assert zenodo["upload_type"] == "publication"
    assert zenodo["publication_type"] == "workingpaper"
    assert zenodo["license"] == "cc-by-4.0"
    assert zenodo["creators"]
    assert all(creator["name"].strip() for creator in zenodo["creators"])


def test_the_version_is_the_same_everywhere(citation, zenodo, project):
    assert citation["version"] == zenodo["version"] == project["version"]


def test_the_title_is_the_same_everywhere(citation, zenodo):
    assert citation["preferred-citation"]["title"] == zenodo["title"]


def test_the_code_is_mit_and_the_paper_cc_by(citation, project):
    assert citation["license"] == project["license"] == "MIT"
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
    assert "creativecommons.org/licenses/by/4.0" in (ROOT / "LICENSE-TEXT.md").read_text(
        encoding="utf-8"
    )


def test_a_paper_made_from_the_template_has_its_own_title(zenodo):
    """In GitHub's CI for any other repository, the template's placeholder title fails the run."""
    repository = os.environ.get("GITHUB_REPOSITORY")
    if repository is None or repository == TEMPLATE_REPOSITORY:
        pytest.skip("only a paper's own repository must replace the template's title")
    assert zenodo["title"] != TEMPLATE_TITLE, "give the paper its title: README, step 2"
