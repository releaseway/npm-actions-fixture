"""Validate candidate identity/version before changing fixture metadata."""
import json
import os
from pathlib import Path
import re
import subprocess


def prepare(env=os.environ, root=Path('.')):
    candidate = env['ACTION_REF']
    if not re.fullmatch(r'[0-9a-fA-F]{40}', candidate):
        raise ValueError('action-ref must be a full 40-character commit SHA')
    kind = env['FIXTURE_KIND']
    version = env['FIXTURE_VERSION']
    if kind not in ('fixture', 'native') or not re.fullmatch(r'0\.0\.[1-9][0-9]*-' + kind + r'\.[0-9]+', version):
        raise ValueError('invalid fixture version')
    source = env['VERSION_SOURCE']
    if source not in ('package-json', 'git-tag'):
        raise ValueError('invalid version-source')
    if source == 'git-tag':
        tag = 'npm-fixture-v' + version
        subprocess.run(['git', 'fetch', 'origin', f'refs/tags/{tag}:refs/tags/{tag}'], cwd=root, check=True)
        commit = subprocess.check_output(['git', 'rev-parse', tag + '^{commit}'], cwd=root, text=True).strip()
        if commit != env['GITHUB_SHA']:
            raise ValueError('version tag must target the fixture workflow commit')
    package_path = root / 'package.json'
    package = json.loads(package_path.read_text())
    if source == 'package-json':
        package['version'] = version
    if kind == 'native':
        package['bin'] = {'npm-actions-native-fixture': 'bin/npm-actions-native-fixture'}
        package['publishConfig']['tag'] = 'native'
    policy = 'schema: 1\n\npublish:\n  mode: ' + ('direct' if kind == 'native' else 'stage') + '\n'
    if source == 'git-tag':
        policy += '\nversion:\n  source: git-tag\n  prefix: npm-fixture-v\n  prerelease-tag: ' + kind + '\n'
    if kind == 'native':
        policy += '''
packages:
  "@releaseway/npm-actions-fixture":
    distribution:
      type: github-release
      tag: "native-v{version}"
      targets:
        linux-x64-gnu:
          asset: npm-actions-native-fixture_linux_x64.tar.gz
          executable: bin/npm-actions-native-fixture
'''
    package_path.write_text(json.dumps(package, indent=2) + '\n')
    (root / '.github/npm/packages.yml').write_text(policy)
    with open(env['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'version={version}\ntag=native-v{version}\nasset=npm-actions-native-fixture_linux_x64.tar.gz\n')


if __name__ == '__main__':
    prepare()
