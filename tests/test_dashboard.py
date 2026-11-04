"""Exercise assignment updates, safe rendering, and concurrent CLI writers."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    store = Path(directory) / 'board'
    command = [str(root / 'bin/dashboard'), '--store', str(store)]
    def run(*arguments, ok=True):
        result = subprocess.run([*command, *arguments], text=True, capture_output=True)
        assert (result.returncode == 0) == ok, result.stderr
        return result
    run('render')
    assert not (store / 'assignments.json').exists()
    run('set', 'suppress', '--agent', 'gke-2', '--task', 'Product suppression', '--mission', 'Keep a sibling rendering.', '--url', 'https://example.org/task')
    run('set', 'suppress', '--status', 'working', '--note', 'Testing native calls.')
    data = json.loads(run('list').stdout)['assignments']
    assert data['suppress']['mission'] == 'Keep a sibling rendering.'
    assert data['suppress']['status'] == 'working'
    run('set', 'suppress', '--status', 'blocked', '--note', '')
    assert json.loads(run('list').stdout)['assignments']['suppress']['note'] == ''
    before = (store / 'assignments.json').read_bytes()
    run('set', 'bad', '--agent', 'nobody', ok=False)
    run('set', 'suppress', '--mission', ' ', ok=False)
    run('set', 'suppress', '--url', 'javascript:alert(1)', ok=False)
    assert (store / 'assignments.json').read_bytes() == before
    run('set', 'unsafe', '--agent', '<script>alert(1)</script>', '--task', '"<&', '--mission', '</p><img src=x onerror=alert(1)>', '--url', '/tmp/a b.md')
    html = (store / 'index.html').read_text()
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '<img src=x' not in html
    assert 'file:///tmp/a%20b.md' in html
    writers = [subprocess.Popen([*command, 'set', f'parallel-{i}', '--agent', f'agent-{i}', '--task', 'Task', '--mission', 'Mission'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(12)]
    for writer in writers:
        stdout, stderr = writer.communicate(timeout=20)
        assert writer.returncode == 0, stderr
    data = json.loads(run('list').stdout)['assignments']
    assert len(data) == 14
    html = (store / 'index.html').read_text()
    assert html.count('<article class="card"') == 14
    run('remove', 'unsafe')
    run('remove', 'missing', ok=False)
    (store / 'assignments.json').write_text('{broken')
    run('set', 'suppress', '--status', 'done', ok=False)
    assert (store / 'assignments.json').read_text() == '{broken'
    assert not list(store.glob('.assignments.json*'))
    default = Path(directory) / 'default'
    env = {**os.environ, 'DASHBOARD_HOME': str(default)}
    result = subprocess.run([root / 'bin/dashboard'], env=env, text=True, capture_output=True, check=True)
    assert Path(result.stdout.strip()) == default / 'index.html'
print('dashboard updates, concurrency, validation, and HTML escaping are valid')
