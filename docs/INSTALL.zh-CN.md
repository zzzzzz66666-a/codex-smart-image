# 智能生图插件安装指南（Windows）

适用 0.1.1。发布包不预填服务地址或密钥。

## 1. 准备

需要 Windows、Python 3.11+、Codex 桌面应用及支持 plugin 命令的 CLI。无 pip 依赖。打开 PowerShell 检查：

    codex --version
    codex plugin --help
    python --version

python 找不到时，安装器会尝试 Codex 自带 Python，也可传 -PythonPath。codex 找不到时，先让 CLI 在当前终端 PATH 可用。

## 2. 下载与解压

从本仓库 Releases 下载 codex-smart-image-0.1.1.zip 及同名 .sha256；也可使用 Code → Download ZIP。用 Get-FileHash 检查 ZIP 的 SHA256，与校验文件比较。

解压后进入含 README.md、smart_image、scripts 的目录，在该目录打开 PowerShell。

## 3. 安装到 Codex

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1

安装器复制运行文件至 %LOCALAPPDATA%\CodexSmartImage\marketplace，生成当前电脑的 Python/脚本绝对路径并注册插件。它会写当前用户 Codex 插件配置，不生成图片，也不自动配置 Key。

指定自己的 Python 可使用：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -PythonPath 'C:\Python312\python.exe'

示例路径请换成自己实际路径。-PrepareOnly 只准备文件，不注册插件。

## 4. 本地填写接口和 Key

使用安装器实际使用的 Python。Codex 常见自带位置：

    $imagePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    Test-Path -LiteralPath $imagePython

False 表示该路径不存在，请用自己 Python 的完整路径替换（可查看 (Get-Command python).Source）。

完成 Python 路径设置后，已有配置且无需更改时，跳到第 5 步，不覆盖配置或重新输入 Key。只修改服务地址或模型、保留已有 Key 时，在下面 configure 命令末尾增加 --keep-key。

服务地址和模型 ID 在自己电脑上输入：

    $imageApiBase = Read-Host '填写你自己的 API Base URL'
    $imageModelId = Read-Host '填写服务商给出的准确图像模型 ID'
    & $imagePython .\scripts\run.py configure --base-url $imageApiBase --model $imageModelId

随后提示 API Key，输入隐藏。不要将 Key 发到聊天、截图、代码或 issue。Windows DPAPI 为当前用户加密 Key；普通 config.json 不含 Key，但包含服务地址和模型 ID，因此也不要上传配置目录。

插件请求 POST /images/generations，接受 data[0].b64_json 或 data[0].url。Base URL 是服务商提供的兼容接口前缀，不是网页登录页，也不是完整 /images/generations 地址。准确模型 ID 以服务商实际提供的值为准。

## 5. 验证配置

    & $imagePython .\scripts\run.py status
    & $imagePython .\scripts\run.py models
    codex plugin list --json

status 的 provider_configured、key_configured、ready 都为 true，表示本地配置齐全，不代表远程调用已通过。status 会显示自己的服务地址，分享输出前遮盖。models 只读模型列表，不生图；401/403 核对 Key/权限，404 核对地址/协议。如果平台不支持模型列表，请向平台确认准确 ID。

## 6. 使用

安装后新开 Codex 聊天。插件或工具没有出现时先检查 plugin list，必要时重启 Codex。

可说：“使用 $smart-image 生成一张咖啡店网页主视觉。”也可让 Codex 制作需要摄影或插画的页面，它会根据任务判断是否选用。未自动触发时使用显式 Skill 名。

**生成图片可能收费。** 愿意发起真实生图后，可运行：

    $imageOutput = Join-Path (Get-Location) 'images'
    & $imagePython .\scripts\run.py generate --prompt '自然光下的一杯咖啡，简洁网站主视觉' --output-dir $imageOutput --request-id first-coffee-test

成功返回绝对路径，检查图片能打开及内容是否合适。相同 ID 与参数复用已有结果；超时、中断、未知状态或 uncertain=true 时停止所有自动重试，包括沿用相同 ID。先核对是否已生成或收费，不更换 ID 自动重发。

## 7. 更新和卸载

更新：解压新版，从新版目录重复运行 install.ps1，开新聊天。本地配置和图片保留。Python 路径变化后重新指定 -PythonPath 安装。

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\uninstall.ps1

卸载保留配置、加密 Key、请求记录、marketplace 文件和项目图片。删除本地加密 Key：

    & $imagePython .\scripts\run.py clear-key

若设置过 CODEX_SMART_IMAGE_API_KEY 环境变量，需自行清理。不要上传运行配置目录。

## 8. 验收边界

自动化验证包含加密、本地 HTTP、去重、下载、MCP 真子进程和隔离安装卸载。真实服务参数、模型权限、收费结果，以及桌面聊天自动调用，需要在自己环境验收。开发者可运行 python -m unittest discover -s tests -v。
