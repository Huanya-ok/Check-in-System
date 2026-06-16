# 人脸识别签到系统

纯手机端签到应用 + 云端 API 服务。详细设计见 [docs/DESIGN.md](docs/DESIGN.md)。

## 架构

```
mobile/（手机 H5）  ──HTTP API──►  server/（FastAPI 纯后端）
                                      │
                                      ▼
                                 华为云 FRS
```

学生与教师均在**手机浏览器**中使用，服务端只提供 API。

## 快速启动

### 1. 启动服务端

```bash
docker compose up -d --build
```

API 文档：http://localhost:8000/docs

### 2. 启动手机端

```bash
cd mobile
# 编辑 js/config.js，API_BASE 改为 http://<服务器IP>:8000/api
python -m http.server 3000
```

手机浏览器访问：`http://<电脑局域网IP>:3000`

### 3. 配置华为云 FRS

在 `server/.env` 填入 `HUAWEI_AK`、`HUAWEI_SK`、`HUAWEI_PROJECT_ID`（见 `server/.env.example`）。

## 教师账号

- 手机打开：`http://<IP>:3000/dashboard.html`
- 账号：`teacher` / `teacher123`

## 项目结构

```
Check-in-System/
├── mobile/          # 手机端 H5（刘杨）
├── server/          # 后端 API（陆俊睿）+ FRS（卞浩宇）
├── docs/DESIGN.md
└── docker-compose.yml
```

## 演示流程

1. 手机打开注册页 → 注册并上传人脸照
2. 手机签到页拍照签到
3. 教师用手机打开总览页查看全班情况
4. 电脑截图数据库作为服务端佐证

更多说明见 [mobile/README.md](mobile/README.md)。
