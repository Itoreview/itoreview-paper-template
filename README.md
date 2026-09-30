# Itoreview paper template

[![Reproduce](https://github.com/Itoreview/itoreview-paper-template/actions/workflows/reproduce.yml/badge.svg)](https://github.com/Itoreview/itoreview-paper-template/actions/workflows/reproduce.yml)

Every paper on [itoreview.org](https://itoreview.org) publishes the code behind its figures, so
anyone can check it, rerun it and cite it. Each paper's code lives in its own repository, made from
this template. It comes with a worked example: prices that follow geometric Brownian motion, and
the Black–Scholes price of a call checked against Monte Carlo.

## Reproduce every figure

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. In this folder, run:
   ```bash
   uv run figures
   ```
   uv installs the exact Python and library versions recorded in `uv.lock`, then redraws every
   figure into `figures/`.
3. To rerun the checks too: `uv run pytest`. To compare with the committed figures without
   changing them: `uv run figures --check`.

GitHub reruns the same checks on every change and every week (the badge above). The latest result
is published as [`status.json`](https://itoreview.github.io/itoreview-paper-template/status.json),
which the paper's page on itoreview.org shows as its reproducibility badge.

## What's where

| Path | What |
|---|---|
| `src/paper/model.py` | The model: the maths behind the numbers |
| `src/paper/figures.py` | Every figure, as a function of its parameters, and the `figures` command |
| `figures/` | What the code draws, committed: SVG for print, PNG for the web |
| `tests/` | The maths against known values, the figures against `figures/`, the metadata against itself |
| `data/` | Any data the paper uses, each file with its source, date and SHA-256 in `sources.json` |
| `pyodide/check.mjs` | Draws every figure in Pyodide, the Python in readers' browsers |
| `CITATION.cff`, `.zenodo.json` | How to cite the paper, and how Zenodo files each release |
| `LICENSE`, `LICENSE-TEXT.md` | MIT for the code; CC BY 4.0 for the text and figures |

## Start a new paper

1. **Make the repository.** On GitHub, **Use this template → Create a new repository**: owner
   `Itoreview`, public, named after the paper's address on itoreview.org. For
   `itoreview.org/research/ito-to-black-scholes/`, name it `ito-to-black-scholes`.
2. **Give it the paper's identity.** Replace the template's title, authors, description and
   keywords in `.zenodo.json`, `CITATION.cff` (both titles) and `pyproject.toml`, and this README's
   title and first paragraph. In `.zenodo.json`, write authors as `Family, Given`, with an ORCID
   where they have one. CI fails until the title changes.
3. **Publish its status.** **Settings → Pages → Source: GitHub Actions.** The next run publishes
   `https://itoreview.github.io/<repository>/status.json`.
4. **Write the paper's code.** Replace the model and the figures with the paper's own. Keep each
   figure a function of keyword parameters with defaults, using only NumPy, matplotlib and the
   standard library, so readers' browsers can run it. Put any data in `data/`, with its entry in
   `data/sources.json`. Then run `uv run figures`, look at `figures/`, run `uv run pytest`, and
   commit.
5. **Archive it.** Sign in to [Zenodo](https://zenodo.org) with GitHub, open **GitHub** in the
   account menu, and switch the repository on. It's needed once per repository.
6. **Release a version.** When the paper is published or revised, set the same version in
   `pyproject.toml`, `CITATION.cff` and `.zenodo.json`, commit, and publish a GitHub release
   tagged `v<version>`, such as `v1.0.0`. Zenodo archives that release and mints its DOI.
7. **Link it from the paper.** On the paper's page in Itoreview's admin, add the repository's
   address and the version's DOI.

## Why it's built this way

- **Locked versions.** `uv.lock` records every library's exact version and checksum, and
  `.python-version` the Python version, so the figures come out the same years from now.
- **The browser's versions.** NumPy, matplotlib and the libraries beneath them are pinned to
  exactly what Pyodide 314.0.7 ships, so a figure a reader redraws in the browser matches the
  committed one. CI draws every figure there too.
- **Checked figures.** CI redraws every figure on a fresh machine and compares it, pixel by pixel,
  with the committed file, allowing only anti-aliasing noise.
- **Fixed seeds.** Every random draw starts from `SEED` in `model.py`.
- **No pyplot.** The figures use matplotlib's object-oriented API, which needs no screen, in CI or
  in a browser.
