---
name: smart-image
description: Use when a task benefits from new raster images, photos, illustrations, posters, backgrounds, website hero assets, or bitmap artwork, including implicit visual needs while building a webpage, slide, or document. Routes generation to the user's configured dedicated GPT Image 2 API. 不要求用户明确说“生成图片”；不用于流程图、数据图表、已有 SVG 编辑。
---

# 智能生图

用户为新位图指定了专用服务。需要生成位图时优先使用本插件的 smart_image MCP 工具，保留用户本轮明确指定的服务选择。

## 判断与调用

1. 若用户本轮明确指定其他服务，直接使用该服务的流程，跳过本插件配置检查。其余情况判断是否需要新位图：网页摄影主图、插画、海报、背景和纹理通常适合；流程图用 Mermaid，数据图用绘图工具，已有 SVG 直接改源文件。要求真实证据照片时用可核实素材，不生成替代证据。
2. 简要说明图片用途。调用 get_image_config；它只返回接口、模型和是否已配置凭据。若 ready=false、没有服务地址或 Key，告诉用户在本地运行 configure --base-url，继续可独立进行的工作。不要要求把 Key 发进聊天，不要静默切换内置生图服务。
3. 提示词包括主体、构图、风格、用途、比例、准确文字。一次一张，size 默认 auto；仅在需求和服务支持明确时指定尺寸或 quality。
4. 调用 generate_image，output_dir 使用当前项目内的绝对 images/ 或 assets/ 路径。每张逻辑图片创建唯一且稳定的 request_id（英文、数字、短横线或下划线）。同一请求中断或工具返回重复结果时保留同一个 ID。
5. 成功后检查本地图片，嵌入交付物或展示绝对路径。API 成功只代表生成文件，需要另行检查视觉质量。

## 错误与恢复

- 模型 ID 不兼容时调用 list_image_models，核对用户配置的 GPT Image 2 真实 ID；不要猜测并自动切换其他模型。
- timeout、network_error、request_unknown 或 uncertain=true：服务可能已收费。报告状态；停止自动 generate_image 调用，包括使用原 ID 的自动重试。只有用户明确要求新一次生成时创建新 ID。
- 恢复中断任务时从当前聊天中原 generate_image 调用找回 request_id、提示词和输出目录，不凭猜测创建新 ID；找不到原调用时先报告结果未知。服务端持久记录用于阻止原 ID 重发，不提供按提示词查找记录的工具。
- 原文件缺失或修改时不通过新请求自动补生。已有图片可继续复用。
- 用户要求新视觉版本时修改提示词，使用新 ID，说明这是新一次生成。

## 本地命令

插件根目录 scripts/run.py 提供 configure、status、models、generate、serve、clear-key。configure 在用户本地交互终端隐藏输入 Key；命令见插件 README.md。模型工具不接收密钥。此 Skill 支持自动发现，具体调用时机由 Codex 判断；也可显式使用 $smart-image。
