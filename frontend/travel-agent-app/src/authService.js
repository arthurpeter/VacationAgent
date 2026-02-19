const ACCESS_TOKEN_KEY = "access_token";

let isRefreshing = false;
let refreshPromise = null;

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

async function refreshAccessToken() {
  if (isRefreshing) {
    return refreshPromise;
  }

  isRefreshing = true;

  refreshPromise = (async () => {
    try {
      const csrfToken = getCSRFToken();
      const refreshHeaders = {
        "Content-Type": "application/json"
      };
      
      if (csrfToken) {
        refreshHeaders["X-CSRF-TOKEN-Refresh"] = csrfToken;
      }
      
      const refreshRes = await fetch("http://localhost:5000/auth/refresh", {
        method: "POST",
        headers: refreshHeaders,
        credentials: "include",
      });

      if (!refreshRes.ok) {
        throw new Error("Refresh failed");
      }

      const tokens = await refreshRes.json();
      setTokens(tokens.access_token);
      return tokens.access_token;
    } catch (error) {
      clearTokens();
      window.location.href = "/login";
      throw error;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
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
  if (res.status === 401 || res.status === 403 || res.status === 422) {
    try {
      // 3. Wait for the singleton refresh to complete and get the new token
      const newAccessToken = await refreshAccessToken();
      
      // 4. RETRY ORIGINAL REQUEST with the new token
      const retryOptions = {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${newAccessToken}`, // Use new token here
        }
      };

      if (method !== "GET" && method !== "HEAD") {
        retryOptions.body = JSON.stringify(body);
      }

      res = await fetch(url, retryOptions);

      // 5. If it fails again even after refresh, log them out
      if (res.status === 401 || res.status === 403 || res.status === 422) {
        clearTokens();
        window.location.href = "/login";
        return null;
      }
    } catch (error) {
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
