const ACCESS_TOKEN_KEY = "access_token";

export function setTokens(accessToken) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
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
    // Try to refresh
    const refreshRes = await fetch("http://localhost:5000/auth/refresh", {
      method: "POST",
      credentials: "include",
    });

    if (refreshRes.ok) {
      const tokens = await refreshRes.json();
      setTokens(tokens.access_token);
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

  return res;
}
