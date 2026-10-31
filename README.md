# Codex Smart Image 智能生图插件

让 Codex 判断任务何时需要照片、插画、海报或背景，通过用户本地配置的图像 API 生成并保存到项目。支持自动发现，也可显式使用 $smart-image。

**公开版本不包含任何用户服务地址、账户或 API Key。** 兼容 POST /images/generations，可配置模型 ID，默认 gpt-image-2。

当前版本 0.1.2：正式包含交互配置、显式更换 Key 和本地重置入口。已有 Key 默认保留，只有 -ReplaceKey 才进入隐藏输入；重置必须显式指定 -ConfirmReset。

## 安装

详见 [中文安装指南](docs/INSTALL.zh-CN.md)。交给其他 AI 安装，使用 [安装 Skill](installer-skill/codex-smart-image-install/SKILL.md)。

需要 Windows、Python 3.11+ 和支持 plugin 命令的 Codex，无 pip 依赖。解压发布包，在项目根目录 PowerShell 执行：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1

然后在包根目录运行：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\configure.ps1

按提示填写服务地址、模型 ID，再在隐藏输入处粘贴 Key。更换 Key 在命令末尾增加 -ReplaceKey。安装、配置和模型列表查询不发起图片生成。

## 功能

- 自动配图判断的 Skill 与 stdio MCP：配置状态、模型列表、文字生图。
- Windows 当前用户 DPAPI 加密 Key，图片保存至项目目录。
- base64、直接或签名图片 URL，下载不携带 API Key。
- 稳定 request_id 去重；未知结果不自动重发收费请求。
- 原生 Codex 插件安装、更新、卸载，源码包及独立安装 Skill 包。
- 配置入口可从解压包或安装目录运行，兼容空格/单引号路径；重置保留插件和项目图片。

流程图、数据图表、已有 SVG 编辑使用对应工具。首版没有图生图或独立 GUI。不会静默切换到其他图像服务。

## 开发

    python -m unittest discover -s tests -v
    python .\scripts\build_release.py
    python .\scripts\check_release_privacy.py .

DPAPI 测试需要正常 Windows 用户环境；Codex 集成测试需要 CLI，只使用临时隔离配置。HTTP 测试连接本地替身，不验证任何用户真实服务。

[需求](docs/PRD.md)、[计划](docs/DEVELOPMENT_PLAN.md)、[测试记录](docs/VALIDATION.md)、[发布流程](docs/RELEASING.md)。可复用开发 Skill 及相关参考资料位于 development-skill/。

## 隐私与限制

配置和加密凭据保存在本机 %LOCALAPPDATA%\CodexSmartImage；不应上传该目录、.env、请求记录、日志和生成图片。安装时生成的绝对路径 MCP 清单只保留在安装机器。

发布采用文件白名单和压缩包内部扫描；可用仅本地 denylist 补充私有域名和个人标识。真实服务兼容性、准确模型 ID、权限及聊天自动调用需要用户本地验收。自动选择是模型判断，不能保证所有措辞都触发。
