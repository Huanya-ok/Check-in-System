# 人脸识别签到系统

基于移动端拍照 + 云端人脸识别的签到系统。详细设计见 [docs/DESIGN.md](docs/DESIGN.md)。

## 功能模块

| 模块 | 登录 | 说明 |
|------|------|------|
| 签到 | 否 | 拍照上传 → 人脸识别 → 记录签到 |
| 照片库管理 | 是 | 录入/删除人脸底库 |
| 签到记录 | 是 | 按日期查询历史记录 |

## 技术栈

- **后端**：Python 3.11 + FastAPI
- **人脸识别**：InsightFace（RetinaFace 检测 + ArcFace 编码）+ FAISS 向量检索
- **数据库**：PostgreSQL + Redis
- **移动端**：HTML5 响应式页面（浏览器拍照）

## 快速启动

### Docker（推荐）

```bash
docker compose up -d --build
```

访问 http://localhost:8000 进行签到，http://localhost:8000/admin.html 进入管理页。

默认管理员：`admin` / `admin123`

### 本地开发

```bash
# 启动 PostgreSQL 和 Redis（或使用 docker compose up db redis -d）
cd server
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

首次运行会自动下载 InsightFace 模型权重（约 300MB）。

## 项目结构

```
Check-in-System/
├── docs/DESIGN.md       # 系统设计文档
├── server/              # FastAPI 后端
│   └── app/
│       ├── api/         # API 路由
│       ├── models/      # 数据库模型
│       ├── services/    # 人脸识别服务
│       └── core/        # 认证与安全
├── mobile/              # H5 移动端页面
└── docker-compose.yml
```

## API 概览

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/check-in` | 否 | 上传照片签到 |
| POST | `/api/auth/login` | 否 | 管理员登录 |
| POST | `/api/faces` | 是 | 录入人脸 |
| GET | `/api/faces` | 是 | 列出底库 |
| GET | `/api/check-in/records` | 是 | 查询签到记录 |

完整 API 文档：启动后访问 http://localhost:8000/docs
