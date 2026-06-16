# 人脸识别签到系统 — 设计文档

## 小组成员

| 姓名 | 学号 |
|------|------|
| 黄彦 | 231250197 |
| 陆俊睿 | 231250050 |
| 卞浩宇 | 221098106 |
| 刘杨 | 231880158 |

---

## 1. 项目概述

本系统面向课堂签到场景：学生与教师均通过手机浏览器使用签到应用，服务端提供 API 与华为云 FRS 人脸识别能力。

系统分为以下核心模块：

| 模块 | 是否需要登录 | 说明 |
|------|-------------|------|
| 用户注册 | 否 | 填写基本信息（姓名、学号、账号、密码）+ 上传标准人脸照片 |
| 登录 / 注销 | — | 用户登录后获取 JWT；注销清除本地令牌 |
| 签到 | 否 | 拍照上传 → 人脸识别 → 记录签到（不依赖设备标识） |
| 签到记录查看 | 是（学生） | 登录后查看本人签到历史 |
| 教师签到总览 | 是（教师） | 查看全班签到统计、已签到列表、未签到名单 |

---

## 1.1 课程里程碑

### 本周（2）：前后端连通框架

同步开发手机端与服务器端，演示前后端可联调的完整框架，包含以下功能：

| 功能 | 前端页面 | 后端 API | 数据库变化 |
|------|----------|----------|------------|
| 注册 | `register.html` | `POST /api/auth/register` | `users` + `face_profiles` 新增记录 |
| 登录 | `login.html` | `POST /api/auth/login` | — |
| 注销 | `records.html` 等 | `POST /api/auth/logout` + 客户端清 Token | — |
| 拍照上传 | 注册页 / 签到页 | 接收 `multipart/form-data` 图片 | 照片文件写入存储 |

**提交物**：手机端页面截图 + 服务器数据库变化截图（如 pgAdmin / `\dt` / 表数据查询结果）。

### 本周（3）：签到与记录

完成并演示完整签到流程及签到记录查看功能。

| 功能 | 前端页面 | 后端 API | 数据库变化 |
|------|----------|----------|------------|
| 签到 | `index.html`（无需登录） | `POST /api/check-in` | `check_in_records` 新增记录 |
| 查看个人记录 | `records.html`（学生登录） | `GET /api/check-in/records` | 读取 `check_in_records` |
| 教师总览（扩展） | `dashboard.html`（教师登录） | `GET /api/teacher/overview` | 聚合查询各表 |

**提交物**：手机端签到/记录页面截图 + 服务器端截图（API 响应、数据库记录、教师总览页等）。

---

## 1.2 前端架构说明

本项目采用**手机端与服务端分离**架构：

| 部分 | 目录 | 说明 |
|------|------|------|
| **手机端** | `mobile/` | 纯 H5 页面，独立部署，学生与教师均在手机浏览器使用 |
| **服务端** | `server/` | 仅提供 REST API（`/api/*`），不托管前端页面 |

手机端通过 `mobile/js/config.js` 配置服务端地址（如 `http://192.168.1.100:8000/api`），跨域由服务端 CORS 支持。

| 页面 | 用户 | 说明 |
|------|------|------|
| `index.html` | 学生 | 拍照签到（无需登录） |
| `register.html` | 学生 | 注册 + 上传人脸照 |
| `login.html` | 学生/教师 | 登录 |
| `records.html` | 学生 | 个人签到记录 |
| `dashboard.html` | 教师 | 全班签到总览（手机端列表） |

---

## 2. 系统架构

### 2.1 总体架构图

```
┌──────────────────────────────────┐         HTTPS          ┌──────────────────────────────────┐
│   手机端 H5（mobile/）            │ ◄────────────────────► │      云服务器 / 本机（server/）    │
│  - 学生：注册 / 签到 / 个人记录    │      REST API          │  ┌────────────────────────────┐  │
│  - 教师：签到总览（手机查看）      │                        │  │   FastAPI（纯 API）         │  │
└──────────────────────────────────┘                        │  │  - /api/auth/*             │  │
                                                            │  │  - /api/check-in           │  │
                                                            │  │  - /api/teacher/overview   │  │
                                                            │  └─────────────┬──────────────┘  │
                                                            │                │                  │
                                                            │  ┌─────────────▼──────────────┐  │
                                                            │  │   华为云 FRS 人脸识别       │  │
                                                            │  └─────────────┬──────────────┘  │
                                                            └────────────────┼──────────────────┘
                                                                             │
                           ┌─────────────────────────────┼─────────────────┐
                           │                             │                 │
                 ┌─────────▼─────────┐       ┌───────────▼──────┐  ┌───────▼──────┐
                 │   PostgreSQL      │       │      Redis       │  │  文件存储     │
                 │  - 用户/角色      │       │  - 缓存（扩展）   │  │  - 人脸/签到照│
                 │  - 人脸底库       │       │                  │  │              │
                 │  - 签到记录       │       │                  │  │              │
                 └───────────────────┘       └──────────────────┘  └──────────────┘
```

### 2.2 核心数据流

#### 用户注册流程（无需登录）

```
填写基本信息（姓名、学号、用户名、密码）
    → 上传标准人脸照片 → 华为 FRS 人脸检测
    → 添加至华为云人脸库（FaceSet）→ 本地记录 frs_face_id
    → 写入 users 表 + face_profiles 表 → 返回注册成功
```

#### 签到流程（无需登录）

```
用户拍照 → 上传图片 → 服务端接收
    → 华为 FRS 人脸检测 → 在人脸库中 1:N 搜索（SearchFace）
    → 相似度 > 阈值则匹配成功（external_image_id 对应 profile_id）
    → 写入 check_in_records → 返回「签到成功 + 姓名」
```

#### 查看签到记录（学生，需登录）

```
学生登录 → 携带 JWT 请求 /api/check-in/records
    → 按 face_profile_id 筛选本人记录（可按日期）
    → 返回个人签到历史列表
```

#### 教师签到总览（教师，需登录）

```
教师登录（role=teacher）→ 携带 JWT 请求 /api/teacher/overview?date=YYYY-MM-DD
    → 统计已注册人数、当日已签到人数、未签到人数
    → 返回已签到明细表 + 未签到学生名单
```

### 2.3 高并发设计

| 策略 | 方案 |
|------|------|
| API 层 | FastAPI 异步 I/O；`asyncio.to_thread` 调用 FRS SDK |
| 人脸识别 | 华为云 FRS 托管推理，无需本地 GPU |
| 人脸底库 | 华为云 FaceSet（云端存储特征，容量 10 万） |
| 缓存 | Redis 签到限流（同用户 N 秒内不可重复签到，扩展） |
| 数据库 | PostgreSQL 连接池 (asyncpg) |
| 负载均衡 | Nginx 反向代理 + 多 API 实例 |

---

## 3. 人脸识别方案选型（华为云 FRS）

按课程要求，人脸识别统一使用**华为云人脸识别服务 FRS**，不再本地部署 InsightFace / FAISS。

### 3.1 方案对比

| 方案 | 优点 | 缺点 | 选用 |
|------|------|------|------|
| 本地 InsightFace + FAISS | 无云服务费用、可离线 | 需下载模型、占资源、不符合课程要求 | 弃用 |
| **华为云 FRS** | 云端托管、SDK 成熟、支持人脸库 1:N 搜索 | 需开通服务、配置 AK/SK | **主选** |

### 3.2 使用的 FRS 能力

| FRS API | 用途 | 调用时机 |
|---------|------|----------|
| `DetectFaceByBase64` | 人脸检测 | 注册时校验照片含人脸 |
| `CreateFaceSet` | 创建人脸库 | 服务首次启动 |
| `AddFacesByBase64` | 添加人脸 | 用户注册 |
| `SearchFaceByBase64` | 1:N 人脸搜索 | 签到识别 |
| `DeleteFaceByFaceId` | 删除人脸 | 更新/禁用人脸（扩展） |

### 3.3 匹配策略

- **相似度度量**：华为 FRS 返回 `similarity`（0~1）
- **默认阈值**：0.8（可通过 `.env` 中 `FACE_SIMILARITY_THRESHOLD` 调整）
- **身份映射**：添加人脸时 `external_image_id` 设为本地 `face_profile.id`，搜索时反查

### 3.4 华为云 FRS 接入步骤（卞浩宇负责）

1. **开通服务**：华为云控制台开通 FRS，开通人脸检测、人脸搜索等 API
2. **在线调试**：控制台 API Explorer 完成人脸检测在线调试
3. **本地 SDK 调试**：安装 `huaweicloudsdkfrs`，配置 AK/SK，运行 `scripts/frs_detect_test.py`
4. **集成到项目**：在 `face_service.py` 中封装检测、入库、搜索接口

### 3.5 技术栈汇总

| 层次 | 技术 |
|------|------|
| 前端 | HTML5 + CSS + JavaScript（`mobile/`，独立部署） |
| 后端 | Python 3.11 + FastAPI |
| 人脸识别 | **华为云 FRS**（`huaweicloudsdkfrs`） |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 部署 | Docker Compose / 华为云 ECS 公网 IP |

---

## 4. 数据库设计

### 4.1 ER 关系

```
User (用户)              FaceProfile (人脸底库)         CheckInRecord (签到记录)
┌──────────────┐      ┌──────────────────┐         ┌─────────────────────┐
│ id           │──1:1─│ id               │──1:N────│ id                  │
│ username     │      │ user_id (FK)     │         │ face_profile_id (FK)│
│ password_hash│      │ name             │         │ check_in_time       │
│ name         │      │ student_no       │         │ similarity_score    │
│ student_no   │      │ photo_path       │         │ photo_path          │
│ role         │      │ frs_face_id      │         │ created_at          │
│ created_at   │      │ created_at       │         └─────────────────────┘
└──────────────┘      └──────────────────┘
```

角色说明：`role` 取值为 `student`（默认，注册创建）或 `teacher`（系统预置，无 face_profile）。

### 4.2 主要表结构

**users** — 用户账户

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| username | VARCHAR(64) UNIQUE | 登录名 |
| password_hash | VARCHAR(256) | bcrypt 哈希 |
| name | VARCHAR(64) | 真实姓名 |
| student_no | VARCHAR(32) UNIQUE | 学号（教师账号使用占位学号） |
| role | VARCHAR(16) | `student` / `teacher` |
| created_at | TIMESTAMP | |

预置教师账号：`teacher` / `teacher123`（`role=teacher`，服务首次启动时自动创建）。

**face_profiles** — 人脸底库（与 users 一对一）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| user_id | FK → users.id | 关联用户 |
| name | VARCHAR(64) | 姓名（冗余，便于检索展示） |
| student_no | VARCHAR(32) UNIQUE | 学号 |
| photo_path | VARCHAR(512) | 注册时上传的标准人脸照 |
| frs_face_id | VARCHAR(64) | 华为 FRS 返回的人脸 ID |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | |

**check_in_records** — 签到记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| face_profile_id | FK | 匹配到的人脸 |
| check_in_time | TIMESTAMP | 签到时间 |
| similarity_score | FLOAT | 匹配置信度 |
| photo_path | VARCHAR(512) | 签到时上传的照片 |

---

## 5. API 设计

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 否 | 注册：基本信息 + 标准人脸照片 |
| POST | `/api/auth/login` | 否 | 登录，返回 JWT 及 `role` |
| POST | `/api/auth/logout` | 是 | 注销（客户端清除 Token；可选 Redis 黑名单） |
| POST | `/api/check-in` | 否 | 上传照片签到 |
| GET | `/api/check-in/records` | 是 | 查询本人签到记录（支持日期筛选） |
| GET | `/api/teacher/overview` | 教师 | 全班签到总览（统计 + 已签到 + 未签到） |
| GET | `/api/health` | 否 | 健康检查 |

### 签到接口响应示例

```json
// 成功
{ "success": true, "name": "张三", "student_no": "2021001", "message": "签到成功" }

// 失败
{ "success": false, "message": "未识别到匹配的人脸，请重试" }
```

### 教师总览接口响应示例

```json
{
  "date": "2026-06-16",
  "total_registered": 30,
  "checked_in_count": 25,
  "absent_count": 5,
  "records": [
    {
      "id": 1,
      "name": "张三",
      "student_no": "231250197",
      "check_in_time": "2026-06-16T08:30:00",
      "similarity_score": 0.82
    }
  ],
  "absent_students": [
    { "name": "李四", "student_no": "231250050" }
  ]
}
```

---

## 6. 目录结构

```
Check-in-System/
├── docs/
│   └── DESIGN.md              # 本文档
├── mobile/                    # 手机端 H5（独立部署）
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── records.html
│   ├── dashboard.html         # 教师总览（手机）
│   ├── js/config.js           # 服务端 API 地址
│   └── css/
├── server/                    # 服务端（纯 API）
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置
│   │   ├── api/               # 路由
│   │   ├── models/            # ORM 模型
│   │   ├── schemas/           # 请求/响应模型
│   │   ├── services/          # 业务逻辑（含人脸识别）
│   │   └── core/              # 认证、安全
│   ├── scripts/
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 7. 部署与运行

采用**手机端与服务端分离部署**：服务端仅提供 API；手机端在 `mobile/` 独立运行。

### 7.1 启动步骤

**服务端：** `docker compose up -d --build`（端口 8000）

**手机端：**
```bash
cd mobile
# 编辑 js/config.js → API_BASE = http://<服务器IP>:8000/api
python -m http.server 3000
```

### 7.2 访问地址

| 地址 | 说明 |
|------|------|
| `http://<IP>:3000/` | 手机端签到页 |
| `http://<IP>:3000/dashboard.html` | 教师总览（手机） |
| `http://<IP>:8000/api/docs` | API 文档 |

### 7.3 演示方案

| 步骤 | 设备 | 操作 |
|------|------|------|
| 1 | 电脑 | 启动服务端 |
| 2 | 手机 | 注册 + 签到 |
| 3 | 手机（教师） | `dashboard.html` 查看总览 |
| 4 | 电脑 | 数据库截图 |

---

## 8. 小组分工

按**技术层次**四人分工，功能任务不变；开发阶段各层并行推进，**部署、测试与项目统筹**由黄彦在最后阶段统一负责。

### 8.0 分工总览

| 成员 | 负责层次 | 主要目录 / 文件 |
|------|----------|-------------------|
| **陆俊睿** | 后端 | `server/app/api/`、`models/`、`schemas/`、`core/` |
| **卞浩宇** | 华为云 FRS | `face_service.py`、FRS SDK 接入与本地调试 |
| **刘杨** | H5 手机端 | `mobile/`（全部页面、CSS、JS、`config.js`） |
| **黄彦** | 部署 + 测试 + 统筹 | `docker-compose.yml`、`Dockerfile`、联调集成、演示彩排 |

### 8.1 各成员详细职责

#### 陆俊睿 — 后端

- 数据库表设计与 ORM 模型（`users`、`face_profiles`、`check_in_records`）
- 全部 REST API：`/api/auth/register`、`login`、`logout`、`/api/check-in`、`/api/check-in/records`、`/api/teacher/overview`
- JWT 认证与安全模块（`core/security.py`、`core/deps.py`）
- 在路由中调用人脸服务（`face_service.add_face` / `search`）
- 文件上传与业务数据读写逻辑

#### 卞浩宇 — 华为云 FRS

- 华为云控制台开通 FRS 服务，完成人脸检测**在线调试**
- 本地安装 `huaweicloudsdkfrs`，运行 `scripts/frs_detect_test.py` 完成**本地调试**
- 维护 `face_service.py`：人脸检测、人脸库管理、添加人脸、1:N 搜索
- 调优 `FACE_SIMILARITY_THRESHOLD` 相似度阈值

#### 刘杨 — H5 手机端

- 维护 `mobile/` 全部页面（学生 + 教师均在手机上使用）
- `js/config.js` 服务端地址配置
- 摄像头拍照 / 相册上传组件
- 教师总览页手机端列表布局

#### 黄彦 — 部署、测试与统筹

- `docker-compose.yml`、`server/Dockerfile` 及运行环境配置
- PostgreSQL / Redis 容器部署，局域网与公网访问配置
- 端到端测试、数据核查、演示彩排
- 项目统筹：进度协调、前后端联调组织、设计文档维护、Git 合并
- 演示时的数据库截图与服务器端截图

### 8.2 数据管理分工

| 数据类型 | 存储 | 负责人 |
|----------|------|--------|
| 业务数据（用户、底库、签到记录） | PostgreSQL | **陆俊睿**（表结构与 API 读写） |
| 人脸特征与人脸库 | 华为云 FRS FaceSet | **卞浩宇** |
| 人脸照 / 签到照 | `uploads/` 目录 | **陆俊睿**（保存逻辑） |
| 数据库容器运维与演示截图 | Docker 环境 | **黄彦** |

### 8.3 按课程周次的任务安排

| 周次 | 陆俊睿（后端） | 卞浩宇（人脸识别） | 刘杨（前端） | 黄彦（部署/测试/统筹） |
|------|----------------|-------------------|--------------|------------------------|
| **本周（2）** | 注册 API（调 FRS 添脸） | 开通 FRS + 在线调试 + 本地 SDK 调试 | 注册页、登录页 | Docker 环境、数据库截图 |
| **本周（3）** | 签到 / 记录 / 教师总览 API | FRS 人脸搜索与阈值调优 | 签到页、记录页、教师总览 | 端到端联调、演示彩排 |

### 8.4 验收清单

**本周（2）**

- [ ] **陆俊睿**：`POST /api/auth/register` 写入 `users` + `face_profiles`
- [ ] **卞浩宇**：FRS 人脸检测在线调试 + 本地 SDK 调试通过；注册时可添脸入库
- [ ] **刘杨**：注册页、登录页可用，拍照上传正常
- [ ] **黄彦**：Docker 一键启动，数据库截图就绪

**本周（3）**

- [ ] **陆俊睿**：签到与记录、教师总览 API 可用
- [ ] **卞浩宇**：签到人脸识别匹配准确
- [ ] **刘杨**：签到页、记录页、教师总览页完成
- [ ] **黄彦**：全系统联调通过，演示彩排完成

### 8.5 协作约定

1. **陆俊睿**先定 API 接口（Swagger），**刘杨**按文档并行开发前端。
2. **卞浩宇**维护 `face_service`，提供异步接口供**陆俊睿**在 API 路由中调用。
3. 前端样式由**刘杨**统一维护，后端改动接口须提前同步。
4. 开发完成后由**黄彦**组织联调、部署上线与演示；Git 合并由**黄彦**负责。

---

## 9. 后续迭代计划

- [x] 华为云 FRS 接入（`face_service.py` + 本地调试脚本）
- [x] 教师签到总览页（`dashboard.html` + `/api/teacher/overview`）
- [ ] 完善移动端 UI（PWA / 原生 App）
- [ ] GPU 推理加速与模型量化
- [ ] 活体检测（防照片攻击，FRS 扩展能力）
- [ ] 签到统计报表导出（Excel / PDF）
- [ ] pgvector 替代本地向量存储（已使用华为云 FaceSet，暂不需要）
