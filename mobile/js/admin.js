const API_BASE = '/api';

let token = localStorage.getItem('token') || '';

const loginSection = document.getElementById('loginSection');
const adminPanel = document.getElementById('adminPanel');

function authHeaders() {
  return { Authorization: `Bearer ${token}` };
}

function showPanel(loggedIn) {
  loginSection.hidden = loggedIn;
  adminPanel.hidden = !loggedIn;
  if (loggedIn) loadFaces();
}

document.getElementById('btnLogin').addEventListener('click', async () => {
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    alert('登录失败');
    return;
  }
  const data = await res.json();
  token = data.access_token;
  localStorage.setItem('token', token);
  showPanel(true);
});

document.getElementById('btnLogout').addEventListener('click', () => {
  token = '';
  localStorage.removeItem('token');
  showPanel(false);
});

document.querySelectorAll('.tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    const name = tab.dataset.tab;
    document.getElementById('tabFaces').hidden = name !== 'faces';
    document.getElementById('tabRecords').hidden = name !== 'records';
    if (name === 'records') loadRecords();
  });
});

async function loadFaces() {
  const res = await fetch(`${API_BASE}/faces`, { headers: authHeaders() });
  if (!res.ok) return;
  const faces = await res.json();
  const list = document.getElementById('faceList');
  list.innerHTML = faces.map((f) =>
    `<li><span>${f.name} (${f.employee_no})</span>
     <button onclick="deleteFace(${f.id})">删除</button></li>`
  ).join('');
}

window.deleteFace = async (id) => {
  if (!confirm('确认删除？')) return;
  await fetch(`${API_BASE}/faces/${id}`, { method: 'DELETE', headers: authHeaders() });
  loadFaces();
};

document.getElementById('btnAddFace').addEventListener('click', async () => {
  const name = document.getElementById('faceName').value.trim();
  const employee_no = document.getElementById('faceEmployeeNo').value.trim();
  const file = document.getElementById('facePhoto').files[0];
  if (!name || !employee_no || !file) {
    alert('请填写完整信息并选择照片');
    return;
  }
  const form = new FormData();
  form.append('name', name);
  form.append('employee_no', employee_no);
  form.append('photo', file);
  const res = await fetch(`${API_BASE}/faces`, { method: 'POST', headers: authHeaders(), body: form });
  if (!res.ok) {
    const err = await res.json();
    alert(err.detail || '添加失败');
    return;
  }
  document.getElementById('faceName').value = '';
  document.getElementById('faceEmployeeNo').value = '';
  document.getElementById('facePhoto').value = '';
  loadFaces();
});

async function loadRecords() {
  const date = document.getElementById('recordDate').value;
  let url = `${API_BASE}/check-in/records`;
  if (date) url += `?date=${date}`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) return;
  const records = await res.json();
  const list = document.getElementById('recordList');
  list.innerHTML = records.map((r) =>
    `<li><span>${r.name} (${r.employee_no})</span>
     <span>${new Date(r.check_in_time).toLocaleString()} · ${(r.similarity_score * 100).toFixed(1)}%</span></li>`
  ).join('') || '<li>暂无记录</li>';
}

document.getElementById('btnLoadRecords').addEventListener('click', loadRecords);

if (token) showPanel(true);
