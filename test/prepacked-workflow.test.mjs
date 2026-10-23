import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { parse } from "yaml";

for (const [file, mode] of [["direct.yml", "direct"], ["publish.yml", "stage"]]) {
  test(`${file} preserves caller OIDC and transfers the exact verified artifact`, () => {
    const workflow = parse(readFileSync(new URL(`../.github/workflows/${file}`, import.meta.url), "utf8"));
    assert.equal(workflow.on.workflow_dispatch.inputs["prepacked-version"].default, "");
    const build = workflow.jobs["prepacked-build"], publish = workflow.jobs["prepacked-publish"];
    assert.deepEqual(build.permissions, { contents: "read" });
    assert.deepEqual(publish.permissions, { contents: "read", "id-token": "write" });
    assert.equal(publish.env.PREPACKED_MODE, mode);
    assert.equal(publish.needs, "prepacked-build");
    assert.equal(build.outputs["artifact-id"], "${{ steps.bundle.outputs.artifact-id }}");
    const download = publish.steps.find(step => step.uses?.startsWith("actions/download-artifact@"));
    assert.equal(download.with["artifact-ids"], "${{ needs.prepacked-build.outputs.artifact-id }}");
    assert.equal(download.with.name, undefined);
    assert.equal(publish.steps.find(step => step.id === "negative")["continue-on-error"], true);
    assert.equal(publish.steps.find(step => step.id === "retry").if, "env.PREPACKED_MODE == 'direct'");
    assert.equal(publish.steps.find(step => step.name === "Verify and preserve prepacked evidence").env.WORKFLOW_FILE, file);
    assert.ok(workflow.jobs.publish);
  });
}
