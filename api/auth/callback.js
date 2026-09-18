// api/auth/callback.js - Vercel Serverless Function (Node.js)
// GitHub OAuth callback for Decap CMS. Returns the auth code to the opener
// window (the CMS popup) via postMessage so Decap can complete token exchange.

const BASE_URL = "https://lepointre-vercel.vercel.app";

module.exports = async (req, res) => {
  const url = new URL(req.url, `https://${req.headers.host}`);
  const query = url.searchParams;

  const code = query.get("code");
  const state = query.get("state");

  if (!code) {
    return res.status(400).send("Missing code parameter");
  }

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
};