const loginHint = document.getElementById('loginHint');
const recordsPanel = document.getElementById('recordsPanel');
const userInfo = document.getElementById('userInfo');
const recordList = document.getElementById('recordList');
const recordDate = document.getElementById('recordDate');

function showLoggedIn() {
  loginHint.hidden = true;
  recordsPanel.hidden = false;
  const name = localStorage.getItem('name') || '';
  const username = localStorage.getItem('username') || '';
  userInfo.textContent = name ? `${name}（${username}）` : username;
  loadRecords(); // 默认加载全部记录
}

async function loadRecords(date = null) {
  let url = `${API_BASE}/check-in/records`;
  if (date) {
    url += `?date=${date}`;
  }

  const res = await fetch(url, { headers: authHeaders() });
  if (res.status === 401) {
    clearAuth();
    window.location.href = 'login.html';
    return;
  }

  const records = await res.json();
  recordList.innerHTML = records.length
    ? records.map((r) =>
        `<li><span>${new Date(r.check_in_time).toLocaleString()}</span></li>`
      ).join('')
    : '<li class="empty">暂无签到记录</li>';
}

// 按日期筛选按钮
document.getElementById('btnLoad').addEventListener('click', () => {
  const date = recordDate.value;
  if (!date) {
    alert('请先选择日期');
    return;
  }
  loadRecords(date);
});

// 查看全部按钮
document.getElementById('btnLoadAll').addEventListener('click', () => {
  recordDate.value = ''; // 清空日期选择
  loadRecords(null);
});

document.getElementById('btnLogout').addEventListener('click', async () => {
  await logout();
  window.location.href = 'login.html';
});

if (isLoggedIn()) {
  showLoggedIn();
}
