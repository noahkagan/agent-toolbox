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
    run('set', 'suppress', '--agent', 'gke-3')
    data = json.loads(run('list').stdout)['assignments']
    assert data['suppress']['mission'] == 'Keep a sibling rendering.'
    assert data['suppress']['agent'] == 'gke-3'
    before_duplicate = (store / 'assignments.json').read_bytes()
    run('set', 'duplicate', '--agent', ' GKE-3 ', '--task', 'Other task', '--mission', 'Other mission', ok=False)
    assert (store / 'assignments.json').read_bytes() == before_duplicate
    run('set', 'suppress', '--task', 'Render admission')
    assert 'note' not in json.loads(run('list').stdout)['assignments']['suppress']
    # Old stores may contain notes; retire them without changing report timestamps.
    legacy = json.loads((store / 'assignments.json').read_text())
    legacy['assignments']['suppress']['note'] = 'Stale progress'
    legacy['assignments']['suppress']['status'] = 'blocked'
    (store / 'assignments.json').write_text(json.dumps(legacy))
    assert 'note' not in json.loads(run('list').stdout)['assignments']['suppress']
    run('render')
    assert 'Latest note' not in (store / 'index.html').read_text()
    assert 'Stale progress' not in (store / 'index.html').read_text()
    assert 'status' not in json.loads(run('list').stdout)['assignments']['suppress']
    for removed in ('class="metrics"', 'class="filters"', 'class="badge', 'class="avatar"', 'A record of responsibility.'):
        assert removed not in (store / 'index.html').read_text()
    assert 'id="search"' in (store / 'index.html').read_text()
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
    run('set', 'parallel-1', '--agent', 'agent-0', ok=False)
    html = (store / 'index.html').read_text()
    assert html.count('<article class="card"') == 14
    run('remove', 'unsafe')
    run('remove', 'missing', ok=False)
    duplicate = json.loads((store / 'assignments.json').read_text())
    duplicate['assignments']['collision'] = dict(duplicate['assignments']['suppress'])
    (store / 'assignments.json').write_text(json.dumps(duplicate))
    run('render', ok=False)
    (store / 'assignments.json').write_text('{broken')
    run('set', 'suppress', '--agent', 'gke-2', ok=False)
    assert (store / 'assignments.json').read_text() == '{broken'
    assert not list(store.glob('.assignments.json*'))
    default = Path(directory) / 'default'
    env = {**os.environ, 'DASHBOARD_HOME': str(default)}
    result = subprocess.run([root / 'bin/dashboard'], env=env, text=True, capture_output=True, check=True)
    assert Path(result.stdout.strip()) == default / 'index.html'
print('dashboard updates, concurrency, validation, and HTML escaping are valid')
