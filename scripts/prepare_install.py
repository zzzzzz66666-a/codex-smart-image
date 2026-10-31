"""Create a persistent local marketplace with resolved Python and runtime paths."""
import argparse
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]


def prepare(destination):
    if sys.version_info < (3, 11):
        raise RuntimeError('Python 3.11+ required')
    destination = Path(destination).resolve()
    if destination == ROOT or ROOT.is_relative_to(destination) or destination.is_relative_to(ROOT):
        raise RuntimeError('Install destination must be separate from the source project')
    plugin = destination / 'plugin'
    for name in ('smart_image', 'skills', '.codex-plugin', 'docs', 'installer-skill', 'development-skill'):
        shutil.copytree(ROOT/name, plugin/name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (plugin/'scripts').mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'scripts/run.py',plugin/'scripts/run.py')
    shutil.copy2(ROOT/'README.md',plugin/'README.md')
    mcp = {'mcpServers':{'smart_image':{
        'command':sys.executable,'args':[str(plugin/'scripts/run.py'),'serve'],
        'startup_timeout_sec':30,'tool_timeout_sec':240,
        'env':{'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'}}}}
    (plugin/'.mcp.json').write_text(json.dumps(mcp,ensure_ascii=False,indent=2),encoding='utf-8')
    marketplace = {'name':'smart-image-local','interface':{'displayName':'智能生图本地插件'},
                   'plugins':[{'name':'smart-image','source':{'source':'local','path':'./plugin'},
                               'policy':{'installation':'AVAILABLE','authentication':'ON_USE'},'category':'Design'}]}
    catalog = destination/'.agents/plugins/marketplace.json'
    catalog.parent.mkdir(parents=True,exist_ok=True)
    catalog.write_text(json.dumps(marketplace,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'marketplace':str(destination),'plugin':str(plugin),'python':sys.executable}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination',required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.destination),ensure_ascii=False))
