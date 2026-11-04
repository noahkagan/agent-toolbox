"""Check journal extraction and published refresh without touching working files."""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'nk-dashboard'))
from journals import Journals, latest_entry

assert latest_entry('') is None
assert latest_entry('# Task updates\n\nNo entries yet.') is None
assert latest_entry('## Empty entry\n') == {'heading': 'Empty entry', 'summary': '', 'body': ''}
text = '''# Task updates

## Older
Old work.

## Latest
The current result
continues on this line.

### Details
Nested detail stays in the latest entry.

```markdown
## Not an entry
```

~~~
## Also not an entry
~~~
'''
entry = latest_entry(text)
assert entry['heading'] == 'Latest'
assert entry['summary'] == 'The current result continues on this line.'
assert '### Details' in entry['body'] and '## Also not an entry' in entry['body']
assert latest_entry(text + '\n## Newest\nA later result.\n')['heading'] == 'Newest'
long = latest_entry('## Long\n' + 'word ' * 100)
assert len(long['summary']) <= 320 and long['summary'].endswith('…')
assert len(long['body']) > len(long['summary'])


def git(path, *args):
    result = subprocess.run(['git', '-C', str(path), *args], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def board(cache):
    return cache.decorate({'tasks': {'task': {}, 'missing': {}, '../escape': {}}})


with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    remote, producer, consumer = (directory / name for name in ('remote.git', 'producer', 'consumer'))
    remote.mkdir()
    git(remote, 'init', '--bare', '--initial-branch=main')
    producer.mkdir()
    git(producer, 'init', '--initial-branch=main')
    git(producer, 'config', 'user.name', 'Test')
    git(producer, 'config', 'user.email', 'test@example.invalid')
    git(producer, 'config', 'commit.gpgsign', 'false')
    (producer / '.nk').mkdir()
    (producer / '.nk/workspace').write_text('1\n')
    journal = producer / 'scratch/task/JOURNAL.md'
    journal.parent.mkdir(parents=True)
    journal.write_text('# Task updates\n\n## First\nFirst result.\n')
    git(producer, 'add', '.')
    git(producer, 'commit', '-m', 'First journal')
    git(producer, 'remote', 'add', 'origin', str(remote))
    git(producer, 'push', '-u', 'origin', 'main')
    git(directory, 'clone', str(remote), str(consumer))
    original_head = git(consumer, 'rev-parse', 'HEAD')
    dirty = consumer / 'scratch/task/JOURNAL.md'
    dirty.write_text('Local unpublished work must survive.\n')
    untracked = consumer / 'notes.txt'
    untracked.write_text('Untracked work must survive.\n')
    original_status = git(consumer, 'status', '--porcelain')
    config = {'path': str(consumer), 'remote': 'origin', 'branch': 'main'}
    cache = Journals()
    cache.refresh(config, ['task', 'missing', '../escape'])
    first = board(cache)
    assert first['tasks']['task']['journal']['heading'] == 'First'
    assert first['tasks']['missing']['journal'] is None
    assert first['tasks']['../escape']['journal'] is None
    assert first['journal_sync']['updated_at'] and first['journal_sync']['error'] is None
    journal.write_text(journal.read_text() + '\n## Second\nPublished progress.\n')
    git(producer, 'add', '.')
    git(producer, 'commit', '-m', 'Second journal')
    git(producer, 'push', 'origin', 'main')
    cache.refresh(config, ['task', 'missing'])
    second = board(cache)
    assert second['tasks']['task']['journal']['summary'] == 'Published progress.'
    assert second['journal_sync']['revision'] != first['journal_sync']['revision']
    assert git(consumer, 'rev-parse', 'HEAD') == original_head
    assert git(consumer, 'status', '--porcelain') == original_status
    assert dirty.read_text() == 'Local unpublished work must survive.\n'
    assert untracked.read_text() == 'Untracked work must survive.\n'
    git(consumer, 'remote', 'set-url', 'origin', str(directory / 'missing.git'))
    cache.refresh(config, ['task'])
    stale = board(cache)
    assert stale['journal_sync']['error']
    assert stale['journal_sync']['updated_at'] == second['journal_sync']['updated_at']
    assert stale['tasks']['task']['journal'] == second['tasks']['task']['journal']
    git(consumer, 'remote', 'set-url', 'origin', str(remote))
    cache.refresh(config, ['task'])
    assert board(cache)['journal_sync']['error'] is None
    changed = {**config, 'branch': 'missing-branch'}
    cache.refresh(changed, ['task'])
    reset = board(cache)
    assert reset['tasks']['task']['journal'] is None
    assert reset['journal_sync']['updated_at'] is None
    assert reset['journal_sync']['revision'] is None
    assert reset['journal_sync']['error']
    cache.refresh(None, ['task'])
    assert board(cache)['journal_sync']['error'] is None

print('journal parsing, published updates, dirty checkout preservation, and failure recovery pass')
