import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "../stores/auth";
import { TOKEN_KEY } from "../api/client";

declare module "vue-router" {
  interface RouteMeta {
    role?: "student" | "admin";
    title?: string;
    section?: string;
  }
}

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: "/login",
      component: () => import("../views/LoginView.vue"),
      meta: { title: "登录" },
    },
    { path: "/", redirect: "/hall" },
    {
      path: "/hall",
      component: () => import("../views/HallView.vue"),
      meta: { role: "student", title: "选课大厅", section: "选课服务" },
    },
    {
      path: "/cart",
      component: () => import("../views/CartView.vue"),
      meta: { role: "student", title: "选课单", section: "选课服务" },
    },
    {
      path: "/sections/:id",
      component: () => import("../views/DetailView.vue"),
      meta: { role: "student", title: "课程详情", section: "选课服务" },
    },
    {
      path: "/my-courses",
      component: () => import("../views/MyCoursesView.vue"),
      meta: { role: "student", title: "我的课程", section: "我的学业" },
    },
    {
      path: "/waitlist",
      component: () => import("../views/WaitlistView.vue"),
      meta: { role: "student", title: "候补队列", section: "选课服务" },
    },
    {
      path: "/timetable",
      component: () => import("../views/TimetableView.vue"),
      meta: { role: "student", title: "每周课表", section: "我的学业" },
    },
    {
      path: "/overview",
      component: () => import("../views/OverviewView.vue"),
      meta: { role: "student", title: "学业概览", section: "我的学业" },
    },
    {
      path: "/admin",
      component: () => import("../views/AdminView.vue"),
      meta: { role: "admin", title: "课程与教学班管理", section: "教务管理" },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});
router.beforeEach(async (to) => {
  const auth = useAuth();
  if (!sessionStorage.getItem(TOKEN_KEY))
    return to.path === "/login" ? true : "/login";
  try {
    await auth.restore();
  } catch {
    auth.logout();
    return to.path === "/login" ? true : "/login";
  }
  const home = auth.user?.role === "admin" ? "/admin" : "/hall";
  if (
    to.path === "/login" ||
    (to.meta.role && to.meta.role !== auth.user?.role)
  )
    return home;
});
router.afterEach((to) => {
  document.title = `${to.meta.title ? `${to.meta.title} · ` : ""}课序选课系统`;
});
