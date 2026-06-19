const loginHint = document.getElementById('loginHint');
const recordsPanel = document.getElementById('recordsPanel');
const userInfo = document.getElementById('userInfo');
const recordList = document.getElementById('recordList');

function showLoggedIn() {
  loginHint.hidden = true;
  recordsPanel.hidden = false;
  const name = localStorage.getItem('name') || '';
  const username = localStorage.getItem('username') || '';
  userInfo.textContent = name ? `${name}（${username}）` : username;
  loadRecords();
}

async function loadRecords() {
  const date = document.getElementById('recordDate').value;
  let url = `${API_BASE}/check-in/records`;
  if (date) url += `?date=${date}`;

  const res = await fetch(url, { headers: authHeaders() });
  if (res.status === 401) {
    clearAuth();
    window.location.href = 'login.html';
    return;
  }
  if (!res.ok) return;

  const records = await res.json();
  recordList.innerHTML = records.length
    ? records.map((r) =>
        `<li><span>${new Date(r.check_in_time).toLocaleString()}</span></li>`
      ).join('')
    : '<li class="empty">暂无签到记录</li>';
}

document.getElementById('btnLoad').addEventListener('click', loadRecords);

document.getElementById('btnLogout').addEventListener('click', async () => {
  await logout();
  window.location.href = 'login.html';
});

if (isLoggedIn()) {
  showLoggedIn();
}
