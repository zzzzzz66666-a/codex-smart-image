import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_prepared_marketplace_mcp_runs_after_copy(self):
        with tempfile.TemporaryDirectory() as d:
            destination = Path(d) / 'marketplace'
            p = subprocess.run([sys.executable,str(ROOT/'scripts'/'prepare_install.py'),'--destination',str(destination)],
                               capture_output=True,text=True,encoding='utf-8',timeout=15)
            self.assertEqual(p.returncode,0,p.stderr)
            marketplace = json.loads((destination/'.agents/plugins/marketplace.json').read_text(encoding='utf-8'))
            self.assertEqual(marketplace['name'],'smart-image-local')
            plugin = destination/'plugin'
            self.assertTrue((plugin/'docs/INSTALL.zh-CN.md').is_file())
            self.assertTrue((plugin/'installer-skill/codex-smart-image-install/SKILL.md').is_file())
            for name in ('configure.ps1','reset.ps1','install.ps1','prepare_install.py','uninstall.ps1'):
                self.assertTrue((plugin/'scripts'/name).is_file(),name)
            manifest = json.loads((plugin/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['name'],'smart-image')
            mcp = json.loads((plugin/'.mcp.json').read_text(encoding='utf-8'))['mcpServers']['smart_image']
            self.assertEqual(mcp['command'],sys.executable)
            self.assertTrue(Path(mcp['args'][0]).is_file())
            message = json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/list'})+'\n'
            env = {**os.environ,'CODEX_SMART_IMAGE_HOME':str(Path(d)/'data'),'PYTHONIOENCODING':'utf-8'}
            started = subprocess.run([mcp['command'],*mcp['args']],input=message,capture_output=True,
                                     text=True,encoding='utf-8',env=env,timeout=10,cwd=d)
            self.assertEqual(started.returncode,0,started.stderr)
            self.assertEqual(len(json.loads(started.stdout)['result']['tools']),3)

    def test_release_zip_contains_no_local_key_or_data(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable,str(ROOT/'scripts'/'build_release.py'),'--output-dir',d],
                               capture_output=True,text=True,encoding='utf-8',timeout=15)
            self.assertEqual(p.returncode,0,p.stderr)
            info = json.loads(p.stdout)
            with zipfile.ZipFile(info['path']) as z:
                names = z.namelist()
                self.assertTrue(any(n.endswith('scripts/install.ps1') for n in names))
                self.assertTrue(any(n.endswith('skills/smart-image/SKILL.md') for n in names))
                self.assertFalse(any(n.endswith('.dpapi') or '__pycache__' in n or 'config.json' in n for n in names))
                self.assertIsNone(z.testzip())
                z.extractall(Path(d)/'unpacked')
            run = Path(d)/'unpacked'/'codex-smart-image-0.1.2'/'scripts'/'run.py'
            env = {**os.environ,'CODEX_SMART_IMAGE_HOME':str(Path(d)/'data'),'CODEX_SMART_IMAGE_API_KEY':'','PYTHONIOENCODING':'utf-8'}
            smoke = subprocess.run([sys.executable,str(run),'status'],capture_output=True,text=True,
                                   encoding='utf-8',timeout=10,env=env,cwd=d)
            self.assertEqual(smoke.returncode,0,smoke.stderr)
            self.assertFalse(json.loads(smoke.stdout)['key_configured'])
