# 多维表格字段规范（「岗位机会」表）

飞书多维表格操作前先读 lark-base skill，按其规范调用 lark-cli。

## 建表

- 表名：`岗位机会`
- 无指定位置时建在云空间根目录；用户指定文件夹则建在对应文件夹
- 已有表格时直接复用，不重建

## 字段规范

| 字段名 | 类型 | 说明 |
|---|---|---|
| 岗位名称 | 文本 | 主字段，必填 |
| 公司名称 | 文本 | 必填 |
| 薪资范围 | 文本 | 如「25-35K·14薪」，无则留空 |
| 工作地点 | 文本 | 必填 |
| 岗位要点 | 文本 | 2-4 句职责要点 |
| 匹配理由 | 文本 | 与画像的交叉点（方向/行业/技能/成果），1-2 句具体表述 |
| 招聘链接 | 文本(URL) | 格式 `[查看岗位](url)`，url 必须为岗位明细页（见 platform-rules.md） |
| 来源平台 | 单选 | 选项：BOSS直聘/猎聘/智联招聘/前程无忧/公司官网/鱼泡直聘/脉脉（实际表内还含：全职招聘网/企查查/自媒体/转载聚合；严禁拉勾网，已关停） |
| 发布日期 | 日期时间 | `YYYY-MM-DD HH:mm:ss`，填收录当天 |
| 状态 | 单选 | 默认「待投递」；不合适/已投递/面试中/已放弃 |
| 备注 | 文本 | 排除原因、跟进备注等 |

## lark-cli 常用命令

```bash
# 导出全部已有记录（用于去重与回读验证）
lark-cli base +record-list --base-token <base_token> --table-id <table_id> --format ndjson --output <file>

# 批量写入新记录（每批 ≤200 条，串行执行；--json 支持 @file 读文件）
lark-cli base +record-batch-create --base-token <base_token> --table-id <table_id> --json @jobs_YYYY-MM-DD.json

# 回读验证：同上 record-list 导出后核对数量与字段
```

注意：导出的 ndjson 顶层是 manifest（含 `record_file` 指向实际记录文件），记录本体在 manifest 的 `record_file` 指向的 `tblYoQXSsCLYQr2W_<ts>.ndjson` 中，解析时直接读该文件。

## 去重键

- 主键：`岗位名称 + 公司名称`（规范化后比对）
- 次键：招聘链接（同一岗位不同来源链接可合并为一条）
- 用 `scripts/dedup_keys.py` 从导出 ndjson 提取主键，新岗位写入前比对

## 数量口径

- 每日收录默认 10-20 条（画像 daily_target 可调）
- 搜索结果少时至少写入 3 条高匹配岗位
- 宁缺毋滥：不写入明显不相关、无明细页链接、已失效的岗位
