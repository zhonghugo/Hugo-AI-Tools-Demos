#!/usr/bin/env python3
"""从 lark-cli 导出的 ndjson 记录中提取去重键，并可检查招聘链接的明细页特征。

用法:
    python3 dedup_keys.py <records.ndjson>                 # 每行: 去重键\t链接
    python3 dedup_keys.py <records.ndjson> --keys-out keys.txt   # 额外输出去重键集合
    python3 dedup_keys.py <records.ndjson> --link-check    # 追加链接特征检查 OK/CHECK

字段名自动适配中英文常见命名：岗位名称/岗位/name/title，公司名称/公司/company，
招聘链接/链接/url/link。链接支持 [查看岗位](url) markdown 形式。
"""
import argparse
import json
import re
import sys

URL_FEATURES = {
    "liepin": re.compile(r"/job/\d+\.shtml|/a/\d+\.shtml"),
    "zhipin": re.compile(r"job_detail"),
    "maimai": re.compile(r"/web/job/|/web/feed/detail\?fid="),
    "zhaopin": re.compile(r"zhaopin\.com"),
    "51job": re.compile(r"51job\.com"),
}

FIELD_CANDIDATES = {
    "name": ["岗位名称", "岗位", "name", "job_title", "title"],
    "company": ["公司名称", "公司", "company", "company_name"],
    "url": ["招聘链接", "链接", "url", "link", "job_url"],
}


def find_field(record, candidates):
    for c in candidates:
        if c in record and record[c]:
            v = record[c]
            return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return ""


def norm(s):
    return re.sub(r"\s+", "", s or "").lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ndjson", help="lark-cli 导出的记录文件")
    parser.add_argument("--keys-out", help="额外输出去重键集合到文件")
    parser.add_argument("--link-check", action="store_true", help="检查链接明细页特征")
    args = parser.parse_args()

    keys = []
    with open(args.ndjson, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            name = norm(find_field(rec, FIELD_CANDIDATES["name"]))
            company = norm(find_field(rec, FIELD_CANDIDATES["company"]))
            url = find_field(rec, FIELD_CANDIDATES["url"])

            # 提取 markdown 链接
            m = re.search(r"\]\((https?://[^)\s]+)\)", url)
            if m:
                url = m.group(1)

            key = f"{name}|{company}"
            keys.append(key)

            out = f"{key}\t{url}"
            if args.link_check and url:
                ok = any(p.search(url) for p in URL_FEATURES.values())
                out += "\t" + ("OK" if ok else "CHECK")
            print(out)

    if args.keys_out:
        with open(args.keys_out, "w", encoding="utf-8") as f:
            for k in sorted(set(keys)):
                f.write(k + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
