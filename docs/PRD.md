# Codex Smart Image 0.1.1 产品说明

## 已确认范围

- Codex 根据任务判断位图素材需要，通过 Skill + MCP 调用用户配置的图像 API。
- OpenAI 兼容文字生图，模型 ID 可配置；一次一张，不自动换服务。
- 地址、Key、账户、本机路径属于用户本地配置，不进入公开仓库。
- Windows DPAPI 隐藏输入加密 Key，项目保存图片。
- 首版不包含图生图、独立 GUI、自动收费重试、云端部署。

## 架构及状态

Skill → stdio MCP → 配置/凭据 → HTTP → 图片结构检查 → 文件保存。工具为 get_image_config、list_image_models、generate_image。Python 3.11+ 标准库，无第三方运行依赖。

GET /models 只读列表。POST /images/generations 发送 model、prompt、n=1、size；quality 仅明确指定时发送。接受 data[0].b64_json 或 url。地址默认空，首次本地配置后才允许网络请求。

新请求先独占写 pending，然后发送一次 POST；成功记录图片摘要和路径。重复 ID/相同参数返回原结果，不同参数报冲突。中断、超时、下载失败、校验失败保留状态并禁止自动重发；服务可能已收费。不存在后台重启自动续传。

## 持久数据

普通配置位于本机 CodexSmartImage/config.json，schema=1；Key 独立加密。requests/ 保存 ID 摘要记录；图片由用户项目管理。CODEX_SMART_IMAGE_HOME 可隔离数据。未知配置 schema 报错，不覆盖。卸载保留配置、凭据、记录、图片。

## 工程默认及验收

超时默认 180 秒、响应上限 80 MiB、单图 50 MiB，均为工程默认而非服务商保证。远端 HTTPS；loopback HTTP 仅用于本地服务及测试；不携带 API Key 下载图片，拒绝重定向。

测试覆盖配置、DPAPI、本地 HTTP、文件校验、幂等/并发、MCP 子进程、CLI、隔离安装/更新/卸载及源码/Skill ZIP。公开发布额外检查源码、暂存内容、提交元数据和压缩包。真实服务的协议、模型及权限与桌面自动调用需要单独验收。
