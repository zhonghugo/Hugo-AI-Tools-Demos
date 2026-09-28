#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地文档智能检索助手
=====================
解决问题：企业文档分散（制度/流程/产品手册/历史项目），找信息靠手动翻文档，
         AI代理每次都要重新读取文档上下文，浪费Token且容易遗漏。

功能：自动扫描文档文件夹→建立倒排索引→Web界面提问→返回相关段落（关键词高亮）

运行方式：
    python3 doc_search.py
    然后浏览器打开 http://localhost:8888

依赖：仅使用Python标准库，无需安装任何第三方包
"""

import os
import re
import json
import math
import html
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "docs_dir": "sample_docs",           # 文档文件夹路径
    "host": "0.0.0.0",                    # Web服务器地址
    "port": 8888,                          # Web服务器端口
    "supported_extensions": [".txt", ".md", ".csv"],  # 支持的文档格式
    "max_results": 10,                     # 最多返回结果数
    "context_chars": 200,                  # 结果上下文字符数
}

# ============================================================
# 第一部分：文档索引
# ============================================================

class DocumentIndex:
    """文档倒排索引：关键词 → 文档片段"""

    def __init__(self, docs_dir):
        self.docs_dir = Path(docs_dir)
        self.documents = []       # 文档列表 [{id, title, path, content, paragraphs}]
        self.inverted_index = {}  # 倒排索引 {word: [(doc_id, para_idx, count), ...]}
        self.doc_freq = {}        # 文档频率 {word: 包含该词的文档数}

    def scan_documents(self):
        """扫描文档文件夹，读取所有支持的文档"""
        if not self.docs_dir.exists():
            print(f"⚠️  文档文件夹不存在：{self.docs_dir}")
            return

        doc_id = 0
        for file_path in sorted(self.docs_dir.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in CONFIG["supported_extensions"]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # 按段落分割（空行分隔）
                    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
                    self.documents.append({
                        "id": doc_id,
                        "title": file_path.stem,
                        "path": str(file_path),
                        "content": content,
                        "paragraphs": paragraphs,
                        "word_count": len(content)
                    })
                    doc_id += 1
                    print(f"  📄 已索引：{file_path.name} ({len(paragraphs)}段, {len(content)}字)")
                except Exception as e:
                    print(f"  ⚠️  读取失败：{file_path.name} - {e}")

        print(f"✅ 共索引 {len(self.documents)} 个文档")

    def build_index(self):
        """构建倒排索引"""
        for doc in self.documents:
            doc_words = set()
            for para_idx, paragraph in enumerate(doc["paragraphs"]):
                words = self._tokenize(paragraph)
                word_count = {}
                for w in words:
                    word_count[w] = word_count.get(w, 0) + 1
                for word, count in word_count.items():
                    if word not in self.inverted_index:
                        self.inverted_index[word] = []
                    self.inverted_index[word].append((doc["id"], para_idx, count))
                    doc_words.add(word)
            for word in doc_words:
                self.doc_freq[word] = self.doc_freq.get(word, 0) + 1

        print(f"✅ 索引构建完成：{len(self.inverted_index)} 个关键词")

    def _tokenize(self, text):
        """简单分词：英文按空格，中文按单字+常见双字词"""
        text = text.lower()
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z][a-zA-Z0-9_]+', text)
        # 提取中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        # 中文双字词（滑动窗口）
        chinese_bigrams = []
        for i in range(len(chinese_chars) - 1):
            chinese_bigrams.append(chinese_chars[i] + chinese_chars[i + 1])

        return english_words + chinese_chars + chinese_bigrams

    def search(self, query, top_k=10):
        """
        搜索相关文档段落
        使用TF-IDF评分：词频 × 逆文档频率
        """
        query_words = self._tokenize(query)
        if not query_words:
            return []

        # 计算每个段落的得分
        paragraph_scores = {}  # (doc_id, para_idx) -> score

        for word in query_words:
            if word not in self.inverted_index:
                continue
            # IDF：逆文档频率
            idf = math.log(len(self.documents) / (self.doc_freq.get(word, 1) + 1)) + 1
            for doc_id, para_idx, tf in self.inverted_index[word]:
                key = (doc_id, para_idx)
                # TF-IDF 得分
                score = tf * idf
                paragraph_scores[key] = paragraph_scores.get(key, 0) + score

        # 按得分排序
        sorted_results = sorted(paragraph_scores.items(), key=lambda x: x[1], reverse=True)

        # 构造结果
        results = []
        for (doc_id, para_idx), score in sorted_results[:top_k]:
            doc = self.documents[doc_id]
            paragraph = doc["paragraphs"][para_idx]
            # 提取上下文（前后扩展）
            context = self._get_context(doc, para_idx)
            results.append({
                "doc_id": doc_id,
                "doc_title": doc["title"],
                "para_idx": para_idx,
                "score": round(score, 2),
                "paragraph": paragraph,
                "context": context,
                "matched_words": self._find_matched_words(query_words, paragraph)
            })

        return results

    def _get_context(self, doc, para_idx):
        """获取段落上下文（前一段+当前段+后一段）"""
        parts = []
        if para_idx > 0:
            parts.append(doc["paragraphs"][para_idx - 1][:100] + "...")
        parts.append(doc["paragraphs"][para_idx])
        if para_idx < len(doc["paragraphs"]) - 1:
            parts.append("..." + doc["paragraphs"][para_idx + 1][:100])
        return "\n\n".join(parts)

    def _find_matched_words(self, query_words, text):
        """找出文本中匹配的查询词（用于高亮）"""
        text_lower = text.lower()
        matched = set()
        for word in query_words:
            if word in text_lower and len(word) >= 2:
                matched.add(word)
        return list(matched)

    def get_stats(self):
        """获取索引统计信息"""
        total_paragraphs = sum(len(d["paragraphs"]) for d in self.documents)
        total_words = sum(d["word_count"] for d in self.documents)
        return {
            "doc_count": len(self.documents),
            "paragraph_count": total_paragraphs,
            "word_count": total_words,
            "index_size": len(self.inverted_index),
            "documents": [{"title": d["title"], "paragraphs": len(d["paragraphs"]), "words": d["word_count"]} for d in self.documents]
        }


# ============================================================
# 第二部分：Web界面
# ============================================================

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>本地文档智能检索助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f7fa; color: #333; }
        .container { max-width: 900px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 30px 0; }
        .header h1 { font-size: 28px; color: #2c3e50; margin-bottom: 8px; }
        .header p { color: #7f8c8d; font-size: 14px; }
        .search-box { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 20px; }
        .search-input { width: 100%; padding: 14px 18px; font-size: 16px; border: 2px solid #e0e6ed; border-radius: 8px; outline: none; transition: border-color 0.3s; }
        .search-input:focus { border-color: #3498db; }
        .search-btn { width: 100%; margin-top: 12px; padding: 12px; font-size: 16px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer; transition: background 0.3s; }
        .search-btn:hover { background: #2980b9; }
        .stats { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat-card { flex: 1; min-width: 120px; background: white; border-radius: 8px; padding: 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
        .stat-card .num { font-size: 24px; font-weight: bold; color: #3498db; }
        .stat-card .label { font-size: 12px; color: #95a5a6; margin-top: 4px; }
        .results { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
        .result-header { font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #ecf0f1; }
        .result-item { padding: 16px; border-bottom: 1px solid #f0f3f5; }
        .result-item:last-child { border-bottom: none; }
        .result-title { font-size: 15px; font-weight: bold; color: #2980b9; margin-bottom: 6px; }
        .result-score { font-size: 12px; color: #95a5a6; margin-left: 8px; }
        .result-content { font-size: 14px; line-height: 1.7; color: #555; white-space: pre-wrap; }
        .highlight { background: #fff3cd; padding: 1px 3px; border-radius: 3px; font-weight: bold; }
        .no-result { text-align: center; padding: 40px; color: #95a5a6; }
        .doc-list { margin-top: 12px; font-size: 13px; color: #7f8c8d; }
        .doc-list li { margin: 4px 0; list-style: none; }
        .doc-list li::before { content: "📄 "; }
        .footer { text-align: center; padding: 20px; color: #bdc3c7; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 本地文档智能检索助手</h1>
            <p>企业文档智能检索 · 无需联网 · 数据不出本地</p>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card"><div class="num" id="docCount">-</div><div class="label">文档数</div></div>
            <div class="stat-card"><div class="num" id="paraCount">-</div><div class="label">段落数</div></div>
            <div class="stat-card"><div class="num" id="wordCount">-</div><div class="label">总字数</div></div>
            <div class="stat-card"><div class="num" id="indexSize">-</div><div class="label">索引词数</div></div>
        </div>

        <div class="search-box">
            <input type="text" class="search-input" id="query" placeholder="输入问题，例如：报销流程是什么？产品定价策略？" onkeypress="if(event.key==='Enter')search()">
            <button class="search-btn" onclick="search()">🔍 搜索</button>
        </div>

        <div class="results" id="results" style="display:none;">
            <div class="result-header" id="resultHeader"></div>
            <div id="resultList"></div>
        </div>

        <div class="footer">
            本地文档智能检索助手 · 基于TF-IDF算法 · 仅使用Python标准库
        </div>
    </div>

    <script>
        // 页面加载时获取统计信息
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('docCount').textContent = data.doc_count;
                document.getElementById('paraCount').textContent = data.paragraph_count;
                document.getElementById('wordCount').textContent = data.word_count.toLocaleString();
                document.getElementById('indexSize').textContent = data.index_size.toLocaleString();
            });

        function search() {
            const query = document.getElementById('query').value.trim();
            if (!query) return;

            document.getElementById('results').style.display = 'block';
            document.getElementById('resultHeader').textContent = '搜索中...';
            document.getElementById('resultList').innerHTML = '';

            fetch('/api/search?q=' + encodeURIComponent(query))
                .then(r => r.json())
                .then(data => {
                    document.getElementById('resultHeader').textContent = `找到 ${data.results.length} 个相关段落（查询："${query}"）`;
                    if (data.results.length === 0) {
                        document.getElementById('resultList').innerHTML = '<div class="no-result">😔 未找到相关内容，试试其他关键词</div>';
                        return;
                    }
                    let html = '';
                    data.results.forEach((item, i) => {
                        let content = item.context;
                        // 高亮匹配词
                        item.matched_words.forEach(word => {
                            const regex = new RegExp('(' + word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
                            content = content.replace(regex, '<span class="highlight">$1</span>');
                        });
                        html += `
                            <div class="result-item">
                                <div class="result-title">${i+1}. ${item.doc_title} <span class="result-score">相关度: ${item.score}</span></div>
                                <div class="result-content">${content}</div>
                            </div>
                        `;
                    });
                    document.getElementById('resultList').innerHTML = html;
                });
        }
    </script>
</body>
</html>"""


class SearchHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(INDEX_HTML)
        elif parsed.path == "/api/stats":
            self._send_json(self.server.index.get_stats())
        elif parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            results = self.server.index.search(query, top_k=CONFIG["max_results"])
            self._send_json({"query": query, "results": results})
        else:
            self._send_error(404, "Not Found")

    def _send_html(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _send_json(self, data):
        content = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format, *args):
        """简化日志输出"""
        print(f"  🌐 {args[0]}")


# ============================================================
# 第三部分：主函数
# ============================================================

def main():
    print("=" * 60)
    print("  🔍 本地文档智能检索助手")
    print("=" * 60)
    print()

    # 1. 初始化索引
    docs_dir = Path(CONFIG["docs_dir"])
    if not docs_dir.exists():
        print(f"⚠️  文档文件夹不存在，正在创建：{docs_dir}")
        docs_dir.mkdir(parents=True, exist_ok=True)
        print("   请将文档（.txt/.md/.csv）放入该文件夹后重新运行")

    index = DocumentIndex(docs_dir)
    print("📂 正在扫描文档...")
    index.scan_documents()

    if len(index.documents) == 0:
        print("\n⚠️  没有找到可索引的文档")
        print("   请将 .txt / .md / .csv 文件放入 sample_docs/ 文件夹")
        print("   然后重新运行本脚本")
        return

    print("\n🔧 正在构建索引...")
    index.build_index()

    # 2. 启动Web服务器
    print()
    print("🌐 启动Web服务器...")
    server = HTTPServer((CONFIG["host"], CONFIG["port"]), SearchHandler)
    server.index = index

    print()
    print("=" * 60)
    print(f"  ✅ 服务已启动！")
    print(f"  📍 访问地址：http://localhost:{CONFIG['port']}")
    print(f"  📂 文档目录：{docs_dir.absolute()}")
    print(f"  📊 已索引：{len(index.documents)}个文档, {len(index.inverted_index)}个关键词")
    print("=" * 60)
    print()
    print("  💡 使用方法：")
    print("     1. 浏览器打开上面的地址")
    print("     2. 在搜索框输入问题（如：报销流程是什么？）")
    print("     3. 点击搜索，查看相关文档段落")
    print("     4. 添加新文档：放入 sample_docs/ 文件夹，重启脚本")
    print()
    print("  ⏹️  按 Ctrl+C 停止服务")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  👋 服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
