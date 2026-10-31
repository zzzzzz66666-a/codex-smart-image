import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CodexInstallTests(unittest.TestCase):
    def test_powershell_install_upgrade_and_uninstall_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)/'codex-home'
            home.mkdir()
            destination = Path(d)/'marketplace'
            env = {**os.environ,'CODEX_HOME':str(home),'PYTHONIOENCODING':'utf-8',
                   'CODEX_SMART_IMAGE_HOME':str(Path(d)/'image-data')}
            ps = shutil.which('pwsh') or shutil.which('powershell')
            self.assertIsNotNone(ps)
            command = [ps,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',
                       str(ROOT/'scripts/install.ps1'),'-PythonPath',sys.executable,'-InstallRoot',str(destination)]
            for _ in range(2):
                p = subprocess.run(command,env=env,input='',capture_output=True,text=True,
                                   encoding='utf-8',errors='replace',timeout=30)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            p = subprocess.run([ps,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',
                                str(ROOT/'scripts/uninstall.ps1')],env=env,input='',capture_output=True,
                               text=True,encoding='utf-8',errors='replace',timeout=30)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertTrue((destination/'plugin/scripts/run.py').is_file())

    def test_native_plugin_install_list_remove_with_isolated_codex_home(self):
        codex = shutil.which('codex')
        self.assertIsNotNone(codex, 'Codex CLI is required for the local integration acceptance test')
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)/'codex-home'
            home.mkdir()
            destination = Path(d)/'marketplace'
            env = {**os.environ, 'CODEX_HOME':str(home), 'PYTHONIOENCODING':'utf-8',
                   'CODEX_SMART_IMAGE_HOME':str(Path(d)/'image-data')}
            prepared = subprocess.run([sys.executable,str(ROOT/'scripts/prepare_install.py'),'--destination',str(destination)],
                                      env=env,capture_output=True,text=True,encoding='utf-8',timeout=20)
            self.assertEqual(prepared.returncode,0,prepared.stderr)
            def run(*args):
                p = subprocess.run([codex,'plugin',*args],env=env,capture_output=True,text=True,
                                   encoding='utf-8',errors='replace',timeout=30)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
                return p.stdout
            run('marketplace','add',str(destination),'--json')
            installed = run('add','smart-image@smart-image-local','--json')
            self.assertIn('smart-image',installed)
            listed = run('list','--json')
            self.assertIn('smart-image',listed)
            manifests = list(home.rglob('plugin.json'))
            self.assertTrue(manifests,'Codex did not create a plugin cache')
            matching = [p for p in manifests if json.loads(p.read_text(encoding='utf-8')).get('name') == 'smart-image']
            self.assertEqual(len(matching),1)
            cached = matching[0].parent.parent
            self.assertTrue((cached/'skills/smart-image/SKILL.md').exists())
            self.assertTrue((cached/'.mcp.json').exists())
            run('remove','smart-image@smart-image-local')
            self.assertTrue((destination/'plugin/scripts/run.py').exists())
