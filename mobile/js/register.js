const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const preview = document.getElementById('preview');
const btnCapture = document.getElementById('btnCapture');
const fileInput = document.getElementById('fileInput');
const btnRegister = document.getElementById('btnRegister');
const resultEl = document.getElementById('result');

let photoBlob = null;

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    });
    video.srcObject = stream;
  } catch {
    showResult('无法访问摄像头，请使用相册上传', false);
  }
}

function setPhoto(blob) {
  photoBlob = blob;
  preview.src = URL.createObjectURL(blob);
  preview.hidden = false;
  video.hidden = true;
}

function showResult(message, success) {
  resultEl.hidden = false;
  resultEl.textContent = message;
  resultEl.className = 'result ' + (success ? 'success' : 'error');
}

btnCapture.addEventListener('click', () => {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  canvas.toBlob((blob) => setPhoto(blob), 'image/jpeg', 0.9);
});

fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) setPhoto(file);
});

btnRegister.addEventListener('click', async () => {
  const name = document.getElementById('name').value.trim();
  const studentNo = document.getElementById('studentNo').value.trim();
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;

  if (!name || !studentNo || !username || !password || !photoBlob) {
    showResult('请填写完整信息并上传人脸照片', false);
    return;
  }

  btnRegister.disabled = true;
  const form = new FormData();
  form.append('name', name);
  form.append('student_no', studentNo);
  form.append('username', username);
  form.append('password', password);
  form.append('photo', photoBlob, 'face.jpg');

  try {
    const res = await fetch(`${API_BASE}/auth/register`, { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) {
      showResult(data.detail || '注册失败', false);
      return;
    }
    setAuth(data.access_token, { username: data.username, name: data.name, role: 'student' });
    showResult(`${data.message}，即将跳转...`, true);
    setTimeout(() => { window.location.href = 'records.html'; }, 1500);
  } catch {
    showResult('网络错误，请稍后重试', false);
  } finally {
    btnRegister.disabled = false;
  }
});

startCamera();
