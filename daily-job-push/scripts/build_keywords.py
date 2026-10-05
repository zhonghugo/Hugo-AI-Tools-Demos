#!/usr/bin/env python3
"""由求职画像生成搜索关键词列表（城市 × 方向）。

用法:
    python3 build_keywords.py <profile.json>
    python3 build_keywords.py <profile.json> --limit 20

profile.json 结构（与 references/profile-template.md 一致）:
{
  "city": "深圳",
  "directions": ["RPA/流程自动化实施", "数字化运营"],
  "keyword_templates": ["{city} {direction}", "{city} {direction} 招聘"]
}

- directions 缺失时使用内置默认方向集（RPA/流程自动化/数字化运营/AI落地等）
- keyword_templates 缺失时使用默认模板
- 输出：每行一个关键词
"""
import argparse
import json
import sys

DEFAULT_DIRECTIONS = [
    "RPA实施工程师", "RPA开发", "流程自动化", "低代码自动化",
    "数字化运营", "数据运营", "业务数字化", "业务中台", "数字化转型顾问",
    "AI落地", "AI Agent自动化", "AI应用实施",
    "AI运营", "AI产品运营", "AI应用运营", "AIGC运营",
    "AI工具落地", "AI Agent运营", "大模型应用运营",
    "AI变革", "AI变革经理", "AI转型", "AI转型顾问", "企业AI转型", "智能化转型",
    "数据体系", "数据看板", "餐饮连锁数字化",
]

DEFAULT_TEMPLATES = [
    "{city} {direction}",
    "{city} {direction} 招聘",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", help="profile.json 路径")
    parser.add_argument("--limit", type=int, default=30, help="最多输出关键词数")
    args = parser.parse_args()

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)

    city = profile.get("city", "深圳")
    directions = profile.get("directions") or DEFAULT_DIRECTIONS
    templates = profile.get("keyword_templates") or DEFAULT_TEMPLATES

    keywords = []
    for d in directions:
        for t in templates:
            try:
                k = t.format(city=city, direction=d).strip()
            except (KeyError, IndexError):
                continue
            if k and k not in keywords:
                keywords.append(k)

    if not keywords:
        keywords.append(f"{city} 数字化运营")

    for k in keywords[: args.limit]:
        print(k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
