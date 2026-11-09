"""Archive real nk tasks without allowing assigned tasks or losing failed cards."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary)
    workspace = directory / 'workspace'
    nk = [sys.executable, str(root / 'bin/nk')]
    subprocess.run(['git', 'init', '-q', str(workspace)], check=True)
    subprocess.run([*nk, 'init', str(workspace)], check=True, capture_output=True)
    slug = '2026-11-09-archive-example'
    subprocess.run([*nk, 'task', 'create', '--workspace', str(workspace), slug], check=True, capture_output=True)
    config = directory / 'config.json'
    settings = {'agents': [{'name': 'worker'}], 'commands': {}}
    config.write_text(json.dumps(settings))
    command = [sys.executable, str(root / 'bin/nk-dashboard'), '--config', str(config), '--store', str(directory / 'store')]

    def run(*args, ok=True):
        result = subprocess.run([*command, *args], capture_output=True, text=True)
        assert (result.returncode == 0) == ok, result.stderr
        return json.loads(result.stdout) if ok else result.stderr

    run('pin', slug, '--task', 'Archive example', '--mission', 'Exercise archiving')
    assert 'Configure an archive command' in run('archive', slug, ok=False)
    settings['commands']['archive'] = [*nk, 'task', 'archive', '--workspace', str(workspace), '{id}']
    config.write_text(json.dumps(settings))
    run('assign', slug, '--agent', 'worker')
    assert 'Unassign the task' in run('archive', slug, ok=False)
    assert run('list')['tasks'][slug]['agent'] == 'worker'
    run('unassign', slug)
    # No assignment hook may be called during archive.
    settings['commands']['unassign'] = [sys.executable, '-c', 'raise SystemExit(99)']
    config.write_text(json.dumps(settings))
    run('pin', 'missing', '--task', 'Missing', '--mission', 'Failure keeps the card')
    run('archive', 'missing', ok=False)
    assert 'missing' in run('list')['tasks']
    assert slug not in run('archive', slug)['tasks']
    todo = (workspace / 'TODO.md').read_text()
    assert slug in todo.split('## Archived', 1)[1]
    assert (workspace / 'scratch' / slug / 'README.md').exists()
print('dashboard archive integration and failure preservation pass')
