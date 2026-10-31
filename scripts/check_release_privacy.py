"""Check source/release bytes without echoing matched sensitive values."""
import argparse
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import zipfile

TOKEN = re.compile(r'(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)')
PERSONAL_PATH = re.compile(r'(?i)(?:[A-Z]:[\\/]+Users[\\/]+(?!Public(?:[\\/]|$)|Default(?:[\\/]|$))[^\\/\s"<>]+|/(?:home|Users)/[^\s/"<>]+)')
URL = re.compile(r'https?://[A-Za-z0-9.\[\]:_-]+')
PUBLIC_HOSTS = {'github.com','api.github.com','uploads.github.com','raw.githubusercontent.com',
                'developers.openai.com','platform.openai.com','learn.chatgpt.com','openai.com',
                'python.org','www.python.org','agentskills.io'}
EXAMPLE_HOSTS = {'host','localhost','127.0.0.1','::1','example.com'}
SKIP_DIRS = {'.git','__pycache__','.pytest_cache'}
PRIVATE_NAMES = {'config.json','api-key.dpapi','.env','auth.json','credentials.json'}


def inspect_bytes(name, data, deny_terms, issues, depth=0):
    if len(data) > 100 * 1024 * 1024:
        issues.append({'file':name,'code':'oversize_unreviewed'})
        return
    parts = Path(name).parts
    if any(part.lower() in PRIVATE_NAMES or part.lower().startswith('.env.') or part.lower().endswith(('.dpapi','.pem','.pfx','.key','.log')) for part in parts):
        issues.append({'file':name,'code':'private_file'})
    text = data.decode('utf-8',errors='replace')
    folded = (name+'\n'+text).casefold()
    if any(term.casefold() in folded for term in deny_terms if term):
        issues.append({'file':name,'code':'private_term'})
    if PERSONAL_PATH.search(text):
        issues.append({'file':name,'code':'personal_path'})
    if TOKEN.search(text):
        issues.append({'file':name,'code':'credential_pattern'})
    for match in URL.finditer(text):
        try:
            host = urlsplit(match.group()).hostname or ''
        except ValueError:
            host = ''
        if host not in PUBLIC_HOSTS and host not in EXAMPLE_HOSTS and not host.endswith(('.example','.invalid')):
            issues.append({'file':name,'code':'unapproved_url'})
            break
    if name.lower().endswith('.zip'):
        if depth >= 3:
            issues.append({'file':name,'code':'nested_archive_limit'})
            return
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if len(z.infolist()) > 2000 or sum(i.file_size for i in z.infolist()) > 100 * 1024 * 1024:
                    issues.append({'file':name,'code':'oversize_archive'})
                    return
                for item in z.infolist():
                    if not item.is_dir():
                        inspect_bytes(name+'!/'+item.filename,z.read(item),deny_terms,issues,depth+1)
        except (ValueError,zipfile.BadZipFile,RuntimeError):
            issues.append({'file':name,'code':'unreadable_archive'})


def audit(targets, deny_terms=()):
    issues=[]
    count=0
    for target in targets:
        path=Path(target)
        if not path.exists():
            issues.append({'file':path.name,'code':'missing_target'})
            continue
        files=[path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(path).parts))
        for item in files:
            count+=1
            name=item.name if path.is_file() else item.relative_to(path).as_posix()
            inspect_bytes(name,item.read_bytes(),deny_terms,issues)
    return {'passed':not issues,'files_checked':count,'issues':issues}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('targets',nargs='+')
    parser.add_argument('--denylist-file',help='Local JSON string list. Never add this file to the release.')
    args=parser.parse_args()
    terms=json.loads(Path(args.denylist_file).read_text(encoding='utf-8')) if args.denylist_file else []
    if not isinstance(terms,list) or not all(isinstance(t,str) for t in terms):
        parser.error('denylist must be a JSON string list')
    result=audit(args.targets,terms)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
