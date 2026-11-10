#!/usr/bin/env python3
"""Copia nel sito le pagine legali dell'app Task Coordinator.

Scarica privacy, condizioni d'uso e DPA (EN + LT) da task.processolution.pro con un
browser headless, li pulisce e genera privacy.html, terms.html, dpa.html nella root
del repo. delete-account.html e support.html vengono dai frammenti in questa cartella.

Uso (dalla root del repo):
    python3 tools/legal/sync_legal.py
Poi controlla le differenze con `git diff` e fai commit.

Il browser: variabile HEADLESS_CHROME, altrimenti il chrome-headless-shell di Playwright
o Google Chrome, se installati.
"""
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP = "https://task.processolution.pro"

# slug sul sito -> (percorso nell'app, titolo EN)
REMOTE = {
    "privacy": ("/privacy", "Privacy Policy"),
    "terms": ("/legal/terms", "Terms of Use"),
    "dpa": ("/legal/dpa", "Data Processing Agreement"),
}
LOCAL = {
    "delete-account": "Account and data deletion",
    "support": "Support",
}
# link interni dell'app -> pagine del sito
LINK_MAP = [
    (r'href="/legal/terms(\?lang=\w+)?"', r'href="/terms\1"'),
    (r'href="/legal/dpa(\?lang=\w+)?"', r'href="/dpa\1"'),
    (r'href="/privacy(\?lang=\w+)?"', r'href="/privacy\1"'),
    (r'href="/delete-account(\?lang=\w+)?"', r'href="/delete-account\1"'),
    (r'href="/(?!privacy|terms|dpa|delete-account|support)([^"]*)"', r'href="%s/\1"' % APP),
]


def find_browser():
    cands = [os.environ.get("HEADLESS_CHROME", "")]
    cands += sorted(glob.glob(os.path.expanduser(
        "~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell")), reverse=True)
    cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit("Nessun browser headless trovato: imposta HEADLESS_CHROME.")


def render(browser, url):
    out = subprocess.run([browser, "--headless", "--disable-gpu", "--virtual-time-budget=8000",
                          "--dump-dom", url], capture_output=True, text=True, timeout=120)
    return out.stdout


def clean(dom, url):
    m = re.search(r"<main\b.*?>(.*)</main>", dom, re.S)
    if not m or "<h1" not in m.group(1):
        sys.exit("Contenuto non trovato in %s: la pagina dell'app è cambiata?" % url)
    s = m.group(1)
    s = re.sub(r"<(svg|script|style|button|img|nav)\b.*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<img\b[^>]*>", "", s)
    # tieni solo href (e colspan/rowspan) come attributi
    def strip_attrs(tag):
        name, attrs = tag.group(1), tag.group(2)
        keep = re.findall(r'\s(?:href|colspan|rowspan)="[^"]*"', attrs)
        return "<%s%s>" % (name, "".join(keep))
    s = re.sub(r"<(\w+)((?:\s[^>]*)?)>", strip_attrs, s)
    s = re.sub(r"</?div>", "", s)
    # gli a capo dentro i paragrafi sono righe visibili nell'app (white-space: pre-line)
    s = re.sub(r"<p>(.*?)</p>", lambda p: "<p>" + re.sub(r"\s*\n\s*", "<br />", p.group(1).strip()) + "</p>", s, flags=re.S)
    s = re.sub(r"<table>", '<div class="table-scroll"><table>', s)
    s = re.sub(r"</table>", "</table></div>", s)
    s = re.sub(r"<a\b[^>]*>\s*</a>", "", s)
    for pat, rep in LINK_MAP:
        s = re.sub(pat, rep, s)
    return s.strip()


def build(slug, title_en, body_en, body_lt):
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    html = (tpl.replace("{{TITLE_EN}}", title_en).replace("{{SLUG}}", slug)
               .replace("{{BODY_EN}}", body_en).replace("{{BODY_LT}}", body_lt))
    path = os.path.join(ROOT, slug + ".html")
    open(path, "w", encoding="utf-8").write(html)
    print("scritto", os.path.relpath(path, ROOT), len(html), "byte")


def main():
    browser = find_browser()
    for slug, (path, title) in REMOTE.items():
        bodies = {}
        for lang in ("en", "lt"):
            url = "%s%s?lang=%s" % (APP, path, lang)
            bodies[lang] = clean(render(browser, url), url)
        if bodies["en"] == bodies["lt"]:
            sys.exit("%s: EN e LT identici, la lingua non è stata applicata." % slug)
        build(slug, title, bodies["en"], bodies["lt"])
    for slug, title in LOCAL.items():
        frag = {l: open(os.path.join(HERE, "%s.%s.html" % (slug, l)), encoding="utf-8").read().strip()
                for l in ("en", "lt")}
        build(slug, title, frag["en"], frag["lt"])


if __name__ == "__main__":
    main()
