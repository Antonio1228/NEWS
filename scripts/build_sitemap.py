from pathlib import Path
from datetime import datetime

DOCS = Path("docs")
PAGES = DOCS / "p"


def main():
    urls = []

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # 加入首頁
    urls.append(f"""
<url>
  <loc>/index.html</loc>
  <lastmod>{today}</lastmod>
</url>
""")

    # 加入所有文章頁
    for file in PAGES.glob("*.html"):
        slug = file.name
        urls.append(f"""
<url>
  <loc>/p/{slug}</loc>
  <lastmod>{today}</lastmod>
</url>
""")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>
"""

    (DOCS / "sitemap.xml").write_text(sitemap, encoding="utf-8")


if __name__ == "__main__":
    main()
