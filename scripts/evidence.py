"""Keep candidate execution evidence separate from historical lookup results."""
import base64
import json
import os
from pathlib import Path
import re


def evidence(env=os.environ):
    packages = json.loads(env['PACKAGES'])
    expected = {'name': '@releaseway/npm-actions-fixture', 'version': env['FIXTURE_VERSION'], 'state': env['EXPECTED_STATE']}
    if packages != [expected]:
        raise ValueError('unexpected publication result')
    result = dict(schema=1, candidate_repository='releaseway/npm-actions', candidate_sha=env['ACTION_REF'].lower(),
                  fixture_repository=env['GITHUB_REPOSITORY'], fixture_commit=env['GITHUB_SHA'],
                  run_id=int(env['GITHUB_RUN_ID']), run_attempt=int(env['GITHUB_RUN_ATTEMPT']),
                  workflow=env['WORKFLOW_FILE'], scenario=env['SCENARIO'], version_source=env['VERSION_SOURCE'],
                  version=expected['version'], state=expected['state'])
    if expected['state'] != 'already-published':
        report = json.loads(Path(env['REPORT_PATH']).read_text())
        if report['status'] != 'success' or report['source'] != {'repository': env['GITHUB_REPOSITORY'], 'commit': env['GITHUB_SHA']} or report['results'] != packages:
            raise ValueError('report source/result mismatch')
        plan = report['plan']
        if len(plan) != 1 or plan[0]['name'] != expected['name'] or plan[0]['version'] != expected['version']:
            raise ValueError('report plan mismatch')
        integrity = plan[0]['integrity']
        if not re.fullmatch(r'sha512-[A-Za-z0-9+/]{86}==', integrity) or len(base64.b64decode(integrity[7:], validate=True)) != 64:
            raise ValueError('invalid planned integrity')
        if plan[0]['mode'] != ('stage' if env['SCENARIO'] == 'npm-stage' else 'direct'):
            raise ValueError('report publication mode mismatch')
        result['integrity'] = integrity
    Path('acceptance.json').write_text(json.dumps(result, indent=2) + '\n')
    with open(env['GITHUB_OUTPUT'], 'a') as output:
        output.write('integrity=' + result.get('integrity', '') + '\n')


if __name__ == '__main__':
    evidence()
