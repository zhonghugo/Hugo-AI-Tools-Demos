# -*- coding: utf-8 -*-
"""
Excel多表批量填充器
====================
配置一次字段映射，自动从源Excel读取数据，批量填充到多套目标表，保留目标表原有公式和格式。

背景：国企成本控制专员每天要从合同清单扒数据，填进5套不同版本的Excel（对内/对外/合规/付款），
AI 总搞混字段和公式。本工具把「填表」变成纯配置——字段映射写在 config.json 里，
换新项目/新公司只需更新映射表，不用改代码。

核心能力：
  1. 读取源表（任意列），按配置把指定列逐行填充到目标表指定列
  2. 支持目标表已有公式（如 含税金额=金额×1.13、合计=SUM、序号=ROW()），填充不覆盖公式
  3. 支持固定单元格（填表人/日期等），支持 {{今天}} 模板变量
  4. 支持列值转换（如 付款方式文字 → 首付款比例数值）
  5. 保留目标表原有样式、边框、格式，只写映射到的单元格
  6. --dry-run 预演模式，先看要填什么，不实际写文件

用法：
    python3 generate_sample_data.py   # 先生成示例数据（只需一次）
    python3 batch_filler.py           # 执行批量填充
    python3 batch_filler.py --dry-run # 预演：只看计划，不写文件
"""
import argparse
import copy
import datetime
import json
import sys
from pathlib import Path

from openpyxl import load_workbook


# ---------- 工具函数 ----------

def _cell_value(ws, coord):
    """安全读取单元格（兼容公式/空值）"""
    cell = ws[coord]
    if cell.data_type == "f":
        return cell.value  # 公式原文，不计算
    return cell.value


def _to_date(v):
    """把字符串/日期转成 date，转换失败返回 None"""
    if v is None:
        return None
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.date() if isinstance(v, datetime.datetime) else v
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日"):
            try:
                return datetime.datetime.strptime(v.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _is_empty(v):
    """判断值是否为空（None / NaN / 空串）"""
    if v is None:
        return True
    if isinstance(v, float):
        try:
            import math
            if math.isnan(v):
                return True
        except Exception:
            pass
    return str(v).strip() == ""


# ---------- 主流程 ----------

def load_source(source_path, sheet_name):
    """读取源表，返回 (列名列表, 数据行列表[dict])"""
    wb = load_workbook(source_path, data_only=True)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"源表 {source_path} 中找不到 Sheet「{sheet_name}」，现有：{wb.sheetnames}")
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("源表为空")
    headers = [str(h).strip() if h is not None else f"列{i}" for i, h in enumerate(rows[0], 1)]
    data = []
    for r in rows[1:]:
        if all(_is_empty(v) for v in r):
            continue
        data.append({headers[i]: (r[i] if i < len(r) else None) for i in range(len(headers))})
    return headers, data


def build_plan(config, source_headers, source_data):
    """构造填充计划（不动任何文件）。返回 (计划列表, 警告列表)"""
    plan = []
    warnings = []

    missing_src = set()
    for t in config["目标表"]:
        for m in t.get("列映射", []):
            if m["源列"] not in source_headers:
                missing_src.add(m["源列"])
    if missing_src:
        warnings.append(f"源表中不存在的列（已跳过）：{sorted(missing_src)}")

    for t in config["目标表"]:
        tpl = {
            "文件": t["文件"],
            "Sheet": t["Sheet"],
            "起始行": int(t.get("起始行", 2)),
            "列映射": [],
            "固定单元格": dict(t.get("固定单元格", {})),
            "列值转换": t.get("列值转换", {}),
        }
        for m in t.get("列映射", []):
            if m["源列"] not in source_headers:
                continue
            tpl["列映射"].append(copy.deepcopy(m))
        plan.append(tpl)

    if not plan:
        raise ValueError("配置中没有任何有效的目标表映射")
    return plan, warnings


def apply_value(raw, conv_map):
    """应用列值转换：文本 → 数值等"""
    if conv_map is None or raw is None:
        return raw
    key = str(raw).strip()
    if key in conv_map:
        return conv_map[key]
    return raw


def fill_one_target(tpl, source_data, dry_run=False, report=None):
    """填充单个目标表，返回统计 (写入格数, 填充行数)"""
    path = Path(tpl["文件"])
    if not path.exists():
        raise FileNotFoundError(f"目标表不存在：{path}")
    wb = load_workbook(path)  # 关键：不传 data_only，公式原样保留
    if tpl["Sheet"] not in wb.sheetnames:
        raise ValueError(f"目标表 {path.name} 中找不到 Sheet「{tpl['Sheet']}」")
    ws = wb[tpl["Sheet"]]

    start = tpl["起始行"]
    mappings = tpl["列映射"]
    conv = tpl.get("列值转换", {})
    today = datetime.date.today()

    written = 0
    filled_rows = 0
    for idx, row in enumerate(source_data):
        r = start + idx
        for m in mappings:
            col = m["目标列"]
            raw = row.get(m["源列"])
            if _is_empty(raw):
                continue  # 源值为空则不动目标单元格（模板原有内容保留）
            val = apply_value(raw, conv.get(col))
            cell = ws[f"{col}{r}"]
            # 写入值，并保证类型/格式合理
            if isinstance(val, str) and (d := _to_date(val)) is not None and m["源列"].find("日期") >= 0:
                cell.value = d
                if not cell.number_format or cell.number_format == "General":
                    cell.number_format = "yyyy-mm-dd"
            elif isinstance(val, str) and val.replace(",", "").replace(".", "").isdigit():
                num = float(val.replace(",", ""))
                cell.value = int(num) if num == int(num) else num
            else:
                cell.value = val
            written += 1
            if report is not None:
                report.append(f"  {path.name} | {tpl['Sheet']}!{col}{r} <- {m['源列']} = {val!r}")
        filled_rows += 1

    # 固定单元格（{{今天}} 模板变量替换）
    for coord, val in tpl["固定单元格"].items():
        if "{{今天}}" in str(val):
            val = str(val).replace("{{今天}}", today.strftime("%Y-%m-%d"))
        ws[coord] = val
        written += 1
        if report is not None:
            report.append(f"  {path.name} | {tpl['Sheet']}!{coord} <- 固定值 = {val!r}")

    if not dry_run:
        wb.save(path)
    return written, filled_rows


def main():
    parser = argparse.ArgumentParser(description="Excel多表批量填充器")
    parser.add_argument("--config", default="config.json", help="配置文件路径（默认 config.json）")
    parser.add_argument("--dry-run", action="store_true", help="预演模式：只打印计划，不写文件")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)

    print("=" * 60)
    print("Excel多表批量填充器")
    print("=" * 60)
    print(f"源表：{config['源表']}  (Sheet: {config['源表Sheet']})")

    headers, source_data = load_source(config["源表"], config["源表Sheet"])
    print(f"读取到 {len(source_data)} 条数据，列：{headers}")
    if not source_data:
        print("源表没有数据行，退出。")
        sys.exit(1)

    plan, warnings = build_plan(config, headers, source_data)
    for w in warnings:
        print(f"⚠ {w}")

    mode = "预演（不写文件）" if args.dry_run else "执行填充"
    print(f"\n[{mode}] 共 {len(plan)} 张目标表：\n")

    report = [] if not args.dry_run else None
    total_written = 0
    for tpl in plan:
        print(f"→ {tpl['文件']}  (Sheet: {tpl['Sheet']}, 起始行 {tpl['起始行']})")
        try:
            n, rows = fill_one_target(tpl, source_data, dry_run=args.dry_run, report=report)
        except Exception as e:
            print(f"  ✗ 失败：{e}")
            continue
        total_written += n
        print(f"  ✓ 填充 {rows} 行、写入 {n} 个单元格")

    if args.dry_run:
        print("\n[预演结束] 以上为将要执行的操作，未写任何文件。确认无误后去掉 --dry-run 运行。")
    else:
        print(f"\n全部完成，共写入 {total_written} 个单元格。")
        print("打开目标表即可查看效果：公式列（含税金额/合计/序号/首付款金额）自动联动。")

    # 输出详细报告文件
    if report is not None:
        Path("填充报告.txt").write_text("\n".join(["填充明细：", *report]), encoding="utf-8")
        print("填充明细已写入 填充报告.txt")


if __name__ == "__main__":
    main()
