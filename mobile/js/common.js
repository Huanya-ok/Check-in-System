const API_BASE = window.APP_CONFIG.API_BASE;

function getToken() {
  return localStorage.getItem('token') || '';
}

function setAuth(token, user) {
  localStorage.setItem('token', token);
  if (user) {
    localStorage.setItem('username', user.username || '');
    localStorage.setItem('name', user.name || '');
    localStorage.setItem('role', user.role || 'student');
  }
}

function clearAuth() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('name');
  localStorage.removeItem('role');
}

function getRole() {
  return localStorage.getItem('role') || 'student';
}

function isTeacher() {
  return isLoggedIn() && getRole() === 'teacher';
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function isLoggedIn() {
  return !!getToken();
}

async function logout() {
  const token = getToken();
  if (token) {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: authHeaders(),
      });
    } catch (_) {
      /* 网络失败仍清除本地登录态 */
    }
  }
  clearAuth();
}
