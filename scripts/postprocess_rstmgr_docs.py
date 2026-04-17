# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Post-process scraped Restart Manager docs:
  1. Strip MS Learn UI boilerplate (nav junk, feedback sections, etc.)
  2. Rewrite links to point to local .md files where possible
  3. Generate a structured entrypoint (index.md)
  4. Ensure consistent formatting across all files

Usage:
    uv run scripts/postprocess_rstmgr_docs.py
"""

import re
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs" / "rstmgr"

# ── 1. URL-to-local-file mapping ────────────────────────────────────────────

# All known URL path patterns that map to local files.
# We build this from the actual filenames on disk.
URL_TO_FILE: dict[str, str] = {}


def build_url_map():
    """Build a mapping from MS Learn URL path fragments to local filenames."""
    for f in DOCS_DIR.glob("*.md"):
        if f.name.startswith("_") or f.name == "index.md":
            continue
        name = f.stem  # e.g. "restartmanager_nf-restartmanager-rmstartsession"

        # Read frontmatter to get source URL
        text = f.read_text(encoding="utf-8")
        m = re.search(r'^source:\s*"([^"]+)"', text, re.MULTILINE)
        if m:
            source_url = m.group(1)
            # Store multiple path variants that might appear in links
            path = source_url.replace("https://learn.microsoft.com", "")
            URL_TO_FILE[path] = f.name
            # Also store /windows/desktop/ variant (MS docs use both)
            desktop_path = path.replace("/windows/win32/", "/windows/desktop/")
            URL_TO_FILE[desktop_path] = f.name
            # Case-insensitive: store lowercase
            URL_TO_FILE[path.lower()] = f.name
            URL_TO_FILE[desktop_path.lower()] = f.name

    # Also register bare page-name variants for relative links within rstmgr/
    # e.g. "critical-system-services" → "rstmgr_critical-system-services.md"
    for f in DOCS_DIR.glob("rstmgr_*.md"):
        bare_name = f.stem.removeprefix("rstmgr_")
        URL_TO_FILE[bare_name] = f.name
        URL_TO_FILE[bare_name.lower()] = f.name


# ── 2. Boilerplate stripping ────────────────────────────────────────────────

# Lines/patterns to remove from the top boilerplate
BOILERPLATE_PATTERNS = [
    r"^Table of contents\s*$",
    r"^Exit editor mode\s*$",
    r"^Ask Learn\s*$",
    r"^Focus mode\s*$",
    r"^\[Read in English\].*$",
    r"^Add\s*$",
    r"^Add to plan\s*$",
    r"^\[Edit\]\(https://github\.com/.*$",
    r"^#### Share via\s*$",
    r"^\[Facebook\].*$",
    r"^\[x\.com\].*$",
    r"^\[LinkedIn\].*$",
    r"^\[Email\].*$",
    r"^Copy Markdown\s*$",
    r"^Print\s*$",
    r"^Note\s*$",
    r"^Access to this page requires authorization.*$",
    r"^Feedback\s*$",
    r"^Summarize this article for me\s*$",
]

# Sections to strip from the bottom
BOTTOM_SECTIONS = [
    r"^## Feedback\s*$",
    r"^## Additional resources\s*$",
    r"^## Additional Links\s*$",
]


def strip_boilerplate(text: str) -> str:
    """Remove MS Learn UI junk from markdown content."""
    lines = text.split("\n")

    # Find the frontmatter end
    fm_end = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                fm_end = i + 1
                break

    frontmatter = "\n".join(lines[:fm_end])
    body_lines = lines[fm_end:]

    # Remove individual boilerplate lines
    compiled = [re.compile(p, re.IGNORECASE) for p in BOILERPLATE_PATTERNS]
    cleaned = []
    for line in body_lines:
        stripped = line.strip()
        if any(pat.match(stripped) for pat in compiled):
            continue
        cleaned.append(line)

    # Find and remove bottom sections (Feedback, Additional resources, etc.)
    bottom_compiled = [re.compile(p) for p in BOTTOM_SECTIONS]
    cut_index = len(cleaned)
    for i, line in enumerate(cleaned):
        stripped = line.strip()
        if any(pat.match(stripped) for pat in bottom_compiled):
            cut_index = i
            break
    cleaned = cleaned[:cut_index]

    body = "\n".join(cleaned)

    # Remove "Yes\n\nNo\n\nNo" and "Need help with this topic" leftovers
    body = re.sub(r"\n\s*Yes\s*\n+\s*No\s*\n+\s*No\s*\n", "\n", body)
    body = re.sub(r"Need help with this topic\?.*?Ask Learn", "", body, flags=re.DOTALL)
    body = re.sub(r"Suggest a fix\?", "", body)
    body = re.sub(r"Want to try using Ask Learn.*?Ask Learn", "", body, flags=re.DOTALL)

    # Remove orphaned horizontal rules (top and bottom)
    body = body.rstrip()
    while body.endswith("---"):
        body = body[:-3].rstrip()

    # Strip leading orphaned "---" blocks (leftover from stripped Share/nav sections)
    body = re.sub(r"^(\s*---\s*\n)+", "", body)

    # Remove excessive blank lines
    body = re.sub(r"\n{4,}", "\n\n\n", body)

    # Re-combine
    result = frontmatter + "\n\n" + body.strip() + "\n"
    return result


# ── 3. Link rewriting ───────────────────────────────────────────────────────

# Pattern for markdown links: [text](url)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

MS_LEARN_BASE = "https://learn.microsoft.com"


def rewrite_link(match: re.Match) -> str:
    """Rewrite a single markdown link to local file if in scope."""
    text = match.group(1)
    url = match.group(2)

    # Skip anchors-only links
    if url.startswith("#"):
        return match.group(0)

    # Normalise the URL for lookup
    lookup = url
    # Strip fragment
    if "#" in lookup:
        lookup, fragment = lookup.split("#", 1)
    else:
        fragment = None

    # Strip full domain if present
    for prefix in [
        "https://learn.microsoft.com",
        "http://learn.microsoft.com",
    ]:
        if lookup.startswith(prefix):
            lookup = lookup[len(prefix):]
            break

    # Strip trailing slash
    lookup = lookup.rstrip("/")

    # Try to find in our map
    local_file = (
        URL_TO_FILE.get(lookup)
        or URL_TO_FILE.get(lookup.lower())
    )

    if local_file:
        new_url = local_file
        if fragment:
            new_url += "#" + fragment
        return f"[{text}]({new_url})"

    # If it's a relative link (no leading /), try matching
    if not lookup.startswith("/") and not lookup.startswith("http"):
        local_file = URL_TO_FILE.get(lookup) or URL_TO_FILE.get(lookup.lower())
        if local_file:
            new_url = local_file
            if fragment:
                new_url += "#" + fragment
            return f"[{text}]({new_url})"

    # For MS Learn links that are out of scope, make them absolute
    if lookup.startswith("/en-us/"):
        new_url = MS_LEARN_BASE + lookup
        if fragment:
            new_url += "#" + fragment
        return f"[{text}]({new_url})"

    return match.group(0)


def rewrite_links(text: str) -> str:
    """Rewrite all links in the document."""
    return LINK_RE.sub(rewrite_link, text)


# ── 4. Formatting cleanup ───────────────────────────────────────────────────

def fix_formatting(text: str) -> str:
    """Ensure consistent formatting."""
    # Ensure single blank line before headings
    text = re.sub(r"\n{3,}(#{1,4} )", r"\n\n\1", text)

    # Remove trailing whitespace on each line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Ensure file ends with single newline
    text = text.rstrip() + "\n"

    return text


# ── 5. Entrypoint generation ────────────────────────────────────────────────

def read_title(filepath: Path) -> str:
    """Read the title from frontmatter."""
    text = filepath.read_text(encoding="utf-8")
    m = re.search(r'^title:\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else filepath.stem


def generate_entrypoint():
    """Generate a structured index.md as the documentation entrypoint."""
    # Categorise files
    functions = []
    enums = []
    structs = []
    callbacks = []
    guides = []
    overview = []

    for f in sorted(DOCS_DIR.glob("*.md")):
        if f.name.startswith("_") or f.name == "index.md":
            continue
        title = read_title(f)
        entry = (f.name, title)

        stem = f.stem.lower()
        if "_nf-" in stem:
            functions.append(entry)
        elif "_ne-" in stem:
            enums.append(entry)
        elif "_ns-" in stem:
            structs.append(entry)
        elif "_nc-" in stem:
            callbacks.append(entry)
        elif stem.startswith("rstmgr_") and any(kw in stem for kw in [
            "using-", "guidelines-", "canceling-", "getting-the-status",
        ]):
            guides.append(entry)
        else:
            overview.append(entry)

    lines = [
        "# Restart Manager API — Documentation\n",
        "",
        "> Local mirror of the [Windows Restart Manager](https://learn.microsoft.com/en-us/windows/win32/rstmgr/restart-manager-portal) documentation from Microsoft Learn.",
        "> Scraped for offline use and fast searchability.",
        "",
        "---",
        "",
        "## Overview",
        "",
    ]
    for fname, title in overview:
        lines.append(f"- [{title}]({fname})")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Functions")
    lines.append("")
    lines.append("| Function | Description |")
    lines.append("|----------|-------------|")
    for fname, title in functions:
        # Extract short function name from title
        fn_name = title.split("(")[0].strip() if "(" in title else title
        lines.append(f"| [{fn_name}]({fname}) | `{fn_name}` |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Structures")
    lines.append("")
    for fname, title in structs:
        struct_name = title.split("(")[0].strip() if "(" in title else title
        lines.append(f"- [{struct_name}]({fname})")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Enumerations")
    lines.append("")
    for fname, title in enums:
        enum_name = title.split("(")[0].strip() if "(" in title else title
        lines.append(f"- [{enum_name}]({fname})")
    lines.append("")

    if callbacks:
        lines.append("---")
        lines.append("")
        lines.append("## Callback Functions")
        lines.append("")
        for fname, title in callbacks:
            cb_name = title.split("(")[0].strip() if "(" in title else title
            lines.append(f"- [{cb_name}]({fname})")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Guides & Usage")
    lines.append("")
    for fname, title in guides:
        lines.append(f"- [{title}]({fname})")
    lines.append("")

    readme = "\n".join(lines) + "\n"
    out = DOCS_DIR / "index.md"
    out.write_text(readme, encoding="utf-8")
    print(f"  ✓ Created {out.name}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"📝 Post-processing docs in {DOCS_DIR}\n")

    build_url_map()
    print(f"  ✓ Built URL map with {len(URL_TO_FILE)} entries\n")

    md_files = [f for f in DOCS_DIR.glob("*.md") if not f.name.startswith("_") and f.name != "index.md"]

    for f in sorted(md_files):
        text = f.read_text(encoding="utf-8")
        original = text

        text = strip_boilerplate(text)
        text = rewrite_links(text)
        text = fix_formatting(text)

        if text != original:
            f.write_text(text, encoding="utf-8")
            print(f"  ✓ Fixed {f.name}")
        else:
            print(f"  · Unchanged {f.name}")

    print()
    generate_entrypoint()

    # Remove old _index.md
    old_index = DOCS_DIR / "_index.md"
    if old_index.exists():
        old_index.unlink()
        print(f"  ✓ Removed old {old_index.name}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
