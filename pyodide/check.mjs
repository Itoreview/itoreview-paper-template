// Draws every figure in Pyodide, the Python that runs in readers' browsers, and checks that each
// SVG matches the committed one byte for byte. The PNGs may differ slightly, because Pyodide
// smooths text with a newer FreeType. A paper's "Run" button on itoreview.org redraws its figures
// this way, so a figure that fails here would fail for readers too.
// Run from the repository root: npm ci --prefix pyodide && node pyodide/check.mjs
import { readdir, readFile } from "node:fs/promises";
import { loadPyodide } from "pyodide";

const root = new URL("../", import.meta.url);
const pyodide = await loadPyodide();
await pyodide.loadPackage(["numpy", "matplotlib"], { messageCallback: () => {} });

async function copyInto(folder, target, suffixes) {
  pyodide.FS.mkdirTree(target);
  for (const name of await readdir(new URL(folder, root))) {
    if (suffixes.some((suffix) => name.endsWith(suffix))) {
      pyodide.FS.writeFile(`${target}/${name}`, await readFile(new URL(folder + name, root)));
    }
  }
}
await copyInto("src/paper/", "/home/pyodide/paper", [".py"]);
await copyInto("figures/", "/home/pyodide/figures", [".png", ".svg"]);

const problems = pyodide
  .runPython(`
import sys
from pathlib import Path

sys.path.insert(0, "/home/pyodide")
from paper import figures

redrawn = Path("/tmp/redrawn")
redrawn.mkdir()
for figure in figures.FIGURES:
    figures.render(figure, redrawn)
    print(f"drew {figure.name} in Pyodide")
figures.differences(Path("/home/pyodide/figures"), redrawn, compare_pixels=False)
`)
  .toJs();

for (const problem of problems) console.error(`differs in Pyodide: ${problem}`);
if (problems.length > 0) process.exit(1);
console.log(`Every figure draws exactly the same in Pyodide ${pyodide.version} as in figures/.`);
