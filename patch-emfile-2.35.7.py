#!/usr/bin/env python3
"""Patch n8n 2.35.7's static-asset fanout only when its source matches exactly.
Run while n8n is STOPPED, after backing up commands/start.js. Does not start or stop n8n.
"""
import hashlib
import os
import pathlib
import sys

version = pathlib.Path.home() / 'n8n/lib/node_modules/n8n/package.json'
target = pathlib.Path.home() / 'n8n/lib/node_modules/n8n/dist/commands/start.js'
if not version.is_file() or not target.is_file():
    sys.exit('n8n files missing at expected ~/n8n location. Stop; check npm prefix.')
import json
if json.loads(version.read_text())['version'] != '2.35.7':
    sys.exit('Wrong n8n version. This patch only supports 2.35.7.')
original = target.read_bytes()
upstream_sha256 = '90a54103642da694d2d6e61b2654d8159c19533203901e3c5540ff04f098de99'
patched_sha256 = 'c20ce4bd3d993de8bac5bec03d5075e455ee477aa8b202d52c7967fbc8bdc18c'
digest = hashlib.sha256(original).hexdigest()
if digest == patched_sha256:
    print('Already patched; no changes.')
    sys.exit(0)
if digest != upstream_sha256:
    sys.exit('start.js is not the unmodified npm n8n@2.35.7 file. No changes; inspect the diff manually.')
old = b"await Promise.all([compileFile('index.html'), ...files.map(compileFile)]);"
new = b"const allAssets = ['index.html', ...files]; for (let i = 0; i < allAssets.length; i += 40) { await Promise.all(allAssets.slice(i, i + 40).map(compileFile)); }"
if original.count(old) != 1:
    sys.exit('Patch anchor missing or repeated; no changes.')
backup = target.with_name('start.js.before-emfile-patch')
if backup.exists():
    sys.exit(f'Backup already exists: {backup}; no changes.')
backup.write_bytes(original)
try:
    target.write_bytes(original.replace(old, new, 1))
    if hashlib.sha256(target.read_bytes()).hexdigest() != patched_sha256:
        raise RuntimeError('patched checksum mismatch')
except Exception:
    target.write_bytes(original)
    raise
print(f'Patched {target}; original backed up at {backup}')
