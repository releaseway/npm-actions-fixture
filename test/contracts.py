import base64
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
prepare = runpy.run_path(str(ROOT / 'scripts/prepare.py'))['prepare']
evidence = runpy.run_path(str(ROOT / 'scripts/evidence.py'))['evidence']


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / '.github/npm').mkdir(parents=True)
        (self.root / 'package.json').write_text((ROOT / 'package.json').read_text())
        self.env = dict(ACTION_REF='a' * 40, FIXTURE_KIND='fixture', FIXTURE_VERSION='0.0.8-fixture.0', VERSION_SOURCE='package-json', GITHUB_OUTPUT=str(self.root / 'output'))

    def test_invalid_sha_and_version_do_not_mutate(self):
        before = (self.root / 'package.json').read_bytes()
        for key, value in [('ACTION_REF', 'main'), ('ACTION_REF', 'a' * 39), ('FIXTURE_VERSION', '1.0.0'), ('VERSION_SOURCE', 'other')]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError): prepare({**self.env, key: value}, self.root)
                self.assertEqual((self.root / 'package.json').read_bytes(), before)
                self.assertFalse((self.root / '.github/npm/packages.yml').exists())

    def test_direct_native_policy(self):
        prepare({**self.env, 'FIXTURE_KIND': 'native', 'FIXTURE_VERSION': '0.0.8-native.0'}, self.root)
        package = json.loads((self.root / 'package.json').read_text())
        self.assertNotIn('tag', package['publishConfig'])
        self.assertIn('prerelease: next', (self.root / '.github/npm/packages.yml').read_text())
        self.assertIn('mode: direct', (self.root / '.github/npm/packages.yml').read_text())
        self.assertIn('bin/npm-actions-native-fixture', package['bin'].values())

    def test_tag_derived_version_and_wrong_commit(self):
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=self.root, text=True, stderr=subprocess.DEVNULL).strip()
        git('init', '--quiet')
        git('config', 'user.name', 'Fixture Test')
        git('config', 'user.email', 'fixture@example.invalid')
        git('config', 'commit.gpgsign', 'false')
        git('config', 'tag.gpgsign', 'false')
        git('config', 'core.hooksPath', '/dev/null')
        git('add', '.')
        git('commit', '--quiet', '-m', 'fixture')
        sha = git('rev-parse', 'HEAD')
        git('tag', '-a', 'npm-fixture-v0.0.8-fixture.0', '-m', 'version')
        git('remote', 'add', 'origin', str(self.root))
        before = (self.root / 'package.json').read_bytes()
        env = {**self.env, 'VERSION_SOURCE': 'git-tag', 'GITHUB_SHA': 'b' * 40}
        with self.assertRaises(ValueError): prepare(env, self.root)
        self.assertEqual((self.root / 'package.json').read_bytes(), before)
        self.assertFalse((self.root / '.github/npm/packages.yml').exists())
        prepare({**env, 'GITHUB_SHA': sha}, self.root)
        self.assertEqual(json.loads((self.root / 'package.json').read_text())['version'], json.loads(before)['version'])
        policy = (self.root / '.github/npm/packages.yml').read_text()
        self.assertIn('source: git-tag', policy)
        self.assertIn('prefix: npm-fixture-v', policy)
        self.assertIn('prerelease: next', policy)

    def test_fresh_report_and_historical_lookup(self):
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        packages = [dict(name='@releaseway/npm-actions-fixture', version='0.0.8-fixture.0', state='staged')]
        integrity = 'sha512-' + base64.b64encode(b'x' * 64).decode()
        report = dict(status='success', source=dict(repository='releaseway/npm-actions-fixture', commit='b' * 40), results=packages,
                      plan=[dict(name=packages[0]['name'], version=packages[0]['version'], integrity=integrity, mode='stage')])
        Path('report.json').write_text(json.dumps(report))
        env = {**self.env, 'PACKAGES': json.dumps(packages), 'EXPECTED_STATE': 'staged', 'REPORT_PATH': 'report.json', 'SCENARIO': 'npm-stage', 'WORKFLOW_FILE': 'publish.yml',
               'GITHUB_REPOSITORY': 'releaseway/npm-actions-fixture', 'GITHUB_SHA': 'b' * 40, 'GITHUB_RUN_ID': '1', 'GITHUB_RUN_ATTEMPT': '2'}
        evidence(env)
        self.assertEqual(json.loads(Path('acceptance.json').read_text())['integrity'], integrity)
        report['source']['commit'] = 'c' * 40
        Path('report.json').write_text(json.dumps(report))
        with self.assertRaises(ValueError): evidence(env)
        packages[0]['state'] = 'already-published'
        evidence({**env, 'PACKAGES': json.dumps(packages), 'EXPECTED_STATE': 'already-published', 'REPORT_PATH': 'absent.json'})
        self.assertNotIn('integrity', json.loads(Path('acceptance.json').read_text()))

    def test_workflow_identity_and_consumer_contracts(self):
        for workflow in ['publish.yml', 'direct.yml']:
            text = (ROOT / '.github/workflows' / workflow).read_text()
            self.assertIn('uses: ./npm-action', text)
            self.assertIn('FIXTURE_KIND:', text)
            self.assertLess(text.index('python3 scripts/prepare.py'), text.index('uses: ./npm-action'))
            self.assertIn('git -C npm-action rev-parse HEAD', text)
            self.assertIn('releaseway-acceptance-${{ github.run_attempt }}', text)
        direct = (ROOT / '.github/workflows/direct.yml').read_text()
        for version in ['22', '24', '26']:
            self.assertIn('node-version: "' + version + '"', direct)
            step = direct.split('Install and execute native CLI on Node ' + version)[1].split('      - ')[0]
            self.assertIn('FIXTURE_VERSION: ${{ inputs.fixture-version }}', step)
            self.assertIn('native-cache-' + version + '-', step)
            self.assertIn('run: bash scripts/verify-native.sh', step)
        self.assertLess(direct.index('Install and execute native CLI on Node 26'), direct.index('Record verified consumer runtimes'))
        self.assertIn('FIXTURE_VERSION: ${{ inputs.fixture-version }}', direct.split('Install and execute native CLI on Node 22')[1])
        self.assertIn('FIXTURE_VERSION: ${{ inputs.fixture-version }}', direct.split('Install and execute native CLI on Node 24')[1])
        consumer = (ROOT / 'scripts/verify-native.sh').read_text()
        self.assertIn('--ignore-scripts', consumer)
        self.assertIn('EXPECTED_INTEGRITY', consumer)
        self.assertIn('diff -u', consumer)


if __name__ == '__main__':
    unittest.main()
