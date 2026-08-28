#!/usr/bin/env python3
"""FULL Overblog migration -> editable content + optimized assets.
Captures ALL image hosts (image.over-blog.com AND img.over-blog-kiwi.com),
downloads + optimizes everything, and writes client-editable content files.
Idempotent: rerun regenerates cleanly.
"""
import os, re, ssl, json, hashlib, shutil
from urllib.request import Request, urlopen
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

SRC = "https://artiste-peintre-lepointre.over-blog.com"
ROOT = r"C:\Users\lagur\lepointre-vercel"
CONTENT = os.path.join(ROOT, "content")
IMG_DIR = os.path.join(ROOT, "assets", "img")
POSTS_DIR = os.path.join(CONTENT, "posts")
PAGES_DIR = os.path.join(CONTENT, "pages")
SITEMAP_IDX = SRC + "/sitemap.xml"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

def fetch(u, mb=4):
    with urlopen(Request(u, headers=UA), timeout=60, context=ctx) as r:
        return r.read(mb*1_000_000).decode("utf-8","ignore")

def slugify(s):
    s=unquote(s).lower(); s=re.sub(r"\.html$","",s); s=s.strip("/").split("/")[-1]
    return re.sub(r"[^a-z0-9]+","-",s).strip("-") or "post"

# ---- 1. discover posts ----
print("== discover posts ==")
idx=fetch(SITEMAP_IDX,3); smaps=re.findall(r"<loc>(.*?)</loc>",idx)
for n in range(2,12): smaps.append(f"{SRC}/sitemap{n}.xml")
urls=set()
for s in dict.fromkeys(smaps):
    try:
        for l in re.findall(r"<loc>(.*?)</loc>", fetch(s,4)): urls.add(l)
    except: pass
posts_urls=sorted(u for u in urls if re.search(r"\d{4}/\d{2}/",u) or re.search(r"-\d+\.html$",u) or "/article/" in u)
print(f"  {len(posts_urls)} posts")

# ---- 2. extract images (ANY over-blog image host) ----
OB_HOST=re.compile(r'https?://(?:img\.over-blog-kiwi\.com|image\.over-blog\.com|[^"\'\s]*over-blog[^"\'\s]*\.(?:jpg|jpeg|png|gif|webp))', re.I)
ALLIMG=re.compile(r'src="([^"]+)"|data-src="([^"]+)"|data-original="([^"]+)"', re.I)

def find_images(html):
    found=[]
    # JSON/inline bare urls too
    found += OB_HOST.findall(html)
    for m in ALLIMG.findall(html):
        for g in m:
            if g: found.append(g)
    out=[]
    for u in found:
        if u.startswith("//"): u="https:"+u
        low=u.lower()
        if any(low.endswith(e) for e in (".js",".css",".svg")): continue
        if "/filters:" in low and "https%3a" in low:  # proxied yt thumb
            inner=unquote(u.rsplit("/",1)[-1])
            if inner.startswith("http"): out.append(inner); continue
        if "over-blog" in low: out.append(u)
    return list(dict.fromkeys(out))

def img_basename(u):
    # stable filename from the real file name in the url
    if "image%2f" in u.lower():
        key=unquote(re.search(r'image%2[fF]?/?(.+?)(?:\?|$)', u, re.I).group(1))
        base=key.rstrip("/").split("/")[-1]
    else:
        base=u.split("?")[0].rstrip("/").split("/")[-1]
    base=re.sub(r"\?.*$","",base)
    base=re.sub(r"[^a-z0-9._-]","-",base.lower())
    h=hashlib.sha1(u.encode()).hexdigest()[:8]
    return f"{h}_{base}" if base else f"{h}.jpg"

# ---- 3. scrape + collect ----
print("== scrape + collect images ==")
IMAP={}  # url -> local rel path
posts=[]
for u in posts_urls:
    h=fetch(u,4)
    art=re.search(r'<article[^>]*class="Post[^"]*"[^>]*>(.*?)</article>', h, re.S)
    body=art.group(1) if art else h
    tm=re.search(r'<h1[^>]*class="Post-title"[^>]*>(.*?)</h1>', body, re.S) or re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S)
    title=re.sub(r"<[^>]+>","",tm.group(1)).strip() if tm else slugify(u)
    dm=re.search(r"/(\d{4})/(\d{2})/", u); date=f"{dm.group(1)}-{dm.group(2)}" if dm else ""
    for junk in ["ShareBar","Related","PostPreview","Header","NavSearch","ob-Social","PostMeta"]:
        body=re.sub(r'<div[^>]*class="[^"]*%s[^"]*"[^>]*>.*?</div>'%junk,"",body,flags=re.S)
    body=re.sub(r"<script.*?</script>","",body,flags=re.S)
    body=re.sub(r"<style.*?</style>","",body,flags=re.S)
    imgs=find_images(h)
    posts.append({"slug":slugify(u),"url":u,"title":title,"date":date,"body":body,"images":imgs})
    for im in imgs: IMAP.setdefault(im, img_basename(im))
    print(f"  [{len(imgs):>3}] {title[:46]}")

# ---- 4. download + optimize ----
os.makedirs(IMG_DIR, exist_ok=True)
unique=list(IMAP.items())
print(f"\n== download {len(unique)} unique images ==")
def dl(item):
    url, base=item
    full=os.path.join(IMG_DIR,"full_"+base); thumb=os.path.join(IMG_DIR,"thumb_"+base)
    if os.path.exists(full) and os.path.exists(thumb): return url, base, "cached"
    req=Request(url, headers=UA)
    data=urlopen(req,timeout=60,context=ctx).read()
    open(full,"wb").write(data)
    im=Image.open(full)
    if im.mode in ("RGBA","P"): im=im.convert("RGB")
    t=im.copy(); t.thumbnail((800,800)); t.save(thumb,"JPEG",quality=82)
    f=im.copy(); f.thumbnail((1600,1600)); f.save(full,"JPEG",quality=85)
    return url, base, "ok"
ok=0; fail=0
with ThreadPoolExecutor(max_workers=10) as ex:
    for res in as_completed([ex.submit(dl,it) for it in unique]):
        try:
            url,base,st=res.result(); ok+=1
            if ok%40==0: print(f"  {ok}/{len(unique)}")
        except Exception as e:
            fail+=1; print("  FAIL", e)
print(f"  done ok={ok} fail={fail}")

# ---- 5. rewrite bodies to local + write content ----
def rewrite(body):
    def r(m):
        u=m.group(1)
        if u.startswith("//"): u="https:"+u
        if u in IMAP:
            b=IMAP[u]; return f'src="assets/img/full_{b}" data-full="assets/img/full_{b}" loading="lazy"'
        if "/filters:" in u and "https%3a" in u.lower():
            inner=unquote(u.rsplit("/",1)[-1])
            if inner.startswith("http"): return f'src="{inner}" loading="lazy"'
        return m.group(0)
    body=re.sub(r'(?:src|data-src|data-original)="([^"]*over-blog[^"]*|(?<!")https?://[^"\']*\.(?:jpg|jpeg|png|gif|webp)[^"]*)"', r, body, flags=re.I)
    # parent <a href> wrapping over-blog images
    body=re.sub(r'href="(https?://[^"]*over-blog[^"]*)"',
                lambda m: f'href="assets/img/full_{IMAP[m.group(1)]}"' if m.group(1) in IMAP else m.group(0), body, flags=re.I)
    # internal links to other posts
    body=re.sub(r'href="https://artiste-peintre-lepointre\.over-blog\.com/([^"]+)"',
                lambda m: f'href="posts/{slugify(m.group(1))}.html"', body)
    return body

if os.path.exists(POSTS_DIR): shutil.rmtree(POSTS_DIR)
os.makedirs(POSTS_DIR)
for p in posts:
    b=rewrite(p["body"])
    md=f"---\ntitle: {json.dumps(p['title'],ensure_ascii=False)}\ndate: {p['date']}\n---\n\n{b}\n"
    open(os.path.join(POSTS_DIR,p["slug"]+".md"),"w",encoding="utf-8").write(md)

# ---- 6. site.json (keep existing featured if present) ----
sj=os.path.join(CONTENT,"site.json")
if os.path.exists(sj):
    site=json.load(open(sj,encoding="utf-8"))
else:
    site={"artist":"Le Pointre","tagline":"Peintre. Toiles, portraits et expositions.",
          "hero_image":"","accent":"#e23b2e","featured":[]}
# auto-feature top-8 by image count if empty
if not site.get("featured"):
    ranked=sorted(posts,key=lambda x:len(x["images"]),reverse=True)
    site["featured"]=[p["slug"] for p in ranked[:8]]
json.dump(site, open(sj,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"\n== DONE: {len(posts)} posts, {len(unique)} images ({ok} ok, {fail} fail) ==")
print("content/posts written:", len(os.listdir(POSTS_DIR)))
