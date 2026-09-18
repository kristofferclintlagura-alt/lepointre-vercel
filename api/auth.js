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

  if (url.pathname === "/api/auth" || url.pathname === "/api/auth/") {
      const state = Math.random().toString(36).slice(2);

      const githubAuthURL =
        `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}` +
        `&redirect_uri=${encodeURIComponent(BASE_URL + "/api/auth/callback")}` +
        `&state=${state}&scope=public_repo`;

      return res.writeHead(302, { Location: githubAuthURL }).end();
    }

    res.status(404).send("Not found");
  };
