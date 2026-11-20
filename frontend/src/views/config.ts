// 前端展示配置：学期、选课轮次、节次时间与公告。
// 这些内容目前接口契约中没有对应字段，统一在此维护；后端提供接口后替换即可。
// 真正的“选课是否开放”以服务端 selection_open / 423 SELECTION_CLOSED 为准。

export const TERM = {
  code: "2026-FALL",
  name: "2026–2027 学年秋季学期",
  short: "2026 秋季",
};

export const TERMS = [
  { code: "2026-FALL", name: "2026 秋季学期" },
  { code: "2026-SPRING", name: "2026 春季学期" },
  { code: "2025-FALL", name: "2025 秋季学期" },
];

/** 学分指导区间（培养方案建议值，不由前端强制）。 */
export const CREDIT_RULE = { min: 12, max: 25 };

export interface Round {
  key: string;
  name: string;
  start: string;
  end: string;
  desc: string;
}

export const ROUNDS: Round[] = [
  {
    key: "pre",
    name: "预选登记",
    start: "2026-11-10T09:00:00+08:00",
    end: "2026-11-14T17:00:00+08:00",
    desc: "浏览课程、加入选课单，不占用名额",
  },
  {
    key: "main",
    name: "正选",
    start: "2026-11-17T09:00:00+08:00",
    end: "2026-11-24T17:00:00+08:00",
    desc: "实时抢占名额，满员可加入候补",
  },
  {
    key: "adjust",
    name: "补退选",
    start: "2026-11-27T09:00:00+08:00",
    end: "2026-12-01T17:00:00+08:00",
    desc: "补选空余名额，退课后候补自动晋升",
  },
  {
    key: "publish",
    name: "结果公布",
    start: "2026-12-03T09:00:00+08:00",
    end: "2026-12-03T18:00:00+08:00",
    desc: "名单锁定，生成正式课表",
  },
];

export type RoundStatus = "done" | "current" | "upcoming";

export function roundStatus(round: Round, now: number): RoundStatus {
  if (now >= Date.parse(round.end)) return "done";
  if (now >= Date.parse(round.start)) return "current";
  return "upcoming";
}

/** 当前进行中的轮次；若处于间隔期则返回下一个轮次。 */
export function activeRound(now: number) {
  const current = ROUNDS.find((r) => roundStatus(r, now) === "current");
  if (current)
    return { round: current, running: true, target: Date.parse(current.end) };
  const next = ROUNDS.find((r) => roundStatus(r, now) === "upcoming");
  if (next)
    return { round: next, running: false, target: Date.parse(next.start) };
  return undefined;
}

export function countdown(target: number, now: number) {
  const diff = Math.max(0, target - now);
  return {
    days: Math.floor(diff / 86_400_000),
    hours: Math.floor((diff % 86_400_000) / 3_600_000),
    minutes: Math.floor((diff % 3_600_000) / 60_000),
  };
}

/** 1–12 节作息时间。 */
export const PERIODS: [string, string][] = [
  ["08:00", "08:45"],
  ["08:50", "09:35"],
  ["10:05", "10:50"],
  ["10:55", "11:40"],
  ["14:00", "14:45"],
  ["14:50", "15:35"],
  ["16:05", "16:50"],
  ["16:55", "17:40"],
  ["19:00", "19:45"],
  ["19:50", "20:35"],
  ["20:40", "21:25"],
  ["21:30", "22:15"],
];

export const PERIOD_GROUPS = [
  { label: "上午", from: 1, to: 4 },
  { label: "下午", from: 5, to: 8 },
  { label: "晚上", from: 9, to: 12 },
];

export interface Notice {
  id: number;
  date: string;
  tag: string;
  title: string;
  body: string;
  important?: boolean;
}

export const NOTICES: Notice[] = [
  {
    id: 4,
    date: "2026-11-19",
    tag: "选课",
    title: "2026 秋季学期研究生正选阶段开放通知",
    body: "正选阶段于 11 月 17 日 09:00 开放，11 月 24 日 17:00 截止。名额实时校验、先到先得，满员课程可选择加入候补队列。",
    important: true,
  },
  {
    id: 3,
    date: "2026-11-18",
    tag: "候补",
    title: "关于候补队列自动晋升规则的说明",
    body: "教学班出现空余名额时，系统按候补加入时间顺序自动晋升，晋升结果可在“我的课程”中查看，存在时间冲突的候补将被跳过。",
  },
  {
    id: 2,
    date: "2026-11-15",
    tag: "教务",
    title: "补退选阶段时间安排及注意事项",
    body: "补退选阶段为 11 月 27 日至 12 月 1 日。退课操作立即生效，释放的名额将优先分配给候补同学，请谨慎操作。",
  },
  {
    id: 1,
    date: "2026-11-12",
    tag: "系统",
    title: "选课高峰期访问指引",
    body: "开放首小时访问量较大，请勿频繁刷新或使用脚本提交。系统对单个账号限流（5 次/秒），提交后请以页面返回结果为准。",
  },
];

export const RULES = [
  "选课结果以服务端提交结果为准，页面名额仅供参考。",
  "同一教学班不可重复选择，已候补的课程也视为已选。",
  "与已选课程时间冲突的教学班将被拒绝。",
  "满员课程可加入候补，退出后再次加入需重新排队。",
];

export const PALETTE = [
  "#2f5fb3",
  "#2b8a6e",
  "#c26a2b",
  "#8150b8",
  "#c23f5f",
  "#25869e",
  "#9b7a1c",
  "#4f5cc7",
];
