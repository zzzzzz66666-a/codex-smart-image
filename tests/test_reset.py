import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ResetTests(unittest.TestCase):
    def run_reset(self, data, *, confirm=False, env_key='', shell=None):
        entry=ROOT/'scripts/reset.ps1'
        self.assertTrue(entry.is_file(),'Release lacks the explicit local reset entry')
        command=[shell or shutil.which('pwsh'),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
                 '-File',str(entry),'-PythonPath',sys.executable]
        if confirm: command.append('-ConfirmReset')
        env={**os.environ,'CODEX_SMART_IMAGE_HOME':str(data),'CODEX_SMART_IMAGE_API_KEY':env_key,
             'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
        return subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=20)

    def seed(self, data):
        data.mkdir()
        for name in ('config.json','api-key.dpapi','config.json.bak','.writing-fixture'):
            (data/name).write_text('isolated dummy state')
        for name in ('requests','logs','marketplace','images'):
            (data/name).mkdir()
            (data/name/'keep-or-remove.txt').write_text(name)

    def test_reset_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'state'
            self.seed(data)
            p=self.run_reset(data)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertFalse(json.loads(p.stdout)['reset_performed'])
            self.assertTrue((data/'api-key.dpapi').is_file())
            self.assertTrue((data/'requests/keep-or-remove.txt').is_file())

    def test_confirmed_reset_removes_runtime_state_and_preserves_plugin_and_images(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'state'
            self.seed(data)
            p=self.run_reset(data,confirm=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            result=json.loads(p.stdout)
            self.assertTrue(result['reset_performed'])
            for name in ('config.json','api-key.dpapi','config.json.bak','.writing-fixture','requests','logs'):
                self.assertFalse((data/name).exists(),name)
            self.assertEqual((data/'marketplace/keep-or-remove.txt').read_text(),'marketplace')
            self.assertEqual((data/'images/keep-or-remove.txt').read_text(),'images')
            self.assertFalse(result['ready'])

    def test_environment_key_blocks_reset_before_any_file_is_deleted(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'state'
            self.seed(data)
            p=self.run_reset(data,confirm=True,env_key='isolated-environment-credential')
            self.assertNotEqual(p.returncode,0)
            self.assertTrue((data/'config.json').is_file())
            self.assertTrue((data/'api-key.dpapi').is_file())

    def test_redirected_record_directory_is_rejected_before_deletion(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/'state'
            outside=Path(d)/'outside'
            data.mkdir()
            outside.mkdir()
            (data/'config.json').write_text('isolated dummy state')
            (outside/'keep.txt').write_text('unrelated data')
            env={**os.environ,'RESET_TEST_LINK':str(data/'requests'),'RESET_TEST_TARGET':str(outside)}
            made=subprocess.run([shutil.which('pwsh'),'-NoProfile','-NonInteractive','-Command',
                'New-Item -ItemType Junction -Path $env:RESET_TEST_LINK -Target $env:RESET_TEST_TARGET | Out-Null'],
                env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
            self.assertEqual(made.returncode,0,made.stderr)
            p=self.run_reset(data,confirm=True)
            self.assertNotEqual(p.returncode,0)
            self.assertTrue((data/'config.json').is_file())
            self.assertEqual((outside/'keep.txt').read_text(),'unrelated data')

    def check_redirected_home(self, ancestor):
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)
            actual=directory/'outside'
            actual.mkdir()
            target=actual/'state' if ancestor else actual
            if ancestor: target.mkdir()
            (target/'config.json').write_text('unrelated state')
            link=directory/'redirected'
            env={**os.environ,'RESET_TEST_LINK':str(link),'RESET_TEST_TARGET':str(actual)}
            made=subprocess.run([shutil.which('pwsh'),'-NoProfile','-NonInteractive','-Command',
                'New-Item -ItemType Junction -Path $env:RESET_TEST_LINK -Target $env:RESET_TEST_TARGET | Out-Null'],
                env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
            self.assertEqual(made.returncode,0,made.stderr)
            data=link/'state' if ancestor else link
            p=self.run_reset(data,confirm=True)
            self.assertNotEqual(p.returncode,0)
            self.assertEqual((target/'config.json').read_text(),'unrelated state')

    def test_redirected_data_home_is_rejected_before_resolution(self):
        self.check_redirected_home(False)

    def test_redirected_data_home_ancestor_is_rejected_before_resolution(self):
        self.check_redirected_home(True)

    def test_confirmed_reset_also_works_in_windows_powershell(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)/"person's isolated state"
            self.seed(data)
            shell=str(Path(os.environ['WINDIR'])/'System32/WindowsPowerShell/v1.0/powershell.exe')
            p=self.run_reset(data,confirm=True,shell=shell)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertTrue(json.loads(p.stdout)['reset_performed'])
            self.assertTrue((data/'images/keep-or-remove.txt').is_file())
