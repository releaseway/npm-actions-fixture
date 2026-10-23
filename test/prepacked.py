"""Contracts for the extra ordinary-tarball jobs on the existing OIDC workflows."""
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT/'scripts'))
P = runpy.run_path(str(ROOT/'scripts/prepacked.py'))
V = runpy.run_path(str(ROOT/'scripts/verify-prepacked.py'))


class PrepackedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'package.json').write_bytes((ROOT/'package.json').read_bytes())
        (self.root/'index.js').write_bytes((ROOT/'index.js').read_bytes())
        self.env = dict(ACTION_REF='b'*40, PREPACKED_MODE='direct', PREPACKED_VERSION='0.0.101-prepacked.0',
            FIXTURE_VERSION='0.0.101-native.0', GITHUB_SHA='a'*40, GITHUB_REPOSITORY='releaseway/npm-actions-fixture',
            GITHUB_RUN_ID='10', GITHUB_RUN_ATTEMPT='1', SOURCE_ARTIFACT_ID='11', WORKFLOW_FILE='direct.yml',
            BUNDLE_DIR=str(self.root/'bundle'), EVIDENCE_DIR=str(self.root/'evidence'))

    def test_invalid_selection_preserves_metadata(self):
        before = (self.root/'package.json').read_bytes()
        for key, value in [('ACTION_REF','main'), ('PREPACKED_MODE','other'), ('PREPACKED_VERSION','0.0.1-native.0'), ('GITHUB_SHA','x')]:
            with self.assertRaises(ValueError):
                P['prepare']({**self.env,key:value}, self.root)
            self.assertEqual((self.root/'package.json').read_bytes(), before)

    def test_ordinary_policy_preserves_existing_package_and_channels(self):
        for mode in ['direct','stage']:
            package = P['prepare']({**self.env,'PREPACKED_MODE':mode}, self.root)
            self.assertEqual(package['name'],'@releaseway/npm-actions-fixture')
            self.assertEqual(package['version'],self.env['PREPACKED_VERSION'])
            self.assertNotIn('bin',package)
            policy = (self.root/'.github/npm/packages.yml').read_text()
            self.assertIn('mode: '+mode,policy)
            self.assertIn('prerelease: next',policy)
            self.assertNotIn('distribution:',policy)

    def evidence_fixture(self, mode):
        env = {**self.env,'PREPACKED_MODE':mode,'WORKFLOW_FILE':'direct.yml' if mode=='direct' else 'publish.yml'}
        bundle = Path(env['BUNDLE_DIR']); bundle.mkdir()
        digest = 'sha512-' + 'A'*86 + '=='
        source = dict(repository=env['GITHUB_REPOSITORY'],commit=env['GITHUB_SHA'])
        entry = dict(name='@releaseway/npm-actions-fixture',version=env['PREPACKED_VERSION'],tarball='package.tgz',integrity=digest)
        (bundle/'artifacts.json').write_text(json.dumps(dict(schema=1,source=source,packages=[entry])))
        state = 'published' if mode=='direct' else 'staged'
        row = dict(name=entry['name'],version=entry['version'],coverage='supplied',expectedIntegrity=digest,localIntegrity=digest,
                   localVerification='matched',publicVerification='matched' if mode=='direct' else 'not-checked',
                   publicIntegrity=digest if mode=='direct' else None,publication=state)
        report = dict(schema=1,status='success',preflight='passed',source=source,publicationCommit=env['GITHUB_SHA'],
                      manifestIntegrity=P['integrity'](bundle/'artifacts.json'),packages=[row])
        negative = dict(status='failed',source=source,preflight='not-complete',packages=[dict(row,localVerification='mismatched')],
                        error=dict(code='ARTIFACT_INTEGRITY_MISMATCH',remoteState='unchanged',package=dict(name=entry['name'],version=entry['version'])))
        paths = dict(ARTIFACT_REPORT=self.root/'report.json', NEGATIVE_REPORT=self.root/'negative.json', RETRY_REPORT=self.root/'retry.json')
        for key, path in paths.items(): env[key]=str(path)
        paths['ARTIFACT_REPORT'].write_text(json.dumps(report)); paths['NEGATIVE_REPORT'].write_text(json.dumps(negative))
        paths['RETRY_REPORT'].write_text(json.dumps(dict(report,packages=[dict(row,localVerification='not-required',publication='already-published')])))
        env['PACKAGES']=json.dumps([dict(name=entry['name'],version=entry['version'],state=state)])
        env['RETRY_PACKAGES']=json.dumps([dict(name=entry['name'],version=entry['version'],state='already-published')])
        return env, report

    def test_direct_receipt_binds_source_bytes_and_fileless_retry(self):
        env, report = self.evidence_fixture('direct')
        receipt = V['verify'](env)
        self.assertEqual(receipt['source_artifact_id'],11)
        self.assertEqual(receipt['retry_state'],'already-published')
        for key, value in [('ACTION_REF','main'),('SOURCE_ARTIFACT_ID','0'),('WORKFLOW_FILE','other.yml')]:
            with self.assertRaises(ValueError): V['verify']({**env,key:value})
        report['source']=dict(report['source'],commit='c'*40)
        Path(env['ARTIFACT_REPORT']).write_text(json.dumps(report))
        with self.assertRaises(ValueError): V['verify'](env)

    def test_stage_receipt_never_claims_public_integrity_or_approval(self):
        env, report = self.evidence_fixture('stage')
        receipt = V['verify'](env)
        self.assertEqual(receipt['state'],'staged'); self.assertIsNone(receipt['retry_state'])
        report['packages'][0]['publicVerification']='matched'
        Path(env['ARTIFACT_REPORT']).write_text(json.dumps(report))
        with self.assertRaises(ValueError): V['verify'](env)


if __name__=='__main__': unittest.main()
