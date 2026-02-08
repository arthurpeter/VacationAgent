const ACCESS_TOKEN_KEY = "access_token";

// Helper function to get cookie value by name
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

// Get CSRF token from cookies
export function getCSRFToken() {
  return getCookie('csrf_refresh_token');
}

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
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
    },
  };

  if (method !== "GET" && method !== "HEAD") {
    options.body = JSON.stringify(body);
  }

  let res = await fetch(url, options);

  // If unauthorized, try to refresh
  if (res.status === 401 || res.status === 422) {
    // Try to refresh
    const csrfToken = getCSRFToken();
    const refreshHeaders = {
      "Content-Type": "application/json"
    };
    
    // Add CSRF token header if available
    if (csrfToken) {
      refreshHeaders["X-CSRF-TOKEN-Refresh"] = csrfToken;
    }
    
    const refreshRes = await fetch("http://localhost:5000/auth/refresh", {
      method: "POST",
      headers: refreshHeaders,
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
