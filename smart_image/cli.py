import argparse
import getpass
import json
import sys
from .client import ImageService
from .config import Settings, default_home
from .credentials import set_key, clear_key
from .errors import ImageError
from .server import config_status, serve


def main(argv=None):
    parser = argparse.ArgumentParser(description='Codex 智能生图：本地配置专用 GPT Image 2 服务')
    sub = parser.add_subparsers(dest='command', required=True)
    configure = sub.add_parser('configure', help='隐藏输入并加密保存 API Key')
    configure.add_argument('--base-url')
    configure.add_argument('--model')
    configure.add_argument('--timeout', type=float)
    configure.add_argument('--keep-key', action='store_true', help='只修改普通配置，保留已有 Key')
    for name in ['status','models','serve','clear-key']:
        sub.add_parser(name)
    generate = sub.add_parser('generate', help='生成一张图片；会调用付费服务')
    for name in ['prompt','output-dir','request-id']:
        generate.add_argument('--' + name, required=True)
    generate.add_argument('--size', default='auto')
    generate.add_argument('--quality', choices=['auto','low','medium','high'])
    args = parser.parse_args(argv)
    home = default_home()
    try:
        if args.command == 'serve':
            serve(home)
            return 0
        if args.command == 'configure':
            old = Settings.load(home)
            settings = Settings(base_url=args.base_url if args.base_url is not None else old.base_url,
                                model=args.model if args.model is not None else old.model,
                                timeout_seconds=args.timeout if args.timeout is not None else old.timeout_seconds)
            if not settings.base_url:
                raise ImageError('missing_endpoint', '首次配置请在本地提供 --base-url；发布包不包含任何个人服务地址。')
            if not args.keep_key:
                if not sys.stdin.isatty():
                    raise ImageError('interactive_required', '请在本地交互终端运行 configure 后隐藏输入 Key；自动化环境可设置 CODEX_SMART_IMAGE_API_KEY，普通配置使用 --keep-key。')
                key = getpass.getpass('API Key（隐藏输入）：')
                set_key(home, key)
            settings.save(home)
            value = config_status(home)
        elif args.command == 'status':
            value = config_status(home)
        elif args.command == 'clear-key':
            clear_key(home)
            value = {'stored_key_deleted':True,'note':'环境变量中的 Key 由用户自行清除。'}
        elif args.command == 'models':
            value = {'models':ImageService(Settings.load(home),home).models()}
        else:
            value = ImageService(Settings.load(home),home).generate(args.prompt,args.output_dir,args.request_id,args.size,args.quality)
        print(json.dumps(value,ensure_ascii=False,indent=2))
        return 0
    except ImageError as e:
        print(json.dumps(e.as_dict(),ensure_ascii=False),file=sys.stderr)
        return 1
    except (OSError, EOFError):
        print(json.dumps({'code':'local_error','message':'本地文件操作或输入失败，请检查路径权限。'},ensure_ascii=False),file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('操作已取消；已发送的生图请求可能仍在服务端进行。',file=sys.stderr)
        return 130
