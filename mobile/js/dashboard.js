const loginSection = document.getElementById('loginSection');
const dashboardPanel = document.getElementById('dashboardPanel');
const loginResult = document.getElementById('loginResult');
const userInfo = document.getElementById('userInfo');

function showLoginResult(message, success) {
  loginResult.hidden = false;
  loginResult.textContent = message;
  loginResult.className = 'result ' + (success ? 'success' : 'error');
}

function showDashboard() {
  loginSection.hidden = true;
  dashboardPanel.hidden = false;
  const name = localStorage.getItem('name') || '';
  userInfo.textContent = `${name} · 签到总览`;
  if (!document.getElementById('overviewDate').value) {
    document.getElementById('overviewDate').value = new Date().toISOString().slice(0, 10);
  }
  loadOverview();
}

async function loadOverview() {
  const date = document.getElementById('overviewDate').value;
  let url = `${API_BASE}/teacher/overview`;
  if (date) url += `?date=${date}`;

  const res = await fetch(url, { headers: authHeaders() });
  if (res.status === 401 || res.status === 403) {
    clearAuth();
    loginSection.hidden = false;
    dashboardPanel.hidden = true;
    showLoginResult('请使用教师账号登录', false);
    return;
  }
  if (!res.ok) return;

  const data = await res.json();
  document.getElementById('statTotal').textContent = data.total_registered;
  document.getElementById('statChecked').textContent = data.checked_in_count;
  document.getElementById('statAbsent').textContent = data.absent_count;

  const checkedList = document.getElementById('checkedList');
  checkedList.innerHTML = data.records.length
    ? data.records.map((r) =>
        `<li>
          <span>${r.name}（${r.student_no}）</span>
          <span>${new Date(r.check_in_time).toLocaleTimeString()} · ${(r.similarity_score * 100).toFixed(0)}%</span>
        </li>`
      ).join('')
    : '<li class="empty">当日暂无签到</li>';

  const absentList = document.getElementById('absentList');
  absentList.innerHTML = data.absent_students.length
    ? data.absent_students.map((s) =>
        `<li><span>${s.name}</span><span>${s.student_no}</span></li>`
      ).join('')
    : '<li class="empty">全员已签到</li>';
}

document.getElementById('btnLogin').addEventListener('click', async () => {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  if (!username || !password) {
    showLoginResult('请输入账号和密码', false);
    return;
  }

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) {
    showLoginResult(data.detail || '登录失败', false);
    return;
  }
  if (data.role !== 'teacher') {
    showLoginResult('该账号不是教师账号', false);
    return;
  }
  setAuth(data.access_token, { username: data.username, name: data.name, role: data.role });
  showDashboard();
});

document.getElementById('btnRefresh').addEventListener('click', loadOverview);

document.getElementById('btnLogout').addEventListener('click', async () => {
  await logout();
  loginSection.hidden = false;
  dashboardPanel.hidden = true;
  userInfo.textContent = '查看全班签到情况';
  loginResult.hidden = true;
});

if (isTeacher()) {
  showDashboard();
}
