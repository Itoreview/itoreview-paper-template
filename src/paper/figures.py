"""Every figure in the paper, and the one command that redraws them all.

    uv run figures            redraw every figure into figures/
    uv run figures --check    redraw them elsewhere and compare with figures/, changing nothing

Each figure is a function of keyword parameters with defaults that returns a matplotlib Figure;
the files in figures/ are what the defaults draw. The functions use matplotlib's object-oriented
API, never pyplot, so they need no screen and run unchanged in readers' browsers (Pyodide), where
a paper's "Run" button on itoreview.org will let readers change the parameters.
"""

from __future__ import annotations

import argparse
import io
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.figure import Figure

from paper import model

# Applied while drawing and saving: bundled fonts only, and no dates or version stamps in the
# files, so the same code draws the same bytes every time.
STYLE = {
    "font.family": "DejaVu Sans",
    "mathtext.fontset": "cm",
    "svg.hashsalt": "itoreview",
    "axes.spines.top": False,
    "axes.spines.right": False,
}
INK = "#1b2a41"
MUTED = "#8a9bb0"
PNG_DPI = 200
# How far a redrawn PNG may stray from the committed one: the root-mean-square difference per
# pixel, on a 0-255 scale. It absorbs anti-aliasing noise between machines; a moved line or a
# changed number is far above it. The SVGs get no such allowance: they must match exactly.
TOLERANCE = 1.0


@dataclass(frozen=True)
class PaperFigure:
    name: str  # its files' name in figures/, without the extension
    draw: Callable[[], Figure]


def price_paths(
    *,
    s0: float = 100.0,
    mu: float = 0.08,
    sigma: float = 0.2,
    horizon: float = 1.0,
    paths: int = 20,
) -> Figure:
    """Simulated prices under geometric Brownian motion, around their expected value."""
    times, prices = model.price_paths(s0, mu, sigma, horizon, steps=250, paths=paths)
    figure = Figure(figsize=(6.4, 4.0), layout="constrained")
    axes = figure.add_subplot()
    axes.plot(times, prices.T, color=MUTED, linewidth=0.8)
    axes.plot(
        times,
        s0 * np.exp(mu * times),
        color=INK,
        linewidth=2.0,
        label=r"$\mathrm{E}[S_t] = S_0\,e^{\mu t}$",
    )
    axes.set_xlabel("Time $t$ (years)")
    axes.set_ylabel("Price $S_t$")
    axes.set_xlim(0.0, horizon)
    axes.legend(frameon=False, loc="upper left")
    return figure


def price_by_strike(
    *,
    s0: float = 100.0,
    r: float = 0.05,
    sigma: float = 0.2,
    maturity: float = 1.0,
    paths: int = 20_000,
) -> Figure:
    """The Black–Scholes price of a call across strikes, and Monte Carlo estimates of it. The
    estimates' 95% intervals are too narrow to see against the prices, so a second panel shows
    each estimate's distance from the formula."""
    strikes = np.linspace(60.0, 140.0, 161)
    formula = [model.black_scholes_call(s0, k, r, sigma, maturity) for k in strikes]
    sampled = np.arange(60.0, 141.0, 10.0)
    estimates = [model.monte_carlo_call(s0, k, r, sigma, maturity, paths) for k in sampled]
    means = np.array([mean for mean, _ in estimates])
    exact = np.array([model.black_scholes_call(s0, k, r, sigma, maturity) for k in sampled])

    figure = Figure(figsize=(6.4, 5.2), layout="constrained")
    prices, gaps = figure.subplots(2, 1, sharex=True, height_ratios=(3, 2))
    prices.plot(strikes, formula, color=INK, linewidth=2.0, label="Black–Scholes formula")
    prices.plot(sampled, means, "o", color=MUTED, markersize=5, label="Monte Carlo estimate")
    prices.set_ylabel("Call price $C$")
    prices.legend(frameon=False)
    gaps.axhline(0.0, color=INK, linewidth=1.0)
    gaps.errorbar(
        sampled,
        means - exact,
        yerr=[1.96 * error for _, error in estimates],
        fmt="o",
        color=MUTED,
        markersize=4,
        capsize=3,
    )
    gaps.set_title("Estimate minus formula, with 95% intervals", loc="left", fontsize="medium")
    gaps.set_xlabel("Strike $K$")
    gaps.set_ylabel("Difference")
    return figure


FIGURES: tuple[PaperFigure, ...] = (
    PaperFigure("price-paths", price_paths),
    PaperFigure("price-by-strike", price_by_strike),
)


def render(figure: PaperFigure, directory: Path) -> list[Path]:
    """Draw the figure with its defaults, and save it in `directory` as SVG and PNG.

    The SVG is written with Unix line endings, so its bytes are the same on every system.
    """
    svg, png = directory / f"{figure.name}.svg", directory / f"{figure.name}.png"
    with matplotlib.rc_context(STYLE):
        drawn = figure.draw()
        text = io.StringIO()
        drawn.savefig(text, format="svg", metadata={"Date": None, "Creator": None})
        svg.write_text(text.getvalue(), encoding="utf-8", newline="\n")
        drawn.savefig(png, dpi=PNG_DPI, metadata={"Software": None})
    return [svg, png]


def file_names() -> set[str]:
    """Every file the figures make."""
    return {f"{figure.name}.{suffix}" for figure in FIGURES for suffix in ("svg", "png")}


def differences(committed: Path, redrawn: Path, *, compare_pixels: bool = True) -> list[str]:
    """Why the redrawn figures don't match the committed ones; empty when they all do.

    Each SVG must match byte for byte. It holds every line and letter as exact coordinates, which
    come out the same on every machine, and in Pyodide too. Each PNG is compared pixel by pixel,
    allowing only anti-aliasing noise. Pyodide skips that step (compare_pixels=False): its
    matplotlib smooths text with a newer FreeType, which moves text pixels but no coordinates.
    """
    from matplotlib.testing.compare import compare_images  # only checking needs it
    from matplotlib.testing.exceptions import ImageComparisonFailure

    problems = []
    for figure in FIGURES:
        svg, png = committed / f"{figure.name}.svg", committed / f"{figure.name}.png"
        if not svg.is_file() or not png.is_file():
            problems.append(f"{figure.name}: not in figures/ yet")
            continue
        if svg.read_bytes() != (redrawn / svg.name).read_bytes():
            problems.append(f"{svg.name}: the code now draws something different")
        if not compare_pixels:
            continue
        try:
            outcome = compare_images(str(png), str(redrawn / png.name), tol=TOLERANCE)
        except ImageComparisonFailure as failure:  # such as a different size
            outcome = str(failure)
        if outcome:
            problems.append(f"{png.name}: {outcome}")
    problems += [
        f"{path.name}: no figure draws it any more"
        for path in sorted(committed.glob("*"))
        if path.name not in file_names()
    ]
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="figures", description="Redraw every figure in the paper into figures/."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="redraw them elsewhere and compare with figures/, changing nothing",
    )
    options = parser.parse_args(argv)
    committed = Path(__file__).resolve().parents[2] / "figures"

    if not options.check:
        committed.mkdir(exist_ok=True)
        for stale in sorted(committed.glob("*")):
            if stale.name not in file_names():  # figures/ holds only what the code draws
                stale.unlink()
                print(f"removed figures/{stale.name}: no figure draws it any more")
        for figure in FIGURES:
            for path in render(figure, committed):
                print(f"drew figures/{path.name}")
        return 0

    with tempfile.TemporaryDirectory() as scratch:
        for figure in FIGURES:
            render(figure, Path(scratch))
        problems = differences(committed, Path(scratch))
    for problem in problems:
        print(f"differs: {problem}")
    if problems:
        print(
            "The committed figures aren't what the code draws: run `uv run figures`, look, commit."
        )
        return 1
    print(f"All {len(FIGURES)} figures match what the code draws.")
    return 0
