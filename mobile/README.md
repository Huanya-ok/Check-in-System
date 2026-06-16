# 手机端（H5）

纯手机端签到应用，与 `server/` 后端分离部署，通过 HTTP 调用 REST API。

## 配置

编辑 `js/config.js`，将 `API_BASE` 改为服务端地址：

```javascript
window.APP_CONFIG = {
  API_BASE: 'http://192.168.1.100:8000/api',  // 改为你的服务器 IP
};
```

## 本地运行

```bash
# 在 mobile 目录启动静态服务
cd mobile
python -m http.server 3000
```

手机浏览器访问：`http://<电脑IP>:3000`

> 手机需与电脑在同一 WiFi；`config.js` 中的 API 地址指向后端 `server`（默认 8000 端口）。

## 页面

| 页面 | 说明 |
|------|------|
| `index.html` | 学生签到（无需登录） |
| `register.html` | 学生注册 |
| `login.html` | 登录 |
| `records.html` | 学生个人记录 |
| `dashboard.html` | 教师总览（手机端） |

## 演示建议

- **学生**：用自己手机打开 `http://<IP>:3000` 完成注册、签到
- **教师**：同样用手机打开 `http://<IP>:3000/dashboard.html` 查看全班情况
