import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "../stores/auth";
import { TOKEN_KEY } from "../api/client";
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("../views/LoginView.vue") },
    { path: "/", redirect: "/hall" },
    {
      path: "/hall",
      component: () => import("../views/HallView.vue"),
      meta: { role: "student" },
    },
    {
      path: "/sections/:id",
      component: () => import("../views/DetailView.vue"),
      meta: { role: "student" },
    },
    {
      path: "/my-courses",
      component: () => import("../views/MyCoursesView.vue"),
      meta: { role: "student" },
    },
    {
      path: "/waitlist",
      component: () => import("../views/WaitlistView.vue"),
      meta: { role: "student" },
    },
    {
      path: "/timetable",
      component: () => import("../views/TimetableView.vue"),
      meta: { role: "student" },
    },
    {
      path: "/admin",
      component: () => import("../views/AdminView.vue"),
      meta: { role: "admin" },
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
