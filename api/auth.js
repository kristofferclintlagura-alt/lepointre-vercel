// api/auth.js - Vercel Serverless Function (Node.js)
// Handles GitHub OAuth flow for Decap CMS on Vercel (FREE TIER COMPATIBLE)
//
// This approach avoids needing Vercel Environment Variables (which require
// a Pro account) by returning the authorization code directly to the browser
// popup, where Decap CMS handles token exchange via a Personal Access Token
// (PAT) embedded in base64 inside admin/config.yml.

const GITHUB_CLIENT_ID = "Ov23li0JGrhXeyNWOw0a"; // public client id
const BASE_URL = "https://lepointre-vercel.vercel.app";

module.exports = async (req, res) => {
  const url = new URL(req.url, `https://${req.headers.host}`);
  const query = url.searchParams;

  if (url.pathname === "/api/auth") {
    const state = Math.random().toString(36).slice(2);

    const githubAuthURL =
      `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}` +
      `&redirect_uri=${encodeURIComponent(BASE_URL + "/api/auth/callback")}` +
      `&state=${state}&scope=public_repo`;

    return res.writeHead(302, { Location: githubAuthURL }).end();
  }

  if (url.pathname === "/api/auth/callback") {
    const code = query.get("code");
    const state = query.get("state");

    if (!code) {
      return res.status(400).send("Missing code parameter");
    }

    // Return the code back to the opener window (the CMS popup)
    // Decap CMS can handle this via its frontend or we provide a script
    // that injects the code into the CMS flow.
    const html = `<!DOCTYPE html>
<html>
<head><title>Authorization complete</title></head>
<body>
<script>
  if (window.opener) {
    window.opener.postMessage({
      provider: 'github',
      code: '${code}',
      state: '${state || ""}',
      info: { name: 'GitHub User' }
    }, '${BASE_URL}');
  } else {
    document.write('<p>Authorization successful. Please return to the CMS.</p>');
  }
  setTimeout(function() { window.close(); }, 5000);
</script>
<p>Authentication successful. You can close this window.</p>
</body>
</html>`;

    res.writeHead(200, { "Content-Type": "text/html" });
    return res.end(html);
  }

  res.status(404).send("Not found");
};
