import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { delimiter, join, resolve } from "node:path";
import test from "node:test";

test("native consumer retries only delayed install metadata and preserves other errors", async () => {
  const root = await mkdtemp(join(tmpdir(), "fixture-consumer-"));
  try {
    await writeFile(join(root, "pnpm"), `#!/usr/bin/env bash
count=0
if [ -f "$CALLS" ]; then count=$(cat "$CALLS"); fi
count=$((count + 1))
printf '%s' "$count" > "$CALLS"
if [ "$FAILURE" = missing ] && [ "$count" = 1 ]; then
  echo ERR_PNPM_NO_MATCHING_VERSION >&2
  exit 19
fi
if [ "$FAILURE" = fatal ]; then
  echo ERR_PNPM_TARBALL_INTEGRITY >&2
  exit 17
fi
`, { mode: 0o755 });
    const run = failure => spawnSync("bash", [resolve("scripts/install-native-fixture.sh"), root], {
      encoding: "utf8", timeout: 15_000,
      env: { ...process.env, PATH: root + delimiter + process.env.PATH, CALLS: join(root, "calls"), FAILURE: failure, FIXTURE_VERSION: "0.0.20-native.1" },
    });
    assert.equal(run("missing").status, 0);
    assert.equal(await readFile(join(root, "calls"), "utf8"), "2");
    await rm(join(root, "calls"));
    const fatal = run("fatal");
    assert.equal(fatal.status, 17);
    assert.match(fatal.stderr, /ERR_PNPM_TARBALL_INTEGRITY/);
    assert.equal(await readFile(join(root, "calls"), "utf8"), "1");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
