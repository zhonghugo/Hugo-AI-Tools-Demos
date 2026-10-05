# daily-job-push（每日岗位机会推送）

一个可复用的 AI Agent Skill：按求职者画像，每天自动搜索招聘岗位，经筛选、去重后写入飞书多维表格，并可推送当日摘要。

## 功能

- 按求职画像（方向/城市/薪资/排除项）参数化搜索与筛选，画像模板见 `references/profile-template.md`
- 多平台渠道：BOSS直聘、猎聘、智联招聘、前程无忧、脉脉、公司官网，内置各平台明细页链接规则与岗位有效性校验（`references/platform-rules.md`）
- 自动去重、写入飞书多维表格、回读验证（`references/table-schema.md`）
- 可选：创建每日定时任务，定时推送当日摘要

## 安装

将本目录整体放入 Agent 的 skills 目录（例如 `.user_skills/daily-job-push/`），保持目录结构完整，即完成安装。

## 使用

对 Agent 说"帮我推岗位""每日岗位推送""今日有什么合适岗位"，并提供求职画像（求职方向、城市、薪资区间、排除项）。未提供画像时，Agent 会按 `references/profile-template.md` 引导填写。

需要每天自动推送时，加一句"每天推送"即可创建每日定时任务（默认每日 10:00）。

## 目录结构

```
daily-job-push/
├── SKILL.md                        # 主流程（解析画像→搜索→筛选→去重→写入→推送）
├── references/
│   ├── profile-template.md         # 求职画像字段说明、JSON 模板、完整示例
│   ├── platform-rules.md           # 允许/禁用平台、明细页 URL 规则、有效性检查、历史踩坑
│   ├── maimai-api.md               # 脉脉可选 API 通道（job_search 端点、详情页构造、合规）
│   └── table-schema.md             # 多维表格字段规范、去重键、lark-cli 读写命令
└── scripts/
    ├── build_keywords.py           # 由画像生成搜索关键词列表
    └── dedup_keys.py               # 从导出记录提取去重键、检查链接明细页特征
```

## 依赖

- 运行环境：具备 `general_search` 搜索能力与 `lark-cli`（飞书多维表格/IM）能力的 AI Agent
- 目标平台：飞书多维表格（写入岗位记录）+ 飞书 IM（推送摘要）
- 可选：`doubao-cron-scheduler`（创建每日定时任务）

## License

MIT
