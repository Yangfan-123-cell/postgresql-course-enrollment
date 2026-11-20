import { setupWorker } from "msw/browser";
import { http, HttpResponse } from "msw";
import type {
  Course,
  Section,
  Enrollment,
  Waitlist,
  CourseInput,
  SectionInput,
  User,
} from "./types";

const names = [
  "高级数据库系统",
  "机器学习",
  "分布式系统",
  "计算机网络",
  "算法设计与分析",
  "操作系统",
  "人工智能导论",
  "信息安全",
  "编译原理",
  "软件工程",
  "计算机图形学",
  "并发编程",
];
const courses: Course[] = names.map((name, i) => ({
  id: i + 1,
  code: `CS${301 + i}`,
  name,
  credits: i % 3 === 0 ? 4 : 3,
  dept: "计算机学院",
  archived: false,
}));
const sections: Section[] = courses.map((course, i) => ({
  id: i + 1,
  course,
  term: "2026-FALL",
  teacher: ["陈教授", "李老师", "王教授", "张老师"][i % 4]!,
  capacity: 60,
  enrolled_count: i === 1 ? 60 : 25 + i,
  remaining: i === 1 ? 0 : 35 - i,
  waitlist_count: i === 1 ? 3 : 0,
  meetings: [
    {
      weekday: (i % 5) + 1,
      start_period: Math.floor(i / 5) * 2 + 1,
      end_period: Math.floor(i / 5) * 2 + 2,
    },
  ],
  description: `${course.name}课程注重理论与实践结合，通过课堂研讨与实验项目掌握关键方法。`,
  batch: "研究生秋季选课",
}));
const students = new Map<
  string,
  { items: Enrollment[]; waiting: Waitlist[] }
>();
// 特意保留一个时间冲突教学班，用于验证 TIME_CONFLICT 展示。
sections[11]!.meetings = [{ weekday: 1, start_period: 1, end_period: 2 }];
let serial = 100,
  selectionOpen = true;
const base = "/api/v1";
const fail = (status: number, code: string, message: string, details = {}) =>
  HttpResponse.json({ error: { code, message, details } }, { status });
function user(request: Request): User | undefined {
  const token = request.headers
    .get("Authorization")
    ?.replace("Bearer mock-", "");
  if (!token || !["S0001", "S0002", "admin"].includes(token)) return undefined;
  return {
    id: token === "admin" ? 1 : Number(token.slice(1)) + 1,
    student_no: token,
    name:
      token === "admin"
        ? "教务管理员"
        : token === "S0001"
          ? "杨帆"
          : "演示同学",
    role: token === "admin" ? "admin" : "student",
    major: "计算机技术",
  };
}
function state(request: Request) {
  const no = user(request)!.student_no;
  if (!students.has(no)) students.set(no, { items: [], waiting: [] });
  return students.get(no)!;
}
function paged<T>(items: T[], url: URL) {
  const page = Number(url.searchParams.get("page") || 1),
    size = Number(url.searchParams.get("size") || 20);
  return HttpResponse.json({
    items: items.slice((page - 1) * size, page * size),
    total: items.length,
    page,
    size,
  });
}
// 演示服务仅复现契约，不用于验证 PostgreSQL 并发正确性。
export const worker = setupWorker(
  http.all(`${base}/*`, ({ request }) => {
    if (new URL(request.url).pathname === `${base}/auth/login`) return;
    const current = user(request);
    if (!current) return fail(401, "UNAUTHORIZED", "登录已过期，请重新登录");
    const path = new URL(request.url).pathname;
    if (path.includes("/admin/") && current.role !== "admin")
      return fail(403, "FORBIDDEN", "仅管理员可操作");
    if (
      (path.includes("/me/") ||
        path.includes("/enrollments") ||
        path.includes("/waitlist")) &&
      current.role !== "student"
    )
      return fail(403, "FORBIDDEN", "仅学生可操作");
  }),
  http.post(`${base}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as {
      student_no: string;
      password: string;
    };
    if (
      !["S0001", "S0002", "admin"].includes(body.student_no) ||
      body.password !== "Passw0rd!"
    )
      return fail(401, "UNAUTHORIZED", "账号或密码错误");
    const headers = new Headers({
      Authorization: `Bearer mock-${body.student_no}`,
    });
    return HttpResponse.json({
      access_token: `mock-${body.student_no}`,
      token_type: "bearer",
      expires_in: 43200,
      user: user(new Request(request.url, { headers })),
    });
  }),
  http.get(`${base}/auth/me`, ({ request }) =>
    HttpResponse.json(user(request)),
  ),
  http.get(`${base}/sections`, ({ request }) => {
    const url = new URL(request.url),
      keyword = url.searchParams.get("keyword") || "";
    return paged(
      sections.filter(
        (s) =>
          s.term === url.searchParams.get("term") &&
          `${s.course.name}${s.course.code}`.includes(keyword) &&
          (url.searchParams.get("only_open") !== "true" || s.remaining > 0) &&
          (!url.searchParams.get("dept_id") ||
            url.searchParams.get("dept_id") === "1"),
      ),
      url,
    );
  }),
  http.get(`${base}/sections/:id`, ({ params }) => {
    const section = sections.find((s) => s.id === Number(params.id));
    return section
      ? HttpResponse.json(section)
      : fail(404, "NOT_FOUND", "教学班不存在");
  }),
  http.post(`${base}/enrollments`, async ({ request }) => {
    if (!selectionOpen)
      return fail(423, "SELECTION_CLOSED", "当前选课阶段已关闭");
    const body = (await request.json()) as {
        section_id: number;
        allow_waitlist: boolean;
      },
      section = sections.find((s) => s.id === body.section_id),
      current = state(request);
    if (!section) return fail(404, "NOT_FOUND", "教学班不存在");
    if (
      current.items.some((e) => e.section_id === section.id) ||
      current.waiting.some((e) => e.section_id === section.id)
    )
      return fail(409, "ALREADY_ENROLLED", "该课程已选或已在候补队列");
    const conflicts = current.items.flatMap((e) =>
      e.meetings
        .filter((a) =>
          section.meetings.some(
            (b) =>
              a.weekday === b.weekday &&
              a.start_period <= b.end_period &&
              b.start_period <= a.end_period,
          ),
        )
        .map((m) => ({ ...m, with_course_name: e.course.name })),
    );
    if (conflicts.length)
      return fail(409, "TIME_CONFLICT", "与已选课程时间冲突", { conflicts });
    if (!section.remaining) {
      if (!body.allow_waitlist)
        return fail(409, "SECTION_FULL", "该教学班已满");
      const entry: Waitlist = {
        id: ++serial,
        section_id: section.id,
        course_name: section.course.name,
        position: ++section.waitlist_count,
        section_enrolled: section.enrolled_count,
        section_capacity: section.capacity,
        joined_at: new Date().toISOString(),
      };
      current.waiting.push(entry);
      return HttpResponse.json(
        { status: "WAITLISTED", waitlist: entry },
        { status: 202 },
      );
    }
    const entry: Enrollment = {
      enrollment_id: ++serial,
      section_id: section.id,
      course: section.course,
      meetings: section.meetings,
      enrolled_at: new Date().toISOString(),
    };
    current.items.push(entry);
    section.enrolled_count++;
    section.remaining--;
    return HttpResponse.json(
      {
        status: "ENROLLED",
        enrollment: {
          id: entry.enrollment_id,
          section_id: section.id,
          course_name: section.course.name,
          teacher: section.teacher,
          meetings: section.meetings,
          enrolled_at: entry.enrolled_at,
        },
      },
      { status: 201 },
    );
  }),
  http.get(`${base}/me/enrollments`, ({ request }) =>
    HttpResponse.json({
      items: state(request).items,
      total: state(request).items.length,
    }),
  ),
  http.get(`${base}/me/waitlist`, ({ request }) =>
    HttpResponse.json({
      items: state(request).waiting,
      total: state(request).waiting.length,
    }),
  ),
  http.delete(`${base}/enrollments/:id`, ({ request, params }) => {
    if (!selectionOpen)
      return fail(423, "SELECTION_CLOSED", "选课已关闭，暂不能退课");
    const current = state(request),
      entry = current.items.find((e) => e.enrollment_id === Number(params.id));
    if (!entry) return fail(404, "NOT_FOUND", "选课记录不存在");
    current.items = current.items.filter((e) => e !== entry);
    const section = sections.find((s) => s.id === entry.section_id)!;
    section.enrolled_count--;
    section.remaining++;
    return new HttpResponse(null, { status: 204 });
  }),
  http.delete(`${base}/waitlist/:id`, ({ request, params }) => {
    const current = state(request),
      entry = current.waiting.find((e) => e.id === Number(params.id));
    if (!entry)
      return fail(409, "ALREADY_ENROLLED", "候补状态已变化，请刷新我的课程");
    current.waiting = current.waiting.filter((e) => e !== entry);
    sections.find((s) => s.id === entry.section_id)!.waitlist_count--;
    return new HttpResponse(null, { status: 204 });
  }),
  http.get(`${base}/me/timetable`, ({ request }) =>
    HttpResponse.json({
      term: "2026-FALL",
      cells: state(request).items.flatMap((e) =>
        e.meetings.map((m) => ({
          ...m,
          course_name: e.course.name,
          section_id: e.section_id,
          color: "#4E79A7",
        })),
      ),
    }),
  ),
  http.get(`${base}/admin/courses`, ({ request }) => {
    const url = new URL(request.url);
    return paged(
      courses.filter(
        (c) =>
          c.archived === (url.searchParams.get("archived") === "true") &&
          `${c.code}${c.name}`.includes(url.searchParams.get("keyword") || ""),
      ),
      url,
    );
  }),
  http.post(`${base}/admin/courses`, async ({ request }) => {
    const body = (await request.json()) as CourseInput;
    if (courses.some((c) => c.code === body.code))
      return fail(409, "DUPLICATE_RESOURCE", "课程号已存在");
    const course = {
      ...body,
      id: ++serial,
      dept: `院系 ${body.dept_id}`,
      archived: false,
    };
    courses.push(course);
    return HttpResponse.json(course, { status: 201 });
  }),
  http.patch(`${base}/admin/courses/:id`, async ({ request, params }) => {
    const course = courses.find((c) => c.id === Number(params.id)),
      body = (await request.json()) as Partial<CourseInput>;
    if (!course) return fail(404, "NOT_FOUND", "课程不存在");
    if (courses.some((c) => c.id !== course.id && c.code === body.code))
      return fail(409, "DUPLICATE_RESOURCE", "课程号已存在");
    Object.assign(course, body);
    return HttpResponse.json(course);
  }),
  http.get(`${base}/admin/sections`, ({ request }) => {
    const url = new URL(request.url);
    return paged(
      sections
        .filter((s) => s.term === url.searchParams.get("term"))
        .map((s) => ({ ...s, selection_open: selectionOpen })),
      url,
    );
  }),
  http.post(`${base}/admin/sections`, async ({ request }) => {
    const body = (await request.json()) as SectionInput,
      course = courses.find((c) => c.id === body.course_id);
    if (!course) return fail(404, "NOT_FOUND", "课程 ID 不存在");
    if (
      sections.some(
        (s) => s.course.id === body.course_id && s.term === body.term,
      )
    )
      return fail(409, "DUPLICATE_RESOURCE", "同课程同学期已有教学班");
    const section = {
      ...body,
      id: ++serial,
      course,
      enrolled_count: 0,
      remaining: body.capacity,
      waitlist_count: 0,
    };
    sections.push(section);
    return HttpResponse.json(section, { status: 201 });
  }),
  http.patch(`${base}/admin/sections/:id`, async ({ request, params }) => {
    const body = (await request.json()) as SectionInput,
      section = sections.find((s) => s.id === Number(params.id));
    if (!section) return fail(404, "NOT_FOUND", "教学班不存在");
    if (body.capacity < section.enrolled_count)
      return fail(409, "CAPACITY_BELOW_ENROLLED", "容量不能小于当前选课人数");
    Object.assign(section, body);
    section.remaining = section.capacity - section.enrolled_count;
    return HttpResponse.json(section);
  }),
  http.get(`${base}/admin/sections/:id/roster`, ({ request }) =>
    paged(
      [
        {
          student_no: "S0001",
          name: "杨帆",
          enrolled_at: new Date().toISOString(),
          source: "ENROLL",
        },
      ],
      new URL(request.url),
    ),
  ),
  http.get(
    `${base}/admin/sections/:id/roster.csv`,
    () =>
      new HttpResponse(
        "\uFEFF学号,姓名,选课时间,来源\nS0001,杨帆,2026-11-20T10:00:00+08:00,ENROLL",
        { headers: { "Content-Type": "text/csv; charset=utf-8" } },
      ),
  ),
  http.post(`${base}/admin/selection/:action`, ({ params }) => {
    selectionOpen = params.action === "open";
    return HttpResponse.json({ selection_open: selectionOpen });
  }),
);
