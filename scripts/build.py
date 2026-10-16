#!/usr/bin/env python3
"""Build deterministic zipapp and source archive. GPL-3.0-or-later."""
import argparse
import hashlib
import io
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from codemark import __version__


def archive_bytes(entries, prefix=b''):
    output = io.BytesIO()
    output.write(prefix)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            mode = 0o755 if name.endswith(('.sh', '.pyz')) else 0o644
            item.external_attr = (0o100000 | mode) << 16
            archive.writestr(item, data)
    return output.getvalue()


def checksum_entries(entries):
    return ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
                   for name, data in sorted(entries.items())).encode('utf-8')


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    package = {str(path.relative_to(ROOT)).replace('\\', '/'): path.read_bytes()
               for path in sorted((ROOT / 'codemark').glob('*.py'))}
    package['__main__.py'] = b'from codemark.cli import main\nraise SystemExit(main())\n'
    package['COPYING'] = (ROOT / 'COPYING').read_bytes()
    portable = archive_bytes(package, b'#!/usr/bin/env python3\n')
    (output / 'codemark.pyz').write_bytes(portable)
    (output / 'codemark.pyz').chmod(0o755)
    sources = {}
    for directory in ('codemark', 'docs', 'tests', 'scripts', 'examples', '.github'):
        for path in sorted((ROOT / directory).rglob('*')):
            if path.is_symlink():
                raise RuntimeError('Do not ship symlinks: ' + str(path))
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                sources[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in ('README.md', 'COPYING', 'PROMPT-GOD-TIER.md', 'PROMPT-PRODUCAO-0.2.0.md', 'codemark.py', 'iniciar.sh',
                 'Iniciar.bat', '.gitignore', 'CHANGELOG.md'):
        if (ROOT / name).is_file():
            sources[name] = (ROOT / name).read_bytes()
    sources['codemark.pyz'] = portable
    sources['SHA256SUMS'] = checksum_entries(sources)
    name = f'secops-codemark-{__version__}.zip'
    prefix = f'secops-codemark-{__version__}/'
    zipped = archive_bytes({prefix + key: value for key, value in sources.items()})
    (output / name).write_bytes(zipped)
    (output / 'SHA256SUMS').write_bytes(checksum_entries({'codemark.pyz': portable, name: zipped}))
    return output / name


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    print(build(args.output.resolve()))
