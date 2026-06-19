const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const preview = document.getElementById('preview');
const btnCamera = document.getElementById('btnCamera');
const btnCapture = document.getElementById('btnCapture');
const btnRetake = document.getElementById('btnRetake');
const fileInput = document.getElementById('fileInput');
const resultEl = document.getElementById('result');
const cameraPlaceholder = document.getElementById('cameraPlaceholder');

let stream = null;
let isCameraOn = false;

cameraPlaceholder.hidden = false;

// 启动/关闭摄像头
async function toggleCamera() {
  if (isCameraOn) {
    // 关闭摄像头
    stopCamera();
  } else {
    // 启动摄像头
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
    cameraPlaceholder.hidden = true;
    video.hidden = false;
    preview.hidden = true;
    
    isCameraOn = true;
    btnCamera.textContent = '关闭摄像头';
    btnCapture.disabled = false; // 启用拍照按钮
    
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
  cameraPlaceholder.hidden = false;
  video.hidden = true;
  
  isCameraOn = false;
  btnCamera.textContent = '启动摄像头';
  btnCapture.disabled = true; // 禁用拍照按钮
  
  console.log('[Camera] 摄像头已关闭');
}

function showResult(message, success) {
  resultEl.hidden = false;
  resultEl.textContent = message;
  resultEl.className = 'result ' + (success ? 'success' : 'error');
}

async function submitCheckIn(blob, shouldFlip = false) {
  btnCapture.disabled = true;
  resultEl.hidden = false;
  resultEl.textContent = '识别中...';
  resultEl.className = 'result';

  const form = new FormData();
  form.append('photo', blob, 'checkin.jpg');

  try {
    const res = await fetch(`${API_BASE}/check-in`, { method: 'POST', body: form });
    const data = await res.json();
    showResult(data.message, data.success);
  } catch {
    showResult('网络错误,请稍后重试', false);
  } finally {
    cameraPlaceholder.hidden = true;
    btnCapture.disabled = false;
  }
}

function captureFromVideo() {
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
  
  canvas.toBlob(async (blob) => {
    // 预览时也应用翻转样式
    preview.src = URL.createObjectURL(blob);
    preview.classList.add('flipped'); // 添加翻转类
    preview.hidden = false;
    video.hidden = true;
    btnRetake.hidden = false;
    
    await submitCheckIn(blob, true);
  }, 'image/jpeg', 0.9);
}

btnCamera.addEventListener('click', toggleCamera);

btnCapture.addEventListener('click', captureFromVideo);

btnRetake.addEventListener('click', () => {
  resultEl.hidden = true;
  btnRetake.hidden = true;
  preview.classList.remove('flipped'); // 移除翻转类
  preview.hidden = true;
  
  if (isCameraOn) {
    video.hidden = false;
    cameraPlaceholder.hidden = true;
  } else {
    // 如果摄像头未开启,显示提示
    showResult('请重新启动摄像头', false);
    btnCapture.disabled = true;
    cameraPlaceholder.hidden = false;
  }
});

fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  // 从相册上传的照片不翻转
  preview.src = URL.createObjectURL(file);
  preview.classList.remove('flipped'); // 确保没有翻转类
  preview.hidden = false;
  video.hidden = true;
  
  // 如果摄像头正在运行,先关闭
  if (isCameraOn) {
    stopCamera();
  }
  
  await submitCheckIn(file, false);
});

// 页面加载时自动启动摄像头
// startCamera();
