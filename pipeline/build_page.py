#!/usr/bin/env python3
"""Assemble la console (template + data-block.js), injecte le pont, chiffre et ecrit la page gate.

Utilise en local par build.sh ET par le workflow GitHub Actions (.github/workflows/refresh.yml).
Le pont (__BRIDGE_URL__/__BRIDGE_KEY__) vient de l'environnement, sinon de thomas-dashboard/bridge.json,
sinon les placeholders restent (bouton en mode lien Claude).

Usage : python3 build_page.py [--out=chemin/index.html] [--src-out=console-suivi-lp-i30.html] [--full-out=console-full.html]
Env : CONSOLE_CODE (defaut Alex99), BRIDGE_URL, BRIDGE_KEY
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
opts = {a.split('=', 1)[0]: a.split('=', 1)[1] for a in sys.argv[1:] if '=' in a}
out_path = opts.get('--out', os.path.join(HERE, 'console-repo', 'index.html'))
src_out = opts.get('--src-out')
full_out = opts.get('--full-out')
code = os.environ.get('CONSOLE_CODE') or os.environ.get('PAGE_CODE') or 'Alex99'

burl, bkey = os.environ.get('BRIDGE_URL'), os.environ.get('BRIDGE_KEY')
if not (burl and bkey):
    bj = '/Users/alex/Alex/thomas-dashboard/bridge.json'
    if os.path.exists(bj):
        b = json.load(open(bj))
        burl, bkey = b['url'], b['key']

tpl = open(os.path.join(HERE, 'console-template.html'), encoding='utf-8').read()
data = open(os.path.join(HERE, 'data-block.js'), encoding='utf-8').read().strip()
assert '__DATA__' in tpl, 'placeholder __DATA__ absent du template'
src = tpl.replace('__DATA__', data)
if burl and bkey:
    src = src.replace('__BRIDGE_URL__', burl).replace('__BRIDGE_KEY__', bkey)
if src_out:
    open(src_out, 'w', encoding='utf-8').write(src)
full = ('<!DOCTYPE html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="robots" content="noindex">\n</head>\n<body>\n' + src + '\n</body>\n</html>\n')
if full_out:
    open(full_out, 'w', encoding='utf-8').write(full)

with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
    f.write(full)
    tmp = f.name
try:
    enc = subprocess.run(['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-iter', '100000', '-md', 'sha256',
                          '-salt', '-base64', '-A', '-pass', 'pass:' + code, '-in', tmp],
                         check=True, capture_output=True).stdout.decode().strip()
finally:
    os.unlink(tmp)
gate = open(os.path.join(HERE, 'console-gate-template.html'), encoding='utf-8').read()
open(out_path, 'w', encoding='utf-8').write(gate.replace('__PAYLOAD__', enc))
print('page chiffree ->', out_path, '(', len(enc), 'octets de payload, pont', 'injecte' if burl and bkey else 'ABSENT', ')')
