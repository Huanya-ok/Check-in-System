const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const preview = document.getElementById('preview');
const btnCapture = document.getElementById('btnCapture');
const btnRetake = document.getElementById('btnRetake');
const fileInput = document.getElementById('fileInput');
const resultEl = document.getElementById('result');

let stream = null;

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    });
    video.srcObject = stream;
    video.hidden = false;
    preview.hidden = true;
  } catch {
    showResult('无法访问摄像头，请使用相册上传', false);
  }
}

function showResult(message, success) {
  resultEl.hidden = false;
  resultEl.textContent = message;
  resultEl.className = 'result ' + (success ? 'success' : 'error');
}

async function submitCheckIn(blob) {
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
    showResult('网络错误，请稍后重试', false);
  } finally {
    btnCapture.disabled = false;
  }
}

function captureFromVideo() {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  canvas.toBlob(async (blob) => {
    preview.src = URL.createObjectURL(blob);
    preview.hidden = false;
    video.hidden = true;
    btnRetake.hidden = false;
    await submitCheckIn(blob);
  }, 'image/jpeg', 0.9);
}

btnCapture.addEventListener('click', captureFromVideo);

btnRetake.addEventListener('click', () => {
  resultEl.hidden = true;
  btnRetake.hidden = true;
  video.hidden = false;
  preview.hidden = true;
  startCamera();
});

fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  video.hidden = true;
  await submitCheckIn(file);
});

startCamera();
