"""Verify released files without network access or third-party dependencies."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    failures = []
    for item in manifest['files']:
        path = ROOT / item['path']
        if not path.is_file():
            failures.append(item['path'] + ': missing')
            continue
        data = path.read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            failures.append(item['path'] + ': checksum mismatch')
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1
    print(f"Verified {len(manifest['files'])} released files.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
