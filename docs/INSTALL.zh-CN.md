# 智能生图插件安装指南（Windows）

适用 0.1.2。发布包不预填私人服务地址或密钥。

## 1. 准备与下载

需要 Windows、Python 3.11+、Codex 桌面应用及支持 plugin 命令的 CLI，无 pip 依赖。在 PowerShell 检查 codex --version、codex plugin --help。安装器优先尝试 Codex 自带 Python，也可用 -PythonPath 指定已有 Python。

从本仓库 Releases 下载 codex-smart-image-0.1.2.zip 和同名 .sha256，用 Get-FileHash 核对 SHA256。解压后进入含 README.md、smart_image、scripts 的目录，在该目录打开 PowerShell。

## 2. 安装与更新

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1

安装器将运行文件、文档和配置/清理脚本复制到 %LOCALAPPDATA%\CodexSmartImage\marketplace，并注册 smart-image@smart-image-local。生成的绝对路径清单只属于当前电脑，不上传。安装不配置 Key、不生成图片。更新从新版解压目录重复安装，已有配置、Key、记录和图片保留。

指定 Python 示例（换成自己的实际路径）：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -PythonPath 'C:\Python312\python.exe'

-PrepareOnly 只准备文件，不注册插件。codex 找不到时先使 CLI 在当前终端 PATH 可用。

## 3. 本地配置

在包根目录运行：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\configure.ps1

依次输入：

1. API Base URL：兼容接口前缀，通常以 /v1 结尾；不要填网页登录页或完整 /images/generations 地址。已有值时回车保留。
2. Model ID：服务商提供的准确模型 ID；回车保留已有值或默认 gpt-image-2。
3. 首次配置在 API Key（隐藏输入）提示处粘贴 Key 一次并回车。无文字、星号或光标反馈正常。

Windows Terminal 可用 Ctrl+Shift+V、Shift+Insert 或右键粘贴。不要反复粘贴；输错可取消后重开。Key 由 Windows 当前用户 DPAPI 加密，不进入普通 JSON、命令参数、聊天或截图。服务地址和模型 ID 也属于本地配置，不上传配置目录。

已有 Key 默认保留，不再出现可见的“输入 replace 或 Key”选项。更换 Key 要显式运行：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\configure.ps1 -ReplaceKey

只在随后真正的隐藏 Key 提示处粘贴新 Key。曝光的 Key 需在服务商后台撤销并重新生成；清本地数据不会使服务商凭据失效。

如果通过 CODEX_SMART_IMAGE_API_KEY 环境变量提供 Key，该值优先于加密本地文件。更换曝光的环境变量 Key 时，先在自己的终端和保存它的环境变量设置中移除或更新，再重新打开终端；-ReplaceKey 检测到当前环境 Key 时会在修改配置前停止，避免新旧 Key 混用。

-CheckOnly 只检查入口启动，不提示输入或改配置。-PythonPath 指定实际 Python。入口从自身位置定位代码，实际使用相对路径启动，兼容空格/单引号路径，不依赖以前终端中的变量。

## 4. 验证

provider_configured、key_configured、ready 都为 True 只表示本地配置完整，不代表真实 API 请求通过。配置入口仅显示这三个状态，不回显地址或 Key。

手工检查时使用安装时的 Python（按实际路径调整第一行），在包根目录执行：

    $imagePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    & $imagePython .\scripts\run.py status
    & $imagePython .\scripts\run.py models
    codex plugin list --json

status 包含自己的地址，分享前遮盖。models 只查询模型列表，不生图。401/403 核对 Key/权限，404 核对地址/协议；平台不支持列表时向服务商确认模型 ID。插件使用 POST /images/generations，接受 data[0].b64_json 或 data[0].url，参数须与自己的服务兼容。

## 5. 使用

安装后新开 Codex 聊天，必要时重启。可以说：“使用 $smart-image 生成一张咖啡店网页主视觉。”需要照片/插画的任务也可自动选用；未触发时显式指定 Skill。

真实生图可能收费，需任务授权。同一逻辑请求使用稳定 request_id。超时、中断、未知结果或 uncertain=true 时停止所有自动重试，包括同 ID；不换 ID 自动重发。成功后检查图片能打开、内容合适。

## 6. 清理旧记录并重新配置

仅在明确需要清理时使用，安装和更新不需要重置。不带确认只预览：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\reset.ps1

确认清理并接着在同一终端重新配置：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\reset.ps1 -ConfirmReset -Reconfigure

删除旧配置、加密 Key、requests、logs、相关配置/Key 备份和写入临时文件，保留插件和项目图片。删除记录会失去历史去重保护，不能用它来重发结果未知的收费请求。重定向目录和过宽根目录会被拦截，检查在删除前完成。

使用 CODEX_SMART_IMAGE_API_KEY 环境变量时，先在自己的终端/环境变量设置中清理；脚本不擅改系统环境，检测到当前环境 Key 会在删文件前停止。聊天、终端滚动内容、服务商后台记录和凭据撤销不由本地重置处理。

## 7. 卸载与安装目录入口

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\uninstall.ps1

卸载保留配置、Key、记录、marketplace 和项目图片。配置、清理和卸载脚本也在安装目录，解压包被移动后，可从 %LOCALAPPDATA%\CodexSmartImage\marketplace\plugin 打开 PowerShell，使用相同相对命令。

## 8. 验收边界

自动化检查使用临时隔离配置、本地 HTTP 和真实 MCP 子进程，覆盖安装、升级、卸载、配置交互、显式清理和打包。真实服务兼容性、模型权限、收费结果和聊天自动调用需在自己的环境另行验收。
