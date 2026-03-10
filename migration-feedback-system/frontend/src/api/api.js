const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/+$/, "");

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

export function validateToken(token) {
  return request(`/api/feedback/validate?token=${encodeURIComponent(token)}`);
}

export function submitFeedback(payload) {
  return request("/api/feedback/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function adminLogin(username, password) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function adminSignup(username, display_name, password) {
  return request("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ username, display_name, password }),
  });
}

function authHeaders() {
  const token = sessionStorage.getItem("admin_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getDashboardSummary() {
  return request("/api/dashboard/summary", { headers: authHeaders() });
}

export function getLeaderboard() {
  return request("/api/dashboard/leaderboard", { headers: authHeaders() });
}

export function getRecentFeedbacks(limit = 50) {
  return request(`/api/dashboard/feedbacks?limit=${limit}`, { headers: authHeaders() });
}

export function getDailyTrends(startDate, endDate) {
  let url = "/api/dashboard/trends";
  if (startDate && endDate) {
    url += `?start_date=${startDate}&end_date=${endDate}`;
  }
  return request(url, { headers: authHeaders() });
}
