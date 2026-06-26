# Mock 模式使用指南

## 📋 概述

Mock 模式允许前端在**完全不依赖后端服务器**的情况下运行和测试,所有 API 请求都会被拦截并返回模拟数据。数据存储在浏览器的 `localStorage` 中,刷新页面后数据仍然保留。

## 🚀 快速启动

### Windows 用户

双击运行 `start-mock.bat` 即可自动启动服务器并打开浏览器。

### Mac/Linux 用户

```bash
chmod +x start-mock.sh
./start-mock.sh
```

### 手动启动

```bash
cd mobile
python -m http.server 3000
```

然后在浏览器访问: **http://localhost:3000**

## ⚙️ 配置说明

Mock 模式的开关位于 [`js/config.js`](js/config.js):

```javascript
window.APP_CONFIG = {
  API_BASE: 'http://localhost:8000/api',
  MOCK_MODE: true,  // ← 设置为 true 启用 Mock 模式
};
```

- **MOCK_MODE = true**: 启用 Mock 模式,所有 API 请求被拦截
- **MOCK_MODE = false**: 关闭 Mock 模式,连接真实后端服务器

## 👥 测试账号

系统预置了以下测试账号:

### 学生账号

| 用户名 | 密码 | 姓名 | 学号 |
|--------|------|------|------|
| zhangsan | 123456 | 张三 | 231250197 |
| lisi | 123456 | 李四 | 231250050 |

### 教师账号

| 用户名 | 密码 | 姓名 | 角色 |
|--------|------|------|------|
| teacher | teacher123 | 王老师 | teacher |

## 🧪 功能测试流程

### 1. 签到功能(无需登录)

1. 访问首页 `http://localhost:3000`
2. 点击"拍照签到"或"从相册选择"
3. 系统会随机匹配一个已注册的学生并显示签到成功
4. 多次签到可生成多条记录

**预期结果:**
- ✅ 显示"签到成功!欢迎 XXX"
- ✅ 相似度在 85%~95% 之间
- ✅ 控制台输出 `[Mock] POST /check-in`

### 2. 用户注册

1. 访问 `http://localhost:3000/register.html`
2. 填写姓名、学号、用户名、密码
3. 拍照或上传人脸照片
4. 点击"提交注册"

**预期结果:**
- ✅ 显示"注册成功,即将跳转..."
- ✅ 自动跳转到个人记录页
- ✅ 新用户数据保存在 localStorage

**注意:** 
- 用户名和学号不能重复
- 注册后会自动登录

### 3. 用户登录

1. 访问 `http://localhost:3000/login.html`
2. 输入测试账号(如 `zhangsan` / `123456`)
3. 点击"登录"

**预期结果:**
- ✅ 学生账号跳转到 `records.html`
- ✅ 教师账号跳转到 `dashboard.html`
- ✅ Token 保存在 localStorage

### 4. 查看个人签到记录(学生)

1. 以学生身份登录
2. 访问 `http://localhost:3000/records.html`
3. 可查看历史签到记录
4. 支持按日期筛选

**预期结果:**
- ✅ 显示该学生的所有签到记录
- ✅ 包含签到时间和相似度
- ✅ 按时间倒序排列

### 5. 教师签到总览(教师)

1. 以教师身份登录(`teacher` / `teacher123`)
2. 访问 `http://localhost:3000/dashboard.html`
3. 查看全班签到统计

**预期结果:**
- ✅ 显示已注册人数、已签到人数、未签到人数
- ✅ 列出已签到学生明细(姓名、学号、时间、相似度)
- ✅ 列出未签到学生名单
- ✅ 支持按日期查询

## 🔧 技术实现

### API 拦截机制

[`mock-data.js`](js/mock-data.js) 通过重写 `window.fetch` 实现 API 拦截:

```javascript
if (window.MOCK_MODE) {
  const originalFetch = window.fetch;
  
  window.fetch = async function(url, options = {}) {
    if (typeof url === 'string' && url.startsWith(API_BASE)) {
      return await handleMockRequest(url, options);
    }
    return originalFetch.apply(this, arguments);
  };
}
```

### 数据存储

所有数据存储在 `localStorage`:

- `mock_users`: 用户列表
- `mock_face_profiles`: 人脸底库
- `mock_check_in_records`: 签到记录
- `mock_initialized`: 初始化标记

### 模拟的 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 注销 |
| POST | `/api/check-in` | 人脸签到 |
| GET | `/api/check-in/records` | 查询个人记录 |
| GET | `/api/teacher/overview` | 教师签到总览 |
| GET | `/api/health` | 健康检查 |

## 🐛 调试技巧

### 查看控制台日志

打开浏览器开发者工具(F12),可以看到所有 Mock API 调用:

```
[Mock] Mock 模式已启用
[Mock] 初始数据已加载
[Mock] Fetch 拦截器已安装
[Mock] POST /check-in
[Mock] GET /check-in/records
```

### 清除测试数据

如需重置所有 Mock 数据:

1. 打开浏览器控制台
2. 执行: `localStorage.clear()`
3. 刷新页面

系统会重新加载初始数据。

### 切换真实后端

1. 编辑 [`js/config.js`](js/config.js)
2. 设置 `MOCK_MODE: false`
3. 修改 `API_BASE` 为真实服务器地址
4. 刷新页面

## ⚠️ 注意事项

1. **隐私保护**: Mock 模式下密码明文存储,仅用于开发测试
2. **数据持久化**: 数据保存在浏览器本地,清除缓存会丢失
3. **人脸识别**: Mock 模式下随机匹配学生,不进行真实人脸比对
4. **兼容性**: Mock 模式与真实后端 API 完全兼容,可无缝切换
5. **网络延迟**: 模拟了 200-800ms 的网络延迟,更接近真实体验

## 📝 常见问题

### Q: 为什么签到总是匹配到同一个人?
A: Mock 模式采用随机匹配算法,多签几次会匹配到不同学生。

### Q: 如何添加更多测试学生?
A: 在 [`mock-data.js`](js/mock-data.js) 的 `MOCK_INITIAL_DATA.users` 中添加新用户,然后清除 localStorage 刷新页面。

### Q: 注册时提示"用户名已存在"?
A: 尝试其他用户名,或清除 localStorage 重置数据。

### Q: 教师总览显示"未授权"?
A: 确保使用教师账号(`teacher` / `teacher123`)登录。

## 🎯 下一步

- 完成前端功能测试后,可将 `MOCK_MODE` 设为 `false` 连接真实后端
- 参考 [`DESIGN.md`](../docs/DESIGN.md) 了解完整系统设计
- 查看 [`README.md`](README.md) 获取项目整体说明

---

**祝测试顺利! 🎉**
