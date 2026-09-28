# Excel日报自动化生成器

## 解决什么问题

每天重复做Excel日报：清洗数据 → 计算指标 → 做图 → 输出，步骤固定但繁琐。
本工具让你**配置一次**，以后每天只需放入新数据，一键生成完整日报。

## 快速开始

```bash
# 1. 生成示例数据（首次使用）
python3 create_sample_data.py

# 2. 运行日报生成器
python3 daily_report_generator.py

# 3. 查看生成的日报
# 打开 daily_report.xlsx
```

## 文件说明

| 文件 | 说明 |
|---|---|
| `daily_report_generator.py` | 主程序，读取配置+数据，自动生成日报 |
| `config.json` | 配置文件，定义清洗规则、指标、分组、图表 |
| `create_sample_data.py` | 生成示例数据（50条模拟销售数据） |
| `sample_data.xlsx` | 示例输入数据（运行create_sample_data.py后生成） |
| `daily_report.xlsx` | 生成的日报输出（运行主程序后生成） |

## 如何配置自己的日报

编辑 `config.json`：

### 1. 文件路径
```json
{
  "input_file": "你的数据.xlsx",
  "output_file": "输出日报.xlsx",
  "sheet_name": "Sheet1"
}
```

### 2. 数据清洗规则
```json
"cleaning": {
  "drop_duplicates": true,        // 是否去重
  "fillna": {"销售额": 0},         // 空值填充
  "date_column": "日期",            // 日期列名（自动格式化）
  "date_format": "%Y-%m-%d"
}
```

### 3. 计算指标
支持的公式：`sum`（求和）、`count`（计数）、`mean`（均值）、`max`（最大）、`min`（最小）
```json
"metrics": [
  {"name": "总销售额", "formula": "sum", "column": "销售额"},
  {"name": "订单数", "formula": "count", "column": "订单号"}
]
```

### 4. 分组和图表
```json
"group_by": "产品类别",    // 按哪个维度分组
"charts": [
  {"type": "bar", "title": "各类别销售额", "x": "产品类别", "y": "销售额"}
]
```

## 命令行参数

```bash
# 使用自定义配置文件
python3 daily_report_generator.py --config my_config.json

# 临时指定输入输出文件（不修改config.json）
python3 daily_report_generator.py --input 今日数据.xlsx --output 今日日报.xlsx
```

## 生成的日报包含什么

| Sheet | 内容 |
|---|---|
| 日报概览 | 标题 + 所有指标汇总（美化格式） |
| 清洗后数据 | 去重、空值填充、日期格式化后的完整数据 |
| 分组指标 | 按维度分组的指标数据 + 柱状图/折线图 |

## 依赖

- Python 3.8+
- pandas
- openpyxl

安装依赖：`pip install pandas openpyxl`

## 扩展方向

- 增加更多图表类型（饼图、散点图）
- 支持多Sheet数据合并
- 增加邮件自动发送功能
- 增加定时任务（每天自动运行）
- 支持自定义Excel模板
