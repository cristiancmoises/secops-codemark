"""Reversible source marks and bounded, offline provenance inventories.

SPDX-License-Identifier: GPL-3.0-or-later
"""
from contextlib import contextmanager, nullcontext
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import uuid

from .fingerprint import fingerprint, similarity

MAX_FILES = 5000
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_PAIRS = 2_000_000
MAX_MATCHES = 10000
MAX_ENTRIES = 20000
MAX_METADATA_BYTES = 64 * 1024 * 1024
MARK_OVERHEAD_BYTES = 4096
EXCLUDED = {'.git', '.hg', '.svn', '.codemark', '.venv', 'venv', 'node_modules',
            'vendor', 'third_party', 'third-party', 'dist', 'build', 'target',
            '__pycache__', '.cache', '.tox', '.mypy_cache', '.pytest_cache'}
STYLES = {
    'hash': ('.py .pyw .sh .bash .zsh .fish .rb .pl .ps1 .yaml .yml .toml .r .nix .cmake', '#', ''),
    'scheme': ('.scm .ss .sld .el .lisp .cl .clj .cljs .rkt', ';;', ''),
    'slash': ('.js .mjs .cjs .jsx .ts .tsx .c .h .cc .cpp .cxx .hpp .java .cs .go .rs .kt .kts .swift .dart .proto', '//', ''),
    'block': ('.css .scss .less', '/*', ' */'),
    'markup': ('.html .htm .xml .svg .vue .svelte', '<!--', ' -->'),
    'dash': ('.sql .lua', '--', ''),
}
EXTENSIONS = {ext: family for family, (extensions, _, _) in STYLES.items() for ext in extensions.split()}
MARK_RE = re.compile(r'^(?:#|;;|//|/\*|<!--|--) CodeMark v1 project=([0-9a-f-]{36}) file=([0-9a-f]{32}) owner=("(?:[^"\\]|\\.)*")(?: \*/| -->)?(?:\r?\n)?$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX32 = re.compile(r'^[0-9a-f]{32}$')
HEX16 = re.compile(r'^[0-9a-f]{16}$')


class CodeMarkError(Exception):
    """Expected, user-facing failure; never contains source snippets."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode('utf-8')


def safe_relative(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        return False
    path = PurePosixPath(name)
    return (not path.is_absolute() and path.as_posix() == name and
            all(part not in ('.', '..', '') for part in path.parts) and
            all(ord(char) >= 32 and ord(char) != 127 for char in name))


def checked_root(root):
    path = Path(os.path.abspath(os.fspath(root)))
    for item in (path, *path.parents):
        if item.is_symlink():
            raise CodeMarkError('Links simbólicos na raiz/caminho não são aceitos.')
    if not path.is_dir():
        raise CodeMarkError('A raiz precisa ser um diretório existente.')
    metadata = path / '.codemark'
    if metadata.is_symlink() or (metadata.exists() and not metadata.is_dir()):
        raise CodeMarkError('.codemark precisa ser um diretório local, sem link.')
    if metadata.exists():
        for name in ('project.json', 'manifest.json', 'manifest.json.asc', 'manifest.json.sshsig', 'lock'):
            item = metadata / name
            if item.is_symlink() or (item.exists() and not item.is_file()):
                raise CodeMarkError('Metadado inválido ou link em .codemark: ' + name)
    return path


def read_regular(path, limit):
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise CodeMarkError('Arquivo especial ou link não aceito: ' + path.name)
        if before.st_size > limit:
            raise CodeMarkError('Arquivo excede o limite de tamanho: ' + path.name)
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, 'rb') as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_ino, opened.st_dev) != (before.st_ino, before.st_dev):
                raise CodeMarkError('Arquivo alterado durante a leitura: ' + path.name)
            data = handle.read(limit + 1)
        if len(data) > limit:
            raise CodeMarkError('Arquivo excede o limite de tamanho: ' + path.name)
        return data
    except OSError as error:
        raise CodeMarkError('Falha ao ler arquivo: ' + path.name) from error


def inventory(root):
    sources, skipped = {}, []
    total = 0
    visited = 0

    def walk(directory, depth=0):
        nonlocal total, visited
        if depth > 64:
            raise CodeMarkError('Profundidade máxima de diretórios excedida.')
        try:
            entries = []
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    visited += 1
                    if visited > MAX_ENTRIES:
                        raise CodeMarkError(f'Mais de {MAX_ENTRIES} entradas; selecione uma raiz menor.')
                    entries.append(entry)
            entries.sort(key=lambda entry: entry.name)
        except OSError as error:
            raise CodeMarkError('Não foi possível listar um diretório.') from error
        for entry in entries:
            path = Path(entry.path)
            name = path.relative_to(root).as_posix()
            if not safe_relative(name):
                raise CodeMarkError('Nome de arquivo não portátil/seguro na árvore.')
            if entry.name in EXCLUDED:
                skipped.append({'path': name, 'reason': 'VCS/dependência/build/metadados'})
                continue
            if entry.is_symlink():
                raise CodeMarkError('Link simbólico não aceito: ' + name)
            if entry.is_dir(follow_symlinks=False):
                walk(path, depth + 1)
                continue
            if not entry.is_file(follow_symlinks=False):
                raise CodeMarkError('Arquivo especial não aceito: ' + name)
            family = EXTENSIONS.get(path.suffix.lower())
            if entry.name in ('Makefile', 'GNUmakefile', 'CMakeLists.txt'):
                family = 'hash'
            if not family or '.min.' in entry.name:
                skipped.append({'path': name, 'reason': 'formato não suportado/gerado'})
                continue
            data = read_regular(path, MAX_FILE_BYTES + MARK_OVERHEAD_BYTES)
            try:
                text = data.decode('utf-8-sig')
            except UnicodeDecodeError:
                skipped.append({'path': name, 'reason': 'encoding diferente de UTF-8'})
                continue
            if '\x00' in text:
                skipped.append({'path': name, 'reason': 'conteúdo binário'})
                continue
            if '# SIG # Begin signature block' in text:
                skipped.append({'path': name, 'reason': 'script já assinado; não alterar'})
                continue
            if text.startswith('#!') and '\n' not in text:
                skipped.append({'path': name, 'reason': 'shebang sem quebra de linha'})
                continue
            position = header_offset(text)
            if position and not text[:position].endswith(('\n', '\r')) and family not in ('markup', 'block'):
                skipped.append({'path': name, 'reason': 'cabeçalho sem quebra de linha final'})
                continue
            logical_bytes = len(remove_marks(data, None))
            if logical_bytes > MAX_FILE_BYTES:
                raise CodeMarkError('Fonte excede 2 MiB, sem contar a marca: ' + name)
            if len(sources) >= MAX_FILES or total + logical_bytes > MAX_TOTAL_BYTES:
                raise CodeMarkError('Limite de fontes/bytes excedido; selecione uma raiz menor.')
            sources[name] = {'data': data, 'family': family, 'mode': stat.S_IMODE(path.stat().st_mode)}
            total += logical_bytes
    walk(root)
    return sources, skipped


def read_json(path):
    try:
        return json.loads(read_regular(path, MAX_METADATA_BYTES))
    except (ValueError, UnicodeDecodeError, RecursionError) as error:
        raise CodeMarkError('JSON inválido: ' + path.name) from error


def valid_config(config):
    if not isinstance(config, dict) or config.get('format') != 1:
        raise CodeMarkError('Formato de configuração inválido.')
    try:
        ident = str(uuid.UUID(config['project_id']))
        if ident != config['project_id']:
            raise ValueError('noncanonical uuid')
        for field, maximum in (('owner', 200), ('project', 200)):
            if not isinstance(config[field], str) or not config[field].strip() or len(config[field]) > maximum:
                raise ValueError(field)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise CodeMarkError('Identidade do projeto inválida.') from error
    return config


def load_config(root, owner=None, project=None):
    path = root / '.codemark/project.json'
    if path.exists():
        config = valid_config(read_json(path))
        if owner is not None and owner != config['owner']:
            raise CodeMarkError('O titular difere da identidade registrada; use a identidade original.')
        if project is not None and project != config['project']:
            raise CodeMarkError('O nome difere da identidade registrada.')
        return config
    if not owner or not owner.strip():
        raise CodeMarkError('Informe --owner na primeira aplicação.')
    return valid_config({'format': 1, 'project_id': str(uuid.uuid4()), 'owner': owner, 'project': project or root.name})


def read_manifest(root, raw=None):
    if raw is None:
        manifest = read_json(root / '.codemark/manifest.json')
    else:
        try:
            manifest = json.loads(raw)
        except (ValueError, UnicodeDecodeError, RecursionError) as error:
            raise CodeMarkError('JSON inválido: manifest.json') from error
    if not isinstance(manifest, dict):
        raise CodeMarkError('Manifesto precisa ser um objeto JSON.')
    valid_config(manifest)
    files = manifest.get('files')
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES:
        raise CodeMarkError('Inventário do manifesto inválido.')
    for name, record in files.items():
        if not safe_relative(name) or name.split('/')[0] in EXCLUDED or not isinstance(record, dict):
            raise CodeMarkError('Caminho/registro inválido no manifesto.')
        try:
            if record['family'] not in STYLES or not HEX32.fullmatch(record['marker_id']):
                raise ValueError('marker')
            if any(not HEX64.fullmatch(record[field]) for field in ('sha256', 'source_sha256', 'normalized_sha256')):
                raise ValueError('hash')
            if type(record['tokens']) is not int or not 0 <= record['tokens'] <= MAX_FILE_BYTES * 2:
                raise ValueError('tokens')
            sketch = record['sketch']
            if not isinstance(sketch, list) or len(sketch) > 256 or any(not isinstance(x, str) or not HEX16.fullmatch(x) for x in sketch):
                raise ValueError('sketch')
        except (KeyError, TypeError, ValueError) as error:
            raise CodeMarkError('Campos inválidos no manifesto: ' + name) from error
    return manifest


def header_offset(text):
    """A comment can only be inserted/removed at this protected prologue slot."""
    if re.match(r'^<\?xml(?:\s|$)', text):
        end = text.find('?>')
        if end < 0:
            raise CodeMarkError('Declaração XML incompleta.')
        end += 2
        return end + (2 if text[end:].startswith('\r\n') else 1 if text[end:].startswith('\n') else 0)
    charset = re.match(r'''^@charset[ \t]+(?:"[^"\r\n]*"|'[^'\r\n]*')[ \t]*;''', text, re.IGNORECASE)
    if charset:
        end = charset.end()
        return end + (2 if text[end:].startswith('\r\n') else 1 if text[end:].startswith('\n') else 0)
    lines = text.splitlines(keepends=True)
    offset, position = 0, 0
    for index, line in enumerate(lines[:2]):
        if MARK_RE.fullmatch(line):
            break
        position += len(line)
        if index == 0 and line.startswith('#!'):
            offset = position
        if re.match(r'^\s*#.*coding[:=]\s*[-\w.]+', line):
            offset = position
        if line.lstrip().startswith(('#', ';', '//', '/*')) and '-*-' in line:
            offset = position
        if re.match(r'^\s*#\s*(?:frozen_string_literal|warn_indent)\s*:', line):
            offset = position
    return offset


def parse_mark(line):
    match = MARK_RE.fullmatch(line)
    if not match:
        return None
    try:
        ident = str(uuid.UUID(match[1]))
        owner = json.loads(match[3])
        if ident != match[1] or not isinstance(owner, str) or len(owner) > 200:
            return None
        body = line.rstrip('\r\n')
        for _, opening, closing in STYLES.values():
            if body.startswith(opening + ' CodeMark v1 '):
                if closing and not body.endswith(closing):
                    return None
                if not closing and not body.endswith(match[3]):
                    return None
                return ident, match[2], owner
    except (ValueError, TypeError):
        pass
    return None


def header_marks(text):
    offset = header_offset(text)
    cursor, items = offset, []
    while cursor < len(text):
        end = text.find('\n', cursor)
        end = len(text) if end < 0 else end + 1
        line = text[cursor:end]
        marker = parse_mark(line)
        if marker is None:
            break
        items.append((line, marker))
        cursor = end
    return text[:offset], items, text[cursor:]


def marks(data):
    _, items, _ = header_marks(data.decode('utf-8-sig'))
    return [marker for _, marker in items]


def remove_marks(data, project_id, owner=None):
    bom = b'\xef\xbb\xbf' if data.startswith(b'\xef\xbb\xbf') else b''
    prefix, items, rest = header_marks(data[len(bom):].decode('utf-8'))
    if project_id is not None and sum(marker[0] == project_id for _, marker in items) > 1:
        raise CodeMarkError('Marcas duplicadas/ambíguas no cabeçalho; revise o arquivo.')
    kept = [line for line, marker in items if not
            ((project_id is None or marker[0] == project_id) and (owner is None or marker[2] == owner))]
    return bom + (prefix + ''.join(kept) + rest).encode('utf-8')


def add_mark(data, family, name, config, marker_id):
    bom = b'\xef\xbb\xbf' if data.startswith(b'\xef\xbb\xbf') else b''
    text = data[len(bom):].decode('utf-8')
    newline = '\r\n' if '\r\n' in text else '\n'
    offset = header_offset(text)
    prefix, rest = text[:offset], text[offset:]
    owner = json.dumps(config['owner'], ensure_ascii=True).replace('/', '\\/').replace('-', '\\u002d').replace('<', '\\u003c').replace('>', '\\u003e')
    _, opening, closing = STYLES[family]
    line = f'{opening} CodeMark v1 project={config["project_id"]} file={marker_id} owner={owner}{closing}{newline}'
    return bom + (prefix + line + rest).encode('utf-8')


def atomic_write(path, data, mode=None):
    path = Path(path)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise CodeMarkError('Destino não é um arquivo local regular: ' + path.name)
    descriptor, temp_name = tempfile.mkstemp(prefix='.codemark-write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600 if mode is None else mode & 0o777)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


@contextmanager
def project_lock(root):
    metadata = root / '.codemark'
    metadata.mkdir(mode=0o700, exist_ok=True)
    checked_root(root)
    lock = metadata / 'lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except OSError as error:
        raise CodeMarkError('Projeto ocupado: existe .codemark/lock; verifique operações em andamento.') from error
    try:
        os.write(descriptor, str(os.getpid()).encode('ascii'))
        os.close(descriptor)
        yield
    finally:
        lock.unlink(missing_ok=True)


def transaction(root, changes):
    previous = []
    try:
        for path, data, mode in changes:
            checked_root(root)
            for parent in path.parents:
                if parent == root:
                    break
                if parent.is_symlink():
                    raise CodeMarkError('Diretório substituído por link durante operação.')
            old = read_regular(path, MAX_METADATA_BYTES) if path.exists() else None
            old_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else mode
            previous.append((path, old, old_mode))
            atomic_write(path, data, mode)
    except BaseException as error:
        failures = []
        for path, old, mode in reversed(previous):
            try:
                if old is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, old, mode)
            except (OSError, CodeMarkError):
                failures.append(path.name)
        detail = ' Rollback incompleto: ' + ', '.join(failures) if failures else ' Alterações revertidas.'
        raise CodeMarkError('Falha na gravação.' + detail) from error


def mark(root, owner=None, project=None, apply=False, *, before_commit=None):
    root = checked_root(root)
    with project_lock(root) if apply else nullcontext():
        return _mark(root, owner, project, apply, before_commit)


def _mark(root, owner, project, apply, before_commit):
    config = load_config(root, owner, project)
    sources, skipped = inventory(root)
    if not sources:
        raise CodeMarkError('Nenhum fonte UTF-8 suportado nesta raiz.')
    manifest = dict(config, files={})
    changes = []
    for name, record in sources.items():
        original = remove_marks(record['data'], config['project_id'], config['owner'])
        marker_id = uuid.uuid5(uuid.UUID(config['project_id']), name).hex
        output = add_mark(original, record['family'], name, config, marker_id)
        if len(output) > MAX_FILE_BYTES + MARK_OVERHEAD_BYTES:
            raise CodeMarkError('Fonte com marca excede o limite de leitura: ' + name)
        manifest['files'][name] = dict(fingerprint(original.decode('utf-8-sig'), record['family']),
            family=record['family'], marker_id=marker_id, source_sha256=digest(original), sha256=digest(output))
        if output != record['data']:
            changes.append((root / name, output, record['mode']))
    count = len(changes)
    config_bytes, manifest_bytes = json_bytes(config), json_bytes(manifest)
    if max(len(config_bytes), len(manifest_bytes)) > MAX_METADATA_BYTES:
        raise CodeMarkError('Manifesto gerado excede 64 MiB; selecione uma raiz menor.')
    report = {'action': 'mark', 'applied': apply, 'project': config['project'], 'owner': config['owner'],
              'project_id': config['project_id'], 'planned': count, 'changed': count if apply else 0,
              'files': len(sources), 'skipped': skipped, 'paths': list(sources), 'authenticated': False}
    if apply:
        # File contents, output sizes and metadata are validated before writing.
        changes.extend([(root / '.codemark/project.json', config_bytes, 0o644),
                        (root / '.codemark/manifest.json', manifest_bytes, 0o644)])
        if before_commit:
            before_commit(report)
        transaction(root, changes)
    return report


def unmark(root, apply=False, *, before_commit=None):
    root = checked_root(root)
    with project_lock(root) if apply else nullcontext():
        return _unmark(root, apply, before_commit)


def _unmark(root, apply, before_commit):
    config = load_config(root)
    if not (root / '.codemark/project.json').exists():
        raise CodeMarkError('Projeto sem identidade registrada.')
    sources, skipped = inventory(root)
    changes = []
    for name, record in sources.items():
        output = remove_marks(record['data'], config['project_id'], config['owner'])
        if output != record['data']:
            changes.append((root / name, output, record['mode']))
    report = {'action': 'unmark', 'applied': apply, 'planned': len(changes),
            'changed': len(changes) if apply else 0, 'skipped': skipped,
            'note': 'O manifesto permanece como referência anterior; verify apontará as marcas removidas.'}
    if apply:
        if before_commit:
            before_commit(report)
        transaction(root, changes)
    return report


def verify(root):
    root = checked_root(root)
    raw_manifest = read_regular(root / '.codemark/manifest.json', MAX_METADATA_BYTES)
    manifest = read_manifest(root, raw_manifest)
    sources, skipped = inventory(root)
    changed, missing, invalid_marks = [], [], []
    for name, reference in manifest['files'].items():
        record = sources.get(name)
        if record is None:
            missing.append(name)
            continue
        if digest(record['data']) != reference['sha256']:
            changed.append(name)
        expected = (manifest['project_id'], reference['marker_id'], manifest['owner'])
        if marks(record['data']).count(expected) != 1:
            invalid_marks.append(name)
    untracked = sorted(set(sources) - set(manifest['files']))
    return {'action': 'verify', 'ok': not (changed or missing or untracked or invalid_marks),
            'project': manifest['project'], 'owner': manifest['owner'],
            'files': len(manifest['files']), 'changed': changed, 'missing': missing,
            'untracked': untracked, 'invalid_marks': invalid_marks, 'skipped': skipped,
            'manifest_sha256': digest(raw_manifest),
            'authenticated': False, 'note': 'Manifesto local; autenticação exige assinatura e chave fixada.'}


def compare(root, suspect, threshold=0.65):
    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 < threshold <= 1:
        raise CodeMarkError('O limiar precisa estar entre 0 (exclusivo) e 1.')
    root, suspect = checked_root(root), checked_root(suspect)
    manifest = read_manifest(root)
    candidates, skipped = inventory(suspect)
    if len(candidates) * len(manifest['files']) > MAX_PAIRS:
        raise CodeMarkError('Comparação excede 2.000.000 pares; use uma pasta menor.')
    matches_found = []
    by_id = {record['marker_id']: name for name, record in manifest['files'].items()}
    for name, candidate in candidates.items():
        claimed = {ident for project_id, ident, _ in marks(candidate['data']) if project_id == manifest['project_id']}
        clean = remove_marks(candidate['data'], manifest['project_id'])
        raw_hash = digest(clean)
        fp = fingerprint(clean.decode('utf-8-sig'), candidate['family'])
        for reference_name, reference in manifest['files'].items():
            method, score = None, 0.0
            if any(by_id.get(ident) == reference_name for ident in claimed):
                method, score = 'watermark', 1.0
            elif raw_hash == reference['source_sha256']:
                method, score = 'exact-content', 1.0
            elif candidate['family'] == reference['family'] and min(fp['tokens'], reference['tokens']) >= 40 and min(len(fp['sketch']), len(reference['sketch'])) >= 8:
                if fp['normalized_sha256'] == reference['normalized_sha256']:
                    method, score = 'normalized-tokens', 1.0
                else:
                    score = similarity(fp['sketch'], reference['sketch'])
                    if score >= threshold:
                        method = 'token-similarity'
            if method:
                if len(matches_found) >= MAX_MATCHES:
                    raise CodeMarkError(f'Comparação excede {MAX_MATCHES} candidatos; use pastas menores. Nenhum resultado parcial foi entregue.')
                matches_found.append({'reference': reference_name, 'candidate': name,
                                      'method': method, 'similarity': round(score, 4)})
    matches_found.sort(key=lambda item: (-item['similarity'], item['candidate'], item['reference']))
    return {'action': 'compare', 'matches': matches_found, 'threshold': threshold,
            'reference_files': len(manifest['files']), 'candidate_files': len(candidates),
            'skipped': skipped, 'authenticated': False,
            'note': 'Indícios heurísticos; marcas podem ser forjadas e similaridade não prova plágio.'}
