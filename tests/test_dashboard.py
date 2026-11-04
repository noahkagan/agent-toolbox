"""Exercise configured transitions, failure recovery, legacy data, and HTTP guards."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    config, log = directory/'config.json', directory/'actions.jsonl'
    hook = directory/'hook.py'
    hook.write_text('''import json, sys
from pathlib import Path
log, action, agent, task = sys.argv[1:]
with Path(log).open('a') as f:
 f.write(json.dumps([action, agent, task])+'\\n')
if agent == 'fail':
 print('deliberate failure', file=sys.stderr)
 sys.exit(1)
''')
    settings = {'agents': [{'name': name} for name in ('one', 'two', 'fail')],
                'commands': {action: [sys.executable, str(hook), str(log), action, '{agent}', '{id}'] for action in ('assign', 'unassign')}}
    config.write_text(json.dumps(settings))
    command = [sys.executable, str(root/'bin/nk-dashboard'), '--config', str(config), '--store', str(directory/'store')]
    def run(*args, ok=True):
        result = subprocess.run([*command, *args], text=True, capture_output=True)
        assert (result.returncode == 0) == ok, result.stderr
        return json.loads(result.stdout) if result.returncode == 0 else result
    def events():
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    task = 'literal-$(touch forbidden);task'
    run('pin', task, '--task', '<Title>', '--mission', 'Mission')
    assert not events()
    assert len(run('list')['agents']) == 3
    run('assign', task, '--agent', 'one')
    run('assign', task, '--agent', 'one')
    assert events() == [['assign', 'one', task]]
    run('pin', 'second', '--task', 'Second', '--mission', 'Other')
    run('assign', 'second', '--agent', 'one', ok=False)
    run('assign', 'second', '--agent', 'unknown', ok=False)
    assert len(events()) == 1
    run('assign', task, '--agent', 'two')
    assert events()[-2:] == [['unassign', 'one', task], ['assign', 'two', task]]
    run('assign', task, '--agent', 'fail', ok=False)
    assert run('list')['tasks'][task]['agent'] is None
    run('assign', task, '--agent', 'one')
    # A failed unassign does not clear ownership.
    saved = json.loads(config.read_text())
    saved['commands']['unassign'] = [sys.executable, '-c', 'raise SystemExit(1)']
    config.write_text(json.dumps(saved))
    run('unassign', task, ok=False)
    assert run('list')['tasks'][task]['agent'] == 'one'
    config.write_text(json.dumps(settings))
    run('unassign', task)
    assert run('list')['tasks'][task]['agent'] is None
    run('pin', 'bad', '--task', 'Bad', '--mission', 'Mission', '--url', 'javascript:alert(1)', ok=False)
    run('set', task, ok=False)
    run('assign', 'second', '--agent', 'two')
    before_remove = events()
    run('remove', 'second')
    assert 'second' not in run('list')['tasks']
    assert events() == before_remove
    run('remove', task)
    assert task not in run('list')['tasks']
    assert events() == before_remove
    # Legacy assignments remain visible without triggering external commands.
    data = {'version': 1, 'assignments': {'legacy': {'agent': 'one', 'task': 'Legacy', 'mission': 'Keep me', 'url': '', 'updated_at': '2026-11-03T00:00:00+00:00'}}}
    store = directory/'store/assignments.json'
    store.write_text(json.dumps(data))
    previous = events()
    assert run('list')['tasks']['legacy']['agent'] == 'one'
    assert events() == previous
    run('pin', 'new', '--task', 'New', '--mission', 'New task')
    assert json.loads(store.read_text())['version'] == 2
    # Server rejects cross-origin writes and stale concurrent transitions.
    process = subprocess.Popen([*command, 'serve', '--port', '0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        base = process.stdout.readline().strip()
        assert base.startswith('http://127.0.0.1:'), process.stderr.read()
        html = urlopen(base).read().decode()
        assert 'PINNED' in html and 'ASSIGNED' in html
        board = json.load(urlopen(base+'/api/board'))
        def post(payload, token=None):
            headers = {'Content-Type': 'application/json'}
            if token:
                headers['X-Dashboard-Token'] = token
            request = Request(base+'/api/action', json.dumps(payload).encode(), headers)
            try:
                response = urlopen(request)
            except HTTPError as error:
                response = error
            return response.status, json.load(response)
        assert post({'action': 'unassign', 'id': 'legacy', 'revision': board['revision']})[0] == 403
        # UI embeds the token in a meta element, not in a query string.
        import re
        token = re.search(r'<meta name="dashboard-token" content="([^"]+)">', html).group(1)
        request = {'action': 'unassign', 'id': 'legacy', 'revision': board['revision']}
        assert post(request, token)[0] == 200
        count = len(events())
        assert post(request, token)[0] == 400
        assert len(events()) == count
        run('assign', 'legacy', '--agent', 'one')
        current = json.load(urlopen(base+'/api/board'))
        before_remove = events()
        status, removed = post({'action': 'remove', 'id': 'legacy', 'revision': current['revision']}, token)
        assert status == 200 and 'legacy' not in removed['tasks']
        assert events() == before_remove
        bad_host = Request(base+'/api/board', headers={'Host': 'attacker.example'})
        try:
            urlopen(bad_host)
            raise AssertionError('untrusted host accepted')
        except HTTPError as error:
            assert error.code == 403
    finally:
        process.terminate()
        process.wait(timeout=5)
print('dashboard transitions, hooks, migration, and HTTP guards pass')
