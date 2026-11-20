// 依据 docs/02_接口设计.md v0.1 手写；C 交付 OpenAPI 后用 gen:api 生成并核对。
export interface User {
  id: number;
  student_no: string;
  name: string;
  role: "student" | "admin";
  major?: string;
}
export interface Meeting {
  weekday: number;
  start_period: number;
  end_period: number;
}
export interface Course {
  id: number;
  code: string;
  name: string;
  credits: number;
  dept: string;
  archived?: boolean;
}
export interface Section {
  id: number;
  course: Course;
  term: string;
  teacher: string;
  capacity: number;
  enrolled_count: number;
  remaining: number;
  waitlist_count: number;
  meetings: Meeting[];
  description?: string;
  batch?: string;
  selection_open?: boolean;
}
export interface Page<T> {
  items: T[];
  total: number;
  page?: number;
  size?: number;
}
export interface Enrollment {
  enrollment_id: number;
  section_id: number;
  course: Course;
  meetings: Meeting[];
  enrolled_at: string;
}
export interface Waitlist {
  id: number;
  section_id: number;
  course_name: string;
  position: number;
  section_enrolled: number;
  section_capacity: number;
  joined_at: string;
}
export interface Cell extends Meeting {
  course_name: string;
  section_id: number;
  color: string;
}
export interface Timetable {
  term: string;
  cells: Cell[];
}
export interface Roster {
  student_no: string;
  name: string;
  enrolled_at: string;
  source: "ENROLL" | "PROMOTED";
}
export type EnrollmentResult =
  | {
      status: "ENROLLED";
      enrollment: {
        id: number;
        section_id: number;
        course_name: string;
        teacher: string;
        meetings: Meeting[];
        enrolled_at: string;
      };
    }
  | {
      status: "WAITLISTED";
      waitlist: {
        id: number;
        section_id: number;
        position: number;
        joined_at: string;
      };
    };
export interface CourseInput {
  code: string;
  name: string;
  credits: number;
  dept_id: number;
  archived?: boolean;
}
export interface SectionInput {
  course_id: number;
  term: string;
  teacher: string;
  capacity: number;
  meetings: Meeting[];
}
