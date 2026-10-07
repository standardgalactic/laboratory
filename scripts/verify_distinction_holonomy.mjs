#!/usr/bin/env node
// Verify that distinction-holonomy.html implements the ℝ² toy model of
// Chapter 9 / Appendix C exactly: the closed-loop transport
//   e^{εX} e^{εY} e^{−εX} e^{−εY}
// equals the closed form [[1+ε²+ε⁴, −ε³],[ε³, 1−ε²]], and the two orderings
// e^{εX}e^{εY} vs e^{εY}e^{εX} differ by ε²[X,Y].
//
// The math is read from the artifact itself (not re-implemented here), so the
// test fails if the page's generators or closed form drift.
//
// Run: node scripts/verify_distinction_holonomy.mjs

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const HTML = join(ROOT, "distinction-holonomy.html");

const source = readFileSync(HTML, "utf8");

// Pull the pure math out of the artifact: every top-level `const` line that
// does not touch the DOM. Some definitions are comma-joined on one line
// (`const expX=..., expY=...`), so evaluate the block as a whole.
const names = ["expX", "expY", "mul", "apply", "det", "trace", "maxError", "closedForm", "operations"];
const pureConstLines = source
  .split("\n")
  .filter((l) => /^\s*const\s/.test(l))
  .filter((l) => !/document|getComputedStyle|canvas|epsilon|window|requestAnimationFrame/.test(l));

const sandbox = {};
const code = pureConstLines.join("\n") + `\nreturn { ${names.map((n) => `${n}`).join(", ")} };`;
let M;
try {
  M = new Function(code)();
} catch (err) {
  console.error(`could not evaluate the artifact's math: ${err.message}`);
  process.exit(1);
}
const missing = names.filter((n) => typeof M[n] === "undefined");
if (missing.length) {
  console.error(`could not extract from ${HTML}: ${missing.join(", ")}`);
  process.exit(1);
}

let failures = 0;
const check = (label, ok, detail = "") => {
  if (!ok) failures++;
  console.log(`  [${ok ? "PASS" : "FAIL"}] ${label}${detail ? "  " + detail : ""}`);
};

const epsilons = [0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 0.9, 1.0];
const flatMax = (A, B) => Math.max(...A.flat().map((x, i) => Math.abs(x - B.flat()[i])));

console.log("distinction-holonomy: ℝ² toy-model correspondence");
for (const e of epsilons) {
  let T = [[1, 0], [0, 1]];
  for (const op of M.operations(e)) T = M.mul(op.matrix, T);
  check(`loop product == closed form at ε=${e}`, flatMax(T, M.closedForm(e)) < 1e-12);
}

for (const e of [0.1, 0.3, 0.7]) {
  const diff = M.mul(M.expX(e), M.expY(e)).map((row, i) =>
    row.map((x, j) => x - M.mul(M.expY(e), M.expX(e))[i][j])
  );
  check(`order difference == ε²[X,Y] at ε=${e}`, flatMax(diff, [[e * e, 0], [0, -e * e]]) < 1e-12);
}

check("identity at ε=0", flatMax(M.closedForm(0), [[1, 0], [0, 1]]) < 1e-12);
check("det(closed form) == (1+ε²+ε⁴)(1−ε²) + ε⁶ at ε=0.4",
  Math.abs(M.det(M.closedForm(0.4)) - ((1 + 0.16 + 0.0256) * (1 - 0.16) + 0.4 ** 6)) < 1e-12);

console.log(failures ? `\nRESULT: FAIL (${failures})` : "\nRESULT: PASS");
process.exit(failures ? 1 : 0);
