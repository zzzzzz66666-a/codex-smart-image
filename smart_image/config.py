from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from .errors import ImageError
from .storage import atomic_json


def default_home():
    override = os.environ.get('CODEX_SMART_IMAGE_HOME')
    if override:
        return Path(override).expanduser().resolve()
    return Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share')) / 'CodexSmartImage'


def validate_url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        raise ImageError('invalid_url', '接口 URL 格式无效。')
    try:
        u = urlsplit(value)
        _ = u.port
    except ValueError:
        raise ImageError('invalid_url', '接口 URL 格式无效。') from None
    loopback = u.hostname in ('127.0.0.1', 'localhost', '::1')
    if (not u.hostname or u.username is not None or u.password is not None or u.query or u.fragment
            or (u.scheme != 'https' and not (loopback and u.scheme == 'http'))):
        raise ImageError('invalid_url', '远程接口必须使用 HTTPS，且 URL 不能包含凭据、查询串或片段。')
    return value.rstrip('/')


@dataclass
class Settings:
    base_url: str = ''
    model: str = 'gpt-image-2'
    timeout_seconds: float = 180
    schema_version: int = 1

    def __post_init__(self):
        if self.base_url != '':
            self.base_url = validate_url(self.base_url)
        if not isinstance(self.model, str) or not self.model.strip() or len(self.model) > 200:
            raise ImageError('invalid_model', '模型 ID 不能为空或超过 200 字符。')
        if (isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, (int, float))
                or not 1 <= self.timeout_seconds <= 1800):
            raise ImageError('invalid_timeout', '超时必须在 1 到 1800 秒之间。')
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ImageError('config_version', '不支持该配置版本；请保留原文件并检查插件版本。')

    @classmethod
    def load(cls, home):
        path = Path(home) / 'config.json'
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError()
            return cls(**data)
        except (ValueError, TypeError, OSError):
            raise ImageError('config_invalid', '配置文件无法读取或包含未知字段；请检查 config.json。') from None

    def save(self, home):
        atomic_json(Path(home) / 'config.json', asdict(self))
