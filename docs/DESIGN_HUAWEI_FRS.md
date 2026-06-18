# 人脸识别签到系统设计文档

## 小组成员

| 姓名 | 学号 |
|------|------|
| 黄彦 | 231250197 |
| 陆俊睿 | 231250050 |
| 卞浩宇 | 221098106 |
| 刘杨 | 231880158 |

---

## 1. 项目概述

本系统面向课堂签到场景：学生与教师通过手机浏览器使用签到应用，服务端提供 REST API，并通过华为云 Python SDK 调用 FRS（Face Recognition Service）完成人脸录入、签到识别和云端人脸删除。

人脸特征由华为云 FaceSet 托管。服务端负责接收图片、调用 FRS、维护用户资料、注册照片、签到照片、华为云返回的 `face_id` 以及签到记录。

系统分为以下核心模块：

| 模块 | 是否需要登录 | 说明 |
|------|-------------|------|
| 用户注册 | 否 | 填写基本信息（姓名、学号、账号、密码）并上传标准人脸照片 |
| 登录 / 注销 | 登录否，注销是 | 登录后获取 JWT；注销时客户端清除本地令牌 |
| 签到 | 否 | 拍照上传，调用华为云 FRS 搜索人脸，匹配成功后记录签到 |
| 签到记录查看 | 是（学生） | 登录后查看本人签到历史 |
| 教师签到总览 | 是（教师） | 查看全班签到统计、已签到列表、未签到名单 |
| 人脸云端管理 | 后端服务层 | 注册时 AddFaces，签到时 SearchFace，删除时 DeleteFace |

---

## 1.1 课程里程碑

### 本周（2）：前后端连通框架

同步开发手机端与服务器端，演示前后端可联调的完整框架，包含以下功能：

| 功能 | 前端页面 | 后端 API | 数据库变化 |
|------|----------|----------|------------|
| 注册 | `register.html` | `POST /api/auth/register` | `users` + `face_profiles` 新增记录 |
| 登录 | `login.html` | `POST /api/auth/login` | 无 |
| 注销 | `records.html` 等 | `POST /api/auth/logout` + 客户端清 Token | 无 |
| 拍照上传 | 注册页 / 签到页 | 接收 `multipart/form-data` 图片 | 照片文件写入本地存储 |
| 人脸入库 | 注册流程内 | 调用华为云 `AddFacesByBase64` | `face_profiles.frs_face_id` 保存云端 `face_id` |

**提交物**：手机端页面截图 + 服务器数据库变化截图（如 pgAdmin / `\dt` / 表数据查询结果）+ 华为云 FRS API Explorer 调试截图。

### 本周（3）：签到与记录

完成并演示完整签到流程及签到记录查看功能。

| 功能 | 前端页面 | 后端 API | 数据库变化 |
|------|----------|----------|------------|
| 签到 | `index.html`（无需登录） | `POST /api/check-in` | `check_in_records` 新增记录 |
| 人脸搜索 | 签到流程内 | 调用华为云 `SearchFaceByBase64` | 读取云端 FaceSet，返回最相似人脸 |
| 查看个人记录 | `records.html`（学生登录） | `GET /api/check-in/records` | 读取 `check_in_records` |
| 教师总览 | `dashboard.html`（教师登录） | `GET /api/teacher/overview` | 聚合查询各表 |

**提交物**：手机端签到/记录页面截图 + 服务器端截图（API 响应、数据库记录、教师总览页等）。

---

## 1.2 前端架构说明

本项目采用手机端与服务端分离架构：

| 部分 | 目录 | 说明 |
|------|------|------|
| 手机端 | `mobile/` | 纯 H5 页面，学生与教师均在手机浏览器使用 |
| 服务端 | `server/` | FastAPI 后端，提供 `/api/*` REST API |

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

```text
┌──────────────────────────────┐          HTTP/HTTPS          ┌──────────────────────────────────┐
│ 手机端 H5（mobile/）          │  ◄──────────────────────────► │ 云服务器 / 本机（server/）         │
│ - 学生：注册 / 签到 / 记录     │                               │ ┌──────────────────────────────┐ │
│ - 教师：签到总览              │                               │ │ FastAPI                       │ │
└──────────────────────────────┘                               │ │ - /api/auth/*                 │ │
                                                               │ │ - /api/check-in               │ │
                                                               │ │ - /api/check-in/records       │ │
                                                               │ │ - /api/teacher/overview       │ │
                                                               │ └──────────────┬───────────────┘ │
                                                               │                │                 │
                                                               │ ┌──────────────▼───────────────┐ │
                                                               │ │ face_service.py               │ │
                                                               │ │ 华为云 Python SDK + Base64     │ │
                                                               │ └──────────────┬───────────────┘ │
                                                               └────────────────┼─────────────────┘
                                                                                │
                                                           HTTPS / SDK 调用       │
                                                                                ▼
                                                               ┌──────────────────────────────────┐
                                                               │ 华为云 FRS 人脸搜索服务           │
                                                               │ - FaceSet: checkinfaces           │
                                                               │ - AddFacesByBase64                │
                                                               │ - SearchFaceByBase64              │
                                                               │ - DeleteFace                      │
                                                               └──────────────────────────────────┘

┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ PostgreSQL          │     │ Redis               │     │ 文件存储 uploads/   │
│ - users             │     │ - 限流/缓存扩展      │     │ - 注册人脸照         │
│ - face_profiles     │     │                     │     │ - 签到照片           │
│ - check_in_records  │     │                     │     │                     │
└────────────────────┘     └────────────────────┘     └────────────────────┘
```

### 2.2 核心数据流

#### 用户注册流程（无需登录）

```text
填写基本信息（姓名、学号、用户名、密码）
    -> 上传标准人脸照片
    -> 服务端保存注册照片到 uploads/faces
    -> 服务端将图片 bytes 转为 Base64
    -> 通过华为云 Python SDK 调用 AddFacesByBase64
       - image_base64: 图片 Base64 字符串
       - external_image_id: 本地唯一标识（如 face_profile.id）
       - single: true
    -> 华为云返回 face_id / external_image_id / bounding_box
    -> 本地保存 users、face_profiles，并记录 frs_face_id
    -> 返回注册成功
```

#### 签到流程（无需登录）

```text
用户拍照
    -> 上传图片到服务端
    -> 服务端将图片 bytes 转为 Base64
    -> 通过华为云 Python SDK 调用 SearchFaceByBase64
       - image_base64: 图片 Base64 字符串
       - top_n: 1
       - threshold: FACE_SIMILARITY_THRESHOLD，默认 0.93
    -> 华为云返回最相似人脸
       - face_id
       - external_image_id
       - similarity
       - bounding_box
    -> 服务端根据 external_image_id 或 face_id 映射本地 FaceProfile
    -> 写入 check_in_records
    -> 返回签到成功、姓名、学号
```

#### 删除人脸流程（教师/管理员扩展）

```text
选择要删除或禁用的人脸记录
    -> 服务端读取本地 face_profiles.frs_face_id
    -> 调用华为云 DeleteFace
       - 优先使用 face_id
       - 如没有 face_id，可使用 external_image_id
    -> 云端删除成功后，本地记录设置 is_active=false
```

#### 查看签到记录（学生，需登录）

```text
学生登录
    -> 携带 JWT 请求 /api/check-in/records
    -> 按 face_profile_id 筛选本人记录（可按日期）
    -> 返回个人签到历史列表
```

#### 教师签到总览（教师，需登录）

```text
教师登录（role=teacher）
    -> 携带 JWT 请求 /api/teacher/overview?date=YYYY-MM-DD
    -> 统计已注册人数、当日已签到人数、未签到人数
    -> 返回已签到明细表 + 未签到学生名单
```

### 2.3 高并发设计

| 策略 | 方案 |
|------|------|
| API 层 | FastAPI 异步 I/O |
| 华为云调用 | 华为云 Python SDK + AK/SK 认证 |
| 图片处理 | 服务端接收上传图片 bytes 后转为 Base64 字符串，再交给 FRS SDK 请求体 |
| 人脸识别 | 华为云 FRS 托管推理，无需本地 GPU |
| 人脸底库 | 华为云 FaceSet（`checkinfaces`）保存人脸特征 |
| 本地数据 | PostgreSQL 保存用户、华为云 `face_id`、签到记录 |
| 缓存 | Redis 可用于签到限流（同用户 N 秒内不可重复签到，扩展） |
| 部署 | Docker Compose / 云服务器 / Nginx 反向代理（扩展） |

---

## 3. 人脸识别方案选型（华为云 FRS）

本项目人脸识别统一使用华为云 FRS 人脸搜索服务。服务端采用华为云 Python SDK + AK/SK 认证方式调用 FRS，并以 Base64 请求体提交图片。

### 3.1 使用的 FRS 能力

| FRS API | 路径 | 用途 | 调用时机 |
|---------|------|------|----------|
| `AddFacesByBase64` | SDK: `AddFacesByBase64Request` | 添加人脸到云端 FaceSet | 用户注册或管理员录入 |
| `SearchFaceByBase64` | SDK: `SearchFaceByBase64Request` | 在云端 FaceSet 中 1:N 搜索 | 用户签到 |
| `DeleteFace` | `DELETE /v2/{project_id}/face-sets/{face_set_name}/faces?face_id=xxx` | 删除云端人脸特征 | 删除或禁用人脸 |

说明：

- 人脸库已在华为云侧创建，名称为 `checkinfaces`。
- 当前实现不在服务启动时自动创建 FaceSet。
- 当前主流程不单独调用 `DetectFace`，注册和签到阶段由 `AddFaces` / `SearchFace` 接口返回错误来处理未检测到人脸、图片质量不足等情况。
- 若后续要改善用户提示，可在注册前增加 `DetectFace` 做质量检查。

### 3.2 当前服务层实现

服务层文件：`server/app/services/face_service.py`

调用方式：

- 使用 `huaweicloudsdkcore` 与 `huaweicloudsdkfrs`
- 使用 `BasicCredentials(AK, SK, project_id)` 初始化客户端
- 使用 `FrsRegion.value_of("cn-east-3")` 指定区域
- 后端收到上传图片 bytes 后，通过 `base64.b64encode(image_bytes).decode("utf-8")` 转为 Base64 字符串
- 添加人脸使用 `AddFacesByBase64Request` + `AddFacesBase64Req`
- 搜索人脸使用 `SearchFaceByBase64Request` + `FaceSearchBase64Req`
- 删除人脸优先使用 `DeleteFaceByFaceIdRequest`，必要时兼容 `DeleteFaceByExternalImageIdRequest`
- 图片处理在内存中完成，调用链路集中在 SDK 请求对象中

核心方法：

| 方法 | 参数 | 返回 |
|------|------|------|
| `add_face(external_image_id, image_bytes)` | `external_image_id`: 本地唯一标识；`image_bytes`: 注册照片 bytes | `{"face_id", "external_image_id", "bounding_box"}` |
| `search(image_bytes)` | `image_bytes`: 签到照片 bytes | `{"face_id", "external_image_id", "similarity", "bounding_box"}` |
| `remove_face(face_id=None, external_image_id=None)` | 优先传 `face_id`，也支持 `external_image_id` | `{"face_number", "face_set_id", "face_set_name", "deleted_by", "deleted_value"}` |

### 3.3 匹配策略

- **相似度来源**：华为云 FRS `SearchFaceByBase64` 返回的 `similarity`。
- **默认阈值**：`0.93`，通过 `.env` 中 `FACE_SIMILARITY_THRESHOLD` 配置。
- **搜索数量**：`top_n=1`，只返回最相似的一张人脸。
- **身份映射**：
  - 添加人脸时，`external_image_id` 使用本地唯一标识，如 `face_profile.id`。
  - 华为云返回 `face_id` 后，本地保存到 `face_profiles.frs_face_id`。
  - 签到搜索后，可通过 `external_image_id` 或 `face_id` 反查本地用户。

### 3.4 华为云 FRS 配置

当前使用区域：

```text
华东-上海一 / cn-east-3
```

当前 FRS Endpoint：

```text
https://face.cn-east-3.myhuaweicloud.com
```

当前 FaceSet：

```text
checkinfaces
```

服务端 `.env` 需要配置：

```env
HUAWEI_FACE_ENDPOINT=https://face.cn-east-3.myhuaweicloud.com
HUAWEI_REGION=cn-east-3
HUAWEI_PROJECT_ID=40159fe350fb46a28fb3114e1af234de
HUAWEI_FACE_SET_NAME=checkinfaces
HUAWEICLOUD_SDK_AK=华为云访问密钥 AK
HUAWEICLOUD_SDK_SK=华为云访问密钥 SK
FACE_SIMILARITY_THRESHOLD=0.93
```

安全约定：

- AK/SK 不写死在代码中，只通过 `.env` 或部署环境变量注入。
- `server/.env` 不提交到 Git。
- `server/.env.example` 只保留字段名和非敏感示例。
- 日志中不打印完整 AK/SK。

### 3.5 认证方式

当前实现使用华为云 Python SDK 的 AK/SK 认证方式。

客户端初始化逻辑：

```python
credentials = BasicCredentials(ak, sk, project_id)

client = (
    FrsClient.new_builder(FrsClient)
    .with_credentials(credentials)
    .with_region(FrsRegion.value_of("cn-east-3"))
    .build()
)
```

如果华为云返回认证错误，应检查：

1. AK/SK 是否正确。
2. AK/SK 所属用户是否有 FRS 调用权限。
3. `HUAWEI_REGION` 是否为 `cn-east-3`。
4. `HUAWEI_PROJECT_ID` 是否为对应区域项目 ID。

### 3.6 技术栈汇总

| 层次 | 技术 |
|------|------|
| 前端 | HTML5 + CSS + JavaScript（`mobile/`） |
| 后端 | Python 3.11 / 3.12 + FastAPI |
| 人脸识别 | 华为云 FRS Python SDK（Base64） |
| 华为云 SDK | `huaweicloudsdkcore`、`huaweicloudsdkfrs` |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 部署 | Docker Compose / 华为云 ECS 公网 IP |

后续依赖管理：

- 保留 `huaweicloudsdkcore` 与 `huaweicloudsdkfrs`。
- 定期移除服务端代码未使用的依赖包，减少镜像体积。

### 3.7 本地链路测试

本项目提供 FRS 添加、搜索、删除的本地测试脚本：

```text
server/scripts/frs_face_flow_test.py
```

从项目根目录执行：

```powershell
python server\scripts\frs_face_flow_test.py 例图1.jpg 例图2.jpg
```

测试流程：

```text
1. 将例图1.jpg 添加到华为云 FaceSet
2. 等待云端人脸库索引同步
3. 使用例图2.jpg 搜索匹配人脸
4. 删除刚才添加的测试人脸
```

一次成功测试输出示例：

```text
添加结果: {'face_id': 'DNQCt4Z8', 'external_image_id': 'test-e289daa85277', ...}
搜索结果: {'face_id': 'YYR4FDBf', 'external_image_id': 'j5Vywoj8', 'similarity': 1.0, ...}
删除结果: {'face_number': 1, 'face_set_name': 'checkinfaces', 'deleted_by': 'face_id', ...}
```

说明：

- `face_number=1` 表示测试添加的人脸已从云端删除。
- 搜索结果不一定命中刚添加的测试人脸；如果库中已有同一人或高度相似人脸，FRS 可能返回已有记录。
- 删除时服务层优先按 `face_id` 删除；若云端提示目标暂不可见且传入了 `external_image_id`，会兜底按 `external_image_id` 删除，并对短暂索引同步延迟做重试。

---

## 4. 数据库设计

### 4.1 ER 关系

```text
User (用户)              FaceProfile (人脸档案)       CheckInRecord (签到记录)
┌──────────────┐      ┌──────────────────┐       ┌─────────────────────┐
│ id           │──1:1─│ id               │──1:N──│ id                  │
│ username     │      │ user_id (FK)     │       │ face_profile_id (FK)│
│ password_hash│      │ name             │       │ check_in_time       │
│ name         │      │ student_no       │       │ similarity_score    │
│ student_no   │      │ photo_path       │       │ photo_path          │
│ role         │      │ frs_face_id      │       └─────────────────────┘
│ created_at   │      │ is_active        │
└──────────────┘      │ created_at       │
                      └──────────────────┘
```

角色说明：`role` 取值为 `student`（默认，注册创建）或 `teacher`（系统预置，无 `face_profile`）。

### 4.2 主要表结构

**users** - 用户账户

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | 用户 ID |
| username | VARCHAR(64) UNIQUE | 登录名 |
| password_hash | VARCHAR(256) | bcrypt 哈希 |
| name | VARCHAR(64) | 真实姓名 |
| student_no | VARCHAR(32) UNIQUE | 学号（教师账号可使用占位学号） |
| role | VARCHAR(16) | `student` / `teacher` |
| created_at | TIMESTAMP | 创建时间 |

预置教师账号：`teacher` / `teacher123`（`role=teacher`，服务首次启动时自动创建）。

**face_profiles** - 本地人脸档案

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | 本地人脸档案 ID |
| user_id | FK -> users.id | 关联用户 |
| name | VARCHAR(64) | 姓名（冗余，便于检索展示） |
| student_no | VARCHAR(32) UNIQUE | 学号 |
| photo_path | VARCHAR(512) | 注册时上传的标准人脸照 |
| frs_face_id | VARCHAR(64) | 华为云 FRS 返回的云端人脸 ID |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |

说明：

- 华为云 FaceSet 保存人脸特征。
- 本地 `frs_face_id` 用于删除和反查。

**check_in_records** - 签到记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | 签到记录 ID |
| face_profile_id | FK | 匹配到的人脸档案 |
| check_in_time | TIMESTAMP | 签到时间 |
| similarity_score | FLOAT | 华为云返回的匹配置信度 |
| photo_path | VARCHAR(512) | 签到时上传的照片 |

---

## 5. API 设计

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 否 | 注册：基本信息 + 标准人脸照片，内部调用 `add_face` |
| POST | `/api/auth/login` | 否 | 登录，返回 JWT 及 `role` |
| POST | `/api/auth/logout` | 是 | 注销（客户端清除 Token；可选 Redis 黑名单） |
| POST | `/api/check-in` | 否 | 上传照片签到，内部调用 `search` |
| GET | `/api/check-in/records` | 是 | 查询本人签到记录（支持日期筛选） |
| GET | `/api/teacher/overview` | 教师 | 全班签到总览（统计 + 已签到 + 未签到） |
| GET | `/api/health` | 否 | 健康检查 |

### 5.1 注册接口内部人脸处理

```text
POST /api/auth/register
    -> 保存上传照片
    -> face_service.add_face(profile.id, image_bytes)
    -> 保存返回的 result["face_id"] 到 face_profiles.frs_face_id
```

### 5.2 签到接口内部人脸处理

```text
POST /api/check-in
    -> face_service.search(image_bytes)
    -> 读取 result["external_image_id"] 或 result["face_id"]
    -> 查询本地 FaceProfile
    -> 保存 similarity_score = result["similarity"]
```

### 5.3 签到接口响应示例

```json
{
  "success": true,
  "name": "张三",
  "student_no": "2021001",
  "message": "签到成功"
}
```

```json
{
  "success": false,
  "message": "未识别到匹配的人脸，请重试"
}
```

### 5.4 教师总览接口响应示例

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
      "similarity_score": 0.96
    }
  ],
  "absent_students": [
    {
      "name": "李四",
      "student_no": "231250050"
    }
  ]
}
```

---

## 6. 目录结构

```text
Check-in-System/
├── docs/
│   ├── DESIGN.md                  # 设计文档
│   └── DESIGN_HUAWEI_FRS.md        # 当前华为云 FRS SDK Base64 版设计文档
├── mobile/                         # 手机端 H5
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── records.html
│   ├── dashboard.html
│   ├── js/
│   └── css/
├── server/                         # 服务端
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置
│   │   ├── api/                    # 路由
│   │   ├── models/                 # ORM 模型
│   │   ├── schemas/                # 请求/响应模型
│   │   ├── services/
│   │   │   └── face_service.py     # 华为云 FRS SDK Base64 封装
│   │   └── core/                   # 认证与安全
│   ├── .env.example                # 配置模板，不包含真实 AK/SK
│   ├── scripts/
│   │   └── frs_face_flow_test.py   # FRS 添加、搜索、删除链路测试脚本
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 7. 部署与运行

### 7.1 服务端环境变量

服务端运行前需要在 `server/.env` 中配置：

```env
DATABASE_URL=postgresql+asyncpg://checkin:checkin@localhost:5432/checkin
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
FACE_SIMILARITY_THRESHOLD=0.93

HUAWEI_FACE_ENDPOINT=https://face.cn-east-3.myhuaweicloud.com
HUAWEI_REGION=cn-east-3
HUAWEI_PROJECT_ID=40159fe350fb46a28fb3114e1af234de
HUAWEI_FACE_SET_NAME=checkinfaces
HUAWEICLOUD_SDK_AK=真实 AK
HUAWEICLOUD_SDK_SK=真实 SK
```

### 7.2 启动步骤

服务端：

```bash
docker compose up -d --build
```

或本地开发：

```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

手机端：

```bash
cd mobile
# 编辑 js/config.js 中的 API_BASE
python -m http.server 3000
```

### 7.3 访问地址

| 地址 | 说明 |
|------|------|
| `http://<IP>:3000/` | 手机端签到页 |
| `http://<IP>:3000/dashboard.html` | 教师总览页 |
| `http://<IP>:8000/docs` | FastAPI 自动文档 |
| `http://<IP>:8000/api/health` | 健康检查 |

### 7.4 演示方案

| 步骤 | 设备 | 操作 |
|------|------|------|
| 1 | 电脑 | 启动 PostgreSQL、Redis、FastAPI 服务 |
| 2 | 电脑/华为云控制台 | 确认 FRS FaceSet `checkinfaces` 已存在，AK/SK 权限有效 |
| 3 | 手机 | 学生注册并上传标准人脸照 |
| 4 | 手机 | 拍照签到 |
| 5 | 手机（教师） | `dashboard.html` 查看总览 |
| 6 | 电脑 | 截图数据库记录、API 响应和华为云调用结果 |

---

## 8. 小组分工

按技术层次四人分工，开发阶段各层并行推进，部署、测试与项目统筹由黄彦在最后阶段统一负责。

### 8.1 分工总览

| 成员 | 负责层次 | 主要目录 / 文件 |
|------|----------|----------------|
| 陆俊睿 | 后端业务 API | `server/app/api/`、`models/`、`schemas/`、`core/` |
| 卞浩宇 | 华为云 FRS | `server/app/services/face_service.py`、FRS API 调试 |
| 刘杨 | H5 手机端 | `mobile/` 页面、CSS、JS、`config.js` |
| 黄彦 | 部署 + 测试 + 统筹 | `docker-compose.yml`、`Dockerfile`、联调集成、演示彩排 |

### 8.2 各成员详细职责

#### 陆俊睿 - 后端

- 数据库表设计与 ORM 模型（`users`、`face_profiles`、`check_in_records`）
- 后端 API：注册、登录、注销、签到、签到记录、教师总览
- JWT 认证与安全模块（`core/security.py`、`core/deps.py`）
- 在路由中调用 `face_service.add_face` / `search` / `remove_face`
- 文件上传与业务数据读写逻辑
- 适配 `face_service.py` 当前结构化返回值

#### 卞浩宇 - 华为云 FRS

- 华为云控制台开通 FRS 人脸搜索服务
- 创建并维护 FaceSet：`checkinfaces`
- 使用 API Explorer 调通 `AddFaces`、`SearchFace`、`DeleteFace`
- 维护 `face_service.py`：
  - `AddFacesByBase64`
  - `SearchFaceByBase64`
  - `DeleteFace`
- 调优 `FACE_SIMILARITY_THRESHOLD` 相似度阈值
- 维护 FRS 相关配置

#### 刘杨 - H5 手机端

- 维护 `mobile/` 全部页面
- `js/config.js` 服务端地址配置
- 摄像头拍照 / 相册上传组件
- 教师总览页手机端列表布局
- 优化移动端上传照片大小，减少 FRS 调用延迟

#### 黄彦 - 部署、测试与统筹

- `docker-compose.yml`、`server/Dockerfile` 及运行环境配置
- PostgreSQL / Redis 容器部署，局域网与公网访问配置
- 端到端测试、数据核查、演示彩排
- 项目统筹：进度协调、前后端联调组织、设计文档维护、Git 合并
- 演示时的数据库截图与服务器端截图

### 8.3 数据管理分工

| 数据类型 | 存储 | 负责人 |
|----------|------|--------|
| 用户、角色、签到记录 | PostgreSQL | 陆俊睿 |
| 人脸特征与云端人脸库 | 华为云 FRS FaceSet | 卞浩宇 |
| 注册人脸照 / 签到照 | `uploads/` 目录 | 陆俊睿 |
| 数据库容器运维与演示截图 | Docker 环境 | 黄彦 |
| 手机端页面状态 | 浏览器本地存储 / 前端状态 | 刘杨 |

### 8.4 按课程周次的任务安排

| 周次 | 陆俊睿（后端） | 卞浩宇（人脸识别） | 刘杨（前端） | 黄彦（部署/测试/统筹） |
|------|----------------|-------------------|--------------|------------------------|
| 本周（2） | 注册 API（调 FRS 添脸） | 开通 FRS + 创建 FaceSet + API Explorer 调试 | 注册页、登录页 | Docker 环境、数据库截图 |
| 本周（3） | 签到 / 记录 / 教师总览 API | FRS 人脸搜索与阈值调优 | 签到页、记录页、教师总览 | 端到端联调、演示彩排 |

### 8.5 验收清单

本周（2）：

- [ ] 陆俊睿：`POST /api/auth/register` 写入 `users` + `face_profiles`
- [ ] 陆俊睿：注册成功后保存 `frs_face_id`
- [ ] 卞浩宇：华为云 `AddFacesByBase64` 调用成功
- [ ] 刘杨：注册页、登录页可用，拍照上传正常
- [ ] 黄彦：Docker 一键启动，数据库截图就绪

本周（3）：

- [ ] 陆俊睿：签到与记录、教师总览 API 可用
- [ ] 卞浩宇：`SearchFaceByBase64` 匹配准确，阈值稳定
- [ ] 卞浩宇：`DeleteFace` 删除流程可用
- [ ] 刘杨：签到页、记录页、教师总览页完成
- [ ] 黄彦：全系统联调通过，演示彩排完成

### 8.6 协作约定

1. 陆俊睿先稳定 API 接口（Swagger），刘杨按文档并行开发前端。
2. 卞浩宇维护 `face_service.py`，提供异步接口供后端路由调用。
3. `server/.env` 不提交到 Git；真实 AK/SK 只保存在本地或部署环境中。
4. 华为云接口文档 txt 属于本地参考资料，不提交到 Git。
5. 开发完成后由黄彦组织联调、部署上线与演示；Git 合并由黄彦负责。

---

## 9. 后续迭代计划

- [x] 华为云 FRS 人脸搜索服务开通
- [x] FaceSet `checkinfaces` 创建
- [x] API Explorer 验证 `AddFaces`、`SearchFace`、`DeleteFace`
- [x] `face_service.py` 完成华为云 SDK Base64 调用封装
- [x] `.env.example` 增加 FRS SDK AK/SK 配置模板
- [x] `frs_face_flow_test.py` 验证添加、搜索、删除链路通过
- [ ] 后端路由适配 `face_service.py` 结构化返回值
- [ ] 移动端上传前压缩图片，降低 FRS 调用耗时
- [ ] 增加 `DetectFace` 做注册照质量检查
- [ ] 增加活体检测，降低照片攻击风险
- [ ] 签到统计报表导出（Excel / PDF）
- [ ] 精简未使用的依赖项
