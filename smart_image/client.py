import base64
import binascii
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import socket
import struct
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit
import uuid
from .image_validation import valid_png, valid_jpeg, valid_webp
from .config import validate_url
from .credentials import get_key
from .errors import ImageError
from .storage import atomic_json

MAX_RESPONSE_BYTES = 80 * 1024 * 1024
MAX_IMAGE_BYTES = 50 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ImageError('redirect_rejected', '服务返回重定向，请核对直接接口或图片地址。')


def image_type(data):
    if len(data) > MAX_IMAGE_BYTES:
        raise ImageError('image_too_large', '图片超过 50 MiB 上限。')
    if data.startswith(b'\x89PNG\r\n\x1a\n') and valid_png(data):
        return 'image/png', '.png'
    if data.startswith(b'\xff\xd8\xff') and valid_jpeg(data):
        return 'image/jpeg', '.jpg'
    if data.startswith(b'RIFF') and len(data) > 20 and data[8:12] == b'WEBP' and valid_webp(data):
        return 'image/webp', '.webp'
    raise ImageError('invalid_image', '服务没有返回可识别的 PNG、JPEG 或 WebP 图片。')


class ImageService:
    def __init__(self, settings, home):
        self.settings = settings
        self.home = Path(home)
        self.opener = urllib.request.build_opener(NoRedirect())

    def _request(self, url, *, body=None, auth=False, limit=MAX_RESPONSE_BYTES):
        if not self.settings.base_url:
            raise ImageError('missing_endpoint', '尚未配置服务地址，请在本地运行 configure --base-url。')
        headers = {'User-Agent':'CodexSmartImage/0.1.1', 'Accept':'application/json' if auth else 'image/*'}
        if auth:
            headers['Authorization'] = 'Bearer ' + get_key(self.home)
        if body is not None:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with self.opener.open(req, timeout=self.settings.timeout_seconds) as response:
                raw = response.read(limit + 1)
                if len(raw) > limit:
                    raise ImageError('response_too_large', '服务响应超过大小上限。', uncertain=body is not None)
                return raw
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            hint = {401:'API Key 无效或未获授权，请在本地重新配置。',
                    403:'服务拒绝访问，请检查账户权限。',
                    404:'接口或模型不存在，请核对 Base URL 和模型 ID。',
                    400:'参数或模型不被接受，请核对服务商支持的模型 ID、size 和 quality。',
                    429:'服务限流或额度不足，请检查账户后手动重试。'}.get(code, '服务返回错误，请检查服务状态。')
            raise ImageError('http_' + str(code), hint, uncertain=body is not None and code >= 500) from None
        except (urllib.error.URLError, TimeoutError, socket.timeout, http.client.HTTPException, OSError, UnicodeError):
            raise ImageError('network_error', '网络请求失败或超时；生图可能仍在服务端进行，请勿自动重复提交。',
                             uncertain=body is not None) from None

    def models(self):
        raw = self._request(self.settings.base_url + '/models', auth=True, limit=1024 * 1024)
        try:
            items = json.loads(raw)['data']
            if not isinstance(items, list):
                raise ValueError()
            return [item['id'] for item in items if isinstance(item, dict) and isinstance(item.get('id'), str)]
        except (ValueError, TypeError, KeyError):
            raise ImageError('invalid_response', '模型列表响应不是兼容的 data 数组。') from None

    def _cached(self, record_path, fingerprint):
        try:
            record = json.loads(record_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise ImageError('request_unknown', '该请求记录不可读，结果未知；请勿自动重发。', uncertain=True) from None
        if record.get('fingerprint') != fingerprint:
            raise ImageError('request_conflict', '同一 request_id 已用于不同参数。')
        if record.get('state') == 'succeeded':
            result = record['result']
            try:
                path = Path(result['path'])
                if path.stat().st_size > MAX_IMAGE_BYTES or hashlib.sha256(path.read_bytes()).hexdigest() != result['sha256']:
                    raise OSError()
            except OSError:
                raise ImageError('artifact_missing', '原图片缺失或已修改；没有再次调用收费接口。') from None
            return {**result, 'cached':True}
        if record.get('state') == 'failed':
            error = record['error']
            raise ImageError(error['code'], error['message'], uncertain=error.get('uncertain', False))
        raise ImageError('request_unknown', '同一请求仍在进行或结果未知；没有再次调用收费接口。', uncertain=True)

    def generate(self, prompt, output_dir, request_id, size='auto', quality=None):
        if not self.settings.base_url:
            raise ImageError('missing_endpoint', '尚未配置服务地址，请在本地运行 configure --base-url。')
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 32000:
            raise ImageError('invalid_prompt', '提示词必须是 1 到 32000 字符的文本。')
        if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', request_id):
            raise ImageError('invalid_request_id', 'request_id 只允许 1 到 100 位英文字母、数字、短横线或下划线。')
        if not isinstance(output_dir, str) or not output_dir or not Path(output_dir).is_absolute():
            raise ImageError('invalid_output_dir', 'output_dir 必须是当前项目内的绝对路径。')
        if not isinstance(size, str) or not re.fullmatch(r'(auto|[1-9][0-9]{1,4}x[1-9][0-9]{1,4})', size):
            raise ImageError('invalid_size', 'size 必须是 auto 或例如 1024x1024 的像素尺寸。')
        if quality is not None and quality not in ('auto', 'low', 'medium', 'high'):
            raise ImageError('invalid_quality', 'quality 必须是 auto、low、medium 或 high。')
        out = Path(output_dir).resolve()
        payload = {'model':self.settings.model, 'prompt':prompt, 'n':1, 'size':size}
        if quality is not None:
            payload['quality'] = quality
        fingerprint = hashlib.sha256(json.dumps([self.settings.base_url, payload, str(out)], sort_keys=True).encode()).hexdigest()
        directory = self.home / 'requests'
        record_path = directory / (hashlib.sha256(request_id.encode()).hexdigest() + '.json')
        if record_path.exists():
            return self._cached(record_path, fingerprint)
        get_key(self.home)  # Missing credentials must not consume a request ID.
        try:
            out.mkdir(parents=True, exist_ok=True)
            directory.mkdir(parents=True, exist_ok=True)
            with record_path.open('x', encoding='utf-8') as f:
                json.dump({'state':'pending', 'fingerprint':fingerprint}, f)
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError:
            return self._cached(record_path, fingerprint)
        except OSError:
            raise ImageError('storage_error', '无法创建输出目录或请求记录，尚未发送生图请求。') from None
        post_succeeded = False
        try:
            raw = self._request(self.settings.base_url + '/images/generations',
                                body=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                                auth=True, limit=MAX_RESPONSE_BYTES)
            post_succeeded = True
            try:
                item = json.loads(raw)['data'][0]
                if not isinstance(item, dict):
                    raise ValueError()
                if isinstance(item.get('b64_json'), str):
                    encoded = item['b64_json']
                    if len(encoded) > (MAX_IMAGE_BYTES + 2) // 3 * 4:
                        raise ImageError('image_too_large', '图片超过 50 MiB 上限。')
                    data = base64.b64decode(encoded, validate=True)
                elif isinstance(item.get('url'), str):
                    url = item['url']
                    try:
                        parts = urlsplit(url)
                        validate_url(urlunsplit(parts._replace(query='')))
                    except ValueError:
                        raise ImageError('invalid_url', '图片下载地址无效。') from None
                    local = ('127.0.0.1', 'localhost', '::1')
                    if parts.hostname in local and urlsplit(self.settings.base_url).hostname not in local:
                        raise ImageError('invalid_url', '远程服务不能要求下载本机地址。')
                    data = self._request(url, limit=MAX_IMAGE_BYTES)
                else:
                    raise ValueError()
            except (ValueError, KeyError, IndexError, TypeError, binascii.Error):
                raise ImageError('invalid_response', '生图响应缺少有效 data[0].b64_json 或 url。', uncertain=True) from None
            mime, suffix = image_type(data)
            path = out / ('image-' + uuid.uuid4().hex + suffix)
            try:
                with path.open('xb') as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
            except OSError:
                path.unlink(missing_ok=True)
                raise
            result = {'path':str(path), 'mime_type':mime, 'sha256':hashlib.sha256(data).hexdigest(),
                      'request_id':request_id, 'model':self.settings.model, 'cached':False}
            atomic_json(record_path, {'state':'succeeded', 'fingerprint':fingerprint, 'result':result})
            return result
        except ImageError as e:
            if post_succeeded:
                e = ImageError(e.code, '生图请求已被服务接受，可能已收费；图片下载或校验未完成。请勿自动重发。错误：' + str(e), uncertain=True)
            try:
                atomic_json(record_path, {'state':'failed', 'fingerprint':fingerprint, 'error':e.as_dict()})
            except OSError:
                pass
            raise e from None
        except OSError:
            raise ImageError('storage_error', '服务可能已生成图片，但本地保存失败；请勿自动重发。', uncertain=True) from None
