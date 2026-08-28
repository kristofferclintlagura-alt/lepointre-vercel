#!/usr/bin/env python3
"""Migrate the posts that were missed in the first pass (incl. client's 'A L'ATELIER - AT HOME').

Fetches each Overblog post page, downloads its images locally into assets/img/,
and writes content/posts/<slug>.md (frontmatter title/date + HTML body, with the
Overblog 'Retour a l'accueil' footer stripped so it never links back to Overblog).
"""
import os, re, json, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "content", "posts")
ASSETS = os.path.join(ROOT, "assets", "img")
os.makedirs(POSTS, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

# (slug, overblog url) for the posts missing from the original migration
MISSING = [
    ("a-l-atelier",           "https://artiste-peintre-lepointre.over-blog.com/a-l-atelier.html"),
    ("mister-big-bucks",      "https://artiste-peintre-lepointre.over-blog.com/mister-big-bucks.html"),
    ("night-work",            "https://artiste-peintre-lepointre.over-blog.com/night-work.html"),
    ("le-pointre-et-les-medias", "https://artiste-peintre-lepointre.over-blog.com/le-pointre-et-les-medias.html"),
    ("les-peintures-de-le-pointre", "https://artiste-peintre-lepointre.over-blog.com/les-peintures-de-le-pointre.html"),
    ("paintings-on-new-york-walls-serie-greenhouse-effect", "https://artiste-peintre-lepointre.over-blog.com/paintings-on-new-york-walls-serie-greenhouse-effect.html"),
    ("paintings-on-new-york-walls-serie-animaux", "https://artiste-peintre-lepointre.over-blog.com/paintings-on-new-york-walls-serie-animaux.html"),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def local_name(url):
    base = url.split("?")[0].rstrip("/")
    fn = base.rsplit("/", 1)[-1]
    if not fn:
        fn = "img_" + str(abs(hash(url)) % 100000)
    if "." not in fn:
        fn += ".jpg"
    return fn

def download(url):
    fn = local_name(url)
    dest = os.path.join(ASSETS, fn)
    if os.path.exists(dest):
        return "assets/img/" + fn
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return "assets/img/" + fn
    except Exception as e:
        print(f"  ! download failed {url}: {e}")
        return url  # leave remote; build will flag

def parse_date(url):
    m = re.search(r"/(\d{4})/(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return ""

for slug, url in MISSING:
    print(f"== {slug}")
    html = fetch(url)
    # title from <title> "X - Les peintures et toiles de Le Pointre"
    tm = re.search(r"<title>(.*?) - Les peintures", html)
    title = tm.group(1).strip() if tm else slug
    # body: the main article container
    am = re.search(r'<div class="ob-section ob-section.*?post-body.*?">(.*?)</div>\s*<div class="ob-section ob-section', html, re.S)
    if not am:
        am = re.search(r'class="post-content"[^>]*>(.*?)</article', html, re.S)
    if not am:
        am = re.search(r'<article[^>]*>(.*?)</article>', html, re.S)
    body = am.group(1) if am else ""
    # isolate the real content block (between first big image set and the share/retour footer)
    # strip Overblog chrome: share bars, related posts, 'Retour a l'accueil'
    body = re.sub(r'<a[^>]*href="https://artiste-peintre-lepointre\.over-blog\.com"[^>]*>.*?</a>', "", body, flags=re.S)
    body = re.sub(r'<a[^>]*>Retour[^<]*</a>', "", body, flags=re.S)
    # remove share / related / comment widgets
    body = re.sub(r'<div class="ob-section ob-section-file[^"]*"[^>]*>.*?</div>', "", body, flags=re.S)
    body = re.sub(r'<div class="ob-RelatedPost.*?</div>\s*</div>', "", body, flags=re.S)
    body = re.sub(r'<div class="ob-ShareBar.*?</div>\s*</div>', "", body, flags=re.S)
    body = re.sub(r'<div class="ob-comments.*?</div>\s*</div>', "", body, flags=re.S)
    # rewrite image src -> local
    def repl(m):
        tag = m.group(0)
        src = m.group(1)
        if "assets.over-blog" in src or "over-blog-kiwi.com/b/" in src:
            return ""  # skip UI chrome images
        local = download(src)
        return tag.replace(src, local)
    body = re.sub(r'<img[^>]*src="([^"]+)"', repl, body)
    # strip empty paragraphs / leftover tags from removed widgets
    body = re.sub(r"<p>\s*</p>", "", body)
    body = body.strip()
    md = f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\ndate: {parse_date(url)}\n---\n\n{body}\n"
    with open(os.path.join(POSTS, slug + ".md"), "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  title={title!r}  imgs_localized -> {slug}.md")
print("DONE")
