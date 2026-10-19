import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

test("installed fixture integrity must match the requested version and candidate plan", async () => {
  const root = await mkdtemp(join(tmpdir(), "fixture-integrity-"));
  try {
    const path = join(root, "pnpm-lock.yaml");
    const expected = "sha512-" + Buffer.alloc(64, 1).toString("base64");
    await writeFile(path, `---\nlockfileVersion: '9.0'\nimporters: {}\n---\nlockfileVersion: '9.0'\npackages:\n  '@releaseway/npm-actions-fixture@1.2.3':\n    resolution: {integrity: '${expected}'}\n`);
    const run = (version, integrity) => spawnSync(process.execPath, [resolve("scripts/verify-installed-integrity.mjs"), path, version, integrity], { encoding: "utf8" });
    assert.equal(run("1.2.3", expected).status, 0);
    assert.notEqual(run("1.2.4", expected).status, 0);
    assert.notEqual(run("1.2.3", "sha512-wrong").status, 0);
    await writeFile(path, "packages: [\n");
    assert.notEqual(run("1.2.3", expected).status, 0);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
