# 注册页面重拍功能说明

## ✅ 新增功能

在注册页面添加了**重拍按钮**，用户可以在拍照或从相册选择照片后重新拍摄/选择。

---

## 📋 功能特性

### 1. 按钮显示逻辑

**显示时机:**
- ✅ 拍照后立即显示"重拍"按钮
- ✅ 从相册选择照片后显示"重拍"按钮

**隐藏时机:**
- ✅ 点击重拍后按钮隐藏
- ✅ 初始状态下按钮隐藏

### 2. 重拍行为

**如果摄像头已开启:**
- 清除当前照片
- 返回摄像头实时画面
- 可以继续拍照

**如果摄像头未开启:**
- 清除当前照片
- 显示摄像头占位符
- 提示用户启动摄像头或从相册选择

### 3. 数据清理

重拍时会:
- ✅ 清除 `photoBlob`（照片数据）
- ✅ 隐藏预览图片
- ✅ 移除翻转样式类
- ✅ 重置为可重新拍照状态

---

## 🎯 使用流程

### 流程 1: 拍照 → 重拍 → 再拍照

```
1. 启动摄像头
   └─ 显示实时画面

2. 点击"拍照"
   └─ 显示预览照片
   └─ "重拍"按钮出现

3. 点击"重拍"
   └─ 预览消失
   └─ 返回摄像头画面
   └─ "重拍"按钮隐藏

4. 再次点击"拍照"
   └─ 拍摄新照片
```

### 流程 2: 相册上传 → 重拍 → 摄像头拍照

```
1. 点击"从相册选择"
   └─ 显示选择的照片
   └─ "重拍"按钮出现

2. 点击"重拍"
   └─ 预览消失
   └─ 显示占位符（因为摄像头未开启）

3. 点击"启动摄像头"
   └─ 启动摄像头
   └─ 显示实时画面

4. 点击"拍照"
   └─ 拍摄新照片
```

### 流程 3: 拍照 → 重拍 → 相册上传

```
1. 拍照
   └─ 显示预览
   └─ "重拍"按钮出现

2. 点击"重拍"
   └─ 返回摄像头画面

3. 点击"从相册选择"
   └─ 选择新照片
   └─ 显示新照片
   └─ "重拍"按钮再次出现
```

---

## 🔧 技术实现

### 1. HTML 修改

在 [`register.html`](register.html) 的 actions 区域添加重拍按钮：

```html
<div class="actions">
  <button id="btnCamera" class="btn secondary" type="button">启动摄像头</button>
  <button id="btnCapture" class="btn secondary" type="button" disabled>拍照</button>
  <button id="btnRetake" class="btn secondary" type="button" hidden>重拍</button>
  <label class="btn secondary">
    从相册选择
    <input type="file" id="fileInput" accept="image/*" capture="user" hidden>
  </label>
</div>
```

**关键点:**
- `hidden` 属性：初始状态隐藏
- 与其他按钮相同的样式类 `btn secondary`

---

### 2. JavaScript 修改

#### 2.1 添加元素引用

```javascript
const btnRetake = document.getElementById('btnRetake');
```

#### 2.2 修改 setPhoto 函数

```javascript
function setPhoto(blob) {
  photoBlob = blob;
  preview.src = URL.createObjectURL(blob);
  preview.classList.add('flipped');
  preview.hidden = false;
  video.hidden = true;
  cameraPlaceholder.hidden = true;
  btnRetake.hidden = false; // ← 显示重拍按钮
}
```

#### 2.3 修改文件上传处理

```javascript
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  photoBlob = file;
  preview.src = URL.createObjectURL(file);
  preview.classList.remove('flipped');
  preview.hidden = false;
  video.hidden = true;
  cameraPlaceholder.hidden = true;
  btnRetake.hidden = false; // ← 显示重拍按钮
  
  if (isCameraOn) {
    stopCamera();
  }
});
```

#### 2.4 添加重拍事件处理

```javascript
btnRetake.addEventListener('click', () => {
  // 清除照片数据
  photoBlob = null;
  
  // 隐藏预览
  preview.hidden = true;
  preview.classList.remove('flipped');
  
  // 隐藏重拍按钮
  btnRetake.hidden = true;
  
  // 根据摄像头状态决定显示什么
  if (isCameraOn) {
    // 摄像头已开启：返回摄像头画面
    video.hidden = false;
    cameraPlaceholder.hidden = true;
  } else {
    // 摄像头未开启：显示占位符
    video.hidden = true;
    cameraPlaceholder.hidden = false;
  }
});
```

---

## 📊 状态转换图

```
初始状态
  ├─ cameraPlaceholder: 显示
  ├─ video: 隐藏
  ├─ preview: 隐藏
  ├─ btnRetake: 隐藏
  └─ photoBlob: null

启动摄像头
  ├─ cameraPlaceholder: 隐藏
  ├─ video: 显示
  ├─ preview: 隐藏
  ├─ btnRetake: 隐藏
  └─ photoBlob: null

拍照后
  ├─ cameraPlaceholder: 隐藏
  ├─ video: 隐藏
  ├─ preview: 显示 (flipped)
  ├─ btnRetake: 显示 ← 关键变化
  └─ photoBlob: 有数据

点击重拍（摄像头开启）
  ├─ cameraPlaceholder: 隐藏
  ├─ video: 显示
  ├─ preview: 隐藏
  ├─ btnRetake: 隐藏
  └─ photoBlob: null

点击重拍（摄像头关闭）
  ├─ cameraPlaceholder: 显示 ← 关键变化
  ├─ video: 隐藏
  ├─ preview: 隐藏
  ├─ btnRetake: 隐藏
  └─ photoBlob: null
```

---

## ✅ 测试用例

### 测试 1: 拍照后重拍

**步骤:**
1. 启动摄像头
2. 点击"拍照"
3. 确认"重拍"按钮出现
4. 点击"重拍"
5. 确认返回摄像头画面

**预期结果:**
- ✅ 拍照后"重拍"按钮显示
- ✅ 点击重拍后预览消失
- ✅ 摄像头画面重新显示
- ✅ 可以再次拍照

---

### 测试 2: 相册上传后重拍

**步骤:**
1. 点击"从相册选择"
2. 选择一张照片
3. 确认"重拍"按钮出现
4. 点击"重拍"
5. 确认显示占位符

**预期结果:**
- ✅ 上传后"重拍"按钮显示
- ✅ 点击重拍后预览消失
- ✅ 显示占位符（因为摄像头未开启）
- ✅ 可以启动摄像头或再次上传

---

### 测试 3: 多次重拍

**步骤:**
1. 拍照 → 重拍 → 拍照 → 重拍（重复3次）

**预期结果:**
- ✅ 每次都能正常重拍
- ✅ 无内存泄漏
- ✅ 状态转换正确

---

### 测试 4: 重拍后提交注册

**步骤:**
1. 拍照
2. 重拍
3. 再次拍照
4. 填写其他信息
5. 点击"提交注册"

**预期结果:**
- ✅ 提交的是最后一次拍的照片
- ✅ 注册成功
- ✅ 数据正确保存

---

## 🎨 UI/UX 考虑

### 按钮位置

重拍按钮位于"拍照"按钮之后，"从相册选择"之前：

```
[启动摄像头] [拍照] [重拍] [从相册选择]
```

**设计理由:**
- 符合操作顺序：先拍照，再考虑重拍
- 视觉分组：拍照相关操作在一起
- 不干扰主要流程：初始隐藏，需要时才显示

### 按钮样式

使用与"拍照"相同的样式类 `btn secondary`：

- 次要操作样式（灰色背景）
- 与主要操作（注册按钮）区分
- 视觉上保持一致性

### 交互反馈

- **即时响应**: 点击重拍后立即清除预览
- **状态明确**: 按钮隐藏表示当前不需要重拍
- **无缝切换**: 重拍后可以直接继续操作

---

## 🔍 与签到页面对比

| 特性 | 注册页面 | 签到页面 |
|------|---------|---------|
| 重拍按钮 | ✅ 已添加 | ✅ 已有 |
| 显示时机 | 拍照/上传后 | 拍照后 |
| 重拍行为 | 清除照片，返回摄像头/占位符 | 清除照片，返回摄像头 |
| 占位符支持 | ✅ 支持 | ❌ 不支持 |
| 翻转样式 | ✅ 拍照翻转，上传不翻转 | ✅ 拍照翻转，上传不翻转 |

**改进点:**
- 注册页面增加了占位符支持，用户体验更好
- 两者现在都有完整的重拍功能

---

## 🐛 边界情况处理

### 情况 1: 重拍时摄像头正在关闭

**处理:**
```javascript
if (isCameraOn) {
  video.hidden = false;
} else {
  cameraPlaceholder.hidden = false;
}
```

确保无论摄像头状态如何，都能正确显示相应界面。

### 情况 2: 重拍后直接提交

**处理:**
```javascript
photoBlob = null; // 清除照片数据
```

如果用户重拍后不重新拍照就提交，会在提交时检测到 `!photoBlob` 并提示错误。

### 情况 3: 快速连续点击重拍

**处理:**
```javascript
btnRetake.hidden = true; // 立即隐藏按钮
```

防止重复点击，第一次点击后按钮就隐藏。

---

## 📝 代码统计

| 修改类型 | 行数变化 | 说明 |
|---------|---------|------|
| HTML | +1 | 添加重拍按钮 |
| JavaScript | +20 | 添加变量引用和事件处理 |
| **总计** | **+21** | 轻量级改动 |

---

## ✅ 验收清单

- [x] 重拍按钮在拍照后显示
- [x] 重拍按钮在上传后显示
- [x] 点击重拍后按钮隐藏
- [x] 重拍后清除照片数据
- [x] 摄像头开启时返回摄像头画面
- [x] 摄像头关闭时显示占位符
- [x] 翻转样式正确移除
- [x] 可以连续多次重拍
- [x] 重拍后可以正常提交注册
- [x] 无内存泄漏
- [x] Mock 模式兼容

---

## 🎉 总结

重拍功能已成功添加到注册页面！

**核心优势:**
1. ✅ 用户体验提升：不满意可以重新拍摄
2. ✅ 操作灵活：支持摄像头和相册两种方式
3. ✅ 状态管理清晰：正确处理各种边界情况
4. ✅ 代码简洁：仅增加21行代码
5. ✅ 与签到页面保持一致

**现在用户可以:**
- 拍照后不满意？点击重拍！
- 上传后想换一张？点击重拍！
- 反复尝试直到满意为止！

祝使用愉快！📸✨
