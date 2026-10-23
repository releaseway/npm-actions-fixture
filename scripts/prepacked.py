"""Produce a verified ordinary tarball for the existing fixture package identity."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def integrity(path):
    return 'sha512-' + base64.b64encode(hashlib.sha512(Path(path).read_bytes()).digest()).decode()


def prepare(env=os.environ, root=Path('.')):
    version = env['PREPACKED_VERSION']
    mode = env['PREPACKED_MODE']
    if not re.fullmatch(r'0\.0\.[1-9][0-9]*-prepacked\.[0-9]+', version) or version == env.get('FIXTURE_VERSION'):
        raise ValueError('prepacked-version must be a distinct fresh 0.0.N-prepacked.M version')
    if mode not in ('direct', 'stage') or not re.fullmatch(r'[0-9a-fA-F]{40}', env['ACTION_REF']):
        raise ValueError('invalid prepacked mode or exact candidate SHA')
    if not re.fullmatch(r'[0-9a-f]{40}', env['GITHUB_SHA']):
        raise ValueError('invalid fixture source SHA')
    package = json.loads((root/'package.json').read_text())
    package['version'] = version
    package.pop('bin', None)
    (root/'package.json').write_text(json.dumps(package, indent=2) + '\n')
    (root/'.github/npm').mkdir(parents=True, exist_ok=True)
    (root/'.github/npm/packages.yml').write_text(
        'schema: 1\npublish:\n  mode: ' + mode + '\n  channels:\n    stable: latest\n    prerelease: next\n')
    return package


def build(env=os.environ, root=Path('.')):
    package = prepare(env, root)
    output = Path(env['BUNDLE_DIR']).resolve()
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(['npm', 'pack', '--ignore-scripts', '--pack-destination', str(output)], cwd=root, check=True)
    tarballs = list(output.glob('*.tgz'))
    if len(tarballs) != 1:
        raise ValueError('expected exactly one producer tarball')
    tarball = tarballs[0]
    # Install the actual archive, never the source workspace. Scripts stay disabled.
    with tempfile.TemporaryDirectory(prefix='prepacked-consumer-') as directory:
        subprocess.run(['npm', 'install', '--ignore-scripts', '--no-audit', '--no-fund', '--package-lock=false',
                        '--prefix', directory, str(tarball)], check=True)
        installed = Path(directory)/'node_modules'/package['name']
        if json.loads((installed/'package.json').read_text())['version'] != package['version']:
            raise ValueError('installed consumer version differs')
        subprocess.run(['node', '--input-type=module', '-e',
            'const m = await import("@releaseway/npm-actions-fixture"); if (m.fixture !== "@releaseway/npm-actions-fixture") throw new Error("consumer exports differ");'],
            cwd=directory, check=True)
    manifest = dict(schema=1, source=dict(repository=env['GITHUB_REPOSITORY'], commit=env['GITHUB_SHA']),
                    packages=[dict(name=package['name'], version=package['version'], tarball=tarball.name, integrity=integrity(tarball))])
    path = output/'artifacts.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def bad(env=os.environ):
    output = Path(env['BUNDLE_DIR'])
    manifest = json.loads((output/'artifacts.json').read_text())
    manifest['packages'][0]['integrity'] = 'sha512-' + base64.b64encode(bytes(64)).decode()
    (output/'wrong.json').write_text(json.dumps(manifest) + '\n')


if __name__ == '__main__':
    {'prepare': prepare, 'build': build, 'bad': bad}[sys.argv[1]]()
