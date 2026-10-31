import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PrivacyTests(unittest.TestCase):
    def check(self, target, denylist=None):
        cmd=[sys.executable,str(ROOT/'scripts/check_release_privacy.py'),str(target)]
        if denylist:
            cmd.extend(['--denylist-file',str(denylist)])
        return subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=10)

    def test_missing_target_cannot_report_a_successful_audit(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.check(Path(d)/'missing-export')
            self.assertEqual(p.returncode,1)
            self.assertFalse(json.loads(p.stdout)['passed'])
            self.assertIn('missing_target',p.stdout)

    def test_safe_example_passes_but_local_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'export'
            root.mkdir()
            (root/'README.md').write_text('Use https://image.example/v1 and configure privately.',encoding='utf-8')
            p=self.check(root)
            self.assertEqual(p.returncode,0,p.stderr)
            (root/'config.json').write_text('{}',encoding='utf-8')
            p=self.check(root)
            self.assertEqual(p.returncode,1)
            self.assertIn('private_file',p.stdout)

    def test_private_terms_inside_archive_are_detected_without_echoing_them(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            term='private-install-fixture'
            deny=root/'deny.json'
            deny.write_text(json.dumps([term]))
            target=root/'source.zip'
            with zipfile.ZipFile(target,'w') as z:
                z.writestr('source/README.md','configured for '+term)
            p=self.check(target,deny)
            self.assertEqual(p.returncode,1)
            self.assertIn('private_term',p.stdout)
            self.assertNotIn(term,p.stdout+p.stderr)

    def test_first_commit_safety_rejects_personal_paths_and_token(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            token='ghp_'+'A'*36
            local_path='C:'+chr(92)+'Users'+chr(92)+'PrivateFixture'+chr(92)+'Desktop'
            (root/'bad.md').write_text(local_path+'\n'+token)
            p=self.check(root)
            self.assertEqual(p.returncode,1)
            self.assertIn('personal_path',p.stdout)
            self.assertIn('credential_pattern',p.stdout)
            self.assertNotIn(token,p.stdout+p.stderr)

    def test_unapproved_service_domain_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'README.md').write_text('https://'+'unapproved-provider.test'+'/v1')
            p=self.check(root)
            self.assertEqual(p.returncode,1)
            self.assertIn('unapproved_url',p.stdout)
