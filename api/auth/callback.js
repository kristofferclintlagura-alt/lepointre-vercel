// api/auth/callback.js — handles GitHub redirect with ?code=...
// Reuses same logic as /api/auth

const CLIENT_ID = process.env.GITHUB_CLIENT_ID || 'Ov23li0JGrhXeyNWOw0a';
const CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET || '';
const BASE_URL = process.env.BASE_URL || 'https://lepointre-vercel.vercel.app';

module.exports = async (req, res) => {
  const { query } = req;
  if (!query.code) {
    return res.writeHead(302, { Location: '/api/auth' }).end();
  }

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
    res.statusCode = 500;
    return res.end(tokenJson.error_description || tokenJson.error);
  }

  const accessToken = tokenJson.access_token;

  let username = '';
  try {
    const userRes = await fetch('https://api.github.com/user', {
      headers: { Authorization: 'Bearer ' + accessToken, Accept: 'application/vnd.github+json' },
    });
    const userJson = await userRes.json();
    username = userJson.login;
  } catch (e) {}

  const popupHtml = '<!DOCTYPE html><html><head><title>Auth Complete</title></head><body>'
    + '<script>'
    + 'function receiveMessage(event){'
    + 'if(event.data && event.data.type==="cms:authentication"){'
    + 'event.source.postMessage({type:"cms:token",token:"' + accessToken + '",provider:"github",user:"' + username + '"},event.origin);'
    + '}'
    + '}';
    + 'window.addEventListener("message",receiveMessage);'
    + 'window.opener.postMessage({type:"cms:authentication"},window.location.origin);'
    + '</script><p>Authentication complete. You can close this window.</p>'
    + '</body></html>';

  res.setHeader('Content-Type', 'text/html');
  return res.writeHead(200).end(popupHtml);
};

export const config = { api: { bodyParser: false } };
