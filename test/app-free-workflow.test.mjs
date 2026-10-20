import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {parseDocument} from 'yaml';

test('App-free acceptance preserves direct.yml caller identity and isolates the existing native scenario',()=>{
 const workflow=parseDocument(readFileSync(new URL('../.github/workflows/direct.yml',import.meta.url),'utf8')).toJS();
 assert.equal(workflow.on.workflow_dispatch.inputs['app-free'].default,false);
 assert.equal(workflow.jobs.publish.if,'${{ !inputs.app-free }}');
 const job=workflow.jobs['app-free'];
 assert.equal(job.if,'${{ inputs.app-free }}');
 assert.equal(job.permissions['id-token'],'write');
 for(const channel of ['rc','stable']){
  const select=job.steps.find(step=>step.id===channel+'-npm');
  assert.ok(select.with['release-tag'].includes(channel+'-plan.outputs.tag'));
  assert.equal(job.steps.find(step=>step.id===channel+'-bind').with.mode,'resume');
 }
 assert.deepEqual(job.steps.filter(step=>step.name?.startsWith('Install both versions')).map(step=>step.name.match(/Node (\d+)/)[1]),['22','24','26']);
 assert.ok(job.steps.findIndex(step=>step.name==='Verify candidate checkout identities before writes')<job.steps.findIndex(step=>step.id==='rc-plan'));
 assert.ok(job.steps.findIndex(step=>step.id==='stable-release')<job.steps.findIndex(step=>step.name==='Prepare fixture-only npm metadata after clean-source tag creation'));
});
