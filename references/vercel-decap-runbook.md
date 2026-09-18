# Vercel + Decap CMS deploy runbook (Overblog migrations)

Reusable, copy-pasteable handoff for the client. Adjust repo/handle/URLs.

## Prereqs the client must create (secrets/accounts only they own)
1. **GitHub repo** (Public): `github.com → ＋ → New repository → name=lepointre-vercel → Public → no README`.
2. **GitHub PAT** (classic, scope `repo`): Settings → Developer settings → PAT → Generate. Used only for the one `git push`.
3. **GitHub OAuth App** (for client editing): Settings → Developer settings → **OAuth Apps** → New OAuth App.
   - Application name: `Le Pointre CMS`
   - Homepage URL: `https://<site>.vercel.app`
   - Authorization callback URL: `https://<site>.vercel.app/admin/`
   - Copy **Client ID** → paste into `admin/config.yml` `client_id:`.

## Push (run on the project machine)
```bash
cd C:/Users/lagur/lepointre-vercel
git remote add origin https://github.com/<USER>/<REPO>.git   # already set in our project
git branch -M main
git push -u origin main
# username: <USER>   password: <PASTE PAT>  (no echo — paste blind)
```

## Deploy (Vercel dashboard — PREFERRED, no token/terminal needed)
- vercel.com → Add New → Project → import `lepointre-vercel` (already in your GitHub).
- Vercel reads `vercel.json`. **Do NOT use `@vercel/static`** — it fails silently on the free tier and serves nothing. Keep only `@vercel/node` for the API route; Vercel serves `public/` as the project root automatically.
  **Do NOT add `cleanUrls`** — it 302-redirect-loops every `.html` page.
- Deploy. Live at `https://<site>.vercel.app`.
- (CLI alternative only if you have a stored Vercel token: `npx vercel --prod`. It is interactive and awkward for a non-technical user — prefer the dashboard.)

## 🔴 CRITICAL: `public/` must NOT be in `.gitignore`
If `.gitignore` contains `public/`, Vercel deploys from git and the built files never reach Vercel's servers — every page returns 404 NOT_FOUND.

**Fix before deploying:**
```bash
# remove public/ from .gitignore
sed -i '/^public\//d' .gitignore
# force-add (in case it was previously ignored)
git add -f public/
git commit -m "fix: unignore public/ so Vercel serves static files"
git push
```

Verify with `git ls-files public/ | wc -l` — should show hundreds of files, not 0.

## 🔴 CRITICAL: Decap CMS on Vercel needs a custom `/api/auth` serverless function
Vercel does **not** provide a native OAuth backend like Netlify's Git Gateway. Decap CMS's default `/auth` route does not exist on a Vercel-hosted static site — clicking "Login" returns a 404 on `/auth?provider=github`.

**Fix:** create a Vercel serverless function at `api/auth.js` that:
1. On `GET /api/auth` → redirects to GitHub's OAuth authorize URL
   (`https://github.com/login/oauth/authorize?client_id=...&redirect_uri=...&scope=public_repo`)
2. On `GET /api/auth/callback` → exchanges the `code` for an access token via
   `https://github.com/login/oauth/access_token`, then returns a popup-closure script
   that posts the token to the CMS opener

Update `admin/config.yml` to point `base_url` at the site (the CMS posts to GitHub directly; the auth function only handles the OAuth handshake).

## 🔴 CRITICAL: Vercel free tier blocks Environment Variables (requires Pro)
Trying to add `GITHUB_CLIENT_SECRET` in Vercel → Settings → Environment Variables prompts an upgrade to Pro. The free (Hobby) plan does **not** include Environment Variables.

**Workarounds:**
- Use a **PKCE-based OAuth flow** (no client secret required)
- Or store the secret in a way the function can read without Vercel env vars

Do not rely on Vercel env vars for secrets on the free tier.

## Custom domain www.lepointre.com
- Vercel → Project → Settings → Domains → add `www.lepointre.com`.
- Add the 2 DNS records Vercel shows at the registrar (usually `CNAME www → <site>.vercel.app`).
- HTTPS issued automatically. Domain itself ~$10/yr at registrar; hosting + connection free.

## Client editing (Decap CMS)
- Visit `https://<site>/admin/` → log in via the OAuth App (GitHub account that owns repo).
- Edits posts/pages/branding/featured-8 → save → Vercel rebuilds + republishes.

## Re-migrate later
```bash
python tools/migrate_full.py    # re-scrape Overblog + refresh content/ + assets/img
python tools/build.py           # regenerate public/
git add -A && git commit -m update && git push
```

## Gotchas
- `/admin` shows "No client_id" if the OAuth App Client ID isn't in `config.yml`. #1 failure.
- Decap needs the repo **Public** (free tier) for GitHub backend.
- Vercel free: 100 GB bandwidth/mo — fine for ~800 optimized JPEGs.
- `git push` from a clean machine needs the PAT every time (no stored credential here).
- **Never set Vercel `cleanUrls:true`** with hand-authored `.html` pages — post pages 302-redirect-loop.
- Text-only posts (Contact, About) render a styled placeholder tile, not a broken image. Don't "fix" it by forcing `src=""`.
- **`@vercel/static` fails silently on free tier** — remove it from `vercel.json`. Let Vercel serve `public/` as root.
- **Decap on Vercel needs `/api/auth`** — there is no native OAuth backend. Without it, login 404s.
- **Vercel free tier has no Environment Variables** — use PKCE or another secret mechanism.