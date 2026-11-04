"""Read published nk journals without modifying the user's working tree."""
from datetime import datetime, timezone
import hashlib
import re
import subprocess
import threading


def latest_entry(text):
    """nk journals append level-two entries; fenced headings are content."""
    heading, lines, fence = None, [], None
    for line in text.splitlines():
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$', line)
        if marker:
            run, suffix = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not suffix.strip():
                fence = None
        if fence is None and line.startswith('## '):
            heading, lines = line[3:].strip(), []
        elif heading is not None:
            lines.append(line)
    if heading is None:
        return None
    body = '\n'.join(lines).strip()
    # An extractive summary keeps source wording and needs no model service.
    paragraph = re.split(r'\n\s*\n', body, maxsplit=1)[0]
    summary = ' '.join(paragraph.split())
    if len(summary) > 320:
        summary = summary[:317].rsplit(' ', 1)[0] + '…'
    return {'heading': heading, 'summary': summary, 'body': body}


def git(path, *args):
    result = subprocess.run(['git', '-C', path, *args], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip()[-1500:])
    return result.stdout


def published_journals(workspace, ids):
    path, remote, branch = (workspace[key] for key in ('path', 'remote', 'branch'))
    identity = hashlib.sha256(f'{remote}\0{branch}'.encode()).hexdigest()[:16]
    ref = 'refs/nk-dashboard/' + identity
    git(path, 'check-ref-format', 'refs/heads/' + branch)
    git(path, 'fetch', '--no-tags', '--', remote, f'+refs/heads/{branch}:{ref}')
    revision = git(path, 'rev-parse', ref).strip()
    if git(path, 'show', revision + ':.nk/workspace').strip() != '1':
        raise ValueError('Published branch is not an nk workspace')
    paths = set(git(path, 'ls-tree', '-r', '--name-only', revision, '--', 'scratch').splitlines())
    entries = {}
    for task_id in ids:
        # Card IDs need not be nk slugs, but must never address other paths.
        if '/' in task_id or '\\' in task_id or task_id in ('.', '..'):
            continue
        path_in_repo = f'scratch/{task_id}/JOURNAL.md'
        if path_in_repo in paths:
            entry = latest_entry(git(path, 'show', revision + ':' + path_in_repo))
            if entry is not None:
                entries[task_id] = entry
    return revision, entries


class Journals:
    def __init__(self):
        self.lock = threading.Lock()
        self.workspace = None
        self.entries = {}
        self.status = {'updated_at': None, 'revision': None, 'error': None}

    def refresh(self, workspace, ids):
        with self.lock:
            if self.workspace != workspace:
                self.workspace = workspace
                self.entries = {}
                self.status = {'updated_at': None, 'revision': None, 'error': None}
        if workspace is None:
            return
        try:
            revision, entries = published_journals(workspace, ids)
            status = {'updated_at': datetime.now(timezone.utc).isoformat(), 'revision': revision, 'error': None}
            with self.lock:
                self.entries, self.status = entries, status
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            self.failed(str(error))

    def failed(self, error):
        with self.lock:
            self.status = {**self.status, 'error': error}

    def decorate(self, board):
        with self.lock:
            board['tasks'] = {key: {**record, 'journal': self.entries.get(key)} for key, record in board['tasks'].items()}
            board['journal_sync'] = dict(self.status)
        return board
