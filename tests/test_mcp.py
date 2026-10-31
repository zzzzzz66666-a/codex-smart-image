import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fixtures import PNG, api_server
from smart_image.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def call_server(messages, home, key='local-test-key'):
    env = {**os.environ, 'CODEX_SMART_IMAGE_HOME':str(home), 'CODEX_SMART_IMAGE_API_KEY':key,
           'PYTHONIOENCODING':'utf-8', 'PYTHONDONTWRITEBYTECODE':'1'}
    p = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'run.py'), 'serve'],
                       input=''.join(json.dumps(m, ensure_ascii=False) + '\n' for m in messages),
                       capture_output=True, text=True, encoding='utf-8', env=env, timeout=20)
    if p.returncode:
        raise AssertionError('MCP process failed: ' + p.stderr)
    return [json.loads(line) for line in p.stdout.splitlines()]


class MCPTests(unittest.TestCase):
    def test_handshake_tools_and_real_generation(self):
        with tempfile.TemporaryDirectory() as d, api_server() as state:
            home = Path(d) / 'data'
            Settings(base_url=state['base']).save(home)
            messages = [
                {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},
                {'jsonrpc':'2.0','method':'notifications/initialized'},
                {'jsonrpc':'2.0','id':2,'method':'tools/list'},
                {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'generate_image','arguments':{'prompt':'咖啡摄影','output_dir':str(Path(d) / 'images'),'request_id':'mcp-1'}}},
                {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'generate_image','arguments':{'prompt':'咖啡摄影','output_dir':str(Path(d) / 'images'),'request_id':'mcp-1'}}}
            ]
            output = call_server(messages, home)
            self.assertEqual([m['id'] for m in output], [1,2,3,4])
            self.assertEqual(output[0]['result']['protocolVersion'], '2024-11-05')
            tools = {t['name']: t for t in output[1]['result']['tools']}
            self.assertEqual(set(tools), {'get_image_config','list_image_models','generate_image'})
            self.assertNotIn('api_key', tools['generate_image']['inputSchema']['properties'])
            result = output[2]['result']
            self.assertFalse(result.get('isError',False))
            data = json.loads(result['content'][0]['text'])
            self.assertEqual(Path(data['path']).read_bytes(), PNG)
            self.assertEqual(len(state['posts']), 1)
            self.assertTrue(json.loads(output[3]['result']['content'][0]['text'])['cached'])

    def test_tool_error_and_bad_arguments_are_safe(self):
        with tempfile.TemporaryDirectory() as d, api_server('401') as state:
            home = Path(d)
            Settings(base_url=state['base']).save(home)
            messages = [
                {'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'generate_image','arguments':{'prompt':'x','output_dir':str(home / 'images'),'request_id':'err'}}},
                {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'generate_image','arguments':{'api_key':'secret'}}},
                {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'not_a_tool','arguments':{}}},
                {'jsonrpc':'2.0','id':4,'method':'unknown'},
                {'jsonrpc':'2.0','id':5,'method':'tools/call','params':{'name':'get_image_config','arguments':{}}}
            ]
            output = call_server(messages, home)
            self.assertTrue(output[0]['result']['isError'])
            self.assertNotIn('local-test-key', json.dumps(output))
            self.assertNotIn('DO-NOT-LEAK', json.dumps(output))
            self.assertEqual(output[1]['error']['code'], -32602)
            self.assertEqual(output[2]['error']['code'], -32602)
            self.assertEqual(output[3]['error']['code'], -32601)
            config = json.loads(output[4]['result']['content'][0]['text'])
            self.assertTrue(config['key_configured'])
            self.assertEqual(config['model'], 'gpt-image-2')

    def test_malformed_message_does_not_crash_process(self):
        with tempfile.TemporaryDirectory() as d:
            output = call_server([[], {'jsonrpc':'2.0','id':1,'method':'ping'}], d)
            self.assertEqual(output[0]['error']['code'], -32600)
            self.assertEqual(output[1]['result'], {})
