---
name: codex-smart-image-install
description: Use when installing, configuring, verifying, upgrading, or uninstalling the Codex Smart Image plugin from its source or release ZIP on Windows. For setup and maintenance, not ordinary image generation.
---

# 安装 Codex 智能生图

适用 0.1.1。目标包根目录同时包含 scripts/install.ps1、scripts/run.py 和 .codex-plugin/plugin.json。用户指定目录优先；本文件单独提供时先找到对应源码或发布包。此 Skill 不是插件运行代码。

## 检查与安装

读取包中 docs/INSTALL.zh-CN.md 和安装脚本。只读确认 Windows、Python 3.11+、codex --version、codex plugin --help。找不到 Python 时检查安装器支持的 Codex 自带路径或用户已有 Python，不额外安装 pip 依赖。

用户已要求安装时执行必要安装；没有授权则只检查并说明将改变的插件配置。遵守当前沙箱，不绕过审批。配置、环境变量、日志和生成的绝对路径清单不能上传。

在包根目录执行（路径使用真实 python.exe，去掉尖括号）：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -PythonPath <实际python.exe>

可不传 -PythonPath，由安装器解析。-PrepareOnly 只准备文件。安装器生成绝对路径 MCP 清单，然后注册 smart-image@smart-image-local；不要直接注册源码的相对路径 .mcp.json，不修改 Codex 程序。

## 私有配置

发布包没有预填服务地址。用户在自己的交互终端运行 configure --base-url <本地输入> --model <准确ID>，Key 由 getpass 隐藏输入后 DPAPI 加密。不要让用户把 Key 发到聊天，不把 Key 写入命令参数、脚本、普通 JSON、MCP 或 shell 历史。缺地址时让用户本地输入，不猜测或搜索其他聊天。不能安全完成交互输入时，给用户命令并标明待办，继续无需凭据的检查。

已有配置不覆盖或清空。普通配置修改使用 --keep-key。服务地址和模型 ID 同样按私有本地配置处理。status 会显示地址；公开报告只汇报 ready/provider_configured/key_configured，省略实际地址。

## 验证、更新和卸载

运行 codex plugin list --json、run.py status；用户配置后运行 run.py models，只读模型列表。本地 ready、模型查询、真实生图、聊天自动调用分别验收，不相互替代。

真实生图可能收费；仅在用户明确要求测试或任务本身需要图片时生成。使用项目内绝对 output_dir、稳定 request_id。unknown、超时、中断或 uncertain=true 停止自动调用，不改 ID 重发。检查图片可打开及视觉质量，不用模拟结果冒充真实验收。

安装后新开 Codex 聊天；工具未出现时按指南检查或重启，用显式 $smart-image 验证。更新在新版目录重复安装。卸载用 scripts/uninstall.ps1，默认保留用户配置和图片；clear-key 需用户明确要求删除 Key。

汇报包版本、安装结果、配置状态、实际验证与待办；不回显服务地址或凭据。
