# 基于 PostgreSQL 行锁与乐观锁的高并发选课系统设计与压测分析

高级数据库系统课程项目。系统覆盖选课防超卖、候补与退课晋升、课表冲突检测、教务管理和统计报表。实验重点是比较 PostgreSQL 并发控制、事务隔离级别和索引对正确性及性能的影响。

计划使用 FastAPI、Vue 3、PostgreSQL 16、Redis 和 k6。当前仓库包含设计文档、建表与种子 SQL、压测和对账脚本，以及杨帆负责的 Vue 3 学生端和教务管理前端。后端和 Docker Compose 配置待实现，k6 脚本需要可用的 API 和测试账号。种子脚本中的账号和凭据为本地测试示例，密码哈希待替换。

## 前端运行（杨帆）

在 Windows PowerShell 中：

```powershell
cd frontend
npm ci
npm run dev:mock
```

打开 `http://127.0.0.1:5173`。Mock 学生账号 `S0001`、`S0002`，管理员 `admin`，演示密码均为 `Passw0rd!`。真实 API 模式运行 `npm run dev`，默认代理至 `http://localhost:8000`；生产构建为 `npm run build`。详细页面、测试和联调限制见 [frontend/README.md](frontend/README.md)。

## 五人分工

| 代号 | 成员 | 负责内容 |
| --- | --- | --- |
| A | 王明磊 | 选课并发策略、退课与候补晋升、排课冲突检测、选课接口及并发测试 |
| B | 李嘉桐 | PostgreSQL 表结构与迁移、种子数据、Docker 与 CI、k6 压测、EXPLAIN 索引实验 |
| C | 汪凯乐 | API 契约、鉴权和错误处理、课程浏览与教务管理等后端接口 |
| D | 杨帆 | 登录、选课大厅、我的课程、候补、课表和管理端页面，负责页面与接口联调 |
| E | 胡河 | 公共组件、统计接口与看板、对账展示、报告与演示 |

每周任务、模块归属和交付节点见[分工与排期](docs/03_五人分工与排期.md)。

## 数据库实验

- 比较 V0 朴素实现、V1 `SELECT ... FOR UPDATE`、V2 基于版本号的乐观锁和 V3 原子条件更新。
- 对比 `READ COMMITTED`、`REPEATABLE READ` 和 `SERIALIZABLE` 下的超卖、锁等待、事务失败与重试。
- 用 k6 记录 QPS、P95/P99 延迟与错误分布，并用对账 SQL 查询超卖、重复选课和计数偏差等问题。
- 用 `EXPLAIN (ANALYZE, BUFFERS)` 对比索引优化前后的查询计划。设计文档中的性能预期将在报告中用实测结果替换。

## 文件索引

| 文件 | 内容 |
| --- | --- |
| [技术设计](docs/01_技术设计文档.md) | 系统架构、数据库约束、并发策略、隔离级别实验与压测方案 |
| [接口设计](docs/02_接口设计.md) | API 路径、请求与响应、错误码、权限矩阵 |
| [Git 与 PR 协作](docs/04_协作规范_Git与PR.md) | 分支命名、提交流程和代码审查 |
| [`sql/01_schema.sql`](sql/01_schema.sql)、[`sql/02_seed.sql`](sql/02_seed.sql) | 建表、索引与测试数据脚本 |
| [`bench/k6_grab.js`](bench/k6_grab.js)、[`bench/k6_browse.js`](bench/k6_browse.js) | 抢课与课程浏览压测 |
| [`bench/reconcile.sql`](bench/reconcile.sql) | 压测后的数据对账 |

## 提交流程

从 `main` 新建功能分支，把改动推送到同一仓库，再提 Pull Request 合入 `main`。接口字段和错误码有变更时，同步更新接口文档并通知相关成员。
