import type { Meeting } from "../api/types";
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
export function dateText(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}
