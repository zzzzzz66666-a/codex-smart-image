import json
import os
from pathlib import Path
import tempfile
import unittest
from smart_image.config import Settings
from smart_image.credentials import set_key, get_key, clear_key
from smart_image.errors import ImageError


class ConfigTests(unittest.TestCase):
    def test_roundtrip_does_not_store_key(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            Settings().save(home)
            self.assertEqual(Settings.load(home).base_url, '')
            self.assertEqual(Settings.load(home).model, 'gpt-image-2')
            self.assertNotIn('api_key', json.loads((home / 'config.json').read_text()))

    def test_url_validation(self):
        for url in ['http://remote.example/v1', 'https://' + 'user:pass@host/v1',
                    'https://host/v1?key=secret', 'https://host/v1#x', 'file:///tmp']:
            with self.subTest(url=url), self.assertRaises(ImageError):
                Settings(base_url=url)
        self.assertEqual(Settings(base_url='https://host/v1/').base_url, 'https://host/v1')
        self.assertEqual(Settings(base_url='http://127.0.0.1:8000/v1').model, 'gpt-image-2')

    def test_reject_unknown_schema_and_malformed_config(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'config.json'
            for contents in ['{', '{"schema_version":99}', '[]', '{"timeout_seconds":false}']:
                p.write_text(contents)
                with self.subTest(contents=contents), self.assertRaises(ImageError):
                    Settings.load(Path(d))

    def test_real_windows_dpapi_roundtrip_and_delete(self):
        if os.name != 'nt':
            self.skipTest('Windows-only DPAPI integration')
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            secret = 'test-only-local-key-中文'
            set_key(home, secret)
            self.assertEqual(get_key(home), secret)
            self.assertNotIn(secret.encode(), (home / 'api-key.dpapi').read_bytes())
            clear_key(home)
            with self.assertRaises(ImageError):
                get_key(home)

    def test_missing_key_and_env_key(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImageError):
                get_key(Path(d))
            with patch.dict(os.environ, {'CODEX_SMART_IMAGE_API_KEY':'local-test'}):
                self.assertEqual(get_key(Path(d)), 'local-test')
                self.assertFalse((Path(d) / 'api-key.dpapi').exists())
