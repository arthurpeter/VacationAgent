const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export function setTokens(accessToken, refreshToken) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Main fetch function
export async function fetchWithAuth(url, body = {}, method = "POST") {
  let accessToken = getAccessToken();

  if (!accessToken) {
    clearTokens();
    window.location.href = "/login";
    return null;
  }

  // Try request with access token
  let res = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
    body: JSON.stringify(body),
  });

  // If unauthorized, try to refresh
  if (res.status === 401) {
    const refreshToken = getRefreshToken();
    // Try to refresh
    const refreshRes = await fetch("http://localhost:5000/auth/refresh", {
      method: "POST",
      headers: { "Authorization": `Bearer ${refreshToken}` },
    });

    if (refreshRes.ok) {
      const tokens = await refreshRes.json();
      setTokens(tokens.access_token, tokens.refresh_token);
      // Retry original request with new access token
      accessToken = tokens.access_token;
      res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`,
        },
        body: JSON.stringify(body),
      });
      if (res.status === 401) {
        clearTokens();
        redirectToLogin();
        return null;
      }
    } else {
      clearTokens();
      redirectToLogin();
      return null;
    }
  }

  // If still unauthorized, redirect
  if (res.status === 401) {
    clearTokens();
    window.location.href = "/login";
    return null;
  }

  return res.json();
}
