const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const preview = document.getElementById('preview');
const btnCamera = document.getElementById('btnCamera');
const btnCapture = document.getElementById('btnCapture');
const btnRetake = document.getElementById('btnRetake');
const fileInput = document.getElementById('fileInput');
const btnRegister = document.getElementById('btnRegister');
const resultEl = document.getElementById('result');
const cameraPlaceholder = document.getElementById('cameraPlaceholder');

let photoBlob = null;
let stream = null;
let isCameraOn = false;

cameraPlaceholder.hidden = false;

// 启动/关闭摄像头
async function toggleCamera() {
  if (isCameraOn) {
    stopCamera();
  } else {
    await startCamera();
  }
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    });
    video.srcObject = stream;
    video.hidden = false;
    cameraPlaceholder.hidden = true;
    preview.hidden = true;
    
    isCameraOn = true;
    btnCamera.textContent = '关闭摄像头';
    btnCapture.disabled = false;
    
    console.log('[Camera] 摄像头已启动');
  } catch (err) {
    console.error('[Camera] 摄像头启动失败:', err);
    showResult('无法访问摄像头,请使用相册上传', false);
    isCameraOn = false;
    btnCamera.textContent = '启动摄像头';
    btnCapture.disabled = true;
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  
  video.srcObject = null;
  video.hidden = true;
  cameraPlaceholder.hidden = false;
  
  isCameraOn = false;
  btnCamera.textContent = '启动摄像头';
  btnCapture.disabled = true;
  
  console.log('[Camera] 摄像头已关闭');
}

function setPhoto(blob) {
  photoBlob = blob;
  preview.src = URL.createObjectURL(blob);
  preview.classList.add('flipped'); // 拍照的照片也翻转
  preview.hidden = false;
  video.hidden = true;
  cameraPlaceholder.hidden = true;
  btnRetake.hidden = false; // 显示重拍按钮
}

function showResult(message, success) {
  resultEl.hidden = false;
  resultEl.textContent = message;
  resultEl.className = 'result ' + (success ? 'success' : 'error');
}

btnCamera.addEventListener('click', toggleCamera);

btnCapture.addEventListener('click', () => {
  if (!isCameraOn) {
    showResult('请先启动摄像头', false);
    return;
  }
  
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');
  
  // 左右翻转绘制(镜像效果)
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(video, 0, 0);
  
  canvas.toBlob((blob) => setPhoto(blob), 'image/jpeg', 0.9);
});

// 重拍按钮事件
btnRetake.addEventListener('click', () => {
  photoBlob = null;
  preview.hidden = true;
  preview.classList.remove('flipped');
  btnRetake.hidden = true;
  
  if (isCameraOn) {
    // 如果摄像头已开启，返回摄像头画面
    video.hidden = false;
    cameraPlaceholder.hidden = true;
  } else {
    // 如果摄像头未开启，显示占位符
    video.hidden = true;
    cameraPlaceholder.hidden = false;
  }
});

fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  // 从相册上传的照片不翻转
  photoBlob = file;
  preview.src = URL.createObjectURL(file);
  preview.classList.remove('flipped'); // 确保没有翻转类
  preview.hidden = false;
  video.hidden = true;
  cameraPlaceholder.hidden = true;
  btnRetake.hidden = false; // 显示重拍按钮
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
    showResult(`${data.message},即将跳转...`, true);
    setTimeout(() => { window.location.href = 'records.html'; }, 1500);
  } catch {
    showResult('网络错误,请稍后重试', false);
  } finally {
    btnRegister.disabled = false;
  }
});

// 页面加载时自动启动摄像头
// startCamera();
