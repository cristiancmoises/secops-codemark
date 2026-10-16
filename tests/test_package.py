import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import json

from codemark import __version__

REPO = Path(__file__).resolve().parents[1]


class PortablePackageTests(unittest.TestCase):
    def test_reproducible_portable_package_runs_outside_repository(self):
        builder = REPO / 'scripts/build.py'
        self.assertTrue(builder.is_file(), 'portable builder is not implemented')
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first, second = base / 'first', base / 'second'
            for output in (first, second):
                result = subprocess.run([sys.executable, str(builder), '--output', str(output)],
                    cwd=base, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((first / 'codemark.pyz').read_bytes(), (second / 'codemark.pyz').read_bytes())
            package = first / f'secops-codemark-{__version__}.zip'
            self.assertEqual(package.read_bytes(), (second / package.name).read_bytes())
            with zipfile.ZipFile(package) as archive:
                prefix = f'secops-codemark-{__version__}/'
                self.assertIn(prefix + 'COPYING', archive.namelist())
                self.assertIn(prefix + 'PROMPT-GOD-TIER.md', archive.namelist())
                self.assertIn(prefix + 'PROMPT-PRODUCAO-0.2.0.md', archive.namelist())
                checksums = archive.read(prefix + 'SHA256SUMS').decode().splitlines()
                for line in checksums:
                    expected, name = line.split('  ', 1)
                    self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), expected)
            executable = first / 'codemark.pyz'
            result = subprocess.run([sys.executable, '-I', str(executable), 'doctor', '--json'],
                                    cwd=base, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['version'], __version__)
            result = subprocess.run([sys.executable, '-I', str(executable), 'self-test', '--json'],
                                    cwd=base, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['ok'])
            project = base / 'project'
            project.mkdir()
            script = project / 'hello.py'
            original = b'print("portable")\n'
            script.write_bytes(original)
            for args in [('mark', project, '--owner', 'Package Test', '--apply'),
                         ('verify', project), ('unmark', project, '--apply')]:
                result = subprocess.run([sys.executable, '-I', str(executable), *map(str, args)],
                                        cwd=base, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(script.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
