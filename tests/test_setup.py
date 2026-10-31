import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
FAKE_RUN='''import json, pathlib, sys
value=json.loads(pathlib.Path('fixture-status.json').read_text())
if '--help' in sys.argv:
    print('configure status')
elif 'status' in sys.argv:
    print(json.dumps(value))
elif 'configure' in sys.argv:
    pathlib.Path('configure-received.json').write_text(json.dumps({'keep_key':'--keep-key' in sys.argv}))
    value.update(provider_configured=True,key_configured=True,ready=True)
    print(json.dumps(value))
else:
    raise SystemExit(2)
'''


class SetupTests(unittest.TestCase):
    def check_case(self, *, existing=True, replace=False, check_only=False, environment_key=False):
        entry=ROOT/'scripts/configure.ps1'
        self.assertTrue(entry.is_file(),'Release lacks the interactive configuration entry')
        shells=[str(Path(os.environ['WINDIR'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),shutil.which('pwsh')]
        for shell in shells:
            self.assertTrue(shell,'Both supported PowerShell versions must be available')
            with self.subTest(shell=Path(shell).name), tempfile.TemporaryDirectory() as d:
                runtime=Path(d)/"setup person's files"
                (runtime/'scripts').mkdir(parents=True)
                (runtime/'smart_image').mkdir()
                shutil.copy2(entry,runtime/'scripts/configure.ps1')
                (runtime/'scripts/run.py').write_text(FAKE_RUN,encoding='utf-8')
                (runtime/'smart_image/cli.py').write_text('# isolated dummy marker\n')
                fixture={'base_url':'https://images.example/v1','model':'gpt-image-2',
                         'provider_configured':True,'key_configured':existing,'ready':existing}
                (runtime/'fixture-status.json').write_text(json.dumps(fixture))
                wrapper=runtime/'wrapper.ps1'
                wrapper.write_text('''$ErrorActionPreference='Stop'
$global:SetupPromptCount=0
function global:Read-Host {
    param([string]$Prompt)
    $global:SetupPromptCount++
    if ($global:SetupPromptCount -gt 2) { throw 'Unexpected visible credential-choice prompt.' }
    return ''
}
& $env:SMART_SETUP_TEST_ENTRY -PythonPath $env:SMART_SETUP_TEST_PYTHON '''+
                    ('-CheckOnly' if check_only else '-ReplaceKey' if replace else '')+'''\n
if ($global:SetupPromptCount -ne '''+('0' if check_only else '2')+''') { throw 'Unexpected prompt count.' }
''',encoding='utf-8')
                env={**os.environ,'SMART_SETUP_TEST_ENTRY':str(runtime/'scripts/configure.ps1'),
                     'SMART_SETUP_TEST_PYTHON':sys.executable,'CODEX_SMART_IMAGE_HOME':str(runtime/'isolated-data'),
                     'CODEX_SMART_IMAGE_API_KEY':'isolated-environment-credential' if environment_key else '',
                     'PYTHONDONTWRITEBYTECODE':'1'}
                p=subprocess.run([shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(wrapper)],
                                 capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=20)
                record=runtime/'configure-received.json'
                if environment_key and replace:
                    self.assertNotEqual(p.returncode,0)
                    self.assertIn('environment',p.stderr.lower())
                    self.assertFalse(record.exists())
                    continue
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
                if check_only:
                    self.assertFalse(record.exists())
                else:
                    self.assertEqual(json.loads(record.read_text())['keep_key'],existing and not replace)

    def test_existing_key_is_preserved_without_visible_key_choice(self):
        self.check_case()

    def test_explicit_replacement_uses_the_hidden_key_entry(self):
        self.check_case(replace=True)

    def test_first_configuration_uses_the_hidden_key_entry(self):
        self.check_case(existing=False)

    def test_check_only_does_not_prompt_or_change_configuration(self):
        self.check_case(check_only=True)

    def test_environment_key_blocks_local_replacement_without_mutation(self):
        self.check_case(replace=True,environment_key=True)
