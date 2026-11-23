#!/usr/bin/env python3
"""Build an unsigned Windows x64 portable ZIP from this checkout."""
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
TARGET = 'x86_64-pc-windows-msvc'


def main():
    if platform.system() != 'Windows':
        raise SystemExit('The portable package requires a Windows host with MSVC and the Windows SDK.')

    identity = json.loads((ROOT / 'packaging/identity.json').read_text(encoding='utf-8'))
    name = f"Oink-{identity['version']}-windows-x64-portable"
    target_dir = ROOT / 'target' / 'portable'
    output = ROOT / 'dist' / 'portable'
    env = dict(os.environ, CARGO_TARGET_DIR=str(target_dir))
    flags = env.get('CARGO_ENCODED_RUSTFLAGS', '')
    if not flags and env.get('RUSTFLAGS'):
        raise SystemExit('Use CARGO_ENCODED_RUSTFLAGS for custom Rust flags when packaging.')
    env['CARGO_ENCODED_RUSTFLAGS'] = '\x1f'.join(filter(None, [
        flags, '-C', 'target-feature=+crt-static',
    ]))
    subprocess.run(['npm.cmd', 'ci'], cwd=ROOT, env=env, check=True)
    subprocess.run([
        'npm.cmd', 'run', '-w', 'apps/oink', 'tauri', '--', 'build', '--ci',
        '--no-bundle', '--no-sign', '--target', TARGET, '--features', 'windows-portable',
        '--', '--locked',
    ], cwd=ROOT, env=env, check=True)

    exe_name = identity['binaries']['ui'] + '.exe'
    exe = target_dir / TARGET / 'release' / exe_name
    files = {'Oink.exe': exe, 'README.txt': ROOT / 'packaging/windows/portable.txt'}
    for notice in ('LICENSE', 'LICENSE-ADDITIONAL-TERMS.md', 'NOTICE', 'PRIVACY.md', 'THIRD_PARTY_LICENSES.md'):
        files[notice] = ROOT / notice

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        archive = Path(temporary) / f'{name}.zip'
        with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=9) as package:
            for filename, path in files.items():
                package.write(path, f'{name}/{filename}')
        archive.replace(output / archive.name)
    print(output / archive.name)


if __name__ == '__main__':
    main()
