# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "beautifulsoup4",
#     "markdownify",
# ]
# ///
"""
Scrape the Windows Restart Manager documentation from Microsoft Learn
and save as local, searchable Markdown files.

Usage:
    uv run scripts/scrape_rstmgr_docs.py

Output goes to docs/rstmgr/
"""

import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

# ── Configuration ────────────────────────────────────────────────────────────

BASE = "https://learn.microsoft.com"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "rstmgr"

# Seed URLs – the three entry points + the header reference page
SEED_URLS = [
    "/en-us/windows/win32/api/_rstmgr/",
    "/en-us/windows/win32/rstmgr/restart-manager-portal",
    "/en-us/windows/win32/rstmgr/functions",
    "/en-us/windows/win32/api/restartmanager/",
]

# URL prefixes we consider "in scope" for crawling
SCOPE_PREFIXES = [
    "/en-us/windows/win32/api/restartmanager/",
    "/en-us/windows/win32/api/_rstmgr/",
    "/en-us/windows/win32/rstmgr/",
]

REQUEST_DELAY = 0.6  # seconds between requests (be polite)
REQUEST_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

# ── Helpers ──────────────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})


def is_in_scope(path: str) -> bool:
    """Check whether a URL path belongs to the Restart Manager docs."""
    return any(path.startswith(prefix) for prefix in SCOPE_PREFIXES)


def normalise_path(path: str) -> str:
    """Strip fragment and query, ensure no trailing slash (except root)."""
    path = urlparse(path).path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return path


def path_to_filename(url_path: str) -> str:
    """
    Convert a URL path to a safe, readable filename.
    e.g. /en-us/windows/win32/api/restartmanager/nf-restartmanager-rmstartsession
         -> api_restartmanager_nf-restartmanager-rmstartsession.md
    """
    # Strip the common prefix
    for prefix in [
        "/en-us/windows/win32/api/",
        "/en-us/windows/win32/",
    ]:
        if url_path.startswith(prefix):
            remainder = url_path[len(prefix):]
            break
    else:
        remainder = url_path.lstrip("/").replace("/", "_")

    # Replace slashes with underscores
    name = remainder.replace("/", "_").strip("_")
    if not name:
        name = "index"
    return name + ".md"


def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a page and return parsed soup, or None on failure."""
    full = url if url.startswith("http") else BASE + url
    try:
        resp = session.get(full, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as exc:
        print(f"  ⚠ Failed to fetch {full}: {exc}")
        return None


def extract_main_content(soup: BeautifulSoup) -> Tag | None:
    """Return the <main> content element from a MS Learn page."""
    # MS Learn puts the article content in <main id="main">
    main = soup.find("main", id="main")
    if main:
        return main
    # Fallback: look for the article element
    article = soup.find("div", class_="content")
    return article


def extract_title(soup: BeautifulSoup) -> str:
    """Extract the page title."""
    title_tag = soup.find("h1")
    if title_tag:
        return title_tag.get_text(strip=True)
    meta = soup.find("meta", {"property": "og:title"})
    if meta:
        return meta.get("content", "Untitled")
    return "Untitled"


def discover_links(soup: BeautifulSoup, current_path: str) -> set[str]:
    """Find all in-scope links on a page."""
    found: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Resolve relative URLs
        resolved = urljoin(BASE + current_path, href)
        parsed = urlparse(resolved)
        # Only keep learn.microsoft.com links
        if parsed.hostname and "learn.microsoft.com" not in parsed.hostname:
            continue
        norm = normalise_path(parsed.path)
        if is_in_scope(norm):
            found.add(norm)
    return found


def html_to_markdown(element: Tag, page_url: str) -> str:
    """Convert an HTML element to clean Markdown."""
    # Remove nav, footer, feedback sections, cookie banners
    for sel in [
        "nav", "footer", ".feedback-section", ".alert",
        "#ms-cookie-banner", ".page-actions", ".contributors-section",
        ".metadata", ".breadcrumb", "#affixed-right-container",
        ".binary-rating-holder",
    ]:
        for tag in element.select(sel):
            tag.decompose()

    # Remove unwanted tags before conversion
    for tag in element.find_all(["img", "script", "style", "svg"]):
        tag.decompose()

    raw_md = md(
        str(element),
        heading_style="ATX",
        code_language_callback=lambda el: _guess_lang(el),
    )

    # Clean up excessive blank lines
    raw_md = re.sub(r"\n{4,}", "\n\n\n", raw_md)
    # Clean up trailing whitespace
    lines = [line.rstrip() for line in raw_md.splitlines()]
    return "\n".join(lines).strip() + "\n"


def _guess_lang(el) -> str:
    """Guess language for code blocks from MS Learn CSS classes."""
    classes = el.get("class", []) if hasattr(el, "get") else []
    for cls in classes:
        if "lang-cpp" in cls or "language-cpp" in cls:
            return "cpp"
        if "lang-c" in cls or "language-c" in cls:
            return "c"
    # Default for restartmanager.h content
    return "cpp"


def build_frontmatter(title: str, url_path: str) -> str:
    """Build YAML front matter for the markdown file."""
    full_url = BASE + url_path
    return (
        f"---\n"
        f"title: \"{title}\"\n"
        f"source: \"{full_url}\"\n"
        f"---\n\n"
    )


# ── Main crawl logic ────────────────────────────────────────────────────────

def crawl():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Queue: paths to visit;  visited: paths already done
    queue: list[str] = [normalise_path(u) for u in SEED_URLS]
    visited: set[str] = set()
    saved_files: list[str] = []

    print(f"🔍 Starting crawl — output → {OUTPUT_DIR}\n")

    while queue:
        path = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)

        filename = path_to_filename(path)
        out_path = OUTPUT_DIR / filename

        print(f"📄 [{len(visited):>3}] {path}")
        print(f"       → {filename}")

        soup = fetch_page(path)
        if soup is None:
            continue

        title = extract_title(soup)
        content_el = extract_main_content(soup)

        if content_el is None:
            print("       ⚠ No main content found, skipping")
            continue

        # Discover new links before we strip the HTML
        new_links = discover_links(soup, path)
        for link in sorted(new_links):
            if link not in visited:
                queue.append(link)

        # Convert to markdown
        body_md = html_to_markdown(content_el, path)
        full_md = build_frontmatter(title, path) + body_md

        out_path.write_text(full_md, encoding="utf-8")
        saved_files.append(filename)
        print(f"       ✓ saved ({len(body_md):,} chars)")

        time.sleep(REQUEST_DELAY)

    # Write an index file
    index_path = OUTPUT_DIR / "_index.md"
    index_lines = [
        "# Restart Manager — Local Documentation Index\n",
        f"Scraped {len(saved_files)} pages from Microsoft Learn.\n\n",
    ]
    for f in sorted(saved_files):
        name = f.removesuffix(".md").replace("_", " / ")
        index_lines.append(f"- [{name}]({f})\n")
    index_path.write_text("".join(index_lines), encoding="utf-8")

    print(f"\n✅ Done! {len(saved_files)} pages saved to {OUTPUT_DIR}")
    print(f"   Index: {index_path}")


if __name__ == "__main__":
    crawl()
