# 杨帆 · 学生端与教务管理前端

使用 Vue 3、TypeScript、Vite、Pinia、Vue Router 和 Axios。全部 HTTP 请求集中在 `src/api/`，业务页面不内联后端 URL；没有修改其他成员的数据库、后端、公共组件和设计文档。

## 运行与检查

以下命令用于 Windows PowerShell，工作目录为 `frontend`。本次验证使用 Node.js 24.14.1，依赖版本由 `package-lock.json` 锁定。

```powershell
npm ci
npm run dev:mock
```

打开 `http://127.0.0.1:5173`。学生演示账号 `S0001`（杨帆）、`S0002`，管理员账号 `admin`，密码均为 `Passw0rd!`。页面顶部始终标记 Mock 演示。演示数据存在当前浏览器页面内存中，整页刷新会重置选课数据；路由切换不会重置。

```powershell
# 真实 API 模式，默认代理 localhost:8000
npm run dev
# TypeScript 检查及生产打包
npm run build
# 浏览器交互测试，默认使用已安装的 Microsoft Edge
npm test
```

没有 Edge 的环境可将 `playwright.config.ts` 的 `channel` 改为已安装浏览器，或安装 Playwright Chromium 后移除 `channel`。测试会自行启动 mock 开发服务器，固定端口 5173；运行测试前请关闭使用同一端口的真实 API 开发服务器。

后端地址可通过 `.env.local` 中的 `API_PROXY_TARGET` 调整，API 前缀由 `VITE_API_BASE_URL` 控制，参考 `.env.example`。生产部署需将 `/api` 反向代理至后端，并将前端路由回退到 `index.html`。默认生产构建不加载 mock 模块；不要以 mock mode 构建交付物。

## 已交付页面

| 路径            | 内容                                                                                  |
| --------------- | ------------------------------------------------------------------------------------- |
| `/login`        | 登录、失败提示、会话恢复、退出与过期重定向                                            |
| `/hall`         | 学期、关键词、院系 ID、余位筛选、分页、201/202/错误三态                               |
| `/sections/:id` | 课程详情、时间、容量、候补选项、冲突详情                                              |
| `/my-courses`   | 课程、学分、选课时间、确认退课与刷新                                                  |
| `/waitlist`     | 排位、容量、确认放弃候补、晋升后状态刷新                                              |
| `/timetable`    | 周一至周日、1–12 节，服务端颜色与跨节次布局                                           |
| `/admin`        | 课程创建/编辑/归档，教学班创建/编辑、多段排课校验、名单分页及 CSV 下载、选课开放/关闭 |

学生与管理员有独立路由守卫，token 使用 sessionStorage 并通过 Axios 添加 Bearer 头。按钮提交期间禁用，错误展示服务端消息。课程院系 ID 需要按后端约定填写，目前契约没有院系列表接口；课程编辑不提交猜测的院系 ID。课表暂在 view 内实现，供 E 交付公共 TimetableGrid 后替换，未占用 `src/components/`。

## 验证结果（2026-11-20）

- `npm run build`：通过，包含 `vue-tsc --noEmit`。
- `npm test`：5 组 Edge 浏览器测试，覆盖登录失败/过期、角色限制、分页/搜索/空态、移动端无横向溢出、201 选课、202 候补、409 满员/重复/时间冲突、退课、放弃候补、课表、课程创建编辑、教学班创建编辑、排课重叠和容量校验、名单和 CSV 下载、开放/关闭选课。
- `npm audit`：未发现已知依赖漏洞。
- 截图输出至被 Git 忽略的 `test-results/`：`hall-desktop.png`、`hall-mobile.png`、`timetable-desktop.png`、`admin-desktop.png`。

## 联调交接与限制

接口依据 `docs/02_接口设计.md` v0.1，`src/api/types.ts` 是手写契约类型，并非已从后端生成。C 尚未交付 OpenAPI，后端就绪后运行 `npm run gen:api` 生成 `src/api/generated.ts`，核对字段并接入类型。尤其需要确认 `/me/enrollments` 中 `course` 的完整结构、管理教学班对象的完整字段，以及 `dept_id` 与当前 SQL `dept` 字符串的映射。

目前没有真实后端，浏览器测试使用独立 MSW 拦截层，因此**未验证真实 JWT、PostgreSQL、候补自动晋升与并发正确性，也未完成真实 API 联调**。Mock 名单和计数是演示夹具，不模拟数据库事务或队列晋升，不能作为数据库实验结果。统计看板和审计对账属于 E，未包含在本次实现。
