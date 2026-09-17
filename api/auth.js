// api/auth.js — Vercel Serverless Function (Node.js)
// Handles GitHub OAuth flow for Decap CMS on Vercel
// Secret managed via Vercel env var GITHUB_CLIENT_SECRET

const GITHUB_CLIENT_ID = "Ov23li0JGrhXeyNWOw0a"; // public client id
const BASE_URL = "https://lepointre-vercel.vercel.app";

module.exports = async (req, res) => {
  const url = new URL(req.url, `https://${req.headers.host}`);
  const query = url.searchParams;

  if (url.pathname === "/api/auth") {
    const state = Math.random().toString(36).slice(2);

    const githubAuthURL = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${encodeURIComponent(BASE_URL + "/api/auth/callback")}&state=${state}&scope=public_repo`;

    return res.writeHead(302, { Location: githubAuthURL }).end();
  }

  if (url.pathname === "/api/auth/callback") {
    const code = query.get("code");

    if (!code) {
      return res.status(400).send("Missing code parameter");
    }

    try {
      const secret = process.env.GITHUB_CLIENT_SECRET;
      if (!secret) {
        console.error("GITHUB_CLIENT_SECRET env var not set");
        return res.status(500).send("Server configuration error");
      }

      const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          client_id: GITHUB_CLIENT_ID,
          client_secret: secret,
          code,
        }),
      });

      const tokenData = await tokenRes.json();

      if (tokenData.error || !tokenData.access_token) {
        console.error("Token exchange error:", tokenData);
        return res.status(401).send(JSON.stringify(tokenData));
      }

      const html = `<!DOCTYPE html>
<html>
<head><title>Authentication complete</title></head>
<body>
<script>
  if (window.opener) {
    window.opener.postMessage({
      provider: 'github',
      token: '${tokenData.access_token}',
      info: { name: 'GitHub User' }
    }, '${BASE_URL}');
  }
  window.close();
</script>
<p>Authentication successful. You can close this window.</p>
</body>
</html>`;
      res.writeHead(200, { "Content-Type": "text/html" });
      return res.end(html);
    } catch (err) {
      console.error("Auth error:", err);
      return res.status(500).send("Internal server error");
    }
  }

  res.status(404).send("Not found");
};
