"""Exercise Markdown notes through CLI and HTTP without agent transitions."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary)
    store = directory / 'store'
    config = directory / 'config.json'
    log = directory / 'hook-log'
    hook = [sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("called")', str(log)]
    config.write_text(json.dumps({'agents': [{'name': 'one'}], 'commands': {'assign': hook, 'unassign': hook}}))
    command = [sys.executable, str(root / 'bin/nk-dashboard'), '--store', str(store), '--config', str(config)]

    def run(*args, content=None, ok=True):
        result = subprocess.run([*command, *args], input=content, text=True, capture_output=True)
        assert (result.returncode == 0) == ok, result.stderr
        return json.loads(result.stdout) if ok else result

    template = subprocess.run([*command, 'note-template'], text=True, capture_output=True, check=True).stdout
    assert all(heading in template for heading in ('# Note title', '## Context', '## Next steps', '## Decisions / open questions'))
    assert not store.exists()
    empty = run('list')
    assert empty['notes'] == {} and empty['tasks'] == {}
    run('pin', 'task', '--task', 'Task', '--mission', 'Mission')
    ledger = (store / 'assignments.json').read_bytes()
    source = directory / 'source.md'
    source.write_text('# Café\n\nA **note** with [a link](https://example.org).\n')
    created = run('pin-note', 'idea', '--file', str(source))
    assert created['notes'] == {'idea': source.read_text()}
    updated = run('pin-note', 'idea', '--file', '-', content='# Edited\n\n- [ ] Next step\n')
    assert updated['notes']['idea'].startswith('# Edited')
    assert updated['revision'] != created['revision']
    assert (store / 'notes/idea.md').read_text() == updated['notes']['idea']
    assert (store / 'assignments.json').read_bytes() == ledger
    assert not log.exists()
    run('assign', 'idea', '--agent', 'one', '--task', 'Bad', '--mission', 'Bad', ok=False)
    run('pin-note', 'task', '--file', str(source), ok=False)
    run('remove', 'idea', ok=False)
    run('remove-note', 'missing', ok=False)
    for key in ('../outside', '/outside', '.', '..', 'a/b', 'a\\b'):
        run('pin-note', key, '--file', str(source), ok=False)
        run('remove-note', key, ok=False)
    outside = directory / 'outside.md'
    outside.write_text('private')
    (store / 'notes/link.md').symlink_to(outside)
    run('list', ok=False)
    run('pin-note', 'link', '--file', str(source), ok=False)
    run('remove-note', 'link', ok=False)
    assert outside.read_text() == 'private'
    (store / 'notes/link.md').unlink()
    (store / 'notes').rename(store / 'original-notes')
    (store / 'notes').symlink_to(store / 'original-notes', target_is_directory=True)
    run('list', ok=False)
    run('pin-note', 'escape', '--file', str(source), ok=False)
    (store / 'notes').unlink()
    (store / 'original-notes').rename(store / 'notes')

    process = subprocess.Popen([*command, 'serve', '--port', '0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        base = process.stdout.readline().strip()
        assert base.startswith('http://127.0.0.1:'), process.stderr.read()
        html = urlopen(base).read().decode()
        token = re.search(r'<meta name="dashboard-token" content="([^"]+)">', html).group(1)

        def post(action, key, revision, **fields):
            data = {'action': action, 'id': key, 'revision': revision, **fields}
            request = Request(base + '/api/action', json.dumps(data).encode(), {'Content-Type': 'application/json', 'X-Dashboard-Token': token})
            try:
                response = urlopen(request)
            except HTTPError as error:
                response = error
            return response.status, json.load(response)

        previous = json.load(urlopen(base + '/api/board'))
        (store / 'notes/idea.md').write_text('# Direct edit\n\nVisible immediately.\n')
        current = json.load(urlopen(base + '/api/board'))
        assert current['notes']['idea'].startswith('# Direct edit')
        assert current['revision'] != previous['revision']
        assert post('assign', 'task', previous['revision'], agent='one')[0] == 400
        assert post('remove-note', 'idea', previous['revision'])[0] == 400
        assert post('assign', 'idea', current['revision'], agent='one')[0] == 400
        assert not log.exists()
        status, removed = post('remove-note', 'idea', current['revision'])
        assert status == 200 and removed['notes'] == {}
        assert not (store / 'notes/idea.md').exists()
        assert removed['tasks'] == created['tasks']
        assert (store / 'assignments.json').read_bytes() == ledger
        assert not log.exists()
    finally:
        process.terminate()
        process.wait(timeout=5)
    run('pin-note', 'idea', '--file', '-', content='')
    run('remove-note', 'idea')
    assert run('list')['notes'] == {}
    assert not log.exists()
print('dashboard note CLI, HTTP, revisions, hook isolation, and paths pass')
