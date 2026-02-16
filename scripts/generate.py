"""
Auto SEO Article Generator
Uses OpenAI to generate HTML articles from topics.csv
"""

import csv
import os
import time
from pathlib import Path
from openai import OpenAI

# ====== 設定 ======
DOCS_DIR = Path("docs")
POSTS_DIR = DOCS_DIR / "p"
TOPIC_FILE = Path("data/topics.csv")

POSTS_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ====== Prompt 生成 ======
def build_prompt(query: str, persona: str) -> str:
    """
    建立 AI 文章 Prompt
    """
    return f"""
Write a helpful web page for:

{query}

Target reader:
{persona}

Make the tone and examples suitable for this type of reader.

Output ONLY HTML inside body.

Structure:

<div class="card">
<h2>Quick Answer</h2>
<ul class="checklist">
<li>...</li>
</ul>
</div>

<div class="card">
<h2>Checklist</h2>
<ul class="checklist">
<li>...</li>
</ul>
</div>

<div class="card">
<h2>Comparison</h2>
<table>
<tr><th>Option</th><th>Pros</th><th>Cons</th></tr>
<tr><td>...</td><td>...</td><td>...</td></tr>
</table>
</div>

<div class="card">
<h2>When to Choose</h2>
<ul>
<li>...</li>
</ul>
</div>

<h2>FAQ</h2>

<div class="faq-item">
<div class="faq-question">Question?</div>
<div class="faq-answer">Answer</div>
</div>

Avoid fluff. Be practical.
"""


# ====== HTML 包裝 ======
def render_page(slug: str, query: str, content: str) -> str:
    """
    包裝成完整 HTML（含 canonical URL）
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{query}</title>

<link rel="canonical" href="/p/{slug}.html">
<link rel="stylesheet" href="/style.css">

</head>
<body>

<h1>{query}</h1>

{content}

</body>
</html>
"""


# ====== AI 生成 ======
def generate_html(query: str, persona: str) -> str:
    """
    呼叫 OpenAI API 生成 HTML 內容
    """
    prompt = build_prompt(query, persona)

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text


# ====== 主程式 ======
def main():
    """
    讀取 topics.csv 並生成 HTML 頁面
    """
    with TOPIC_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            slug = row["slug"].strip()
            query = row["query"].strip()
            persona = row["persona"].strip()

            file_path = POSTS_DIR / f"{slug}.html"

            # 已存在就跳過
            if file_path.exists():
                continue

            print(f"Generating: {slug}")

            html_body = generate_html(query, persona)
            full_html = render_page(slug, query, html_body)

            file_path.write_text(full_html, encoding="utf-8")

            time.sleep(2)


if __name__ == "__main__":
    main()
