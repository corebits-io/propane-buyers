#!/usr/bin/env python3
"""
fetch_site.py: the plain text of a business website, for the personalisation step.
Usage: python3 fetch_site.py https://example.com [--chars 2500]
Prints the visible text of the home page (and /about if it exists), stripped of scripts and tags.
"""
import html, re, subprocess, sys

def text_of(url, timeout=20):
    out = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", "Mozilla/5.0", url],
                         capture_output=True, text=True).stdout
    out = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", out, flags=re.S | re.I)
    out = re.sub(r"<[^>]+>", " ", out)
    return re.sub(r"\s+", " ", html.unescape(out)).strip()

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: fetch_site.py <url> [--chars N]")
    url = sys.argv[1]
    n = int(sys.argv[sys.argv.index("--chars") + 1]) if "--chars" in sys.argv else 2500
    base = url if url.startswith("http") else "https://" + url
    t = text_of(base)
    about = text_of(base.rstrip("/") + "/about")
    if len(about) > 200 and about[:200] != t[:200]:
        t += " || ABOUT: " + about
    print(t[:n] if t else "no text, the site is JavaScript rendered or down")

if __name__ == "__main__":
    main()
