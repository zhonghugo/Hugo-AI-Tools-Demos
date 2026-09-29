# CLAUDE.md — AI 小工具每日工作流（豆包办公会话）

> 本文件供下次会话的 AI 阅读：项目约定、硬边界、已知坑。变更日志不进本文件（归 daily_news_*.json 与飞书台账）。

## 项目定位

用户（钟镇洪，求职方向：流程自动化/RPA+AI落地/数字化运营，11 年美餐网业务+数据+财务信息化背景）维护的**每日 AI 工具资讯 → 小工具 Demo → 求职岗位推送**工作流。核心产出是 demos/ 下的可运行小工具作品集，作为求职筹码。Demo 在「AI小工具demo」会话（conversation_id=38441779771447554）生成，产物同步到本项目 demos/ 目录。

## 目录结构

- `daily_news_MMDD.json` — 每日资讯快照（8:30 定时任务落盘，如 daily_news_0929.json，缺 9/22）
- `demos/YYYY-MM-DD_工具名/` — 每个 demo 一个目录，产物以单文件 HTML 为主（`*_网页版.html` 或 `*.html`）
- `demos/作品集总览/` — `AI小工具Demo作品集_总览.html`（对外展示页，DEMOS 数组按日期倒序）+ `AI小工具Demo台账.xlsx`（本地备份）

## 定时任务（Asia/Shanghai）

| 任务 | cron_job_id | 时间 | 运行环境 | 作用 |
|---|---|---|---|---|
| AI工具资讯日报 | 11879732282882 | 8:30 每天 | 云电脑 | 搜 GitHub/PH/HN/Reddit 资讯写入飞书多维表格，落盘 daily_news_*.json |
| 每日岗位机会推送 | 11890800693762 | 10:00 每天 | 云电脑 | 按求职画像搜深圳岗位→去重→写多维表格→飞书群推送摘要 |
| AI小工具Demo每日生成 | 12342894883074 | 10:30 每天 | 云电脑 | 从当天资讯挑 1 条做可运行 demo，在「AI小工具demo」会话生成 |
| 领取zcode免费token | 12251204140546 | 9/30 8:30/9:30/10:30（3次） | 本地电脑 | rrule 一次性任务，领取 zcode 免费 token |

> 旧 Demo 任务（11901402403074）已于 9/27 删除，新任务 12342894883074 于 9/28 重建。

## 资讯与产出数据源

- 资讯飞书多维表格：base_token=`S3WFbZfNTaMPn6sjgfkcFG3Cn8g`，table_id=`tbltCHyotV8hdemf`（表名「AI工具资讯」）
- 岗位多维表格：base_token=`MwbkbeUnbaTmyYsNjojcJqWQnPf`，table_id=`tblYoQXSsCLYQr2W`（表名「岗位机会」）
- Demo 台账（飞书表格）：https://fes49z7yv9.feishu.cn/sheets/YBJosw8PZhFKkutoXPxca5RTnIe （当前 15 行；状态/链接在第 H/I 列）
- lark-cli base 输出为管道表格文本，直接 grep/wc 处理；record-list 默认 100 条，翻页用 `--offset/--limit`（9/26 起资讯量超过一页）

## Demo 生成规则（继承定时任务 query，最新为准）

1. 选材：当天资讯里 推荐指数≥4星（优先5星）→ VibeCoding机会描述具体 → 类型优先级 Excel/数据处理 > 简单网页 > 自动化脚本 > 复杂系统 → 契合 RPA/数据/财务背景
2. 形式：**单文件自包含 HTML（内联 CSS/JS，无外部依赖，file:// 可跑，示例数据固化进 JS）**——用户明确要求 HTML 形式方便分享；复杂脚本型才用 Python
3. 业务端优先：配置端用业务表单，不用 JSON 编辑器（用户明确要求）
4. 命名：`demos/YYYY-MM-DD_工具名/*_网页版.html`，交付后把 aka 链接回填作品集 DEMOS 数组并更新台账（加一行）

## 验证与交付（必做，踩过坑）

- 交付前用 **Playwright** 端到端断言（html skill 的 shot.py 当前环境可用，路径 `/home/user/.doubao/agent_mode/workspace/.skills/html/scripts/shot.py`）：
  `executable_path="/opt/vm/preinstall/ms-playwright/chromium-1169/chrome-linux/chrome"`（默认 headless shell 不存在）
  断言：交互闭环（点击→状态变化）、CSV/下载回读、移动端 390px 视口、无 console error
- 产物一律 `present_files` 交付；搜索/抓取返回的 URL 不作为交付物
- 台账表更新后跑 `lark_sheet_selfcheck.py` 自检（带回执）再交付
- 每轮改了作品集/台账/demo，全部重新 present_files，不得复用旧卡片

## 已知坑（下次遇到直接照做）

- **时序问题**：10:30 跑时当天资讯可能未入库 → 先查资讯表当天记录 + daily_news 文件，有数据则手动补做 demo
- **9/22 无资讯入库**（未产出 demo）；**9/16、9/17 无 demo 目录**（历史遗留，用户未要求补）
- **9/29 资讯表当天 0 条**（日报任务 8:30 报成功但写多维表格疑似失败）→ 用 `daily_news_0929.json` 兜底选材完成 demo；遇到表空先查当日 daily_news 文件
- jsDelivr 偶发 ERR_TUNNEL_CONNECTION_FAILED：页面自带 cdnjs 兜底
- Chrome 拦截多文件连续下载 → 单文件下载按钮
- 痛点雷达曾修「按提及排序无效」bug（下拉 value=mentions 但字段是 m，加 keyMap）
- 台账本地 xlsx 是中间产物，在线飞书表才是交付物；生成时「状态/链接」列序易错，写入前核对 H/I 列
- lark-cli base record-list 默认 100 条，资讯量超过一页时用 `--offset/--limit` 翻页

## 用户偏好（系统层已持久化，此处仅提醒）

- 岗位推送渠道加**脉脉**；方向加 **AI运营** 岗位
- 生成的图片下载后不带水印
- 解决复杂问题用 **tracer bullet**：纵向切割打通最窄路径再扩展，不按层横向做
- 求职排除：以财务专业知识为核心的岗位、纯流程管理岗、猎头代招岗、纯英文岗
- **每日 demo 完成后自动推送到 GitHub 公开仓库 `zhonghugo/Hugo-AI-Tools-Demos`**
- Demo 在「AI小工具demo」会话（conversation_id=38441779771447554）生成，本会话只做资讯搜索

## 小红书（硬红线）

用户小红书账号因自动化搜索被平台处罚（2026-09-15 起流量受限）。**彻底停止 RedNote-MCP 小红书自动化搜索**，不尝试任何模拟浏览；用户手动分享链接时可用 getNoteContent 单条获取。
