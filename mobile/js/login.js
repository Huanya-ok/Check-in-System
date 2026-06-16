const btnLogin = document.getElementById('btnLogin');
const resultEl = document.getElementById('result');

function showResult(message, success) {
  resultEl.hidden = false;
  resultEl.textContent = message;
  resultEl.className = 'result ' + (success ? 'success' : 'error');
}

btnLogin.addEventListener('click', async () => {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  if (!username || !password) {
    showResult('请输入用户名和密码', false);
    return;
  }

  btnLogin.disabled = true;
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      showResult(data.detail || '登录失败', false);
      return;
    }
    setAuth(data.access_token, { username: data.username, name: data.name, role: data.role });
    showResult('登录成功，即将跳转...', true);
    const target = data.role === 'teacher' ? 'dashboard.html' : 'records.html';
    setTimeout(() => { window.location.href = target; }, 1000);
  } catch {
    showResult('网络错误，请稍后重试', false);
  } finally {
    btnLogin.disabled = false;
  }
});

if (isLoggedIn()) {
  window.location.href = isTeacher() ? 'dashboard.html' : 'records.html';
}
