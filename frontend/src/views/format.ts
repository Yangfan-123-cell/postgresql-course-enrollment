import type { Meeting } from "../api/types";
import { PALETTE, PERIODS } from "./config";

export const weekdays = ["一", "二", "三", "四", "五", "六", "日"];

export function meetingText(meetings: Meeting[]) {
  return (
    meetings
      .map(
        (m) =>
          `周${weekdays[m.weekday - 1]} ${m.start_period}–${m.end_period} 节`,
      )
      .join(" / ") || "暂未排课"
  );
}

/** 节次对应的具体时间，例如 08:00–09:35。 */
export function periodTime(m: Pick<Meeting, "start_period" | "end_period">) {
  const start = PERIODS[m.start_period - 1]?.[0],
    end = PERIODS[m.end_period - 1]?.[1];
  return start && end ? `${start}–${end}` : "";
}

export function dateText(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

export function shortDate(value: string) {
  const d = new Date(value);
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

export function colorOf(id: number) {
  return PALETTE[Math.abs(id) % PALETTE.length]!;
}

export function overlaps(a: Meeting, b: Meeting) {
  return (
    a.weekday === b.weekday &&
    a.start_period <= b.end_period &&
    b.start_period <= a.end_period
  );
}

/** 返回与 meetings 时间冲突的课程名称（去重）。 */
export function conflictNames(
  meetings: Meeting[],
  others: { id: number; name: string; meetings: Meeting[] }[],
  selfId?: number,
) {
  const names = others
    .filter(
      (o) =>
        o.id !== selfId &&
        o.meetings.some((a) => meetings.some((b) => overlaps(a, b))),
    )
    .map((o) => o.name);
  return [...new Set(names)];
}

export function periodCount(meetings: Meeting[]) {
  return meetings.reduce((sum, m) => sum + m.end_period - m.start_period + 1, 0);
}

/** 当前 ISO 周几，1 = 周一。 */
export function todayWeekday() {
  const d = new Date().getDay();
  return d === 0 ? 7 : d;
}

export function greeting() {
  const h = new Date().getHours();
  if (h < 6) return "夜深了";
  if (h < 11) return "早上好";
  if (h < 13) return "中午好";
  if (h < 18) return "下午好";
  return "晚上好";
}

export function fillLevel(enrolled: number, capacity: number) {
  const ratio = capacity ? enrolled / capacity : 1;
  if (ratio >= 1) return "full";
  if (ratio >= 0.85) return "high";
  if (ratio >= 0.5) return "mid";
  return "low";
}

export function downloadCsv(filename: string, rows: (string | number)[][]) {
  const text = rows
    .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const url = URL.createObjectURL(
    new Blob(["\uFEFF" + text], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
