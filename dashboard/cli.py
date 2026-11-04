"""An explicit assignment ledger, independent of task and session tools."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from html import escape
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

STATUSES = ('working', 'blocked', 'queued', 'paused', 'done')
FIELDS = ('agent', 'task', 'mission', 'status', 'note', 'url')


def link_url(value):
    if not value:
        return ''
    if value.startswith('/'):
        return Path(value).as_uri()
    if urlsplit(value).scheme not in ('https', 'http', 'file'):
        raise ValueError('Links must be http(s), file URLs, or absolute file paths')
    return value


def read_store(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('assignments'), dict):
        raise ValueError('Expected version 1 with an assignments object')
    records = data['assignments']
    for key, record in records.items():
        if not key.strip() or not isinstance(record, dict):
            raise ValueError('Invalid assignment record')
        if any(not isinstance(record.get(field), str) for field in (*FIELDS, 'updated_at')):
            raise ValueError(f'{key}: assignment fields must be strings')
        if any(not record[field].strip() for field in ('agent', 'task', 'mission')):
            raise ValueError(f'{key}: agent, task and mission must be nonempty')
        if record['status'] not in STATUSES:
            raise ValueError(f'{key}: invalid status')
        datetime.fromisoformat(record['updated_at'])
        link_url(record['url'])
    return records


def atomic_write(path, content):
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
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


def render(records):
    cards = []
    ordered = sorted(records.items(), key=lambda item: (STATUSES.index(item[1]['status']), item[1]['agent'].casefold(), item[0]))
    for key, record in ordered:
        fields = {name: escape(value, quote=True) for name, value in record.items()}
        url = link_url(record['url'])
        title = fields['task']
        if url:
            title = f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{title}<span aria-hidden="true"> ↗</span></a>'
        updated = datetime.fromisoformat(record['updated_at']).astimezone(timezone.utc).strftime('%b %d · %H:%M UTC')
        note = f'<div class="note"><span>Latest note</span><p>{fields["note"]}</p></div>' if record['note'] else ''
        cards.append(f'''<article class="card" data-status="{fields['status']}">
<div class="card-top"><div class="agent"><span class="avatar" aria-hidden="true">{escape(record['agent'][:2].upper())}</span>{fields['agent']}</div><span class="badge {fields['status']}"><i></i>{fields['status']}</span></div>
<div class="assignment-id">{escape(key)}</div><h2>{title}</h2><p class="mission">{fields['mission']}</p>{note}
<footer><span>Last reported</span><time datetime="{fields['updated_at']}">{updated}</time></footer></article>''')
    counts = {status: sum(r['status'] == status for r in records.values()) for status in STATUSES}
    filters = ''.join(f'<button type="button" data-filter="{s}" aria-pressed="false">{s.capitalize()} <span>{counts[s]}</span></button>' for s in STATUSES)
    template = Path(__file__).with_name('page.html').read_text(encoding='utf-8')
    values = {'cards': '\n'.join(cards), 'total': str(len(records)), 'working': str(counts['working']),
              'blocked': str(counts['blocked']), 'agents': str(len({r['agent'] for r in records.values()})),
              'filters': filters, 'generated': datetime.now(timezone.utc).strftime('%b %d, %Y · %H:%M UTC')}
    for name, value in values.items():
        template = template.replace('<!-- ' + name + ' -->', value)
    return template


def parser():
    result = argparse.ArgumentParser(description='Remember delegated work and render a standalone HTML dashboard.')
    default = os.environ.get('DASHBOARD_HOME') or str(Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'dashboard')
    result.add_argument('--store', type=Path, default=Path(default), help='directory containing assignments.json and index.html')
    commands = result.add_subparsers(dest='command')
    update = commands.add_parser('set', help='create an assignment or update supplied fields; regenerate HTML')
    update.add_argument('id', help='stable assignment ID')
    for field in FIELDS:
        update.add_argument('--' + field, choices=STATUSES if field == 'status' else None)
    remove = commands.add_parser('remove', help='remove an assignment and regenerate HTML')
    remove.add_argument('id')
    commands.add_parser('list', help='print the assignment store as JSON')
    commands.add_parser('render', help='regenerate index.html and print its path (default)')
    return result


def main(argv=None):
    command_parser = parser()
    args = command_parser.parse_args(argv)
    directory = args.store.expanduser().resolve()
    try:
        with locked(directory):
            path = directory / 'assignments.json'
            records = read_store(path)
            if args.command == 'set':
                if not args.id.strip():
                    raise ValueError('Assignment ID must be nonempty')
                record = records.get(args.id, dict.fromkeys(FIELDS, ''))
                record = {**record, **{field: getattr(args, field) for field in FIELDS if getattr(args, field) is not None}}
                record['status'] = record['status'] or 'queued'
                for field in ('agent', 'task', 'mission'):
                    if not record[field].strip():
                        raise ValueError(f'{args.id}: --{field} is required and must be nonempty')
                link_url(record['url'])
                record['updated_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
                records[args.id] = record
            elif args.command == 'remove':
                if args.id not in records:
                    raise ValueError(f'Unknown assignment: {args.id}')
                del records[args.id]
            data = {'version': 1, 'assignments': records}
            if args.command == 'list':
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return 0
            # JSON is authoritative. A failed HTML write can be repaired with render.
            if args.command in ('set', 'remove'):
                atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + '\n')
            page = directory / 'index.html'
            atomic_write(page, render(records))
            print(page)
    except (OSError, ValueError, TypeError) as error:
        command_parser.exit(1, f'dashboard: {error}\n')
    return 0
