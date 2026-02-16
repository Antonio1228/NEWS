import csv
import os
import re
import time
from pathlib import Path
from datetime import datetime, timezone

from openai import OpenAI

SITE_TITLE = "CS + Productivity Lab"
SITE_DESC = "Practical guides, comparisons, and checklists for students and builders."
OUT_DIR = Path("docs/p")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")  # 你也可改成 gpt-4o 等
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def quality_gate(text: str) -> bool:
    """
    防止大量低品質頁面：
    - 長度要夠
    - 要有 checklist / table / FAQ 結構
    - 不能一直重複、不能像模板硬套
    """
    t = text.lower()
    if len(text) < 1200:
        return False
    must_have = ["checklist", "<table", "faq", "when to choose", "trade-off"]
    if sum(1 for m in must_have if m in t) < 3:
        return False
    # 粗略重複檢測：同一句出現太多次
    lines = [clean(x) for x in re.split(r"[.\n]", text) if clean(x)]
    if len(lines) > 0:
        top = max(lines.count(x) for x in set(lines))
        if top >= 5:
            return False
    return True


def render_page(slug: str, query: str, persona: str, body_html: str) -> str:
    canonical = f"/p/{slug}.html"
    published = now_iso()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{query} | {SITE_TITLE}</title>
  <meta name="description" content="{clean(query)} — decision checklist, trade-offs, and FAQs."/>
  <link rel="canonical" href="{canonical}"/>
  <meta name="robots" content="index,follow"/>
  <style>
    body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;max-width:920px;margin:32px auto;padding:0 16px;line-height:1.6}}
    header{{margin-bottom:24px}}
    nav a{{margin-right:12px}}
    .badge{{display:inline-block;padding:2px 10px;border:1px solid #ddd;border-radius:999px;font-size:12px}}
    table{{border-collapse:collapse;width:100%;margin:16px 0}}
    th,td{{border:1px solid #ddd;padding:10px;vertical-align:top}}
    h1{{line-height:1.2}}
    .muted{{color:#666}}
    .box{{border:1px solid #e5e5e5;border-radius:12px;padding:14px;margin:16px 0}}
    footer{{margin-top:40px;font-size:14px;color:#666}}
  </style>
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"Article",
    "headline":{query!r},
    "datePublished":{published!r},
    "dateModified":{published!r},
    "author":{{"@type":"Organization","name":{SITE_TITLE!r}}},
    "mainEntityOfPage":{canonical!r}
  }}
  </script>
</head>
<body>
<header>
  <div class="badge">Auto-generated • Quality-gated</div>
  <h1>{query}</h1>
  <p class="muted">{SITE_DESC}</p>
  <nav>
    <a href="/index.html">Home</a>
    <a href="/sitemap.xml">Sitemap</a>
  </nav>
</header>

{body_html}

<footer>
  <p>Generated: {published} (UTC). Content is generated to help users; it does not copy news articles or reproduce copyrighted text.</p>
</footer>
</body>
</html>
"""


def build_prompt(query: str, persona: str) -> str:
    # 讓每篇有「決策工具」而不是廢話，降低被判定為 scaled content abuse 的風險
    return f"""
You are writing a helpful, original, human-readable web page for the query:
{query}

Target persona: {persona}

Rules:
- Do NOT rewrite or quote news articles or other websites.
- Provide actionable, specific guidance that stands on its own.
- Use clear section headings.
- Must include:
  1) "Quick answer" (2-4 bullet points)
  2) A decision checklist titled "Checklist"
  3) A trade-off table in HTML (<table>...</table>) comparing 2-4 options
  4) A section "When to choose X" (at least 3 scenarios)
  5) "FAQ" with at least 5 Q&As
- Avoid exact prices and time-sensitive claims. If needed, say "check official pricing".
- Output ONLY valid HTML fragments for inside <body> (no <html>, no <head>).

Now write the page.
""".strip()


def generate_body_html(query: str, persona: str) -> str:
    prompt = build_prompt(query, persona)
    resp = client.responses.create(
        model=MODEL,
        input=prompt,
        # 盡量穩定一點
        temperature=0.6,
    )
    return resp.output_text or ""


def main():
    in_csv = Path("data/topics.csv")
    if not in_csv.exists():
        raise SystemExit("Missing data/topics.csv")

    rows = []
    with in_csv.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            slug = clean(r["slug"])
            query = clean(r["query"])
            persona = clean(r.get("persona", "general reader"))
            if slug and query:
                rows.append((slug, query, persona))

    published = 0
    skipped = 0
    for slug, query, persona in rows:
        out = OUT_DIR / f"{slug}.html"
        if out.exists():
            continue  # 已生成就不重做（想重做你再刪檔或改邏輯）

        body = generate_body_html(query, persona)
        if not quality_gate(body):
            skipped += 1
            continue

        html = render_page(slug, query, persona, body)
        out.write_text(html, encoding="utf-8")
        published += 1
        time.sleep(1.2)  # 避免打太快

    print(f"Published: {published}, Skipped (quality): {skipped}")


if __name__ == "__main__":
    main()
