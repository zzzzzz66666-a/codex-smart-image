from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fixtures import PNG, api_server, png_chunk
from smart_image.client import ImageService
from smart_image.client import image_type
from smart_image.client import NoRedirect
from smart_image.config import Settings
from smart_image.errors import ImageError


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'
        self.out = Path(self.temp.name) / 'project' / 'images'
        self.env = patch.dict(os.environ, {'CODEX_SMART_IMAGE_API_KEY':'local-test-key'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def service(self, state, timeout=5):
        return ImageService(Settings(base_url=state['base'], timeout_seconds=timeout), self.home)

    def test_base64_saved_and_exact_request(self):
        with api_server() as state:
            result = self.service(state).generate('一杯咖啡', str(self.out), 'coffee-1')
            self.assertEqual(Path(result['path']).read_bytes(), PNG)
            self.assertTrue(Path(result['path']).is_absolute())
            self.assertEqual(result['sha256'], hashlib.sha256(PNG).hexdigest())
            self.assertEqual(result['mime_type'], 'image/png')
            path, auth, payload = state['posts'][0]
            self.assertEqual(path, '/v1/images/generations')
            self.assertEqual(auth, 'Bearer local-test-key')
            self.assertEqual(payload, {'model':'gpt-image-2', 'prompt':'一杯咖啡', 'n':1, 'size':'auto'})

    def test_url_download_never_forwards_api_key(self):
        with api_server('url') as state:
            result = self.service(state).generate('photo', str(self.out), 'url-1')
            self.assertEqual(Path(result['path']).read_bytes(), PNG)
            self.assertEqual(state['gets'], [('/picture.png', None)])

    def test_model_list_uses_auth_without_generation(self):
        with api_server() as state:
            self.assertEqual(self.service(state).models(), ['gpt-image-2', 'other-model'])
            self.assertEqual(state['posts'], [])
            self.assertEqual(state['gets'], [('/v1/models', 'Bearer local-test-key')])

    def test_signed_download_url_query_is_preserved(self):
        with api_server('signed') as state:
            result = self.service(state).generate('photo', str(self.out), 'signed')
            self.assertEqual(Path(result['path']).read_bytes(), PNG)
            self.assertEqual(state['gets'], [('/picture.png?signature=test-only&expires=123', None)])

    def test_same_id_returns_cached_file_without_second_charge(self):
        with api_server() as state:
            svc = self.service(state)
            first = svc.generate('photo', str(self.out), 'same')
            second = svc.generate('photo', str(self.out), 'same')
            self.assertEqual(first['path'], second['path'])
            self.assertTrue(second['cached'])
            self.assertEqual(len(state['posts']), 1)

    def test_changed_request_id_parameters_are_rejected(self):
        with api_server() as state:
            svc = self.service(state)
            svc.generate('photo', str(self.out), 'same')
            with self.assertRaises(ImageError) as e:
                svc.generate('different', str(self.out), 'same')
            self.assertEqual(e.exception.code, 'request_conflict')
            self.assertEqual(len(state['posts']), 1)

    def test_removed_or_corrupted_artifact_is_not_regenerated(self):
        with api_server() as state:
            svc = self.service(state)
            result = svc.generate('photo', str(self.out), 'same')
            Path(result['path']).write_bytes(b'corrupted')
            with self.assertRaises(ImageError) as e:
                svc.generate('photo', str(self.out), 'same')
            self.assertEqual(e.exception.code, 'artifact_missing')
            self.assertEqual(len(state['posts']), 1)

    def test_401_is_sanitized_and_not_retried(self):
        with api_server('401') as state:
            svc = self.service(state)
            for _ in range(2):
                with self.assertRaises(ImageError) as e:
                    svc.generate('photo', str(self.out), 'auth')
                self.assertNotIn('local-test-key', str(e.exception))
                self.assertNotIn('DO-NOT-LEAK', str(e.exception))
            self.assertEqual(len(state['posts']), 1)

    def test_connection_lost_is_uncertain_and_not_resent(self):
        with api_server('disconnect') as state:
            svc = self.service(state)
            with self.assertRaises(ImageError) as e:
                svc.generate('photo', str(self.out), 'lost')
            self.assertTrue(e.exception.uncertain)
            with self.assertRaises(ImageError):
                self.service(state).generate('photo', str(self.out), 'lost')
            self.assertEqual(len(state['posts']), 1)

    def test_timeout_does_not_automatically_retry(self):
        with api_server('slow') as state:
            with self.assertRaises(ImageError) as e:
                self.service(state, 1).generate('photo', str(self.out), 'timeout')
            self.assertTrue(e.exception.uncertain)
            self.assertEqual(len(state['posts']), 1)

    def test_invalid_responses_leave_no_images(self):
        for mode in ['bad', 'empty', 'invalid_json', 'redirect']:
            with self.subTest(mode=mode), api_server(mode) as state:
                with self.assertRaises(ImageError):
                    self.service(state).generate('photo', str(self.out), mode)
                self.assertEqual(list(self.out.glob('*')), [])

    def test_response_size_is_bounded(self):
        with api_server() as state, patch('smart_image.client.MAX_RESPONSE_BYTES', 10):
            with self.assertRaises(ImageError) as e:
                self.service(state).generate('photo', str(self.out), 'large')
            self.assertEqual(e.exception.code, 'response_too_large')

    def test_forged_signatures_and_truncated_images_are_rejected(self):
        import struct
        forged = [b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',1,1)+b'junkIENDjunk',
                  b'\xff\xd8\xff'+b'not-an-image'+b'\xff\xd9',
                  b'RIFF'+struct.pack('<I',20)+b'WEBP'+b'not-a-valid-webp-frame', PNG[:-4]]
        for body in forged:
            with self.subTest(body=body[:12]), self.assertRaises(ImageError):
                image_type(body)
        with api_server('forged') as state:
            with self.assertRaises(ImageError):
                self.service(state).generate('photo',str(self.out),'forged')
            self.assertEqual(list(self.out.glob('*')),[])

    def test_redirect_rejection_closes_response(self):
        from io import BytesIO
        response = BytesIO(b'')
        with self.assertRaises(ImageError):
            NoRedirect().redirect_request(None,response,302,'redirect',{},'http://evil.example')
        self.assertTrue(response.closed)

    def test_real_webp_structure_accepted(self):
        import base64
        body = base64.b64decode('UklGRjwAAABXRUJQVlA4IDAAAAAQAgCdASoCAAIAAUAmJaACdLoB+AH4AAPIAP7rt6/9rP85R/8t3/2lkvXs/0XAAAA=')
        self.assertEqual(image_type(body),('image/webp','.webp'))

    def test_interlaced_png_requires_complete_adam7_rows(self):
        import struct
        import zlib
        def image(raw):
            return (b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,1))
                    +png_chunk(b'IDAT',zlib.compress(raw))+png_chunk(b'IEND',b''))
        for raw in [b'',b'\x00\xff',b'\x05\xff\x80\x20']:
            with self.subTest(raw=raw), self.assertRaises(ImageError):
                image_type(image(raw))
        self.assertEqual(image_type(image(b'\x00\xff\x80\x20')),('image/png','.png'))

    def test_failure_after_generation_preserves_charge_warning(self):
        import json
        for mode in ['missing_url','bad','redirect']:
            with self.subTest(mode=mode), api_server(mode) as state:
                with self.assertRaises(ImageError) as e:
                    self.service(state).generate('photo',str(self.out),'charged-'+mode)
                self.assertTrue(e.exception.uncertain)
                self.assertIn('收费',str(e.exception))
                records = [json.loads(p.read_text(encoding='utf-8')) for p in (self.home/'requests').glob('*.json')]
                self.assertTrue(all(r['error']['uncertain'] for r in records))

    def test_parallel_duplicate_sends_at_most_once(self):
        with api_server() as state:
            def run(_):
                try:
                    return self.service(state).generate('photo', str(self.out), 'parallel')
                except ImageError as e:
                    return e.code
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(run, range(4)))
            self.assertEqual(len(state['posts']), 1)
            self.assertTrue(any(isinstance(r, dict) for r in results), results)

    def test_validate_before_network_and_no_path_traversal(self):
        with api_server() as state:
            svc = self.service(state)
            for prompt, out, req in [('', str(self.out), 'empty'), ('x', 'relative', 'rel'),
                                     ('x', str(self.out), ''), ('x', str(self.out), '../outside')]:
                with self.subTest(req=req), self.assertRaises(ImageError):
                    svc.generate(prompt, out, req)
            self.assertEqual(state['posts'], [])
