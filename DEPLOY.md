# Le Pointre — Déploiement & Édition (Vercel + GitHub)

Projet local : `C:\Users\lagur\lepointre-vercel`
- `content/posts/*.md`   → articles (éditables par le client)
- `content/pages/*.md`   → pages À propos / Contact / Boutique
- `content/site.json`     → nom, slogan, photo d'en-tête, couleur, 8 articles en une
- `tools/migrate_full.py` → re-scrape Overblog (relancer si nouveaux posts)
- `tools/build.py`        → génère `public/` (le site statique)
- `public/`               → ce que Vercel sert (généré automatiquement au déploi)
- `admin/`                → Decap CMS (édition client sans code)

GitHub : **kristofferclintlagura-alt** · repo : **lepointre-vercel**

## 1. Créer le repo GitHub (vide)
- github.com → ＋ → New repository → nom `lepointre-vercel` → **Public** →
  ne PAS ajouter README/.gitignore → Create.
- Le remote est déjà configuré en local :
  `https://github.com/kristofferclintlagura-alt/lepointre-vercel.git`

## 2. Créer le GitHub OAuth App (OBLIGATOIRE pour l'édition client sur Vercel)
Decap CMS se connecte via GitHub : il faut une "OAuth App" gratuite.
- github.com → avatar → Settings → Developer settings → **OAuth Apps** → New OAuth App.
- **Application name :** Le Pointre CMS
- **Homepage URL :** `https://lepointre-vercel.vercel.app`
- **Authorization callback URL :** `https://lepointre-vercel.vercel.app/admin/`
  (remplacez par votre URL Vercel réelle, ou votre domaine www.lepointre.com plus tard)
- Create → copiez le **Client ID**.
- Dans `admin/config.yml`, remplacez :
  `client_id: <YOUR_GITHUB_OAUTH_CLIENT_ID>` → `client_id: <le-client-id-copié>`
  et ajustez `base_url:` si vous utilisez un domaine custom.
- `git add admin/config.yml && git commit -m "oauth client_id" && git push`

## 3. Pousser le code (a besoin de votre PAT)
Créez un PAT (Settings → Developer settings → Personal access tokens → classic →
cocher `repo`) puis dans le terminal :
```
cd C:/Users/lagur/lepointre-vercel
git push -u origin main
```
Identifiant : `kristofferclintlagura-alt` · Mot de passe : **collez le PAT** (il ne s'affiche pas).

## 4. Déployer sur Vercel (gratuit)
- vercel.com → Add New → Project → importez `lepointre-vercel`.
- Vercel lit `vercel.json` : Build `python tools/build.py`, Output `public`.
- Deploy. URL : `https://lepointre-vercel.vercel.app` (gratuite).

## 5. Brancher www.lepointre.com (gratuit chez Vercel, payant au registraire)
- Vercel : Project → Settings → Domains → ajoutez `www.lepointre.com`.
- Ajoutez les 2 enregistrements DNS fournis chez le registraire (CNAME www → …).
- HTTPS automatique.

## 6. Le client édite sans code (Decap CMS)
- Ouvrez `https://lepointre-vercel.vercel.app/admin/` (ou `/admin/` sur le domaine).
- Connexion via l'OAuth App GitHub (compte kristofferclintlagura-alt).
- Le client peut : modifier articles, pages, nom/couleur/photo d'en-tête, choisir
  les 8 articles de l'accueil. À chaque enregistrement, Vercel republie.

## 7. Mises à jour futures
- Nouveaux posts Overblog : `python tools/migrate_full.py` puis
  `python tools/build.py` puis `git add -A && git commit -m up && git push`.
- Édition client via /admin/ → redéploiement auto.

## 8. Monétisation (boutique / pricing)
- `content/pages/shop.md` prêt. Brancher Stripe/Snipcart sans refonte.

## Notes
- Images optimisées JPEG (plein écran ≤1600px, vignette 800px). 792 œuvres migrées.
- Design "Manifesto" : fond charcoal, Oswald (stencil), tuiles légèrement pivotées.
- 100% responsive (1 mobile / 2 tablette / 4 desktop).
- 0 image manquante, 0 dépendance Overblog.
