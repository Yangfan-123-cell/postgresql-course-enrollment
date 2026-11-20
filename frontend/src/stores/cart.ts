import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import type { Meeting, Section } from "../api/types";
import { useAuth } from "./auth";

/** 选课单（意向课程）只保存在本机浏览器，不提交服务端、不占用名额。 */
export interface CartItem {
  section_id: number;
  code: string;
  name: string;
  credits: number;
  dept: string;
  teacher: string;
  term: string;
  meetings: Meeting[];
  added_at: string;
}

export const useCart = defineStore("cart", () => {
  const auth = useAuth();
  const items = ref<CartItem[]>([]);
  const key = computed(
    () => `course-cart:${auth.user?.student_no ?? "anonymous"}`,
  );
  watch(
    key,
    (k) => {
      try {
        items.value = JSON.parse(localStorage.getItem(k) || "[]");
      } catch {
        items.value = [];
      }
    },
    { immediate: true },
  );
  function persist() {
    localStorage.setItem(key.value, JSON.stringify(items.value));
  }
  const credits = computed(() =>
    items.value.reduce((sum, i) => sum + i.credits, 0),
  );
  function has(id: number) {
    return items.value.some((i) => i.section_id === id);
  }
  function add(s: Section) {
    if (has(s.id)) return;
    items.value = [
      ...items.value,
      {
        section_id: s.id,
        code: s.course.code,
        name: s.course.name,
        credits: s.course.credits,
        dept: s.course.dept,
        teacher: s.teacher,
        term: s.term,
        meetings: s.meetings.map((m) => ({ ...m })),
        added_at: new Date().toISOString(),
      },
    ];
    persist();
  }
  function remove(id: number) {
    items.value = items.value.filter((i) => i.section_id !== id);
    persist();
  }
  function toggle(s: Section) {
    if (has(s.id)) remove(s.id);
    else add(s);
  }
  return { items, credits, has, add, remove, toggle };
});
