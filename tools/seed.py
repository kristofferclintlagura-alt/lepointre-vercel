#!/usr/bin/env python3
"""Seed editable content files from the already-migrated static site.
Reads C:\\Users\\lagur\\lepointre-migrate\\site and writes:
  content/posts/<slug>.md   (frontmatter + HTML body, client-editable)
  content/pages/about.md, contact.md, shop.md
  content/site.json         (branding + featured 8)
"""
import os, re, json

SRC = r"C:\Users\lagur\lepointre-migrate\site"
OUT = r"C:\Users\lagur\lepointre-vercel"
POSTSDIR = os.path.join(OUT, "content", "posts")
PAGESDIR = os.path.join(OUT, "content", "pages")
os.makedirs(POSTSDIR, exist_ok=True)
os.makedirs(PAGESDIR, exist_ok=True)

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()

# ---- convert posts ----
src_posts = os.path.join(SRC, "posts")
n = 0
for fn in os.listdir(src_posts):
    if not fn.endswith(".html"):
        continue
    slug = fn[:-5]
    html = open(os.path.join(src_posts, fn), encoding="utf-8").read()
    m = re.search(r'<article class="post-body">(.*?)</article>', html, re.S)
    if not m:
        continue
    art = m.group(1)
    # date from meta p
    dm = re.search(r'<p class="meta"[^>]*>(.*?)</p>', art, re.S)
    date = strip_tags(dm.group(1)) if dm else ""
    # title from h1
    tm = re.search(r'<h1>(.*?)</h1>', art, re.S)
    title = strip_tags(tm.group(1)) if tm else slug
    # body = after the h1 close
    if tm:
        body = art[tm.end():]
    else:
        body = art
    # unwrap the article wrapper leftover
    body = body.strip()
    md = f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\ndate: {date}\n---\n\n{body}\n"
    with open(os.path.join(POSTSDIR, slug + ".md"), "w", encoding="utf-8") as f:
        f.write(md)
    n += 1
print(f"converted {n} posts -> {POSTSDIR}")

# ---- default pages ----
about = """---
title: À propos
---
# Le Pointre

Artiste peintre. Toiles, portraits et expositions — une rétrospective vivante.

*Contenu à remplir : biographie, parcours, démarche artistique.*

Le site a été migré automatiquement depuis Overblog en conservant l’ensemble des œuvres publiées.
"""
contact = """---
title: Contact
---
# Contact

Pour commission, exposition ou acquisition : *à renseigner*.

Formulaire ou email à ajouter ici (ex. Formspree gratuit, ou lien mailto).
"""
shop = """---
title: Boutique
---
# Boutique

La vente en ligne (pricing, paiement sécurisé) sera activée ultérieurement.

Chaque œuvre peut recevoir un prix et un bouton d’achat (Stripe / Snipcart)
sans refonte du site.
"""
for name, text in [("about", about), ("contact", contact), ("shop", shop)]:
    with open(os.path.join(PAGESDIR, name + ".md"), "w", encoding="utf-8") as f:
        f.write(text)
print("wrote pages:", [p + ".md" for p in ("about","contact","shop")])

# ---- site.json (configurable branding + featured 8) ----
# pick 8 iconic/visual posts (most imagery + recognizable series)
featured = [
    "buffone-paintings",
    "ces-gens-qui-ne-sont-rien-e-macron",
    "franchine-2024-paris-jo-des-qr-code",
    "mother-earth-is-fed-up-with-human-beings",
    "non-au-pass-sanitaire",
    "vaccinal-en-manifs",
    "theatre-occupe-pendant-le-confinement-affiches-le-pointre",
    "paintings-on-new-york-walls-serie-elephants",
]
site = {
    "artist": "Le Pointre",
    "tagline": "Peintre. Toiles, portraits et expositions.",
    "hero_image": "",  # set to "assets/img/hero.jpg" when the real portrait arrives
    "accent": "#e23b2e",
    "featured": featured,
}
with open(os.path.join(OUT, "content", "site.json"), "w", encoding="utf-8") as f:
    json.dump(site, f, ensure_ascii=False, indent=2)
print("wrote content/site.json")
