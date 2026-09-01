#!/usr/bin/env python3
"""Build the Le Pointre Manifesto static site from editable content/ files.

Content model (editable by client via Decap CMS):
  content/site.json        branding: artist, tagline, hero_image, accent, featured[8]
  content/posts/<slug>.md  frontmatter(title,date) + body HTML (images already local)
  content/pages/<name>.md  frontmatter(title) + body HTML

Output: public/  (deploy to Vercel root)
"""
import os, re, json, shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public")
ASSETS = os.path.join(ROOT, "assets")
CONTENT = os.path.join(ROOT, "content")

def read_md(path):
    txt = open(path, encoding="utf-8").read()
    fm = {}
    body = txt
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", txt, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip().strip('"').strip("'")
                fm[k.strip()] = v
        body = m.group(2)
    return fm, body.strip()

def load_site():
    return json.load(open(os.path.join(CONTENT, "site.json"), encoding="utf-8"))

def load_posts():
    posts = []
    pd = os.path.join(CONTENT, "posts")
    for fn in os.listdir(pd):
        if fn.endswith(".md"):
            fm, body = read_md(os.path.join(pd, fn))
            slug = fn[:-3]
            # count images in body for "visual" ranking
            imgs = re.findall(r'src="([^"]+)"', body)
            # sanitize: remove ANY overblog reference (links, footers, comment API)
            # 1) drop "Retour à l'accueil" footer links entirely
            body = re.sub(r'<a\b[^>]*\shref="[^"]*over-blog[^"]*"[^>]*>\s*[^<]*Retour[^<]*</a>', "", body, flags=re.S|re.I)
            # 2) unwrap image links that point to overblog CDN (KEEP the inner <img>)
            body = re.sub(r'<a\b[^>]*\shref="[^"]*over-blog[^"]*"[^>]*>(.*?)</a>', r"\1", body, flags=re.S|re.I)
            # 3) neutralize any other stray overblog href
            body = re.sub(r'href="[^"]*over-blog[^"]*"', 'href="#"', body, flags=re.I)
            # 4) remove overblog comment-count <script> widgets
            body = re.sub(r'<script.*?</script>', "", body, flags=re.S|re.I)
            # 5) strip overblog UI chrome (header/meta/return/footer/pagination)
            body = re.sub(r'<div class="Post-header">.*?</div>\s*', "", body, flags=re.S|re.I)
            body = re.sub(r'<p class="Post-meta[^"]*">.*?</p>', "", body, flags=re.S|re.I)
            body = re.sub(r'<div class="Post-returnToHome">.*?</div>', "", body, flags=re.S|re.I)
            body = re.sub(r'<div class="Pagination[^"]*">.*?</div>', "", body, flags=re.S|re.I)
            body = re.sub(r'<div class="Clear"></div>', "", body, flags=re.S|re.I)
            # 6) unwrap ob-section/ob-sections containers (keep inner content/images)
            body = re.sub(r'</?div class="ob-sections?"[^>]*>', "", body, flags=re.S|re.I)
            body = re.sub(r'</?div class="ob-section[^"]*">', "", body, flags=re.S|re.I)
            body = re.sub(r' class="ob-section[^"]*"', "", body, flags=re.S|re.I)
            # 7) drop empty paragraphs
            body = re.sub(r'<p>\s*</p>', "", body, flags=re.S)
            # 8) strip inline color styles (overblog used black/blue/red that are invisible on dark theme)
            body = re.sub(r'\sstyle="[^"]*color:[^";]*;?', "", body, flags=re.I)
            body = re.sub(r'\sstyle="color:[^"]*"', "", body, flags=re.I)
            date = fm.get("date", "").strip()
            if not date:
                # try to infer from any YYYY-MM occurrence in filename/title
                dm = re.search(r'(19|20)\d{2}[-_]\d{2}', slug)
                date = dm.group(0).replace("_", "-") if dm else ""
            posts.append({"slug": slug, "title": fm.get("title", slug),
                          "date": date, "body": body, "n_img": len(imgs)})
    # sort by date desc
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts

def load_pages():
    pages = {}
    pgd = os.path.join(CONTENT, "pages")
    for fn in os.listdir(pgd):
        if fn.endswith(".md"):
            fm, body = read_md(os.path.join(pgd, fn))
            pages[fn[:-3]] = {"title": fm.get("title", fn[:-3]), "body": body}
    return pages

# ---------- styling ----------
CSS = """/* ===== Le Pointre — MANIFESTO ===== */
:root{
  --bg:#141414; --bg2:#1c1c1c; --fg:#f4f1ea; --muted:#9a958c;
  --line:#2c2c2c; --accent:#e23b2e; --card:#1a1a1a;
  --font-display:"Oswald","Arial Narrow",Impact,sans-serif;
  --font-body:"Inter",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font-body);
  line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px}

/* header */
.site-head{position:sticky;top:0;z-index:30;background:rgba(20,20,20,.9);
  backdrop-filter:blur(8px);border-bottom:2px solid var(--accent)}
.site-head .wrap{display:flex;align-items:center;justify-content:space-between;height:64px}
.brand{font-family:var(--font-display);font-weight:700;letter-spacing:.22em;
  text-transform:uppercase;font-size:24px}
.brand b{color:var(--accent)}
.nav a{margin-left:20px;font-family:var(--font-display);text-transform:uppercase;
  letter-spacing:.12em;font-size:14px;color:var(--muted)}
.nav a:hover{color:var(--accent)}
/* title banner (big, visible — like Overblog) */
.title-banner{background:var(--bg2);border-bottom:2px solid var(--accent);padding:18px 22px;text-align:center}
.title-banner span{font-family:var(--font-display);font-weight:700;text-transform:uppercase;
  letter-spacing:.04em;font-size:clamp(22px,4.4vw,46px);line-height:1.05;color:var(--fg)}
/* photo banner */
.photo-banner{width:100%;padding:14px 16px 4px;display:flex;justify-content:center;background:var(--bg);border-bottom:2px solid var(--line)}
.photo-banner img{width:auto;max-width:min(860px,92%);height:auto;max-height:340px;object-fit:contain;filter:grayscale(.12) contrast(1.03);border:1px solid var(--line)}
/* dropdown nav */
.nav-dd{position:relative;display:inline-block}
.nav-dd .dd-trigger{font-family:var(--font-display);text-transform:uppercase;letter-spacing:.12em;
  font-size:14px;color:var(--muted);margin-left:20px;cursor:pointer}
.nav-dd .dd-trigger:hover{color:var(--accent)}
.dd-box{position:absolute;top:100%;left:0;margin-top:10px;background:var(--bg2);border:1px solid var(--line);
  border-top:2px solid var(--accent);min-width:240px;max-height:60vh;overflow:auto;padding:6px 0;
  display:none;z-index:50;box-shadow:0 14px 40px rgba(0,0,0,.5)}
.dd-box.wide{min-width:320px}
.nav-dd:hover .dd-box,.nav-dd.open .dd-box{display:block}
.dd-box .dd-year{font-family:var(--font-display);color:var(--accent);font-size:12px;letter-spacing:.1em;
  padding:8px 14px 4px;text-transform:uppercase}
.dd-box .dd-item{display:block;padding:6px 14px;color:var(--fg);font-size:13px;line-height:1.25;
  border-bottom:1px solid rgba(255,255,255,.04)}
.dd-box .dd-item:hover{background:var(--accent);color:#fff}
@media(max-width:980px){
  .site-title{display:none}
  .dd-box{max-height:50vh}
}

/* hero */
.hero{position:relative;border-bottom:2px solid var(--line);overflow:hidden}
.hero-img{width:100%;height:62vh;min-height:340px;object-fit:cover;filter:grayscale(.25) contrast(1.05)}
.hero-veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15),rgba(20,20,20,.92))}
.hero-txt{position:absolute;left:0;right:0;bottom:0;padding:34px 22px}
.hero-txt h1{font-family:var(--font-display);font-weight:700;letter-spacing:.04em;
  text-transform:uppercase;font-size:clamp(40px,9vw,110px);margin:0;line-height:.92}
.hero-txt h1 b{color:var(--accent);font-style:italic}
.hero-txt p{font-family:var(--font-display);text-transform:uppercase;letter-spacing:.18em;
  color:var(--fg);opacity:.85;margin:10px 0 0;font-size:clamp(13px,2vw,18px)}
.hero-note{position:absolute;top:18px;left:22px;font-family:var(--font-display);
  text-transform:uppercase;letter-spacing:.3em;font-size:12px;color:var(--accent);
  border:1px solid var(--accent);padding:4px 10px;transform:rotate(-2deg)}

/* section label */
.sec-label{font-family:var(--font-display);text-transform:uppercase;letter-spacing:.3em;
  font-size:13px;color:var(--accent);padding:46px 22px 6px;border-bottom:1px solid var(--line);
  max-width:1180px;margin:0 auto}
.sec-label b{color:var(--fg)}

/* post tiles */
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;
  padding:24px 22px 60px;max-width:1180px;margin:0 auto}
.tile{position:relative;background:var(--card);border:1px solid var(--line);
  overflow:hidden;cursor:pointer;transition:transform .25s,border-color .25s;transform:rotate(var(--rot,0deg))}
.tile:hover{transform:rotate(0) scale(1.02);border-color:var(--accent);z-index:5}
.tile .ph{aspect-ratio:4/3;overflow:hidden;background:#000}
.tile .ph img{width:100%;height:100%;object-fit:cover;filter:grayscale(.2) contrast(1.05);
  transition:transform .4s}
.tile:hover .ph img{transform:scale(1.06);filter:none}
.tile .ph-empty{display:flex;align-items:center;justify-content:center;background:
  repeating-linear-gradient(45deg,#1a1a1a,#1a1a1a 10px,#222 10px,#222 20px)}
.tile .ph-empty span{font-family:var(--font-display);text-transform:uppercase;
  letter-spacing:.06em;font-size:14px;color:var(--muted);text-align:center;padding:10px}
.tile .cap{padding:11px 12px 13px}
.tile .cap h3{margin:0;font-family:var(--font-display);text-transform:uppercase;
  letter-spacing:.04em;font-size:16px;line-height:1.1}
.tile .cap .d{color:var(--muted);font-size:12px;margin-top:4px;letter-spacing:.05em}
.tile .tag{position:absolute;top:8px;left:8px;background:var(--accent);color:#fff;
  font-family:var(--font-display);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
  padding:2px 8px;transform:rotate(-3deg)}

/* gallery strip (every artwork) */
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
  gap:8px;padding:24px 22px 60px;max-width:1180px;margin:0 auto}
.gcell{position:relative;aspect-ratio:1/1;overflow:hidden;background:#000;cursor:zoom-in}
.gcell img{width:100%;height:100%;object-fit:cover;transition:transform .35s,filter .35s;
  filter:grayscale(.25)}
.gcell:hover img{transform:scale(1.06);filter:none}
.gcell .tag{position:absolute;bottom:0;left:0;right:0;padding:6px 8px;font-size:11px;
  background:linear-gradient(transparent,rgba(0,0,0,.8));color:#fff;opacity:0;transition:opacity .3s}
.gcell:hover .tag{opacity:1}

/* post body page */
.post{max-width:860px;margin:0 auto;padding:40px 22px 70px}
.post h1{font-family:var(--font-display);text-transform:uppercase;letter-spacing:.02em;
  font-size:clamp(28px,5vw,52px);line-height:1;margin:0 0 6px}
.post .date{color:var(--accent);font-family:var(--font-display);letter-spacing:.18em;
  text-transform:uppercase;font-size:13px;margin-bottom:26px}
.post .body img{border:1px solid var(--line);margin:18px 0;border-radius:2px;cursor:zoom-in}
.post .body p{font-size:17px}
.backlink{display:inline-block;margin:30px 22px;font-family:var(--font-display);
  text-transform:uppercase;letter-spacing:.15em;color:var(--accent);font-size:13px}

/* generic page */
.page{max-width:760px;margin:0 auto;padding:48px 22px 70px}
.page h1{font-family:var(--font-display);text-transform:uppercase;font-size:clamp(34px,6vw,64px);
  letter-spacing:.02em;margin:0 0 20px}
.page h1 b{color:var(--accent)}
.page p{font-size:17px;line-height:1.6}
.page ul{font-size:17px;line-height:1.7;padding-left:20px}
.page li{margin:6px 0}
.page a{color:var(--accent)}
/* WhatsApp / call-to-action button */
.wa-btn{display:inline-block;margin:14px 0;background:var(--accent);color:#fff !important;
  padding:12px 18px;border-radius:5px;font-family:var(--font-display);text-transform:uppercase;
  letter-spacing:.08em;font-size:15px;font-weight:700;text-decoration:none}
.wa-btn:hover{opacity:.9}
/* listing pages (Pages / Archives) */
.year-group{margin:0 0 26px}
.year-group h2{font-family:var(--font-display);color:var(--accent);font-size:20px;letter-spacing:.08em;
  text-transform:uppercase;margin:0 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}
.post-list{display:grid;grid-template-columns:repeat(2,1fr);gap:10px 22px}
.post-list a{display:block;padding:9px 12px;background:var(--bg2);border:1px solid var(--line);
  color:var(--fg);font-size:14px;border-left:3px solid var(--accent)}
.post-list a:hover{background:var(--accent);color:#fff}
@media(max-width:560px){.post-list{grid-template-columns:1fr}}

/* footer */
.site-foot{border-top:2px solid var(--line);padding:28px 22px;color:var(--muted);
  text-align:center;font-size:13px}
.site-foot b{color:var(--fg)}

/* lightbox */
#lb{position:fixed;inset:0;background:rgba(8,8,8,.96);display:none;align-items:center;
  justify-content:center;z-index:100}
#lb.on{display:flex}
#lb img{max-width:92vw;max-height:88vh;border:1px solid var(--line)}
#lb .x,#lb .p,#lb .n{position:fixed;background:none;border:none;color:#fff;cursor:pointer;
  font-size:42px;opacity:.75}
#lb .x{top:16px;right:22px}#lb .p{left:16px;top:50%}#lb .n{right:16px;top:50%}
#lb .x:hover,#lb .p:hover,#lb .n:hover{color:var(--accent);opacity:1}

/* responsive */
@media(max-width:980px){.tiles{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){
  .tiles{grid-template-columns:1fr}
  .site-head .wrap{height:56px}
  .brand{font-size:19px}
  .nav a{margin-left:13px;font-size:12px}
  .hero-img{height:48vh;min-height:260px}
  .gallery{grid-template-columns:repeat(2,1fr)}
}
"""

JS = """const LB=document.getElementById('lb'),LBI=document.getElementById('lbi');
let G=[],GI=0;
function openLB(list,i){G=list;GI=i;LBI.src=G[GI];LB.classList.add('on');document.body.style.overflow='hidden';}
function closeLB(){LB.classList.remove('on');document.body.style.overflow='';}
function navLB(d){GI=(GI+d+G.length)%G.length;LBI.src=G[GI];}
document.querySelectorAll('.gcell').forEach(c=>c.onclick=()=>openLB(window.__G,c.dataset.i));
document.querySelectorAll('.post .body img').forEach(im=>im.onclick=()=>{LBI.src=im.getAttribute('data-full')||im.src;LB.classList.add('on');G=[];document.body.style.overflow='hidden';});
/* dropdown nav: click to toggle open (so you can scroll inside), click outside to close */
document.querySelectorAll('.nav-dd').forEach(dd=>{
  const trig=dd.querySelector('.dd-trigger');
  trig.addEventListener('click',e=>{e.stopPropagation();
    const open=dd.classList.contains('open');
    document.querySelectorAll('.nav-dd.open').forEach(o=>o.classList.remove('open'));
    if(!open)dd.classList.add('open');
  });
  trig.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();trig.click();}});
});
document.addEventListener('click',()=>document.querySelectorAll('.nav-dd.open').forEach(o=>o.classList.remove('open')));
LB.onclick=e=>{if(e.target===LB)closeLB();};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLB();if(e.key==='ArrowRight')navLB(1);if(e.key==='ArrowLeft')navLB(-1);});
"""

def head(title, site, posts=None, base=""):
    artist = site['artist']
    brand = artist.split()[0] + "<b>·</b>" + (artist.split()[-1] if len(artist.split()) > 1 else "")
    site_title = site.get("site_title", "Les peintures et toiles de " + artist)
    banner_img = site.get("hero_image", "")
    # ---- PAGES dropdown (every post) ----
    pages_menu = ""
    if posts:
        items = "".join(
            f'<a class="dd-item" href="posts/{p["slug"]}.html">{p["title"]}</a>'
            for p in posts)
        pages_menu = f'<div class="nav-dd"><span class="dd-trigger" tabindex="0">Pages ▾</span><div class="dd-box">{items}</div></div>'
        # ---- ARCHIVES dropdown (grouped by year) ----
        years = {}
        for p in posts:
            y = (p["date"][:4] if p["date"] else "Sans date")
            years.setdefault(y, []).append(p)
        arch_items = ""
        for y in sorted(years.keys(), reverse=True):
            arch_items += f'<div class="dd-year">{y}</div>'
            arch_items += "".join(
                f'<a class="dd-item" href="posts/{p["slug"]}.html">{p["title"]}</a>'
                for p in years[y])
        arch_menu = f'<div class="nav-dd"><span class="dd-trigger" tabindex="0">Archives ▾</span><div class="dd-box wide">{arch_items}</div></div>'
    else:
        pages_menu = '<div class="nav-dd"><a class="dd-trigger" href="galerie.html">Pages ▾</a></div>'
        arch_menu = '<div class="nav-dd"><a class="dd-trigger" href="galerie.html">Archives ▾</a></div>'
    banner_html = f'<div class="title-banner"><span>{site_title}</span></div>'
    if banner_img:
        banner_html += f'<div class="photo-banner"><img src="{banner_img}" alt="{artist}"></div>'
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<base href="/">
<title>{title} — {artist}</title>
<meta name="description" content="{artist} — {site.get('tagline','')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="index.html">{brand}</a>
  <nav class="nav">
    <a href="index.html">Accueil</a>
    <a href="galerie.html">Galerie</a>
    {pages_menu}
    {arch_menu}
    <a href="about.html">À propos</a>
    <a href="boutique.html">Boutique</a>
    <a href="contact.html">Contact</a>
  </nav>
</div></header>
{banner_html}
"""

def foot():
    return """<footer class="site-foot"><b>LE POINTRE</b> — peintre. Migré depuis Overblog · hébergé gratuitement, domaine <b>lepointre.com</b> à brancher.</footer>
<div id="lb"><button class="x" onclick="closeLB()">×</button><button class="p" onclick="navLB(-1)">‹</button><img id="lbi" src=""><button class="n" onclick="navLB(1)">›</button></div>
<script src="assets/js/site.js"></script></body></html>"""

def post_cover(post):
    # prefer an image src; skip video/audio sources so the homepage tile isn't a .mp4
    for m in re.finditer(r'src="([^"]+)"', post["body"]):
        u = m.group(1)
        if not u.lower().endswith((".mp4", ".webm", ".ogg", ".mp3", ".wav")):
            return u
    # fallback: use the <video poster="..."> if present
    m = re.search(r'poster="([^"]+)"', post["body"])
    return m.group(1) if m else ""

def build():
    site = load_site()
    posts = load_posts()
    pages = load_pages()
    # fix brand rendering: artist may be one word
    os.makedirs(os.path.join(PUBLIC, "assets", "css"), exist_ok=True)
    os.makedirs(os.path.join(PUBLIC, "assets", "js"), exist_ok=True)
    with open(os.path.join(PUBLIC, "assets", "css", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS.replace("#e23b2e", site.get("accent", "#e23b2e")))
    with open(os.path.join(PUBLIC, "assets", "js", "site.js"), "w", encoding="utf-8") as f:
        f.write(JS)
    # copy ONLY referenced images (lean deploy)
    needed = set()
    for p in posts:
        for u in re.findall(r'src="(assets/img/[^"]+)"', p["body"]):
            needed.add(u.replace("assets/img/", ""))
        # also copy video <source> + <video poster> assets
        for u in re.findall(r'(?:src|poster)="(assets/img/[^"]+)"', p["body"]):
            needed.add(u.replace("assets/img/", ""))
    # also include the hero/photo banner image from site.json
    if site.get("hero_image", "").startswith("assets/img/"):
        needed.add(site["hero_image"].replace("assets/img/", ""))
    os.makedirs(os.path.join(PUBLIC, "assets", "img"), exist_ok=True)
    copied = 0
    for base in needed:
        srcf = os.path.join(ASSETS, "img", base)
        if os.path.exists(srcf):
            dstdir = os.path.dirname(os.path.join(PUBLIC, "assets", "img", base))
            os.makedirs(dstdir, exist_ok=True)
            shutil.copy(srcf, os.path.join(PUBLIC, "assets", "img", base))
            copied += 1
    # copy admin (Decap CMS) into public/admin/
    import shutil as _sh
    adm_src = os.path.join(ROOT, "admin")
    if os.path.isdir(adm_src):
        _sh.copytree(adm_src, os.path.join(PUBLIC, "admin"), dirs_exist_ok=True)
        print("copied admin/ -> public/admin/")


    featured = [p for p in posts if p["slug"] in site.get("featured", [])][:8]
    # posts excluded from the homepage tiles (their content lives elsewhere, e.g. About)
    home_exclude = set(site.get("home_exclude", []))
    # fallback: if featured missing, take top-8 by image count
    if len(featured) < 8:
        extra = [p for p in posts if p not in featured and p["slug"] not in home_exclude]
        extra.sort(key=lambda x: x["n_img"], reverse=True)
        featured += extra[:8 - len(featured)]

    # ---- index ----
    hero = f'<section class="hero" style="background:var(--bg2)"><div class="hero-veil"></div><div class="hero-txt"><h1>{site["artist"].split()[0]}<b>·</b>{site["artist"].split()[-1] if len(site["artist"].split())>1 else ""}</h1><p>{site.get("tagline","")}</p></div></section>'
    tiles = []
    rots = ["-1.2deg","1deg","-0.6deg","0.8deg","-1deg","1.3deg","-0.9deg","0.7deg"]
    for i, p in enumerate(featured):
        cov = post_cover(p)
        if cov:
            ph = f'<div class="ph"><img loading="lazy" src="{cov}" alt="{p["title"]}"></div>'
        else:
            ph = f'<div class="ph ph-empty"><span>{p["title"]}</span></div>'
        tiles.append(f'<a class="tile" style="--rot:{rots[i%len(rots)]}" href="posts/{p["slug"]}.html">{ph}<div class="cap"><h3>{p["title"]}</h3><div class="d">{p["date"]}</div></div></a>')
    idx = (head("Accueil", site, posts) + hero +
           '<div class="sec-label">Sélection — <b>8 œuvres / expositions</b></div>' +
           '<section class="tiles">' + "".join(tiles) + "</section>" +
           '<div class="sec-label">L’intégrale — <b>toutes les toiles</b></div>' +
           f'<section class="tiles">' + "".join(
           (f'<a class="tile" style="--rot:{rots[i%len(rots)]}" href="posts/{p["slug"]}.html"><div class="ph"><img loading="lazy" src="{post_cover(p)}" alt=""></div><div class="cap"><h3>{p["title"]}</h3><div class="d">{p["date"]}</div></div></a>' if (post_cover(p) and p["slug"] not in home_exclude)
            else (f'<a class="tile" style="--rot:{rots[i%len(rots)]}" href="posts/{p["slug"]}.html"><div class="ph ph-empty"><span>{p["title"]}</span></div><div class="cap"><h3>{p["title"]}</h3><div class="d">{p["date"]}</div></div></a>' if p["slug"] not in home_exclude else ""))
           for i, p in enumerate(posts)) + "</section>" + foot())
    open(os.path.join(PUBLIC, "index.html"), "w", encoding="utf-8").write(idx)

    # ---- galerie (every artwork grid + lightbox) ----
    allimgs = []
    seen = set()
    for p in posts:
        for m in re.finditer(r'<img\b[^>]*\bsrc="([^"]+)"', p["body"]):
            u = m.group(1)
            # only real local paintings (skip youtube/embedly video embeds & ui junk)
            if not u.startswith("assets/img/"):
                continue
            if u in seen:
                continue
            seen.add(u)
            allimgs.append({"full": u})
    gal = []
    for i, g in enumerate(allimgs):
        gal.append(f'<div class="gcell" data-i="{i}"><img loading="lazy" src="{g["full"]}" alt=""></div>')
    gjson = json.dumps([g["full"] for g in allimgs], ensure_ascii=False)
    galpage = (head("Galerie", site, posts) +
               '<div class="sec-label">Galerie — <b>toutes les œuvres</b></div>' +
               '<section class="gallery">' + "".join(gal) + "</section>" +
               f'<script>window.__G={gjson};</script>' + foot())
    open(os.path.join(PUBLIC, "galerie.html"), "w", encoding="utf-8").write(galpage)

    # ---- post pages ----
    os.makedirs(os.path.join(PUBLIC, "posts"), exist_ok=True)
    for p in posts:
        body = re.sub(r'<p class="meta"[^>]*>.*?</p>', "", p["body"], flags=re.S)
        html = (head(p["title"], site, posts) +
                f'<article class="post"><h1>{p["title"]}</h1><div class="date">{p["date"]}</div><div class="body">{body}</div></article>' +
                '<a class="backlink" href="index.html">‹ Retour</a>' + foot())
        open(os.path.join(PUBLIC, "posts", p["slug"] + ".html"), "w", encoding="utf-8").write(html)

    # ---- simple pages ----
    def md_to_html(md):
        """Convert lightweight markdown (paragraphs, **bold**, [text](url),
        # headings) to HTML. Raw HTML tags (<a>, <small>) pass through untouched."""
        md = md.replace('\r\n', '\n').strip()
        out = []
        for block in re.split(r'\n\s*\n', md):
            b = block.strip()
            if not b:
                continue
            m = re.match(r'^(#{1,4})\s+(.*)$', b)
            if m:
                lvl = min(len(m.group(1)) + 1, 4)  # page already has h1 -> # becomes h2
                out.append(f'<h{lvl}>{_inline(m.group(2))}</h{lvl}>')
                continue
            out.append(f'<p>{_inline(b)}</p>')
        return '\n'.join(out)

    def _inline(s):
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
        s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
        return s

    for name in ("about", "contact", "shop"):
        if name in pages:
            html = (head(pages[name]["title"], site, posts) +
                    f'<div class="page"><h1>{pages[name]["title"]}</h1>{md_to_html(pages[name]["body"])}</div>' + foot())
            open(os.path.join(PUBLIC, name + ".html"), "w", encoding="utf-8").write(html)

    # ---- PAGES listing (every post) ----
    pages_list = "".join(
        f'<a href="posts/{p["slug"]}.html">{p["title"]}</a>' for p in posts)
    pagespage = (head("Pages", site, posts) +
                 f'<div class="page"><h1>Toutes les pages</h1><div class="post-list">{pages_list}</div></div>' + foot())
    open(os.path.join(PUBLIC, "pages.html"), "w", encoding="utf-8").write(pagespage)

    # ---- ARCHIVES listing (grouped by year) ----
    years = {}
    for p in posts:
        y = (p["date"][:4] if p["date"] else "Sans date")
        years.setdefault(y, []).append(p)
    arch_html = ""
    for y in sorted(years.keys(), reverse=True):
        items = "".join(
            f'<a href="posts/{p["slug"]}.html">{p["title"]}</a>' for p in years[y])
        arch_html += f'<div class="year-group"><h2>{y}</h2><div class="post-list">{items}</div></div>'
    archpage = (head("Archives", site, posts) +
                f'<div class="page"><h1>Archives</h1>{arch_html}</div>' + foot())
    open(os.path.join(PUBLIC, "archives.html"), "w", encoding="utf-8").write(archpage)

    # ---- 404 ----
    open(os.path.join(PUBLIC, "404.html"), "w", encoding="utf-8").write(
        head("404", site, posts) + '<div class="page"><h1>404</h1><p>Page introuvable. <a href="index.html" style="color:var(--accent)">Retour à l’accueil</a></p></div>' + foot())

    print(f"BUILT: {len(posts)} posts, {len(allimgs)} artworks in galerie, featured={[p['slug'] for p in featured]}")

if __name__ == "__main__":
    build()
