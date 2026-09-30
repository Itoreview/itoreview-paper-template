"""Every figure draws the same way every time, from the code alone, and figures/ is up to date."""

import ast
import sys
from pathlib import Path

import pytest

from paper import figures

ROOT = Path(__file__).resolve().parents[1]
# Pyodide, the Python in readers' browsers, has the standard library plus the packages the paper
# pins. CI also runs every figure there (pyodide/check.mjs); this catches a stray import sooner.
BROWSER_PACKAGES = {"numpy", "matplotlib", "paper"}


@pytest.mark.parametrize("figure", figures.FIGURES, ids=lambda figure: figure.name)
def test_every_figure_draws_the_same_bytes_twice(figure, tmp_path):
    (tmp_path / "first").mkdir()
    (tmp_path / "second").mkdir()
    first = figures.render(figure, tmp_path / "first")
    second = figures.render(figure, tmp_path / "second")
    for one, other in zip(first, second, strict=True):
        assert one.read_bytes() == other.read_bytes(), f"{one.name} changes from run to run"


def test_the_committed_figures_are_what_the_code_draws(tmp_path):
    for figure in figures.FIGURES:
        figures.render(figure, tmp_path)
    assert figures.differences(ROOT / "figures", tmp_path) == [], "run `uv run figures`"


def test_a_changed_figure_is_caught(tmp_path):
    (tmp_path / "committed").mkdir()
    (tmp_path / "redrawn").mkdir()
    paths, strikes = figures.FIGURES
    for figure in figures.FIGURES:
        figures.render(figure, tmp_path / "committed")
    figures.render(figures.PaperFigure(paths.name, strikes.draw), tmp_path / "redrawn")
    figures.render(strikes, tmp_path / "redrawn")

    problems = figures.differences(tmp_path / "committed", tmp_path / "redrawn")

    assert f"{paths.name}.svg: the code now draws something different" in problems
    assert all(problem.startswith(f"{paths.name}.") for problem in problems)


def test_the_browser_check_compares_the_svgs_alone(tmp_path):
    """Pyodide smooths text differently, which moves pixels but no coordinates."""
    (tmp_path / "committed").mkdir()
    (tmp_path / "redrawn").mkdir()
    for figure in figures.FIGURES:
        figures.render(figure, tmp_path / "committed")
        figures.render(figure, tmp_path / "redrawn")
    paths, strikes = figures.FIGURES
    other_pixels = (tmp_path / "committed" / f"{strikes.name}.png").read_bytes()
    (tmp_path / "redrawn" / f"{paths.name}.png").write_bytes(other_pixels)

    assert figures.differences(tmp_path / "committed", tmp_path / "redrawn") != []
    assert (
        figures.differences(tmp_path / "committed", tmp_path / "redrawn", compare_pixels=False)
        == []
    )


def test_files_no_figure_draws_are_caught(tmp_path):
    for figure in figures.FIGURES:
        figures.render(figure, tmp_path)
    (tmp_path / "old-figure.png").write_bytes(b"")

    assert figures.differences(tmp_path, tmp_path) == [
        "old-figure.png: no figure draws it any more"
    ]


def test_figure_code_imports_only_what_browsers_can_load():
    for path in (ROOT / "src" / "paper").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules = [node.module]
            else:
                continue
            for module in modules:
                top = module.split(".")[0]
                assert top in sys.stdlib_module_names | BROWSER_PACKAGES, (
                    f"{path.name} imports {module}, which readers' browsers can't load"
                )
