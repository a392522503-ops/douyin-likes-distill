# douyin-likes-distill 🔁

> **把抖音「点赞」变成知识资产。** 你照常刷视频、照常点赞；这条管线把你的喜欢列表自动抓取 → 原声转写 → 按焦点标签评级筛选 → 写入本地知识库 + 腾讯 ima 云知识库——全程零人工、零 API 费。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)]()
[![Powered by](https://img.shields.io/badge/powered%20by-faster--whisper%20%7C%20CDP%20%7C%20ima-green)]()

## 为什么

刷到的干货视频，点完赞就沉底了——三个月后再也找不到。
这条管线把「点赞」这个零成本动作，变成一条**全自动知识流水线**：

```
你点赞 → 抓取 → 原声转写 → 焦点标签评级 → 本地知识库 + ima 云库 → 随时检索/全 agent 共用
```

实测：27 条喜欢视频，抓取 4 分钟、筛选 1 分钟、入库 3 分钟，**人工介入 0 分钟**。

## 管线

```
L1 抓取    likes_harvest.py   CDP 接管你登录的 Chrome → 喜欢列表全量 + 逐条详情
L2 转写    asr_distill.py     faster-whisper 原声转写（词级时间戳）
L3 筛选    rate_filter.py     焦点标签 + 干货信号词 → A/B/C/D 评级
L4 入库    kb_index.py        追加本地 INDEX.jsonl（JSONL，grep 即检索）
L5 云同步  ima 三步流程        精选批次 → 腾讯 ima 知识库（手机随时问答）
```

## 快速开始

见 [SKILL.md](SKILL.md)（含完整参数说明与配置示例）。

```bash
git clone https://github.com/a392522503-ops/douyin-likes-distill.git
cd douyin-likes-distill
pip install faster-whisper websocket-client

# 一次性：专用 Chrome 登录抖音
chrome --remote-debugging-port=9222 --user-data-dir=./_chrome_cdp https://www.douyin.com/

# 每周跑（或挂 cron/计划任务）
python scripts/likes_harvest.py collect
python scripts/likes_harvest.py detail
python scripts/rate_filter.py ./_out --config config.json
python scripts/kb_index.py --batch batch.json --index INDEX.jsonl
```

## 设计原则

- **隐私**：生活娱乐内容只归档不入库；私密信息（家庭/财务/账号）永不入库
- **风控友好**：CDP 接管真实登录态、逐条限速、断点续传、验证码即停
- **零成本**：本地 faster-whisper 转写 + 规则筛选，不用任何付费 API
- **双库**：本地 JSONL（grep 即检索）+ ima 云库（手机问答），纯文本路线已三次独立验证优于向量库
- **通用**：focus_tags 任意领域可换——车改手艺、母婴绘本、健身饮食都行

## Roadmap

- [ ] GitHub Actions 定时运行示例
- [ ] 视频下载 + 场景画面抽取（LLM 视觉理解）
- [ ] 每周知识简报自动生成
- [ ] 更多平台（B站收藏/小红书收藏）

## 致谢

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [腾讯 ima](https://ima.qq.com) · [Agent Skills 规范](https://github.com/anthropics/skills)

## License

MIT
