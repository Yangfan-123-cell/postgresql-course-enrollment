# 选课系统后端

## 本地启动

使用 Python 3.12 和已执行 `sql/01_schema.sql` 的 PostgreSQL 16。以下命令在仓库根目录的 PowerShell 中运行。

```powershell
py -3.12 -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -e "./backend[test]"
if (!(Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
```

编辑 `backend/.env`，将 `DATABASE_URL` 设为本地数据库的连接地址，并填写至少 32 字节的随机 `JWT_SECRET`。现有账号的密码哈希使用 bcrypt。需要共享限流和课程列表缓存时，填写 Redis 7 的 `REDIS_URL`。单进程开发时可以省略 Redis，登录与学生写接口限流由当前进程执行。

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Swagger 在 `http://127.0.0.1:8000/docs`，API 前缀为 `/api/v1`。登录返回的 `access_token` 用作后续请求的 Bearer token。

## 契约与联调

- `openapi.json` 是共享契约快照，包含选课、统计和压测接口的类型。运行时 Swagger 展示已挂载的接口。
- 其他后端路由可重用 `app.core.security` 的 `CurrentUser`、`Admin` 和 `StudentWriter` 依赖，以及 `app.core.errors` 的 `ApiError`。
- 当前 SQL 以文本存储院系。API 使用 `DEPARTMENT_NAMES` 将 `dept_id` 映射为院系名，默认按 1 至 5 映射到计算机、软件工程、数学、物理、电子。
- 教学班详情的 `description` 和 `batch` 在当前 SQL 中无对应列，目前返回 `null`。
- 名单的晋升来源优先从 `audit_log.after.enrollment_id` 识别，也支持 `after.student_id` 或以被晋升学生作为 `actor_id`。
- 抢课压测从同一 IP 批量登录，按接口契约第 6 次请求会返回 `429 RATE_LIMITED`。正式压测前需准备测试 token。

```powershell
.\backend\.venv\Scripts\python.exe -m app.openapi_contract
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
```

将 `TEST_DATABASE_URL` 设为有创建 schema 权限的 PostgreSQL 测试库连接后再运行 pytest，可同时验证真实数据库上的接口。测试创建一个独立 schema 并在结束后删除该测试 schema。
