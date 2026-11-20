export interface GridCell {
  key: string | number;
  weekday: number;
  start_period: number;
  end_period: number;
  title: string;
  sub?: string;
  color: string;
  to?: string;
  /** 选课单中的意向课程，以虚线样式展示。 */
  ghost?: boolean;
  conflict?: boolean;
}
