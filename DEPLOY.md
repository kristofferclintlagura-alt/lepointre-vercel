# Le Pointre — Déploiement & Édition

Projet : `C:\Users\lagur\lepointre-vercel`
- `content/posts/*.md`   → articles (éditables par le client)
- `content/pages/*.md`   → pages À propos / Contact / Boutique
- `content/site.json`     → nom, slogan, photo d'en-tête, couleur, 8 articles en une
- `tools/migrate_full.py` → re-scrape Overblog (à relancer si de nouveaux posts)
- `tools/build.py`        → génère `public/` (le site statique)
- `public/`               → ce qui est déployé (Vercel sert ce dossier)

## 1. Préparer un repo GitHub (nécessaire pour l'édition client)
1. Créez un repo sur github.com (ex: `lagur/lepointre-vercel`).
2. Dans le dossier `lepointre-vercel` :
   git init && git add -A && git commit -m "init" && git branch -M main
   git remote add origin https://github.com/<user>/<repo>.git && git push -u origin main
3. Dans `admin/config.yml`, remplacez :
   repo: <YOUR_GITHUB_USER>/<YOUR_REPO>  →  repo: lagur/lepointre-vercel

## 2. Déployer sur Vercel (gratuit, domaine gratuit)
- Allez sur vercel.com → "Add New" → "Project" → importez le repo GitHub.
- Paramètres détectés automatiquement via `vercel.json` :
  - Build: `python tools/build.py`
  - Output: `public`
- Cliquez "Deploy". Le site est en ligne (URL *.vercel.app gratuite).

## 3. Brancher le domaine www.lepointre.com (payant chez le registraire, gratuit chez Vercel)
1. Dans Vercel : Project → Settings → Domains → ajoutez `www.lepointre.com`.
2. Vercel donne 2 enregistrements DNS. Chez le registraire du domaine, ajoutez :
   - CNAME  www  →  votre-site.vercel.app
   - (Vercel fournit aussi un A record ou ALIAS selon le cas)
3. Attendez la propagation (quelques minutes à 24h). Le HTTPS est automatique.

## 4. Le client édite sans code (Decap CMS)
- Une fois déployé, ouvrez `https://<votre-site>/admin/`.
- Connexion avec le compte GitHub qui a accès au repo.
- Le client peut : modifier un article, changer le texte des pages, éditer le nom/couleur/photo d'en-tête, et choisir les 8 articles de l'accueil.
- À chaque "enregistrement", Vercel reconstruit et republie le site automatiquement.
- Pour ajouter une NOUVELLE image : déposez-la dans `assets/img/` (via le gestionnaire de médias de Decap, ou à la main), puis référencez-la dans l'article.

## 5. Ajouter de nouveaux posts depuis Overblog plus tard
- Relancer : `python tools/migrate_full.py`  (scrape tout, télécharge les nouveaux)
- Puis : `python tools/build.py`
- `git add -A && git commit -m "update" && git push` → Vercel redéploie.

## 6. Monétisation future (boutique / pricing)
- `content/pages/shop.md` est prêt. Brancher Stripe ou Snipcart :
  ajouter un bouton + prix par œuvre, sans refonte.

## Notes techniques
- Images optimisées en JPEG (plein écran ≤1600px, vignette 800px) → site léger.
- Design "Manifesto" : fond charcoal, typographie stencil (Oswald), tuiles légèrement pivotées.
- 100% responsive (1 colonne mobile, 2 tablette, 4 desktop).
- 792 œuvres migrées, 0 image manquante, 0 dépendance à Overblog.
