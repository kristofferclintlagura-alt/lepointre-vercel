# Le Pointre — Client Handover (2026-09-18)

**Site:** https://lepointre-vercel.vercel.app ✅ LIVE
**Target domain:** lepointre.com (pending registration)
**Client:** Michel Cailleau — cailleaumichel@yahoo.fr — +33 7 81 78 56 81

---

## 1. What the client owns

| Item | Value |
|---|---|
| GitHub repo | https://github.com/kristofferclintlagura-alt/lepointre-vercel |
| Vercel project | `lepointre-vercel` (account: kcpl2) |
| Live URL | https://lepointre-vercel.vercel.app |
| Domain | lepointre.com — NOT YET REGISTERED (see §4) |

---

## 2. How the client edits content (no code)

Everything is editable via **Decap CMS** at `/admin/`:

- https://lepointre-vercel.vercel.app/admin/

**What they can change:**
- Posts (articles) — `content/posts/*.md`
- Pages (À propos / Contact / Boutique) — `content/pages/*.md`
- Site settings — artist name, tagline, hero photo, accent colour, which 8 posts appear on the home page — `content/site.json`

**To log in:** click "Login with GitHub" on the admin page and authorise the app.

**Michel's GitHub account:** `lepointrearchive` — https://github.com/lepointrearchive ✅ (account exists)

**You must add him as a collaborator before Monday** (free, 1 minute):
1. Open https://github.com/kristofferclintlagura-alt/lepointre-vercel
2. Click **Settings** → **Collaborators** → **Add collaborator**
3. Type `lepointrearchive`
4. Select **Write** → **Add**
5. He accepts the email invite → he can now log into `/admin/` with his own account

After that, **both of you can edit**. He no longer needs your account.

**After saving:** Vercel rebuilds automatically. Takes ~1-2 minutes.

---

## 3. How to rebuild (if anything looks wrong)

The site is generated from `content/` by a Python script. Run this to rebuild:

```
cd C:\Users\lagur\lepointre-vercel
python tools/build.py
```

Then deploy:

```
vercel deploy --prod
```

Or just `git push` to `main` — Vercel rebuilds on every push automatically.

---

## 4. Domain: lepointre.com

**Status: NOT REGISTERED.** You need to buy it before Monday.

**Recommended registrar (free + simple):** Namecheap — namecheap.com
- Search `lepointre.com`
- Add to cart, checkout (~$12/yr for .com)
- Use your own email (not the client's) as the registrant, then transfer

**Alternative:** GoDaddy, OVH (French, good for a French client), Gandi.

**After buying, point it at Vercel:**
1. Vercel → Project → Settings → Domains → Add domain → `lepointre.com`
2. Vercel gives you DNS records (CNAME / A). Copy them.
3. In the registrar's DNS panel, paste those records exactly.
4. HTTPS is automatic. DNS propagation takes up to 48h but usually 1-4h.

**Also add:** `www.lepointre.com` (same process — Vercel handles both).

---

## 5. Credentials to hand over

| What | Where | Who needs it |
|---|---|---|
| GitHub repo URL | §1 above | Client (read-only link is fine) |
| Vercel project | vercel.com → kcpl2 → lepointre-vercel | You (admin) |
| CMS admin URL | §2 above | Client |
| Domain | §4 | Client (once registered) |

**You keep:** Vercel account admin, GitHub repo owner, domain registrant.
**Client gets:** read access to the repo, the admin URL, the domain URL.

---

## 6. What's NOT included (and what it costs)

- **Vercel Hobby = free forever.** Works for this site. Limits: 100 deploys/day, 100GB bandwidth/month, 1-min serverless function timeout. Fine for an artist's portfolio.
- **If the client wants their own Vercel account** later, the whole project can be transferred (Vercel → Settings → Transfer). Free.
- **If the client wants to edit from their own GitHub account**, they need to be added as a collaborator on the repo. Free.
- **Email addresses** (e.g. contact@lepointre.com) are not set up. Costs extra at most registrars.

---

## 7. Handover meeting checklist

- [ ] Confirm site works: open https://lepointre-vercel.vercel.app on their phone
- [ ] Show them `/admin/` and log in
- [ ] Walk through editing one post (change a title, save, watch it rebuild)
- [ ] Confirm the domain is registered and the DNS is pointing
- [ ] Give them the repo URL
- [ ] Answer: "how do I add new artwork?" → upload images to `assets/img/`, then edit the post in the CMS
- [ ] Answer: "how do I change the home page?" → CMS → Paramètres du site → "Articles mis en avant"