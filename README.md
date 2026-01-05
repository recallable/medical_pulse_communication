# Medical Pulse Communication Backend

## 项目简介

这是一个基于 **FastAPI** 框架构建的高性能异步后端服务，专为医疗脉搏通讯应用设计。项目采用了现代化的异步技术栈，集成了数据库、缓存、对象存储、OCR 识别等多种基础设施，旨在提供稳定、高效、可扩展的医疗数据通讯服务。

## 核心特性

- **高性能异步框架**: 基于 FastAPI，充分利用 Python 的异步特性。
- **异步 ORM**: 使用 Tortoise ORM，支持 PostgreSQL，具备自动建表和迁移功能。
- **高效缓存**: 集成 Redis 连接池，用于短信验证码存储和高频数据缓存。
- **对象存储**: 对接 MinIO，实现医疗影像、身份证等文件的上传与管理。
- **多方式认证**:
  - JWT (JSON Web Token) 无状态认证。
  - 支持账号密码登录。
  - 支持手机短信验证码登录。
  - 策略模式设计，易于扩展第三方登录（如微信、钉钉）。
- **OCR 集成**: 内置百度 OCR 接口，支持身份证正反面自动识别。
- **规范化开发**:
  - 统一的 API 响应格式。
  - 全局异常处理与日志记录。
  - 基于 Pydantic 的强类型数据验证。
  - 依赖注入 (DI) 架构。

## 技术栈

- **Web 框架**: FastAPI
- **语言**: Python 3.10+
- **数据库**: PostgreSQL + Tortoise ORM
- **缓存**: Redis + aioredis
- **对象存储**: MinIO
- **认证安全**: JWT + Passlib (Bcrypt)
- **第三方服务**:
  - 百度 AI (OCR)
  - 容联云 (短信服务)
  - 钉钉 (集成中)

## 目录结构

```
medical_pulse_communication/
├── api/                # API 路由层
│   ├── uploader/       # 文件上传相关接口
│   └── user/           # 用户相关接口
├── core/               # 核心配置与组件
│   ├── config.py       # 环境变量配置
│   ├── deps.py         # 依赖注入
│   └── redis_client.py # Redis 客户端管理
├── crud/               # 数据库访问层 (CRUD)
├── middleware/         # 中间件 (认证、日志、异常)
│   ├── authentication.py # JWT 认证中间件
│   ├── exception.py      # 全局异常处理
│   └── logging.py        # 访问日志记录
├── models/             # 数据模型
│   ├── entity/         # 数据库实体 (ORM)
│   └── schemas/        # Pydantic 校验模型
├── services/           # 业务逻辑层
│   ├── strategy/       # 策略模式实现 (如登录策略)
│   └── minio_service.py # MinIO 业务封装
├── utils/              # 工具类
│   ├── jwt_utils.py      # JWT 工具
│   ├── password_utils.py # 密码加密工具
│   ├── response.py       # 统一响应封装
│   └── sms_utils.py      # 短信发送工具
└── main.py             # 程序入口
```

## 快速开始

### 1. 环境准备

- Python 3.10+
- PostgreSQL
- Redis
- MinIO

### 2. 安装依赖

```bash
pip install -r requirements.txt
```
*(注：请确保项目根目录下有 requirements.txt，或手动安装 fastapi, uvicorn, tortoise-orm, asyncpg, redis, minio, httpx, python-multipart 等库)*

### 3. 配置环境变量

在项目根目录创建 `.env` 文件（或直接修改 `core/config.py` 中的默认值）：

```env
DATABASE_URL=postgres://user:pass@localhost:5432/medical_pulse
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_minio_key
MINIO_SECRET_KEY=your_minio_secret
BAIDU_OCR_APP_KEY=your_baidu_key
BAIDU_OCR_SECRET_KEY=your_baidu_secret
```

### 4. 运行服务

```bash
python main.py
```
或使用 uvicorn 命令：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问文档

启动成功后，访问浏览器查看自动生成的 API 文档：
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 系统架构详解

### 1. 中间件机制 (Middleware)

项目内置了三个核心中间件，确保系统的安全性与可维护性：

- **AuthenticationMiddleware** ([middleware/authentication.py](middleware/authentication.py)):
  - 拦截所有请求，验证 Header 中的 JWT Token。
  - 内置白名单机制，自动放行 `/docs`, `/api/v1/user/login` 等无需认证的接口。
  - 验证通过后，将用户信息注入 `request.state` 供后续业务使用。

- **ExceptionHandlerMiddleware** ([middleware/exception.py](middleware/exception.py)):
  - 全局捕获 `BusinessException` (业务异常)、`HTTPException` (HTTP异常) 和 `RequestValidationError` (参数校验异常)。
  - 统一返回 JSON 格式的错误响应，避免前端处理复杂的 HTML 错误页。

- **AccessLogHandlerMiddleware** ([middleware/logging.py](middleware/logging.py)):
  - 记录每个请求的方法、路径、状态码、客户端 IP 及处理耗时。
  - 日志文件按天自动轮转，保存在 `logs/` 目录下。

### 2. 核心业务流程

#### 身份证 OCR 识别
1. 用户调用 `/api/v1/user/ocr` 上传身份证图片。
2. 后端接收文件，首先通过内部服务将其上传至 MinIO 对象存储，并记录文件元数据到数据库。
3. 随后，后端异步调用百度 AI 开放平台的 OCR 接口。
4. 获取识别结果后，进行业务校验（如身份证正反面、清晰度等）。
5. 最终返回结构化的身份证信息（姓名、身份证号）及文件 ID。

#### 用户登录 (策略模式)
- 采用策略模式设计，支持多种登录方式。
- `UserLoginStrategy` 定义标准接口。
- `UsernamePasswordStrategy` 实现账号密码登录。
- `SmsCodeStrategy` 实现手机验证码登录。
- 通过 `LoginStrategyFactory` 根据请求参数自动选择对应的策略类进行处理。

## API 说明

### 用户模块 (User)

- `POST /api/v1/user/login`: 用户登录
  - 支持 `login_type="username"` (账号密码)
  - 支持 `login_type="sms"` (手机验证码)
- `POST /api/v1/user/ocr`: 身份证 OCR 识别
  - 上传身份证图片，自动识别姓名和身份证号

### 文件模块 (Minio)

- `POST /api/v1/minio/upload`: 文件上传
  - 支持多种文件类型，自动保存至 MinIO 并记录数据库

## 测试指南

项目包含单元测试和集成测试，位于 `test/` 目录下。

```bash
# 运行所有测试
python -m unittest discover test
```

- `baldu_ocr_test.py`: 百度 OCR 接口的独立测试。
- `url_test.py`: API 接口的可用性测试。

## 贡献指南

1. Fork 本项目。
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4. 推送到分支 (`git push origin feature/AmazingFeature`)。
5. 打开一个 Pull Request。
