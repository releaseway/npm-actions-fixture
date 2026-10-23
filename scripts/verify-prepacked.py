"""Check new artifact evidence without changing legacy acceptance receipt semantics."""
import json
import os
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote
from urllib.request import urlopen
sys.dont_write_bytecode = True
from prepacked import integrity


def require(condition, message):
    if not condition:
        raise ValueError(message)


def absent(env=os.environ):
    with urlopen('https://registry.npmjs.org/' + quote('@releaseway/npm-actions-fixture', safe=''), timeout=30) as response:
        metadata = json.load(response)
    require(env['PREPACKED_VERSION'] not in metadata['versions'], 'negative preflight changed public registry or version was not fresh')


def verify(env=os.environ):
    root = Path(env['BUNDLE_DIR'])
    manifest = json.loads((root/'artifacts.json').read_text())
    entry = manifest['packages'][0]
    mode = env['PREPACKED_MODE']
    require(mode in ('direct', 'stage'), 'invalid mode')
    expected_state = 'published' if mode == 'direct' else 'staged'
    expected = dict(name='@releaseway/npm-actions-fixture', version=env['PREPACKED_VERSION'], state=expected_state)
    require(json.loads(env['PACKAGES']) == [expected], 'prepacked publication result differs')
    report_path = Path(env['ARTIFACT_REPORT'])
    report = json.loads(report_path.read_text())
    require(report['schema'] == 1 and report['status'] == 'success' and report['preflight'] == 'passed', 'preflight did not finish')
    require(report['source'] == manifest['source'] == dict(repository=env['GITHUB_REPOSITORY'], commit=env['GITHUB_SHA']), 'source binding differs')
    require(report['publicationCommit'] == env['GITHUB_SHA'] and report['manifestIntegrity'] == integrity(root/'artifacts.json'), 'manifest or publication commit differs')
    require(len(report['packages']) == 1, 'unexpected report packages')
    row = report['packages'][0]
    require(row['name'] == entry['name'] == expected['name'] and row['version'] == entry['version'] == expected['version'], 'artifact identity differs')
    require(row['coverage'] == 'supplied' and row['localVerification'] == 'matched', 'local bytes not verified')
    require(row['expectedIntegrity'] == row['localIntegrity'] == entry['integrity'] and row['publication'] == expected_state, 'artifact digest or state differs')
    require(row['publicVerification'] == ('matched' if mode == 'direct' else 'not-checked'), 'stage/public meaning differs')
    if mode == 'direct':
        require(row['publicIntegrity'] == entry['integrity'], 'public SRI differs')
    negative_path = Path(env['NEGATIVE_REPORT'])
    negative = json.loads(negative_path.read_text())
    require(negative['status'] == 'failed' and negative['error']['code'] == 'ARTIFACT_INTEGRITY_MISMATCH' and
            negative['error']['remoteState'] == 'unchanged', 'negative preflight did not fail closed')
    require(negative['source'] == report['source'] and negative['preflight'] == 'not-complete' and
            negative['error']['package'] == dict(name=entry['name'], version=entry['version']) and
            negative['packages'][0]['localIntegrity'] == entry['integrity'] and
            negative['packages'][0]['localVerification'] == 'mismatched', 'negative artifact identity or bytes differ')
    retry_integrity = None
    if mode == 'direct':
        retry_path = Path(env['RETRY_REPORT'])
        retry = json.loads(retry_path.read_text())
        require(json.loads(env['RETRY_PACKAGES']) == [dict(expected, state='already-published')], 'retry republished')
        require(retry['status'] == 'success' and retry['source'] == report['source'], 'retry source differs')
        require(retry['packages'][0]['localVerification'] == 'not-required' and retry['packages'][0]['publicVerification'] == 'matched' and
                retry['packages'][0]['publicIntegrity'] == entry['integrity'], 'fileless retry was not SHA-512 verified')
        require(not list(root.glob('*.tgz')), 'retry still had local tarball')
        retry_integrity = integrity(retry_path)
    require(re.fullmatch(r'[0-9a-fA-F]{40}', env['ACTION_REF']), 'candidate must be exact SHA')
    workflow = 'direct.yml' if mode == 'direct' else 'publish.yml'
    require(env['WORKFLOW_FILE'] == workflow, 'caller workflow identity changed')
    require(all(int(env[key]) > 0 for key in ['SOURCE_ARTIFACT_ID', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT']), 'invalid artifact/run identity')
    receipt = dict(schema=1, candidate_repository='releaseway/npm-actions', candidate_sha=env['ACTION_REF'].lower(),
        fixture_repository=env['GITHUB_REPOSITORY'], fixture_commit=env['GITHUB_SHA'], run_id=int(env['GITHUB_RUN_ID']),
        run_attempt=int(env['GITHUB_RUN_ATTEMPT']), workflow=workflow, scenario='npm-prepacked-' + mode,
        version_source='prepacked', version=entry['version'], mode=mode, state=expected_state,
        source_artifact_id=int(env['SOURCE_ARTIFACT_ID']), manifest_integrity=report['manifestIntegrity'], integrity=entry['integrity'],
        artifact_report_integrity=integrity(report_path), retry_state='already-published' if mode == 'direct' else None,
        retry_report_integrity=retry_integrity)
    output = Path(env['EVIDENCE_DIR'])
    output.mkdir(parents=True, exist_ok=True)
    (output/'prepacked-acceptance.json').write_text(json.dumps(receipt, indent=2) + '\n')
    shutil.copy2(report_path, output/'artifact-report.json')
    shutil.copy2(negative_path, output/'negative-report.json')
    shutil.copy2(root/'artifacts.json', output/'artifacts.json')
    if mode == 'direct':
        shutil.copy2(env['RETRY_REPORT'], output/'retry-report.json')
    return receipt


if __name__ == '__main__':
    {'absent': absent, 'verify': verify}[sys.argv[1]]()
