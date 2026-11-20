import axios from "axios";

export const TOKEN_KEY = "course-enrollment-token";
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: 15000,
});
http.interceptors.request.use((config) => {
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.endsWith("/auth/login")
    ) {
      sessionStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event("auth-expired"));
    }
    return Promise.reject(error);
  },
);
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data?.error;
    const conflicts = body?.details?.conflicts as
      | {
          with_course_name: string;
          weekday: number;
          start_period: number;
          end_period: number;
        }[]
      | undefined;
    if (conflicts?.length)
      return `${body.message}（${conflicts.map((c) => `${c.with_course_name}，周${c.weekday} ${c.start_period}–${c.end_period} 节`).join("；")}）`;
    return (
      body?.message ||
      (error.response
        ? `请求失败（${error.response.status}），请稍后重试`
        : "无法连接服务，请检查后端连接后重试")
    );
  }
  return error instanceof Error ? error.message : "操作失败，请重试";
}
