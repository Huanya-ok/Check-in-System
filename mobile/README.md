# 手机端(H5)

纯手机端签到应用,与 `server/` 后端分离部署,通过 HTTP 调用 REST API。

## Mock 模式(无需后端)

**快速开始:** 双击运行 `start-mock.bat`(Windows) 或 `./start-mock.sh`(Mac/Linux)

Mock 模式下,前端可以完全不依赖后端服务器独立运行,所有数据存储在浏览器本地。

详细使用说明请查看 [MOCK_GUIDE.md](./docs/MOCK_GUIDE.md)

### 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 学生 | zhangsan | 123456 |
| 学生 | lisi | 123456 |
| 教师 | teacher | teacher123 |

---

## 配置

编辑 `js/config.js`,将 `API_BASE` 改为服务端地址:

```javascript
window.APP_CONFIG = {
  API_BASE: 'http://192.168.1.100:8000/api',  // 改为你的服务器 IP
  MOCK_MODE: true,  // true=Mock模式, false=连接真实后端
};
```

## 本地运行

### Mock 模式(推荐用于开发测试)

```bash
# Windows: 双击 start-mock.bat
# Mac/Linux: ./start-mock.sh

# 或手动启动
cd mobile
python -m http.server 3000
```

访问: `http://localhost:3000`

### 连接真实后端

1. 设置 `MOCK_MODE: false`
2. 修改 `API_BASE` 为后端地址
3. 启动后端服务
4. 重启前端服务

手机浏览器访问: `http://<电脑IP>:3000`

## 页面

| 页面 | 说明 |
|------|------|
| `index.html` | 学生签到(无需登录) |
| `register.html` | 学生注册 |
| `login.html` | 登录 |
| `records.html` | 学生个人记录 |
| `dashboard.html` | 教师总览(手机端) |

## 演示建议

- **学生**:用自己手机打开 `http://<IP>:3000` 完成注册、签到
- **教师**:同样用手机打开 `http://<IP>:3000/dashboard.html` 查看全班情况

## 技术栈

- HTML5 + CSS3 + JavaScript(ES6+)
- Fetch API
- MediaDevices API(摄像头)
- localStorage(数据存储)
- JWT(身份认证)
