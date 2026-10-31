import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fixtures import api_server
from smart_image.config import Settings

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def run_cli(self, home, *args, key=''):
        return subprocess.run([sys.executable, str(ROOT / 'scripts' / 'run.py'), *args],
                              input='', capture_output=True, text=True, encoding='utf-8', timeout=15,
                              env={**os.environ,'CODEX_SMART_IMAGE_HOME':str(home),
                                   'CODEX_SMART_IMAGE_API_KEY':key,'PYTHONIOENCODING':'utf-8'})

    def test_status_missing_key_is_not_ready_and_does_not_leak(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.run_cli(d, 'status')
            self.assertEqual(p.returncode, 0, p.stderr)
            value = json.loads(p.stdout)
            self.assertFalse(value['key_configured'])
            self.assertEqual(value['base_url'], '')
            self.assertFalse(value['provider_configured'])
            self.assertFalse(value['ready'])

    def test_configure_without_prompt_and_models(self):
        with tempfile.TemporaryDirectory() as d, api_server() as state:
            p = self.run_cli(d, 'configure', '--base-url',state['base'],'--model','actual-model-id','--keep-key')
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(Settings.load(d).model, 'actual-model-id')
            p = self.run_cli(d,'models',key='local-test-key')
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)['models'], ['gpt-image-2','other-model'])
            self.assertNotIn('local-test-key',p.stdout+p.stderr)
            self.assertEqual(state['posts'], [])

    def test_noninteractive_key_prompt_fails_without_reading_stdin(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.run_cli(d,'configure')
            self.assertNotEqual(p.returncode, 0)
            self.assertNotIn('Traceback',p.stderr)
            self.assertFalse((Path(d)/'api-key.dpapi').exists())

    def test_configure_requires_local_endpoint(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.run_cli(d,'configure','--keep-key')
            self.assertEqual(p.returncode,1)
            self.assertEqual(json.loads(p.stderr)['code'],'missing_endpoint')
            self.assertFalse((Path(d)/'config.json').exists())

    def test_unconfigured_generation_does_not_create_request_record(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.run_cli(d,'generate','--prompt','photo','--output-dir',str(Path(d)/'out'),
                             '--request-id','missing-provider',key='local-test-key')
            self.assertEqual(p.returncode,1)
            self.assertEqual(json.loads(p.stderr)['code'],'missing_endpoint')
            self.assertFalse((Path(d)/'requests').exists())

    def test_generate_subprocess_saves_file(self):
        with tempfile.TemporaryDirectory() as d, api_server() as state:
            Settings(base_url=state['base']).save(d)
            p = self.run_cli(d,'generate','--prompt','a photo','--output-dir',str(Path(d)/'out'),
                             '--request-id','cli-1',key='local-test-key')
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertTrue(Path(json.loads(p.stdout)['path']).exists())
