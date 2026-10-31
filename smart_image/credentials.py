import ctypes
from ctypes import wintypes
import os
from pathlib import Path
from .errors import ImageError
from .storage import atomic_bytes


class Blob(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_ubyte))]


def _crypt(data, decrypt=False):
    if os.name != 'nt':
        raise ImageError('platform', '加密密钥存储需要 Windows；其他系统请使用环境变量提供 Key。')
    buf = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ImageError('credential_error', 'Windows 无法读取或保存凭据；请使用原 Windows 用户重新配置。')
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(target.pbData, ctypes.c_void_p))


def set_key(home, key):
    if not isinstance(key, str) or not key.strip() or any(c in key for c in '\r\n'):
        raise ImageError('invalid_key', 'Key 不能为空或包含换行。')
    atomic_bytes(Path(home) / 'api-key.dpapi', _crypt(key.strip().encode('utf-8')))


def get_key(home):
    key = os.environ.get('CODEX_SMART_IMAGE_API_KEY', '').strip()
    if key:
        if any(c in key for c in '\r\n'):
            raise ImageError('invalid_key', 'Key 不能包含换行。')
        return key
    path = Path(home) / 'api-key.dpapi'
    if not path.exists():
        raise ImageError('missing_key', '尚未配置 API Key。请在本地运行 configure，或设置 CODEX_SMART_IMAGE_API_KEY。')
    try:
        return _crypt(path.read_bytes(), decrypt=True).decode('utf-8')
    except (OSError, UnicodeError):
        raise ImageError('credential_error', '凭据不可读，请在本地重新配置。') from None


def clear_key(home):
    (Path(home) / 'api-key.dpapi').unlink(missing_ok=True)
