"""Configured task assignments shared by the CLI and local interactive board."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import string
import subprocess
import sys
import tempfile
import threading
from journals import Journals
from urllib.parse import urlsplit

FIELDS = ('task', 'mission', 'url')


def link_url(value):
    if value and not value.startswith('/') and urlsplit(value).scheme not in ('https', 'http', 'file'):
        raise ValueError('Links must be http(s), file URLs, or absolute file paths')
    return value


def read_config(path):
    data = json.loads(path.read_text())
    agents = data.get('agents')
    if not isinstance(agents, list):
        raise ValueError('Configuration requires an agents list')
    names = set()
    for agent in agents:
        name = agent.get('name') if isinstance(agent, dict) else None
        if not isinstance(name, str) or not name.strip() or name != name.strip() or name.casefold() in names:
            raise ValueError('Agent names must be nonempty and unique')
        names.add(name.casefold())
    commands = data.get('commands', {})
    if not isinstance(commands, dict) or set(commands) - {'assign', 'unassign', 'archive'}:
        raise ValueError('Commands may define assign, unassign, and archive only')
    for action, argv in commands.items():
        if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) for arg in argv):
            raise ValueError(f'{action} must be a nonempty argument array')
        for arg in argv:
            for _, field, spec, conversion in string.Formatter().parse(arg):
                if field is not None and (field not in ('id', 'agent', *FIELDS) or spec or conversion):
                    raise ValueError(f'Unsupported command placeholder: {field}')
    workspace = data.get('workspace')
    if workspace is not None:
        if not isinstance(workspace, dict) or any(not isinstance(workspace.get(k), str) or not workspace[k].strip() for k in ('path', 'remote', 'branch')):
            raise ValueError('Workspace requires path, remote, and branch strings')
        workspace = {k: workspace[k] for k in ('path', 'remote', 'branch')}
        workspace['path'] = str(Path(workspace['path']).expanduser().resolve())
    return {'agents': agents, 'commands': commands, 'workspace': workspace}


def read_store(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if data.get('version') == 1:
        tasks = data.get('assignments')
    elif data.get('version') == 2:
        tasks = data.get('tasks')
    else:
        raise ValueError('Unsupported dashboard store version')
    if not isinstance(tasks, dict):
        raise ValueError('Expected task records')
    result, agents = {}, set()
    for key, record in tasks.items():
        if not key.strip() or not isinstance(record, dict):
            raise ValueError('Invalid task record')
        for field in (*FIELDS, 'updated_at'):
            if not isinstance(record.get(field), str):
                raise ValueError(f'{key}: {field} must be a string')
        if not record['task'].strip() or not record['mission'].strip():
            raise ValueError(f'{key}: task and mission must be nonempty')
        agent = record.get('agent')
        if agent is not None:
            if not isinstance(agent, str) or not agent.strip() or agent.casefold() in agents:
                raise ValueError('Invalid or duplicate agent assignment')
            agents.add(agent.casefold())
        link_url(record['url'])
        datetime.fromisoformat(record['updated_at'])
        result[key] = {field: record[field] for field in (*FIELDS, 'updated_at')}
        result[key]['agent'] = agent
    return result


def atomic_write(path, content):
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def note_path(directory, key):
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', key):
        raise ValueError('Note IDs must start with a letter or digit and contain only letters, digits, dots, underscores, or hyphens')
    path = directory / (key + '.md')
    if directory.is_symlink() or path.is_symlink():
        raise ValueError('Note paths must not be symbolic links')
    return path


def read_notes(directory):
    if directory.is_symlink():
        raise ValueError('Note paths must not be symbolic links')
    notes = {}
    for path in sorted(directory.glob('*.md')):
        path = note_path(directory, path.stem)
        if not path.is_file():
            raise ValueError('Notes must be regular Markdown files')
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW)) as stream:
            notes[path.stem] = stream.read()
    return notes


def snapshot(config, tasks, notes):
    names = {agent['name'] for agent in config['agents']}
    unknown = {t['agent'] for t in tasks.values() if t['agent'] is not None} - names
    if unknown:
        raise ValueError(f'Assigned agents missing from configuration: {sorted(unknown)}')
    revision = hashlib.sha256(json.dumps([config, tasks, notes], sort_keys=True).encode()).hexdigest()
    return {'agents': [{'name': agent['name']} for agent in config['agents']], 'tasks': tasks, 'notes': notes, 'revision': revision}


class Board:
    def __init__(self, directory, config_path):
        self.directory = directory
        self.path = directory / 'assignments.json'
        self.notes_directory = directory / 'notes'
        self.config_path = config_path
        self.journals = Journals()

    def read(self):
        with locked(self.directory):
            result = snapshot(read_config(self.config_path), read_store(self.path), read_notes(self.notes_directory))
        return self.journals.decorate(result)

    def save(self, tasks):
        atomic_write(self.path, json.dumps({'version': 2, 'tasks': tasks}, indent=2) + '\n')

    def hook(self, config, action, key, record):
        template = config['commands'].get(action)
        if template is None:
            return
        argv = [arg.format(id=key, **record) for arg in template]
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired as error:
            raise ValueError(f'{action} command timed out; external outcome is unknown. Check the agent before retrying.') from error
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()[-2000:]
            raise ValueError(f'{action} command failed ({result.returncode}): {detail}')

    def action(self, action, key, agent=None, fields=None, revision=None, markdown=None):
        with locked(self.directory):
            config, tasks = read_config(self.config_path), read_store(self.path)
            notes = read_notes(self.notes_directory)
            current = snapshot(config, tasks, notes)
            if revision is not None and revision != current['revision']:
                raise ValueError('The board changed. Refresh and try again.')
            if not isinstance(key, str) or not key.strip():
                raise ValueError('Task ID must be nonempty')
            if action in ('pin-note', 'remove-note'):
                path = note_path(self.notes_directory, key)
                if agent is not None or fields:
                    raise ValueError('Notes cannot have task fields or agent assignments')
                if action == 'pin-note':
                    if key in tasks:
                        raise ValueError(f'Task already uses this ID: {key}')
                    if not isinstance(markdown, str):
                        raise ValueError('Note Markdown is required')
                    self.notes_directory.mkdir(exist_ok=True)
                    atomic_write(path, markdown)
                    notes[key] = markdown
                else:
                    if key not in notes:
                        raise ValueError(f'Unknown note: {key}')
                    path.unlink()
                    del notes[key]
                return snapshot(config, tasks, notes)
            if key in notes:
                raise ValueError('Notes are pinned only; use pin-note or remove-note')
            if action not in ('assign', 'unassign', 'pin', 'remove', 'archive'):
                raise ValueError('Unknown action')
            old = tasks.get(key)
            if action in ('unassign', 'remove', 'archive') and old is None:
                raise ValueError(f'Unknown task: {key}')
            if action == 'archive':
                if old['agent'] is not None:
                    raise ValueError('Unassign the task before archiving it')
                if 'archive' not in config['commands']:
                    raise ValueError('Configure an archive command before archiving tasks')
                self.hook(config, 'archive', key, old)
            record = dict(old or {'task': '', 'mission': '', 'url': '', 'agent': None})
            for field, value in (fields or {}).items():
                if field not in FIELDS or not isinstance(value, str):
                    raise ValueError('Invalid task field')
                record[field] = value
            for field in ('task', 'mission'):
                if not record[field].strip():
                    raise ValueError(f'--{field} is required')
            link_url(record['url'])
            if action == 'assign':
                if agent not in {a['name'] for a in config['agents']}:
                    raise ValueError(f'Unknown agent: {agent}')
                if any(k != key and t['agent'] == agent for k, t in tasks.items()):
                    raise ValueError(f'{agent} is occupied; unassign its task first')
                target = agent
            else:
                target = None
            # Persist each successful transition: a failed handoff leaves the task pinned.
            if action != 'remove' and old and old['agent'] is not None and old['agent'] != target:
                self.hook(config, 'unassign', key, old)
                old = {**old, 'agent': None, 'updated_at': datetime.now(timezone.utc).isoformat()}
                tasks[key] = old
                self.save(tasks)
            if action in ('remove', 'archive'):
                del tasks[key]
            else:
                record['agent'] = target
                record['updated_at'] = datetime.now(timezone.utc).isoformat()
                if target is not None and (old is None or old['agent'] != target):
                    self.hook(config, 'assign', key, record)
                tasks[key] = record
            self.save(tasks)
            return snapshot(config, tasks, notes)


def serve(board, port):
    board.read()
    stopped = threading.Event()
    def refresh_journals():
        while not stopped.is_set():
            try:
                with locked(board.directory):
                    config = read_config(board.config_path)
                    ids = list(read_store(board.path))
                board.journals.refresh(config['workspace'], ids)
            except (OSError, ValueError, TypeError, AttributeError) as error:
                board.journals.failed(str(error))
            stopped.wait(60)
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, value, content_type='application/json'):
            body = (json.dumps(value) if content_type == 'application/json' else value).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.valid_host():
                return self.reply(403, {'error': 'Invalid host'})
            try:
                if self.path == '/':
                    page = Path(__file__).with_name('page.html').read_text().replace('<!-- token -->', token)
                    return self.reply(200, page, 'text/html')
                if self.path == '/api/board':
                    return self.reply(200, board.read())
                self.reply(404, {'error': 'Not found'})
            except (OSError, ValueError, TypeError) as error:
                self.reply(400, {'error': str(error)})

        def do_POST(self):
            if not self.valid_host() or self.headers.get('X-Dashboard-Token') != token:
                return self.reply(403, {'error': 'Invalid request token'})
            if self.path != '/api/action':
                return self.reply(404, {'error': 'Not found'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 65536:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(length))
                if data.get('action') not in ('assign', 'unassign', 'pin', 'remove', 'archive', 'remove-note') or not isinstance(data.get('revision'), str):
                    raise ValueError('Action and board revision are required')
                self.reply(200, board.action(data['action'], data.get('id'), data.get('agent'), revision=data['revision']))
            except (OSError, ValueError, TypeError, AttributeError) as error:
                self.reply(400, {'error': str(error)})
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=refresh_journals, daemon=True).start()
    print(f'http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Pin tasks and assign configured agents through a local interactive board.')
    default = os.environ.get('DASHBOARD_HOME') or str(Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'dashboard')
    parser.add_argument('--store', type=Path, default=Path(default))
    parser.add_argument('--config', type=Path, default=Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'nk-dashboard/config.json')
    commands = parser.add_subparsers(dest='command')
    for action in ('assign', 'pin', 'unassign', 'remove', 'archive'):
        command = commands.add_parser(action)
        command.add_argument('id')
        if action == 'assign':
            command.add_argument('--agent', required=True)
        if action in ('assign', 'pin'):
            for field in FIELDS:
                command.add_argument('--' + field)
    note = commands.add_parser('pin-note')
    note.add_argument('id')
    note.add_argument('--file', required=True)
    commands.add_parser('remove-note').add_argument('id')
    commands.add_parser('note-template')
    commands.add_parser('list')
    server = commands.add_parser('serve')
    server.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    board = Board(args.store.expanduser().resolve(), args.config.expanduser().resolve())
    try:
        if args.command in (None, 'serve'):
            serve(board, getattr(args, 'port', 8765))
        elif args.command == 'note-template':
            print(Path(__file__).with_name('note-template.md').read_text(), end='')
        elif args.command == 'pin-note':
            markdown = sys.stdin.read() if args.file == '-' else Path(args.file).expanduser().read_text()
            print(json.dumps(board.action('pin-note', args.id, markdown=markdown), indent=2))
        elif args.command == 'list':
            print(json.dumps(board.read(), indent=2))
        else:
            fields = {f: getattr(args, f) for f in FIELDS if getattr(args, f, None) is not None}
            print(json.dumps(board.action(args.command, args.id, getattr(args, 'agent', None), fields), indent=2))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        parser.exit(1, f'nk-dashboard: {error}\n')
    return 0
