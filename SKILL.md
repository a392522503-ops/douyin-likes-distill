---
name: douyin-likes-distill
description: Turn your Douyin/TikTok "liked" videos into a structured, searchable knowledge base. Harvests your likes list via CDP, transcribes audio with faster-whisper, rates and filters content by customizable focus tags (SEO/GEO/OPC/AI agents/lifestyle niches...), writes to a local JSONL knowledge index, and syncs curated batches to Tencent ima cloud knowledge base. 全程本地优先，零 API 费。
---

# douyin-likes-distill — 抖音点赞 → 知识库管线

把你在抖音刷到并点赞的视频，变成结构化、可检索、全 agent 共用的知识资产。

## 核心理念（QBS）

问题：刷到的干货视频点完赞就沉底，永远不会再被看到。
经典：个人知识管理（PKM）+ 竞品内容情报（Content Intelligence）。
Skill：本管线——点赞即收藏，收藏即蒸馏，蒸馏即入库，入库即可检索。
结果：你只需要照常刷抖音、照常点赞；知识库自己长大。

## 管线五层（每层可独立运行）

```
[L1 抓取]  likes_harvest.py   CDP 接管登录态 Chrome → 喜欢列表全量 → 详情 JSON
[L2 转写]  asr_distill.py     faster-whisper 逐视频转写原声（词级时间戳）
[L3 筛选]  rate_filter.py     按焦点标签评级（A 直接落地 / B 趋势 / C 储备 / D 归档）
[L4 入库]  kb_index.py        A/B 级追加本地 INDEX.jsonl（全 agent 可检索）
[L5 云同步] ima_upload.py     精选批次 → 腾讯 ima 云知识库（手机随时查）
```

## 快速开始

```bash
# 0. 前置（一次性）：Chrome 专用 profile 打开抖音并扫码登录
chrome --remote-debugging-port=9222 --user-data-dir=./_chrome_cdp https://www.douyin.com/

# 1. 抓取喜欢列表（断点续传，可反复跑）
python scripts/likes_harvest.py collect   # 收集全部视频 ID
python scripts/likes_harvest.py detail    # 逐条抓详情（文案/作者/数据）

# 2. 原声转写（可选：只想按文案筛选可跳过）
python scripts/asr_distill.py ./_out      # faster-whisper large-v3-turbo

# 3. 评级筛选（读取 config 里的焦点标签）
python scripts/rate_filter.py ./_out --focus "AI智能体,自媒体运营,GEO,SEO,OPC,社交,潮流文化"

# 4. 入本地知识库
python scripts/kb_index.py --index ./INDEX.jsonl --batch ./_out/batch.json

# 5. ima 云同步（在支持 ima-mcp 的宿主中）
#    步骤：MCP create_media 拿凭证 → scripts/ima_cos_upload.py 上传 → MCP add_knowledge
```

## 配置

复制 `config.example.json` 为 `config.json`：
- `focus_tags`：你的筛选焦点（任何领域都能用，不限于 AI/自媒体）
- `chrome_profile`：CDP profile 路径
- `ima_knowledge_base_id`：ima 目标库（可从 ima 客户端分享链接或 MCP 查询获得）
- `rate_prompt`：自定义评级标准（喂给本地 LLM 或主 agent）

## 焦点标签示例

| 领域 | focus_tags 示例 |
|---|---|
| AI/自媒体 | AI智能体, AI工作流, 自媒体运营, GEO, SEO, 一人公司, 变现 |
| 车改/手艺 | 汽车改装, 手艺人, 本地生意, 获客 |
| 母婴/教育 | 绘本, 亲子阅读, 儿童教育 |
| 任意领域 | 换成你的关键词即可 |

## 设计决策

- **CDP 接管而非模拟登录**：登录态由用户真实浏览器持有，脚本只读页面，风控友好
- **desc 优先、原声增强**：文案层（desc）足以完成 80% 筛选；原声转写只对 A 级候选做，省算力
- **断点续传**：每层产物落盘，任何一步失败重跑只补增量
- **双库架构**：本地 INDEX.jsonl（agent 检索/grep）+ ima 云库（手机随时问），纯文本 grep 路线已三次独立验证优于向量库
- **隐私红线**：生活娱乐类内容只归档不入库；私密信息（家庭/财务/账号）永不入库

## 已验证数据

- 27 条喜欢视频：抓取 27/27 成功（4 分钟）、筛选 A 级 12 条/B 级 7 条、入库+ima 同步全程零人工
- 原声转写：19 段 374 秒音频 65 秒完成（large-v3-turbo CPU int8）

## License

MIT
