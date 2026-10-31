import json
import sys
from dataclasses import asdict
from .client import ImageService
from .config import Settings
from .credentials import get_key
from .errors import ImageError


def config_status(home):
    value = asdict(Settings.load(home))
    value['provider_configured'] = bool(value['base_url'])
    try:
        get_key(home)
        value['key_configured'] = True
    except ImageError as e:
        value['key_configured'] = False
        value['credential_status'] = e.code
    value['ready'] = value['provider_configured'] and value['key_configured']
    return value


TOOLS = [
    {'name':'get_image_config', 'description':'Read configured dedicated image provider/model and whether a local API key exists. Never returns the key. Use before generating images.',
     'inputSchema':{'type':'object','properties':{},'additionalProperties':False},
     'annotations':{'readOnlyHint':True,'openWorldHint':False}},
    {'name':'list_image_models','description':'List model IDs from the configured image API. Does not generate images. Use to check the exact GPT Image 2 model ID.',
     'inputSchema':{'type':'object','properties':{},'additionalProperties':False},
     'annotations':{'readOnlyHint':True,'openWorldHint':True}},
    {'name':'generate_image','description':'Generate one raster image using the user-configured dedicated GPT Image 2 API and save it in the current project. Useful for photographic website assets, illustrations, posters, backgrounds and bitmap artwork, even when image generation was not explicitly requested. Prefer structured tools for plots, diagrams and SVG editing. Requires locally configured key. request_id is a stable unique ID for this logical image; reuse it after interruptions to prevent duplicate paid requests. Never silently change provider or automatically resubmit a failed request with a new ID.',
     'inputSchema':{'type':'object','properties':{
         'prompt':{'type':'string','minLength':1,'maxLength':32000,'description':'Image brief: subject, composition, style, intended use, and exact text if needed.'},
         'output_dir':{'type':'string','description':'Absolute path inside the active user project, normally its images or assets folder.'},
         'request_id':{'type':'string','pattern':'^[A-Za-z0-9_-]{1,100}$','description':'Stable unique ID, for example coffee-hero-a3f271. Reuse for this same logical request.'},
         'size':{'type':'string','description':'auto (default) or a provider-supported widthxheight, e.g. 1024x1024.'},
         'quality':{'type':'string','enum':['auto','low','medium','high'],'description':'Optional; omitted by default for provider compatibility.'}},
         'required':['prompt','output_dir','request_id'],'additionalProperties':False},
     'annotations':{'readOnlyHint':False,'destructiveHint':False,'idempotentHint':True,'openWorldHint':True}}
]


def tool_call(name, arguments, home):
    if name == 'get_image_config':
        return config_status(home)
    service = ImageService(Settings.load(home), home)
    if name == 'list_image_models':
        return {'models':service.models()}
    return service.generate(**arguments)


def error(ident, code, message):
    return {'jsonrpc':'2.0','id':ident,'error':{'code':code,'message':message}}


def dispatch(message, home):
    if (not isinstance(message, dict) or message.get('jsonrpc') != '2.0'
            or not isinstance(message.get('method'), str)):
        return error(None, -32600, 'Invalid JSON-RPC request')
    if 'id' not in message:
        return None
    ident = message['id']
    method = message['method']
    params = message.get('params', {})
    if not isinstance(params, dict):
        return error(ident, -32602, 'params must be an object')
    if method == 'initialize':
        requested = params.get('protocolVersion')
        version = requested if requested in ('2024-11-05','2025-03-26','2025-06-18') else '2025-06-18'
        result = {'protocolVersion':version,'serverInfo':{'name':'smart-image','version':'0.1.2'},
                  'capabilities':{'tools':{'listChanged':False}}}
    elif method == 'ping':
        result = {}
    elif method == 'tools/list':
        result = {'tools':TOOLS}
    elif method == 'tools/call':
        name = params.get('name')
        args = params.get('arguments', {})
        definition = next((t for t in TOOLS if t['name'] == name), None)
        if definition is None or not isinstance(args, dict):
            return error(ident, -32602, 'Unknown tool or invalid arguments')
        schema = definition['inputSchema']
        if set(args) - set(schema['properties']) or set(schema.get('required', [])) - set(args):
            return error(ident, -32602, 'Unexpected or missing tool arguments')
        try:
            value = tool_call(name, args, home)
            result = {'content':[{'type':'text','text':json.dumps(value,ensure_ascii=False)}]}
        except ImageError as e:
            result = {'isError':True,'content':[{'type':'text','text':json.dumps(e.as_dict(),ensure_ascii=False)}]}
        except (OSError, ValueError, TypeError, KeyError):
            result = {'isError':True,'content':[{'type':'text','text':json.dumps({'code':'internal_error','message':'本地处理失败，请检查配置和输出目录；不会自动重试生图。'},ensure_ascii=False)}]}
    else:
        return error(ident, -32601, 'Method not found')
    return {'jsonrpc':'2.0','id':ident,'result':result}


def serve(home):
    while True:
        line = sys.stdin.buffer.readline(1024 * 1024 + 1)
        if not line:
            return
        if len(line) > 1024 * 1024:
            response = error(None, -32600, 'Request too large')
            # Drain the rest of this line so it cannot become a second message.
            while line and not line.endswith(b'\n'):
                line = sys.stdin.buffer.readline(1024 * 1024 + 1)
        else:
            try:
                response = dispatch(json.loads(line), home)
            except (ValueError, UnicodeError):
                response = error(None, -32700, 'Parse error')
        if response is not None:
            sys.stdout.write(json.dumps(response,ensure_ascii=False) + '\n')
            sys.stdout.flush()
