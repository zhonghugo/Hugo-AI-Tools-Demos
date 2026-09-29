# HANDOFF — 项目交接说明（给接任 AI）

> 2026-09-29 由 neat-freak 同步后整理。接任 AI 先读本文件 + `CLAUDE.md` + `README.md` 再动手。
> 本文件只写「交接时点的事实与下一步」，日常约定在 CLAUDE.md，对外展示在 README.md。

## 1. 项目是什么

用户（钟镇洪，深圳，求职方向：**流程自动化 / RPA+AI 落地 / 数字化运营**，11 年美餐网业务+数据+财务信息化背景，待业求职中）维护的每日工作流：

**AI 工具资讯采集（8:30）→ 挑 1 条做可运行小工具 Demo（10:30）→ 作品集/台账沉淀 → 推 GitHub（当日自动）**，同时 10:00 推送求职岗位。

所有产物都在本项目目录（资讯会话 38441325557356290）：
- `daily_news_MMDD.json` — 每日资讯快照
- `demos/YYYY-MM-DD_工具名/` — 每日 Demo（单文件 HTML 为主）
- `demos/作品集总览/` — 对外作品集 HTML + 台账（本地 xlsx 镜像 + 在线飞书表）
- `CLAUDE.md` / `README.md` / `HANDOFF.md` — 本文件

## 2. 三条工作流与关键 ID

| 任务（系统标题） | cron_job_id | 时间 | 常用叫法 | 产出 |
|---|---|---|---|---|
| AI工具资讯日报 | 11879732282882 | 8:30 | **AI小工具资讯整理** | 资讯飞书多维表格 + daily_news_*.json |
| 每日岗位机会推送 | 11890800693762 | 10:00 | **岗位搜索 / 岗位推送** | 岗位多维表格 + 飞书群摘要 |
| AI小工具Demo每日生成 | 12342894883074 | 10:30 | **AI小工具demo** | demo 目录 + 作品集/台账更新 + 推 GitHub |
| 领取zcode免费token（一次性，9/30 跑完即止） | 12251204140546 | 9/30 三次 | — | — |

> 日常循环任务只有 3 个（前 3 行）；zcode 是 9/30 当天的 rrule 一次性任务，跑完自动结束。

- 资讯表：base_token=`S3WFbZfNTaMPn6sjgfkcFG3Cn8g` / table_id=`tbltCHyotV8hdemf`（表「AI工具资讯」）
- 岗位表：base_token=`MwbkbeUnbaTmyYsNjojcJqWQnPf` / table_id=`tblYoQXSsCLYQr2W`（表「岗位机会」）
- 台账在线表：https://fes49z7yv9.feishu.cn/sheets/YBJosw8PZhFKkutoXPxca5RTnIe （sheet-id `0eshJB`，当前 15 行）
- GitHub 公开仓库：`zhonghugo/Hugo-AI-Tools-Demos`（origin 已配 https 免密，gh 已登录 zhonghugo）

## 3. Demo 生成与交付约定（重点）

1. **选材**：当天资讯 推荐指数≥4星（优先5星）→ VibeCoding 机会描述具体 → 类型优先级 Excel/数据处理 > 简单网页 > 自动化脚本 > 复杂系统 → 契合 RPA/数据/财务背景
2. **形式**：**单文件自包含 HTML**（内联 CSS/JS、无外部依赖、file:// 可跑、示例数据固化进 JS）——用户明确要求 HTML 便于转发；复杂脚本型才用 Python
3. **配置端用业务表单，不用 JSON 编辑器**（用户明确要求）
4. **命名**：`demos/YYYY-MM-DD_工具名/*_网页版.html`；交付后回填作品集 DEMOS 数组（按日期倒序插入）+ 台账加一行（在线表 + 本地 xlsx 镜像同步）
5. **验证**：html skill `shot.py`（当前环境可用）+ Playwright 端到端断言（`executable_path="/opt/vm/preinstall/ms-playwright/chromium-1169/chrome-linux/chrome"`）：交互闭环、下载回读、移动端 390px、无 console error
6. **台账更新后跑** `lark_sheet_selfcheck.py` 自检（带回执，`--confirm "@./文件"` 传 6 条结论；第 2 条须含「在线表且拿不到源文件」等豁免词否则判不合格）
7. **交付**：一律 `present_files`；每次改动后重新交付，不复用旧卡片

## 4. 每日收尾清单（接任 AI 每日必做）

- [ ] 10:30 Demo 任务：选材 → 生成 → 验证 → present_files 交付
- [ ] 更新作品集 HTML（stat 数量 + 新条目）
- [ ] 更新台账：在线飞书表（+dim-insert 插行 + cells-set 写值 + 改标题/说明行）→ 本地 xlsx 镜像同步 → selfcheck
- [ ] README.md 一览表加一行
- [ ] `git add -A && git commit -m "M/D 工具名 demo" && git push origin main`（push 失败先 `git pull --rebase`）
- [ ] 交付说明附 GitHub 链接 https://github.com/zhonghugo/Hugo-AI-Tools-Demos

## 5. 已知坑（遇到直接照做）

- **资讯表当天可能 0 条**（日报写表疑似失败，如 9/29）：先查表再查 `daily_news_MMDD.json`，有数据用本地 json 兜底，不强行生成
- **9/22 无资讯入库**（未产出 demo）；**9/16、9/17 无 demo 目录**（历史遗留，用户未要求补）
- jsDelivr 偶发 ERR_TUNNEL_CONNECTION_FAILED → 页面自带 cdnjs 兜底
- Chrome 拦截多文件连续下载 → 用单文件下载按钮
- 台账「状态/链接」列序易错：状态 H 列、链接 I 列，写入前核对
- lark-cli base record-list 默认 100 条，资讯量超一页用 `--offset/--limit` 翻页
- `lark-cli` 的大 JSON 输出会落盘调试文件：**根目录 `sheets/` 等调试产物不入库**（.gitignore 已配 `/sheets/`、`_shots/`、`*.tmp` 等），发现即删

## 6. 用户偏好与红线（系统层已持久化，此处提醒）

- 岗位推送：渠道加**脉脉**；方向加 **AI运营** 岗位
- 生成的图片下载后不带水印
- 复杂问题用 **tracer bullet**（纵向切最窄路径先打通，再扩展）
- 求职排除：以财务专业知识为核心的岗位（财务信息化经理/财务数字化项目经理等）、纯流程管理岗、猎头代招岗、纯英文岗
- **每日 demo 完成后自动推送 GitHub**
- **小红书自动化搜索是硬红线**：账号已因自动化被处罚（2026-09-15 起流量受限），彻底停止 RedNote-MCP 自动化搜索；用户手动分享链接时可用 getNoteContent 单条获取

## 7. 交接时点状态（2026-09-29）

- 台账：15 个 demo（9/14–9/29，缺 9/22；9/16、9/17 无目录），在线表与本地 xlsx 已同步，selfcheck CHECK_OK
- 作品集 HTML：stat=15、9/14–9/29、含 9/29 条目
- GitHub：HEAD=`6b41c64`（9/29 AI目标驱动工作流 demo），首次合集 commit `29c9eeb`（77 文件）
- 待办：9/30 的 zcode 一次性领取任务会自动跑；Demo 任务 10/30 继续每天执行
