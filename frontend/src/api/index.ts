import { http } from "./client";
import type {
  User,
  Page,
  Section,
  Enrollment,
  Waitlist,
  Timetable,
  EnrollmentResult,
  Course,
  CourseInput,
  SectionInput,
  Roster,
} from "./types";
export interface BrowseQuery {
  term: string;
  keyword?: string;
  dept_id?: number;
  only_open?: boolean;
  page: number;
  size: number;
}
export const api = {
  login: async (student_no: string, password: string) =>
    (
      await http.post<{ access_token: string; user: User }>("/auth/login", {
        student_no,
        password,
      })
    ).data,
  me: async () => (await http.get<User>("/auth/me")).data,
  sections: async (params: BrowseQuery) =>
    (
      await http.get<Page<Section>>("/sections", {
        params: {
          ...params,
          dept_id:
            Number(params.dept_id) > 0 ? Number(params.dept_id) : undefined,
        },
      })
    ).data,
  section: async (id: number) =>
    (await http.get<Section>(`/sections/${id}`)).data,
  enroll: async (section_id: number, allow_waitlist: boolean) =>
    (
      await http.post<EnrollmentResult>("/enrollments", {
        section_id,
        allow_waitlist,
      })
    ).data,
  drop: async (id: number) => {
    await http.delete(`/enrollments/${id}`);
  },
  enrollments: async () =>
    (await http.get<Page<Enrollment>>("/me/enrollments")).data,
  waitlist: async () => (await http.get<Page<Waitlist>>("/me/waitlist")).data,
  cancelWaitlist: async (id: number) => {
    await http.delete(`/waitlist/${id}`);
  },
  timetable: async () => (await http.get<Timetable>("/me/timetable")).data,
  courses: async (params: Record<string, unknown>) =>
    (await http.get<Page<Course>>("/admin/courses", { params })).data,
  saveCourse: async (data: Partial<CourseInput>, id?: number) =>
    id
      ? (await http.patch<Course>(`/admin/courses/${id}`, data)).data
      : (await http.post<Course>("/admin/courses", data)).data,
  adminSections: async (params: Record<string, unknown>) =>
    (await http.get<Page<Section>>("/admin/sections", { params })).data,
  saveSection: async (
    data:
      SectionInput | Pick<SectionInput, "teacher" | "capacity" | "meetings">,
    id?: number,
  ) =>
    id
      ? (await http.patch<Section>(`/admin/sections/${id}`, data)).data
      : (await http.post<Section>("/admin/sections", data)).data,
  roster: async (id: number, page: number) =>
    (
      await http.get<Page<Roster>>(`/admin/sections/${id}/roster`, {
        params: { page, size: 20 },
      })
    ).data,
  exportRoster: async (id: number) => {
    const { data } = await http.get<Blob>(`/admin/sections/${id}/roster.csv`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(data);
    const link = document.createElement("a");
    link.href = url;
    link.download = `section_${id}_roster.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
  selection: async (open: boolean) =>
    (
      await http.post<{ selection_open: boolean }>(
        `/admin/selection/${open ? "open" : "close"}`,
      )
    ).data,
};
