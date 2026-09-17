// api/auth.js — Vercel Serverless Function: GitHub OAuth handshake for Decap CMS
// Route: https://lepointre-vercel.vercel.app/api/auth  (also /api/auth/callback via query)
// Environment: set GITHUB_CLIENT_ID + GITHUB_CLIENT_SECRET in Vercel → Project Settings → Env Vars → "Production"

const CLIENT_ID = process.env.GITHUB_CLIENT_ID || 'Ov23li0JGrhXeyNWOw0a';
const CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET || '';
const BASE_URL = process.env.BASE_URL || 'https://lepointre-vercel.vercel.app';

module.exports = async (req, res) => {
  const { url, method, query, headers } = req;

  // Step 1: redirect user to GitHub for authorization
  if (url.startsWith('/api/auth') && method === 'GET' && !query.code) {
    const ghUrl =
      'https://github.com/login/oauth/authorize' +
      '?client_id=' + CLIENT_ID +
      '&redirect_uri=' + encodeURIComponent(BASE_URL + '/api/auth/callback') +
      '&scope=public_repo' +
      '&state=' + encodeURIComponent(query.state || '');
    return res.writeHead(302, { Location: ghUrl }).end();
  }

  // Step 2: GitHub redirects back to /api/auth/callback?code=.... → exchange for access_token
  if (url.startsWith('/api/auth/callback') && method === 'GET' && query.code) {
    const params = new URLSearchParams();
    params.append('client_id', CLIENT_ID);
    params.append('client_secret', CLIENT_SECRET);
    params.append('code', query.code);
    params.append('redirect_uri', BASE_URL + '/api/auth/callback');

    const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'decap-cms-oauth',
      },
      body: params.toString(),
    });
    const tokenJson = await tokenRes.json();

    if (tokenJson.error) {
      return res.statusCode === 500
        ? res.writeHead(500).end(tokenJson.error_description || tokenJson.error)
        : res.writeHead(500).end(JSON.stringify(tokenJson));
    }

    const accessToken = tokenJson.access_token;

    // Step 3: call GitHub /user to get the user's GitHub username
    const userRes = await fetch('https://api.github.com/user', {
      headers: { Authorization: 'Bearer ' + accessToken, Accept: 'application/vnd.github+json' },
    });
    const userJson = await userRes.json();
    const username = userJson.login;

    // Step 4: build the Decap CMS popup response (JWT returned via postMessage)
    const popupHtml = '<!DOCTYPE html><html><head><title>Auth Complete</title></head><body>'
      + '<script>'
      + '  function receiveMessage(event) {'
      + '    if (event.data && event.data.type === "cms:authentication") {'
      + '      event.source.postMessage({'
      + '        type: "cms:token",'
      + '        token: "' + accessToken + '",'
      + '        provider: "github",'
      + '        user: "' + username + '"'
      + '      }, event.origin);'
      + '    }'
      + '  }'
      + '  window.addEventListener("message", receiveMessage);'
      + '  window.opener.postMessage({type: "cms:authentication"}, window.location.origin);'
      + '</script>'
      + '<p>Authentication complete. You can close this window.</p>'
      + '</body></html>';

    res.setHeader('Content-Type', 'text/html');
    return res.writeHead(200).end(popupHtml);
  }

  // fallback
  res.statusCode = 404;
  res.end('Not found');
};

// Required so Vercel treats this as a serverless function (API route)
export const config = {
  api: { bodyParser: false },
};
